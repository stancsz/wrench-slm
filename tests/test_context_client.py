from __future__ import annotations

import json
import hashlib
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
            raw_body = self.rfile.read(length)
            captured.append(json.loads(raw_body))
            payload = {
                "model": "test-qwen",
                "choices": [{"message": {"content": expected}}],
                "wrench": {
                    "request_id": "fixture-request-1",
                    "client_workflow_id": self.headers["X-Wrench-Workflow-ID"],
                    "client_attempt": int(self.headers["X-Wrench-Client-Attempt"]),
                    "request_body_sha256": hashlib.sha256(raw_body).hexdigest(),
                },
            }
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Wrench-Request-ID", "fixture-request-1")
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
            mechanical_fast_path=False,
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


def test_local_client_fails_closed_on_response_correlation_mismatch(tmp_path: Path):
    (tmp_path / "README.md").write_text("must not be returned\n", encoding="utf-8")
    expected = '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'

    for mismatch in (
        "workflow",
        "attempt",
        "request_id",
        "body_hash",
        "request_id_header",
        "cost_request_id",
        "model",
    ):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers["Content-Length"])
                raw_body = self.rfile.read(length)
                wrench = {
                    "request_id": "fixture-request-1",
                    "client_workflow_id": self.headers["X-Wrench-Workflow-ID"],
                    "client_attempt": int(self.headers["X-Wrench-Client-Attempt"]),
                    "request_body_sha256": hashlib.sha256(raw_body).hexdigest(),
                    "cost_accounting": {
                        "request_id": "fixture-request-1",
                        "token_usage_complete": True,
                        "local_model_tokens": 1,
                        "frontier_tokens": 2,
                        "total_workflow_tokens": 3,
                        "local_model_calls": 1,
                        "frontier_model_calls": 0,
                    },
                }
                if mismatch == "workflow":
                    wrench["client_workflow_id"] = "wrong-workflow"
                elif mismatch == "attempt":
                    wrench["client_attempt"] = 2
                elif mismatch == "request_id":
                    wrench["request_id"] = ""
                elif mismatch == "body_hash":
                    wrench["request_body_sha256"] = "0" * 64
                elif mismatch == "cost_request_id":
                    wrench["cost_accounting"]["request_id"] = "wrong-cost-request"
                model = "wrong-qwen" if mismatch == "model" else "test-qwen"
                header_request_id = (
                    "header-request-differs"
                    if mismatch == "request_id_header"
                    else wrench["request_id"]
                )
                encoded = json.dumps(
                    {
                        "model": model,
                        "choices": [{"message": {"content": expected}}],
                        "wrench": wrench,
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Wrench-Request-ID", header_request_id)
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        ledger = ContextLedger(max_logical_tokens=100)
        ledger.add_segment("context", "verified historical context", 1, token_count=3)
        try:
            result = execute_local_qwen(
                f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                "test-qwen",
                [{"role": "user", "content": "Read README.md."}],
                str(tmp_path),
                mechanical_fast_path=False,
                context_ledger=ledger,
                active_context_token_budget=3,
            )
            assert result["status"] == "abstain"
            expected_reason = (
                "qwen_response_identity_invalid"
                if mismatch == "model"
                else "qwen_response_correlation_invalid"
            )
            assert result["fallback_reason"] == expected_reason
            assert "observation" not in result
            assert result["context_receipt"]["session_hash"] == ledger.session_hash()
            accounting = result["client_retry_accounting"]
            assert accounting["accounting_complete"] is False
            assert accounting["accounted_attempt_count"] == 0
            assert accounting["local_model_tokens"] is None
            assert accounting["frontier_tokens"] is None
        finally:
            server.shutdown()
            thread.join(timeout=2)


def test_local_client_retains_context_receipt_on_mechanical_abstention(tmp_path: Path):
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("context", "historical request context", 1, token_count=3)

    result = execute_local_qwen(
        "http://127.0.0.1:1/v1/chat/completions",
        "test-qwen",
        [{"role": "user", "content": "Read a missing file safely."}],
        str(tmp_path),
        context_ledger=ledger,
        active_context_token_budget=3,
        mechanical_fast_path=True,
    )

    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "missing_path"
    assert result["mechanical_fast_path"] is True
    assert result["context_receipt"]["session_hash"] == ledger.session_hash()


def test_local_client_retains_context_receipt_on_prefill_abstention(tmp_path: Path):
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("context", "historical request context", 1, token_count=3)

    result = execute_local_qwen(
        "http://127.0.0.1:1/v1/chat/completions",
        "test-qwen",
        [{"role": "user", "content": "Read README.md."}],
        str(tmp_path),
        context_ledger=ledger,
        active_context_token_budget=3,
        dynamic_prefill=True,
        dynamic_prefill_budget=0,
        mechanical_fast_path=False,
    )

    assert result["status"] == "abstain"
    assert result["fallback_reason"] == "qwen_dynamic_prefill_invalid"
    assert result["context_receipt"]["session_hash"] == ledger.session_hash()
