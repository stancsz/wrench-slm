from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

from wrench_harness.server import WrenchHTTPServer
from wrench_harness.worker import WrenchWorker


def test_model_local_server_accepts_raw_payload_and_returns_openai_shape(tmp_path: Path):
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "model": "wrench-test",
            "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
            "max_tokens": 64,
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
        assert body["object"] == "chat.completion"
        assert body["choices"][0]["message"]["content"].startswith('{"schema":"wrench.proposal.v1"')
        assert body["wrench"]["backend"] == "embedded-mechanical"
        assert body["wrench"]["model_calls"] == 0
        assert body["usage"]["prompt_tokens"] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_exposes_ollama_compatible_routes(tmp_path: Path):
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path in ("/api/tags", "/api/show"):
            if path == "/api/show":
                request = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}{path}",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                response_context = urllib.request.urlopen(request, timeout=5)
            else:
                response_context = urllib.request.urlopen(
                    f"http://127.0.0.1:{server.server_port}{path}", timeout=5
                )
            with response_context as response:
                body = json.loads(response.read().decode("utf-8"))
            if path == "/api/tags":
                assert body["models"][0]["name"] == "wrench-test"
            else:
                assert body["details"]["context_length"] == 4_000_000

        for path, payload in (
            (
                "/api/chat",
                {
                    "model": "wrench-test",
                    "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
                    "stream": False,
                    "options": {"num_ctx": 4_000_000},
                },
            ),
            (
                "/api/generate",
                {
                    "model": "wrench-test",
                    "prompt": "Read README.md with a 4096 byte limit.",
                    "stream": False,
                },
            ),
        ):
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["message"]["content"] if path == "/api/chat" else body["response"]
            assert content.startswith('{"schema":"wrench.proposal.v1"')
            assert body["wrench"]["mechanical_fast_path"] is True
            assert body["wrench"]["model_calls"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
