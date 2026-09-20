#!/usr/bin/env python3
"""Exercise the package server's 4M raw-input to native-handoff path."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_payload(target_tokens: int) -> str:
    filler = "stale lookup telemetry record status observed unrelated historical reference-only data; "
    current = "CURRENT INTENT: inspect the active repository state and return one bounded proposal."
    filler_tokens = max(1, target_tokens - current.count(" ") - 64)
    return filler * ((filler_tokens + filler.count(" ") - 1) // filler.count(" ")) + current


def _token_estimate(value: str) -> int:
    return max(1, value.count(" ") + value.count("\n") + 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-tokens", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--package-dir",
        type=Path,
        help="load the bundled wrench_runtime from a materialized package",
    )
    parser.add_argument(
        "--surface",
        choices=("api-chat", "api-generate", "v1"),
        default="api-chat",
        help="HTTP surface to exercise; api-chat is the default Ollama-shaped path",
    )
    args = parser.parse_args()
    if args.payload_tokens < 1:
        raise SystemExit("--payload-tokens must be positive")

    if args.package_dir is not None:
        sys.path.insert(0, str(args.package_dir.resolve()))
        from wrench_runtime.server import WrenchHTTPServer
        from wrench_runtime.worker import WrenchWorker

        runtime_import = "bundled_package_runtime"
    else:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from wrench_harness.server import WrenchHTTPServer
        from wrench_harness.worker import WrenchWorker

        runtime_import = "source_runtime"

    captured: dict[str, object] = {}

    class NativeHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            captured["request"] = request
            prompt_tokens = sum(
                _token_estimate(message.get("content", ""))
                for message in request.get("messages", [])
                if isinstance(message, dict) and isinstance(message.get("content"), str)
            )
            body = json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "schema": "wrench.proposal.v1",
                                        "action": "read_file",
                                        "path": "README.md",
                                        "max_bytes": 4096,
                                    }
                                ),
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 2},
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    with tempfile.TemporaryDirectory(prefix="wrench-native-handoff-") as temp_dir:
        allowed_root = Path(temp_dir)
        (allowed_root / "README.md").write_text("handoff fixture\n", encoding="utf-8")
        native = ThreadingHTTPServer(("127.0.0.1", 0), NativeHandler)
        native_thread = threading.Thread(target=native.serve_forever, daemon=True)
        native_thread.start()
        server = WrenchHTTPServer(
            ("127.0.0.1", 0),
            WrenchWorker(tokenizer=None, model=None, allowed_root=allowed_root),
            model_name="wrench-test",
            max_request_bytes=64 * 1024 * 1024,
            upstream_url=f"http://127.0.0.1:{native.server_port}/v1/chat/completions",
            upstream_timeout_seconds=30,
        )
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        try:
            content = _build_payload(args.payload_tokens)
            if args.surface == "api-generate":
                payload = {
                    "model": "wrench-test",
                    "prompt": content,
                    "max_tokens": 64,
                    "stream": False,
                    "options": {"num_ctx": 4_000_000},
                }
            else:
                payload = {
                    "model": "wrench-test",
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": 64,
                    "stream": False,
                    "options": {"num_ctx": 4_000_000},
                }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            started = time.perf_counter()
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/"
                + {
                    "api-chat": "api/chat",
                    "api-generate": "api/generate",
                    "v1": "v1/chat/completions",
                }[args.surface],
                data=body,
                headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=5)
            native.shutdown()
            native.server_close()
            native_thread.join(timeout=5)

    upstream_request = captured.get("request")
    staged_messages = upstream_request.get("messages", []) if isinstance(upstream_request, dict) else []
    staged_tokens = sum(
        _token_estimate(message.get("content", ""))
        for message in staged_messages
        if isinstance(message, dict) and isinstance(message.get("content"), str)
    )
    wrench = response_body.get("wrench", {}) if isinstance(response_body, dict) else {}
    receipt = wrench.get("dynamic_prefill") if isinstance(wrench, dict) else None
    direct_mode = os.environ.get("WRENCH_NATIVE_DIRECT_INPUT", "0") == "1"
    direct_pass = (
        direct_mode
        and isinstance(receipt, dict)
        and receipt.get("mode") == "native_direct_input"
        and staged_tokens >= args.payload_tokens * 0.95
        and receipt.get("native_input_claim") is True
    )
    staged_pass = (
        not direct_mode
        and isinstance(receipt, dict)
        and receipt.get("mode") == "staged_single_pass"
        and staged_tokens <= 64_000
    )
    result = {
        "schema": "wrench.native-handoff-prefill-probe.v1",
        "status": (
            "PASS_NATIVE_DIRECT_RAW_4M"
            if direct_pass and wrench.get("backend") == "native-upstream-verified"
            else "PASS_NATIVE_HANDOFF_STAGED_4M"
            if staged_pass and wrench.get("backend") == "native-upstream-verified"
            else "FAIL"
        ),
        "mode": "native_direct_input" if direct_mode else "staged_single_pass",
        "surface": args.surface,
        "runtime_import": runtime_import,
        "package_dir": str(args.package_dir.resolve()) if args.package_dir is not None else None,
        "requested_payload_tokens": args.payload_tokens,
        "raw_payload_bytes": len(body),
        "raw_token_estimate": _token_estimate(content),
        "staged_token_estimate": staged_tokens,
        "elapsed_ms": elapsed_ms,
        "server_staging_elapsed_ms": (
            receipt.get("server_staging_elapsed_ms") if isinstance(receipt, dict) else None
        ),
        "model_calls": wrench.get("model_calls"),
        "backend": wrench.get("backend"),
        "dynamic_prefill": receipt,
        "native_attention_claim": False,
        "notes": [
            "The upstream is a local protocol stub, not a model-quality evaluation.",
            "This proves raw package intake, mode selection, and native handoff accounting, not dense native 4M attention.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "elapsed_ms": elapsed_ms, "staged_token_estimate": staged_tokens}))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
