"""Small model-local OpenAI-compatible server for the portable Wrench package.

The server is part of the downloaded model directory. It accepts the complete
raw request before the worker chooses a mechanical fast path or stages a
bounded model prefill. It is intentionally narrow and never executes tools.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import request as urllib_request

from .core import execute_model_output
from .mechanical import active_intent_suffix
from .prefill import _estimate_token_count, ordered_payload_sha256
from .ttc import enforce_ttc
from .worker import WrenchWorker, _dynamic_prefill_messages


def _estimated_tokens(value: str) -> int:
    return _estimate_token_count(value)


def _request_token_estimate(messages: list[dict[str, Any]]) -> tuple[int, int, str | None]:
    raw_chars = 0
    raw_tokens = 0
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            raw_chars += len(content)
            raw_tokens += _estimated_tokens(content)
    payload_sha256 = None
    if all(
        isinstance(message, dict)
        and isinstance(message.get("role"), str)
        and isinstance(message.get("content"), str)
        for message in messages
    ):
        payload_sha256 = ordered_payload_sha256(messages)  # type: ignore[arg-type]
    return raw_chars, raw_tokens, payload_sha256


def _cost_accounting_receipt(
    result: dict[str, Any],
    *,
    raw_tokens: int,
    completion_tokens: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    """Expose token-flow facts without pretending they are dollar costs."""

    model_calls = result.get("model_calls", 0)
    model_calls = model_calls if isinstance(model_calls, int) and model_calls >= 0 else 0
    dynamic_prefill = result.get("dynamic_prefill")
    model_prompt_tokens = 0
    if model_calls:
        if isinstance(dynamic_prefill, dict):
            native_prompt = dynamic_prefill.get("native_backend_prompt_tokens")
            staged_prompt = dynamic_prefill.get("model_prefill_token_count")
            if isinstance(native_prompt, int) and native_prompt >= 0:
                model_prompt_tokens = native_prompt
            elif isinstance(staged_prompt, int) and staged_prompt >= 0:
                model_prompt_tokens = staged_prompt
        if model_prompt_tokens == 0:
            model_prompt_tokens = raw_tokens
    model_completion_tokens = completion_tokens if model_calls else 0
    return {
        "schema": "wrench.cost-accounting-receipt.v1",
        "raw_input_tokens": raw_tokens,
        "model_prompt_tokens": model_prompt_tokens,
        "model_completion_tokens": model_completion_tokens,
        "local_model_tokens": model_prompt_tokens + model_completion_tokens,
        "input_tokens_not_sent_to_model": max(0, raw_tokens - model_prompt_tokens),
        "model_calls": model_calls,
        "repair_passes": result.get("repair_pass_count", 0),
        "mechanical_fast_path": bool(result.get("mechanical_fast_path", False)),
        "total_local_elapsed_ms": round(elapsed_ms, 3),
        "usd_cost": None,
        "usd_cost_status": "not_priced_local_runtime",
    }


def _completion_response(
    result: dict[str, Any],
    *,
    model_name: str,
    raw_chars: int,
    raw_tokens: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    content = result.get("raw_model_output")
    if not isinstance(content, str):
        content = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    completion_tokens = _estimated_tokens(content)
    response: dict[str, Any] = {
        "id": f"wrench-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": raw_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": raw_tokens + completion_tokens,
        },
        "wrench": {
            "raw_input_chars": raw_chars,
            "raw_input_tokens_estimate": raw_tokens,
            "elapsed_ms": round(elapsed_ms, 3),
            "status": result.get("status"),
            "backend": result.get("backend"),
            "mechanical_fast_path": result.get("mechanical_fast_path", False),
            "model_calls": result.get("model_calls", 0),
            "context_gate": result.get("context_gate"),
            "dynamic_prefill": result.get("dynamic_prefill"),
            "fallback_reason": result.get("fallback_reason"),
            "ttc": result.get("ttc"),
            "cost_accounting": _cost_accounting_receipt(
                result,
                raw_tokens=raw_tokens,
                completion_tokens=completion_tokens,
                elapsed_ms=elapsed_ms,
            ),
        },
    }
    return response


def _ollama_response(
    result: dict[str, Any],
    *,
    model_name: str,
    raw_chars: int,
    raw_tokens: int,
    elapsed_ms: float,
    chat: bool,
    declared_context_tokens: int | None,
) -> dict[str, Any]:
    """Return the small Ollama-compatible response shape used by local clients.

    This is an API compatibility layer inside the package. It does not claim
    that the stock Ollama binary can load Wrench's hybrid checkpoint.
    """

    content = result.get("raw_model_output")
    if not isinstance(content, str):
        content = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    completion_tokens = _estimated_tokens(content)
    wrench = {
        "raw_input_chars": raw_chars,
        "raw_input_tokens_estimate": raw_tokens,
        "elapsed_ms": round(elapsed_ms, 3),
        "status": result.get("status"),
        "backend": result.get("backend"),
        "mechanical_fast_path": result.get("mechanical_fast_path", False),
        "model_calls": result.get("model_calls", 0),
        "context_gate": result.get("context_gate"),
        "dynamic_prefill": result.get("dynamic_prefill"),
        "fallback_reason": result.get("fallback_reason"),
        "ttc": result.get("ttc"),
        "declared_context_tokens": declared_context_tokens,
        "cost_accounting": _cost_accounting_receipt(
            result,
            raw_tokens=raw_tokens,
            completion_tokens=completion_tokens,
            elapsed_ms=elapsed_ms,
        ),
    }
    response: dict[str, Any] = {
        "model": model_name,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": raw_tokens,
        "eval_count": completion_tokens,
        "wrench": wrench,
    }
    if chat:
        response["message"] = {"role": "assistant", "content": content}
    else:
        response["response"] = content
    return response


def _upstream_payload(
    request: dict[str, Any],
    *,
    path: str,
    messages_override: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Translate package-local Ollama-shaped requests to OpenAI chat input."""

    if messages_override is not None:
        messages = messages_override
    elif path == "/api/generate":
        prompt = request.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        messages: list[dict[str, Any]] = []
        system = request.get("system")
        if isinstance(system, str) and system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
    else:
        messages = request.get("messages")
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
    options = request.get("options")
    max_tokens = request.get("max_tokens", 256)
    if isinstance(options, dict) and isinstance(options.get("num_predict"), int):
        max_tokens = options["num_predict"]
    return {
        "model": str(request.get("model") or "wrench-4b"),
        "messages": messages,
        "max_tokens": max_tokens,
        # The package owns the Ollama-shaped response, so the native backend
        # must return one complete candidate for local verification.
        "stream": False,
    }


