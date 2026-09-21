from __future__ import annotations

import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from wrench_harness.server import WrenchHTTPServer
import wrench_harness.server as server_module
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
        assert body["wrench"]["context_gate"]["stage"] == "mechanical_fast_pruner_cherrypicker"
        assert body["wrench"]["context_gate"]["raw_payload_hash_bound"] is True
        assert body["usage"]["prompt_tokens"] > 0
        accounting = body["wrench"]["cost_accounting"]
        assert accounting["schema"] == "wrench.cost-accounting-receipt.v1"
        assert accounting["raw_input_tokens"] == body["usage"]["prompt_tokens"]
        assert accounting["model_prompt_tokens"] == 0
        assert accounting["local_model_tokens"] == 0
        assert accounting["input_tokens_not_sent_to_model"] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_can_force_model_only_diagnostic(tmp_path: Path):
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-model-only-test",
        max_request_bytes=4 * 1024 * 1024,
        use_mechanical_route=False,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "model": "wrench-model-only-test",
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
        assert body["wrench"]["fallback_reason"] == "model_not_loaded"
        assert body["wrench"]["mechanical_fast_path"] is False
        assert body["wrench"]["backend"] != "embedded-mechanical"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_streams_embedded_read_as_openai_sse(tmp_path: Path):
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
            "stream": True,
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
        events = [line[6:] for line in body.splitlines() if line.startswith("data: ")]
        assert events[-1] == "[DONE]"
        chunks = [json.loads(item) for item in events[:-1]]
        assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"
        content = "".join(
            chunk["choices"][0]["delta"].get("content", "")
            for chunk in chunks
        )
        assert content.startswith('{"schema":"wrench.proposal.v1"')
        assert chunks[-1]["choices"][0]["finish_reason"] == "stop"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_streams_anthropic_read_tool_use(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Wrench SLM\n", encoding="utf-8")
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
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
            "tools": [
                {
                    "name": "Read",
                    "input_schema": {
                        "type": "object",
                        "properties": {"file_path": {"type": "string"}, "max_bytes": {"type": "integer"}},
                        "required": ["file_path"],
                    },
                }
            ],
            "stream": True,
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
        assert "event: message_start" in body
        assert "event: content_block_start" in body
        assert '"type": "tool_use"' in body
        assert '"name": "Read"' in body
        data_events = [
            json.loads(line[6:])
            for line in body.splitlines()
            if line.startswith("data: ")
        ]
        input_delta = next(
            event["delta"]["partial_json"]
            for event in data_events
            if event.get("type") == "content_block_delta"
        )
        assert json.loads(input_delta) == {"file_path": "README.md", "max_bytes": 4096}
        assert "event: message_stop" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_bridges_one_read_tool_and_settles_result(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Wrench SLM\n", encoding="utf-8")
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    tool = {
        "type": "function",
        "function": {
            "name": "read",
            "parameters": {
                "type": "object",
                "properties": {
                    "filePath": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["filePath"],
            },
        },
    }

    def post(payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        first = post(
            {
                "model": "wrench-test",
                "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
                "tools": [tool],
                "stream": False,
            }
        )
        first_choice = first["choices"][0]
        first_message = first_choice["message"]
        assert first_choice["finish_reason"] == "tool_calls"
        assert first_message["tool_calls"][0]["function"]["name"] == "read"
        arguments = json.loads(first_message["tool_calls"][0]["function"]["arguments"])
        assert arguments == {"filePath": "README.md", "limit": 1}
        assert first["wrench"]["model_calls"] == 0

        second = post(
            {
                "model": "wrench-test",
                "messages": [
                    {"role": "user", "content": "Read README.md with a 4096 byte limit."},
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": first_message["tool_calls"],
                    },
                    {
                        "role": "tool",
                        "tool_call_id": first_message["tool_calls"][0]["id"],
                        "content": "# Wrench SLM\n",
                    },
                ],
                "tools": [tool],
                "stream": False,
            }
        )
        second_choice = second["choices"][0]
        second_message = second_choice["message"]
        assert second_choice["finish_reason"] == "stop"
        assert "# Wrench SLM" in second_message["content"]
        assert "tool_calls" not in second_message
        assert second["wrench"]["backend"] == "embedded-mechanical-settlement"
        assert second["wrench"]["model_calls"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_supports_anthropic_messages_tool_use_and_settlement(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Wrench SLM\n", encoding="utf-8")
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    tool = {
        "name": "Read",
        "description": "Read a file",
        "input_schema": {
            "type": "object",
            "properties": {"file_path": {"type": "string"}, "max_bytes": {"type": "integer"}},
            "required": ["file_path"],
        },
    }

    def post(payload: dict[str, object]) -> dict[str, object]:
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        first = post(
            {
                "model": "wrench-test",
                "max_tokens": 64,
                "system": "Use read-only tools.",
                "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
                "tools": [tool],
                "stream": False,
            }
        )
        assert first["type"] == "message"
        assert first["stop_reason"] == "tool_use"
        tool_use = first["content"][0]
        assert tool_use["type"] == "tool_use"
        assert tool_use["name"] == "Read"
        assert tool_use["input"] == {"file_path": "README.md", "max_bytes": 4096}

        second = post(
            {
                "model": "wrench-test",
                "max_tokens": 64,
                "messages": [
                    {"role": "user", "content": "Read README.md with a 4096 byte limit."},
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_use["id"],
                                "name": "Read",
                                "input": tool_use["input"],
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use["id"],
                                "content": "# Wrench SLM\n",
                            }
                        ],
                    },
                ],
                "tools": [tool],
                "stream": False,
            }
        )
        assert second["stop_reason"] == "end_turn"
        assert "# Wrench SLM" in second["content"][0]["text"]
        assert second["wrench"]["backend"] == "embedded-mechanical-settlement"
        assert second["wrench"]["model_calls"] == 0
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
        heartbeat = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/",
            method="HEAD",
        )
        with urllib.request.urlopen(heartbeat, timeout=5) as response:
            assert response.status == 200

        for path in ("/api/version", "/api/tags", "/api/show"):
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
            if path == "/api/version":
                assert body["version"] == "0.32.13"
                assert body["wrench_api"] == "ollama-compatible"
            elif path == "/api/tags":
                assert body["models"][0]["name"] == "wrench-test"
                assert body["models"][0]["digest"].startswith("sha256:")
                assert body["models"][0]["details"]["families"] == ["wrench"]
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
            assert body["wrench"]["context_gate"]["effective_working_context_tokens"] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_rejects_context_above_declared_4m_limit(tmp_path: Path):
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
            "options": {"num_ctx": 4_000_001},
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 400
            body = json.loads(exc.read().decode("utf-8"))
            assert body["error"]["message"] == "options.num_ctx_exceeds_4000000_token_limit"
        else:
            raise AssertionError("expected HTTP 400")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_model_local_server_verifies_native_upstream_before_returning(tmp_path: Path):
    (tmp_path / "README.md").write_text("native upstream fixture\n", encoding="utf-8")
    captured: dict[str, object] = {}

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            captured["request"] = request
            assert request["stream"] is False
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
                    "usage": {"prompt_tokens": 123456, "completion_tokens": 2},
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
        upstream_url=f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "model": "wrench-test",
            "messages": [{"role": "user", "content": "Inspect the repository state."}],
            "stream": False,
            "options": {"num_ctx": 4_000_000},
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
        assert body["message"]["content"].startswith('{"schema": "wrench.proposal.v1"')
        assert body["wrench"]["backend"] == "native-upstream-verified"
        assert body["wrench"]["status"] == "accepted"
        assert body["wrench"]["ttc"]["passed"] is True
        assert body["wrench"]["model_calls"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_native_upstream_receives_staged_prefill_for_monster_payload(
    tmp_path: Path, monkeypatch
):
    (tmp_path / "README.md").write_text("native upstream fixture\n", encoding="utf-8")
    captured: dict[str, object] = {}
    verified_prompt_lengths: list[int] = []
    original_execute_model_output = server_module.execute_model_output

    def capture_verifier_prompt(output, allowed_root, *, request_prompt=None):
        verified_prompt_lengths.append(len(request_prompt or ""))
        return original_execute_model_output(
            output,
            allowed_root,
            request_prompt=request_prompt,
        )

    monkeypatch.setattr(server_module, "execute_model_output", capture_verifier_prompt)

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            captured["request"] = request
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
                    ]
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
        upstream_url=f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        legacy = "old reference deployment logs and unrelated history. " * 20_000
        payload = {
            "model": "wrench-test",
            "messages": [
                {"role": "user", "content": legacy},
                {
                    "role": "user",
                    "content": "Inspect the repository state and return the bounded proposal.",
                },
            ],
            "stream": False,
            "options": {"num_ctx": 4_000_000},
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
        upstream_request = captured["request"]
        assert isinstance(upstream_request, dict)
        staged_messages = upstream_request["messages"]
        assert isinstance(staged_messages, list)
        staged_tokens = sum(
            max(1, item["content"].count(" ") + item["content"].count("\n") + 1)
            for item in staged_messages
        )
        assert staged_tokens <= 64_000
        assert "Inspect the repository state" in staged_messages[-1]["content"]
        assert body["wrench"]["dynamic_prefill"]["mode"] == "staged_single_pass"
        assert body["wrench"]["dynamic_prefill"]["raw_token_count"] > staged_tokens
        assert body["wrench"]["dynamic_prefill"]["native_input_claim"] is False
        assert body["wrench"]["dynamic_prefill"]["server_staging_elapsed_ms"] >= 0
        assert verified_prompt_lengths
        assert verified_prompt_lengths[0] <= 16_000
        assert verified_prompt_lengths[0] < len(legacy)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_native_direct_mode_forwards_raw_messages_and_binds_receipt(tmp_path: Path, monkeypatch):
    (tmp_path / "README.md").write_text("native direct fixture\n", encoding="utf-8")
    captured: dict[str, object] = {}

    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            captured["request"] = request
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
                    "usage": {"prompt_tokens": 123456, "completion_tokens": 2},
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    monkeypatch.setenv("WRENCH_NATIVE_DIRECT_INPUT", "1")
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
        upstream_url=f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "model": "wrench-test",
            "messages": [
                {
                    "role": "user",
                    "content": "stale reference record " * 20_000
                    + " CURRENT INTENT: inspect the active repository state.",
                }
            ],
            "stream": False,
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read().decode("utf-8"))
        upstream_request = captured["request"]
        assert isinstance(upstream_request, dict)
        assert len(upstream_request["messages"][0]["content"]) > 300_000
        receipt = body["wrench"]["dynamic_prefill"]
        assert receipt["mode"] == "native_direct_input"
        assert receipt["native_input_claim"] is True
        assert receipt["model_prefill_token_count"] == receipt["raw_token_count"]
        assert receipt["native_backend_prompt_tokens"] == 123456
        assert receipt["native_backend_usage_available"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_model_local_server_maps_native_timeout_to_504(tmp_path: Path, monkeypatch):
    def timed_out(*args, **kwargs):
        raise TimeoutError("native prefill deadline")

    monkeypatch.setattr(server_module, "_forward_upstream", timed_out)
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-test",
        max_request_bytes=4 * 1024 * 1024,
        upstream_url="http://127.0.0.1:1/v1/chat/completions",
        upstream_timeout_seconds=9,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        payload = {
            "model": "wrench-test",
            "messages": [{"role": "user", "content": "Draft a complex multi-file change."}],
            "max_tokens": 64,
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 504
            body = json.loads(exc.read().decode("utf-8"))
            assert body["error"]["type"] == "upstream_timeout"
        else:
            raise AssertionError("expected HTTP 504")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
