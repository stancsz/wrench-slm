"""Small model-local OpenAI-compatible server for the portable Wrench package.

The server is part of the downloaded model directory. It accepts the complete
raw request before the worker chooses a mechanical fast path or stages a
bounded model prefill. It is intentionally narrow and never executes tools.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .worker import WrenchWorker


def _estimated_tokens(value: str) -> int:
    return max(1, value.count(" ") + value.count("\n") + 1)


def _request_token_estimate(messages: list[dict[str, Any]]) -> tuple[int, int]:
    raw_chars = 0
    raw_tokens = 0
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            raw_chars += len(content)
            raw_tokens += _estimated_tokens(content)
    return raw_chars, raw_tokens


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
            "dynamic_prefill": result.get("dynamic_prefill"),
            "fallback_reason": result.get("fallback_reason"),
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
        "dynamic_prefill": result.get("dynamic_prefill"),
        "fallback_reason": result.get("fallback_reason"),
        "declared_context_tokens": declared_context_tokens,
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


class WrenchRequestHandler(BaseHTTPRequestHandler):
    server_version = "WrenchModelServer/1.0"

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
            raw_chars, raw_tokens = _request_token_estimate(messages)
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
    ) -> None:
        super().__init__(address, WrenchRequestHandler)
        self.worker = worker
        self.model_name = model_name
        self.max_request_bytes = max_request_bytes
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
) -> None:
    worker = WrenchWorker.from_pretrained(
        model_dir,
        allowed_root=allowed_root,
        load_model=load_model,
    )
    server = WrenchHTTPServer(
        (host, port),
        worker,
        model_name=model_name,
        max_request_bytes=max_request_bytes,
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
    args = parser.parse_args()
    serve(
        args.model_dir.resolve(),
        host=args.host,
        port=args.port,
        allowed_root=args.allowed_root.resolve(),
        model_name=args.model_name,
        load_model=not args.mechanical_only,
        max_request_bytes=args.max_request_bytes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