def _forward_upstream(
    upstream_url: str,
    request: dict[str, Any],
    *,
    path: str,
    timeout_seconds: float,
    messages_override: list[dict[str, str]] | None = None,
    response_metadata: dict[str, Any] | None = None,
) -> str:
    """Ask the native backend for text, without giving it execution authority."""

    body = json.dumps(
        _upstream_payload(request, path=path, messages_override=messages_override),
        ensure_ascii=False,
    ).encode("utf-8")
    upstream_request = urllib_request.Request(
        upstream_url,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    with urllib_request.urlopen(upstream_request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if response_metadata is not None and isinstance(payload, dict):
        usage = payload.get("usage")
        if isinstance(usage, dict):
            response_metadata["usage"] = usage
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict) and isinstance(message.get("content"), str):
            return message["content"]
        if isinstance(choices[0].get("text"), str):
            return choices[0]["text"]
    raise ValueError("native_backend_response_missing_text")


def _latest_user_prompt(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user" and isinstance(message.get("content"), str):
            return message["content"]
    return ""


def _bounded_verification_prompt(messages: list[dict[str, Any]]) -> str:
    """Keep verifier work proportional to active intent, not raw history.

    The raw payload is already hash-bound in the prefill receipt. Older
    material is reference-only, so semantic guards and TTC should inspect the
    same bounded current-intent suffix used by the mechanical router. Passing
    a 4M string into repeated ``lower()`` calls here would turn a fast staged
    handoff into a multi-second CPU scan.
    """

    prompt = _latest_user_prompt(messages)
    try:
        suffix_chars = int(os.environ.get("WRENCH_HISTORY_CONTROL_SUFFIX_CHARS", "16000"))
    except ValueError:
        suffix_chars = 16_000
    return active_intent_suffix(prompt, suffix_chars=max(1, suffix_chars))


def _native_direct_input_receipt(
    messages: list[dict[str, str]],
    raw_tokens: int,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    for message in messages:
        digest.update(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        digest.update(b"\n")
    return {
        "schema": "wrench.dynamic-prefill-receipt.v1",
        "mode": "native_direct_input",
        "raw_token_count": raw_tokens,
        "model_prefill_token_count": raw_tokens,
        "compression_ratio": 1.0,
        "native_input_claim": True,
        "native_direct_input": True,
        "source_payload_sha256": digest.hexdigest(),
        "payload_hash_mode": "ordered_message_json",
        "server_staging_elapsed_ms": 0.0,
    }


class WrenchRequestHandler(BaseHTTPRequestHandler):
    server_version = "WrenchModelServer/1.0"
    # A 4M logical request is commonly tens of megabytes on the wire. The
    # stdlib handler's small default buffered reader makes localhost uploads
    # needlessly syscall-bound before MapReduce can even start. Keep the
    # package-local endpoint responsive for monster payload intake without
    # changing the logical context contract.
    rbufsize = 1024 * 1024
    wbufsize = 1024 * 1024

    def _server(self) -> "WrenchHTTPServer":
        return self.server  # type: ignore[return-value]

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_ndjson(self, status: int, payload: dict[str, Any]) -> None:
        body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        server = self._server()
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "model": server.model_name})
            return
        if self.path == "/v1/models":
            self._send_json(
                200,
                {
                    "object": "list",
                    "data": [{"id": server.model_name, "object": "model", "owned_by": "wrench"}],
                },
            )
            return
        if self.path == "/api/tags":
            self._send_json(
                200,
                {
                    "models": [
                        {
                            "name": server.model_name,
                            "model": server.model_name,
                            "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "size": 0,
                            "details": {
                                "family": "wrench",
                                "parameter_size": "3.88B",
                                "quantization_level": "NVFP4-W4A16",
                            },
                        }
                    ]
                },
            )
            return
        if self.path == "/api/show":
            self._send_json(
                200,
                {
                    "name": server.model_name,
                    "details": {
                        "family": "wrench",
                        "parameter_size": "3.88B",
                        "context_length": 4_000_000,
                    },
                    "parameters": "num_ctx 4000000\ntemperature 0",
                    "wrench": {
                        "declared_input_context_tokens": 4_000_000,
                        "effective_working_context_tokens": 64_000,
                        "native_attention_context_tokens_verified": None,
                    },
                },
            )
            return
        self._send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})

    def do_POST(self) -> None:  # noqa: N802
        server = self._server()
        if self.path == "/api/show":
            self._send_json(
                200,
                {
                    "name": server.model_name,
                    "details": {
                        "family": "wrench",
                        "parameter_size": "3.88B",
                        "context_length": 4_000_000,
                    },
                    "parameters": "num_ctx 4000000\ntemperature 0",
                    "wrench": {
                        "declared_input_context_tokens": 4_000_000,
                        "effective_working_context_tokens": 64_000,
                        "native_attention_context_tokens_verified": None,
                    },
                },
            )
            return
        if self.path not in {"/v1/chat/completions", "/api/chat", "/api/generate"}:
            self._send_json(404, {"error": {"message": "not_found", "type": "invalid_request_error"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > server.max_request_bytes:
                raise ValueError("request_body_too_large_or_empty")
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/api/generate":
                prompt = request.get("prompt")
                if not isinstance(prompt, str):
                    raise ValueError("prompt must be a string")
                messages = []
                system = request.get("system")
                if isinstance(system, str) and system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
            else:
                messages = request.get("messages")
            if not isinstance(messages, list):
                raise ValueError("messages must be a list")
            model_name = str(request.get("model") or server.model_name)
            raw_chars, raw_tokens, raw_payload_sha256 = _request_token_estimate(messages)
            options = request.get("options")
            declared_context_tokens = None
            if isinstance(options, dict) and isinstance(options.get("num_ctx"), int):
                declared_context_tokens = options["num_ctx"]
            started = time.perf_counter()
            with server.worker_lock:
                result = server.worker.propose(
                    messages,
                    max_tokens=int(request.get("max_tokens", 256)),
                    use_mechanical_route=True,
                )
                if server.upstream_url and not result.get("mechanical_fast_path", False):
                    # The downloaded package accepts the complete raw request,
                    # but a native backend should only pay model compute for a
                    # deterministic hot set plus lookup cards. Preserve the
                    # original messages for verification and receipt hashing.
                    prefill_started = time.perf_counter()
                    if os.environ.get("WRENCH_NATIVE_DIRECT_INPUT", "0") == "1":
                        staged_messages = messages
                        prefill_receipt = _native_direct_input_receipt(messages, raw_tokens)
                    else:
                        staged_messages, prefill_receipt = _dynamic_prefill_messages(
                            messages,
                            mechanical_index=server.worker.prefill_index,
                            original_payload_sha256=raw_payload_sha256,
                        )
                        if prefill_receipt is not None:
                            prefill_receipt["server_staging_elapsed_ms"] = round(
                                (time.perf_counter() - prefill_started) * 1000,
                                3,
                            )
                            prefill_receipt["cache"] = server.worker.prefill_index.stats()
                    upstream_metadata: dict[str, Any] = {}
                    upstream_output = _forward_upstream(
                        server.upstream_url,
                        request,
                        path=self.path,
                        timeout_seconds=server.upstream_timeout_seconds,
                        messages_override=(
                            staged_messages if prefill_receipt is not None else None
                        ),
                        response_metadata=upstream_metadata,
                    )
                    verified = execute_model_output(
                        upstream_output,
                        server.worker.allowed_root,
                        request_prompt=_bounded_verification_prompt(messages),
                    )
                    if verified.get("status") == "accepted":
                        try:
                            upstream_proposal = json.loads(upstream_output)
                        except json.JSONDecodeError:
                            upstream_proposal = None
                        verified = enforce_ttc(
                            upstream_proposal,
                            _bounded_verification_prompt(messages),
                            verified,
                            context_pressure=prefill_receipt is not None,
                        )
                    verified.update(
                        {
                            "backend": "native-upstream-verified",
                            "mechanical_fast_path": False,
                            "raw_model_output": upstream_output,
                            "model_calls": 1,
                        }
                    )
                    if prefill_receipt is not None:
                        usage = upstream_metadata.get("usage")
                        if isinstance(usage, dict) and isinstance(usage.get("prompt_tokens"), int):
                            prefill_receipt["native_backend_prompt_tokens"] = usage["prompt_tokens"]
                            prefill_receipt["native_backend_usage_available"] = True
                        else:
                            prefill_receipt["native_backend_usage_available"] = False
                        verified["dynamic_prefill"] = prefill_receipt
                    result = verified
            elapsed_ms = (time.perf_counter() - started) * 1000
            if self.path == "/v1/chat/completions":
                response = _completion_response(
                    result,
                    model_name=model_name,
                    raw_chars=raw_chars,
                    raw_tokens=raw_tokens,
                    elapsed_ms=elapsed_ms,
                )
                self._send_json(200, response)
            else:
                response = _ollama_response(
                    result,
                    model_name=model_name,
                    raw_chars=raw_chars,
                    raw_tokens=raw_tokens,
                    elapsed_ms=elapsed_ms,
                    chat=self.path == "/api/chat",
                    declared_context_tokens=declared_context_tokens,
                )
                if bool(request.get("stream", False)):
                    self._send_ndjson(200, response)
                else:
                    self._send_json(200, response)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._send_json(
                400,
                {"error": {"message": str(exc), "type": "invalid_request_error"}},
            )
        except TimeoutError as exc:
            self._send_json(
                504,
                {"error": {"message": str(exc), "type": "upstream_timeout"}},
            )
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            # The client may enforce a shorter deadline than the native
            # backend. The worker request is already bounded by the upstream
            # timeout, and there is no response left to write to this socket.
            return
        except Exception as exc:  # pragma: no cover - defensive serving boundary
            self._send_json(
                500,
                {"error": {"message": str(exc), "type": "server_error"}},
            )

    def log_message(self, format: str, *args: Any) -> None:
        return


class WrenchHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        worker: WrenchWorker,
        *,
        model_name: str,
        max_request_bytes: int,
        upstream_url: str | None = None,
        upstream_timeout_seconds: float = 600.0,
    ) -> None:
        super().__init__(address, WrenchRequestHandler)
        self.worker = worker
        self.model_name = model_name
        self.max_request_bytes = max_request_bytes
        self.upstream_url = upstream_url
        self.upstream_timeout_seconds = upstream_timeout_seconds
        self.worker_lock = threading.Lock()


def serve(
    model_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 28900,
    allowed_root: Path = Path("."),
    model_name: str = "wrench-4b",
    load_model: bool = True,
    max_request_bytes: int = 256 * 1024 * 1024,
    upstream_url: str | None = None,
    upstream_timeout_seconds: float = 600.0,
    prefill_cache_bytes: int | None = None,
) -> None:
    worker = WrenchWorker.from_pretrained(
        model_dir,
        allowed_root=allowed_root,
        load_model=load_model,
        prefill_cache_bytes=prefill_cache_bytes,
    )
    server = WrenchHTTPServer(
        (host, port),
        worker,
        model_name=model_name,
        max_request_bytes=max_request_bytes,
        upstream_url=upstream_url,
        upstream_timeout_seconds=upstream_timeout_seconds,
    )
    print(json.dumps({"status": "READY", "host": host, "port": server.server_port, "model": model_name}))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bundled Wrench model endpoint")
    parser.add_argument("--model-dir", type=Path, default=Path("."))
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=28900)
    parser.add_argument("--model-name", default="wrench-4b")
    parser.add_argument("--mechanical-only", action="store_true")
    parser.add_argument("--max-request-bytes", type=int, default=256 * 1024 * 1024)
    parser.add_argument("--upstream-url", default=None)
    parser.add_argument("--upstream-timeout-seconds", type=float, default=600.0)
    parser.add_argument(
        "--prefill-cache-bytes",
        type=int,
        default=None,
        help="persistent content-addressed native prefill cache; defaults to WRENCH_PREFILL_CACHE_BYTES or 256 MiB",
    )
    args = parser.parse_args()
    serve(
        args.model_dir.resolve(),
        host=args.host,
        port=args.port,
        allowed_root=args.allowed_root.resolve(),
        model_name=args.model_name,
        load_model=not args.mechanical_only,
        max_request_bytes=args.max_request_bytes,
        upstream_url=args.upstream_url,
        upstream_timeout_seconds=args.upstream_timeout_seconds,
        prefill_cache_bytes=args.prefill_cache_bytes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
