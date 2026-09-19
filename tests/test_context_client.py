from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from wrench_harness import ContextLedger, execute_local_qwen


def test_local_client_sends_bounded_retrieved_context(tmp_path: Path):
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    expected = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'
    captured: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers["Content-Length"])
            captured.append(json.loads(self.rfile.read(length)))
            payload = {"model": "test-qwen", "choices": [{"message": {"content": expected}}]}
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format, *args):
            return

    ledger = ContextLedger(max_logical_tokens=2_000_000)
    ledger.add_segment("call", "health deployment status", 1, token_count=4, kind="tool_call", unit_id="u1")
    ledger.add_segment("result", "service status 200", 2, token_count=4, kind="tool_result", unit_id="u1")
    ledger.add_segment("old", "unrelated historical context", 3, token_count=4)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        result = execute_local_qwen(
            endpoint,
            "test-qwen",
            [
                {"role": "system", "content": "Output one proposal."},
                {"role": "user", "content": "old full conversation that must not be forwarded"},
                {"role": "user", "content": "Read README.md."},
            ],
            str(tmp_path),
            capture_trace=True,
            context_ledger=ledger,
            context_query="health deployment",
            active_context_token_budget=8,
            preserve_context_ids=("call",),
        )
        assert result["status"] == "accepted"
        assert result["context_receipt"]["selected_token_count"] == 8
        assert result["context_receipt"]["recent_intent"]["intent"] == "Read README.md."
        assert result["context_receipt"]["recent_intent"]["source_message_index"] == 2
        assert result["request_parameters"]["context_message_count"] == 3
        forwarded = captured[0]["messages"]
        assert len(forwarded) == 3
        assert forwarded[0]["role"] == "system"
        assert "health deployment status" in forwarded[1]["content"]
        assert "old full conversation" not in json.dumps(forwarded)
        assert forwarded[-1]["content"] == "Read README.md."
    finally:
        server.shutdown()
        thread.join(timeout=2)
