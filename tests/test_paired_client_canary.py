import os
import json
import base64
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import ctypes
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import tools.probe_paired_real_client_canary as canary
import tools.windows_job_process as windows_job_process
from tools.probe_paired_real_client_canary import _baseline_clients_correct, _canary_process_exit_code, _classify_canary_status, _classify_request_purpose, _client_for_timestamp, _compare_client_latencies, _effective_baseline_api_key, _LoopbackAccountingProxy, _probe_loopback_spend_logs, _read_trace_jsonl, _trace_identity_accounting, _trace_token_accounting_complete, _usage_from_response, _validate_external_baseline_guard, load_workload


def _test_cost_accounting_binding():
    return {
        "schema": "wrench.provider-cost-accounting-binding.v1",
        "provider": "test-provider",
        "mode": "provider_request_rows",
        "export_endpoint": "https://provider.example/v1/costs",
        "export_path_reference": "test-only-export-path",
    }


def _write_synthetic_test_workload(tmp_path):
    """Create a local-only manifest for tests that exercise preflight guards."""
    workload_path = tmp_path / "synthetic-test-workload.json"
    workload_path.write_text(
        json.dumps({
            "schema": canary.WORKLOAD_SCHEMA,
            "workload_id": "synthetic-preflight-test-only",
            "authorization": "approved_real_workflow",
            "test_fixture_only": True,
            "cases": [{
                "case_id": "synthetic-preflight-case",
                "prompt": "Synthetic test prompt.",
                "expected_observation": "Synthetic expected observation.",
            }],
        }),
        encoding="utf-8",
    )
    return workload_path


def _test_parent_route_allowance(*, endpoint, alias, provider_model):
    return {
        "schema": canary.PARENT_ROUTE_ALLOWANCE_SCHEMA,
        "decision": "human.approve_commit",
        "status": "APPROVED",
        "approved_by": "test-human",
        "approval_reference": "test-only-route-approval",
        "routes": [
            {
                "endpoint": endpoint,
                "gateway_model_alias": alias,
                "expected_provider_model": provider_model,
            }
        ],
    }


def test_local_stub_tokens_cannot_be_reported_as_frontier_or_net_savings():
    accounting = canary._canary_token_accounting(
        baseline_url_configured=False,
        baseline_call_count=4,
        captured_frontier_tokens=None,
        hybrid_frontier_tokens=0,
    )
    assert accounting["baseline_frontier_tokens"] is None
    assert accounting["local_stub_synthetic_tokens_estimate"] == 2064
    assert accounting["diagnostic_raw_token_reduction_rate"] == 1.0
    assert accounting["frontier_token_reduction_rate"] is None
    assert accounting["net_frontier_token_savings_rate"] is None


def test_captured_gateway_tokens_remain_raw_diagnostic_without_net_overhead():
    accounting = canary._canary_token_accounting(
        baseline_url_configured=True,
        baseline_call_count=0,
        captured_frontier_tokens=400,
        hybrid_frontier_tokens=20,
    )
    assert accounting["baseline_frontier_tokens"] == 400
    assert accounting["local_stub_synthetic_tokens_estimate"] is None
    assert accounting["diagnostic_raw_token_reduction_rate"] == pytest.approx(0.95)
    assert accounting["frontier_token_reduction_rate"] is None
    assert accounting["net_frontier_token_savings_rate"] is None

    missing = canary._canary_token_accounting(
        baseline_url_configured=True,
        baseline_call_count=0,
        captured_frontier_tokens=None,
        hybrid_frontier_tokens=0,
    )
    assert missing["diagnostic_raw_token_reduction_rate"] is None


def test_request_purpose_uses_only_exact_source_markers_and_bounded_shape():
    opencode_title = {
        "messages": [
            {"role": "system", "content": "Generate a title for this conversation"},
            {"role": "user", "content": "PRIVATE_SESSION_TEXT"},
        ]
    }
    dsh_title = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Generate the session title from this JSON array of human messages:\n"
                    '[{"text":"PRIVATE_SESSION_TEXT"}]'
                ),
            }
        ]
    }
    near_match = {
        "messages": [
            {"role": "user", "content": "Generate a title for that conversation"}
        ]
    }
    quoted_marker = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Explain this phrase: Generate a title for this conversation"
                ),
            }
        ]
    }

    assert _classify_request_purpose(opencode_title) == (
        "session_title_auxiliary",
        "opencode_session_title_v1",
        "exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(dsh_title) == (
        "session_title_auxiliary",
        "dsh_session_title_v1",
        "exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(near_match) == (
        "unknown",
        None,
        "no_exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(quoted_marker) == (
        "unknown",
        None,
        "no_exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(
        {"messages": dsh_title["messages"], "tools": [{"type": "function"}]}
    ) == ("unknown", None, "request_shape_out_of_scope")


def test_opt_in_task_marker_requires_task_state_and_title_classification_wins():
    marker = "wrench-task-diagnostic-7f4c1e"
    proposal = {
        "messages": [{"role": "user", "content": f"Read README.md. {marker}"}],
        "tools": [{"type": "function", "function": {"name": "read_file"}}],
    }
    final = {
        "messages": [
            {"role": "user", "content": f"Read README.md. {marker}"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1"}]},
            {"role": "tool", "tool_call_id": "call-1", "content": "heading"},
        ]
    }
    title = {
        "messages": [
            {"role": "system", "content": "Generate a title for this conversation"},
            {"role": "user", "content": f"{marker}"},
        ]
    }
    marker_id = f"task_marker_sha256:{canary.hashlib.sha256(marker.encode()).hexdigest()}"

    assert _classify_request_purpose(proposal, task_marker=marker) == (
        "primary_task_workflow",
        marker_id,
        "opt_in_task_marker_and_task_state",
    )
    assert _classify_request_purpose(final, task_marker=marker) == (
        "primary_task_workflow",
        marker_id,
        "opt_in_task_marker_and_task_state",
    )
    assert _classify_request_purpose(title, task_marker=marker) == (
        "session_title_auxiliary",
        "opencode_session_title_v1",
        "exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(
        {"messages": [{"role": "user", "content": marker}]}, task_marker=marker
    )[0] == "unknown"


def test_known_workload_prompt_uses_hmac_and_only_user_task_shapes():
    prompt = "Read README.md and report its first heading."
    key = b"per-run-test-secret-key-32-bytes"
    proposal = {
        "messages": [{"role": "user", "content": f"  {prompt}  "}],
        "tools": [{"type": "function", "function": {"name": "read"}}],
    }
    final = {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1"}]},
            {"role": "tool", "tool_call_id": "call-1", "content": "heading"},
        ]
    }
    title = {
        "messages": [
            {"role": "user", "content": f"Generate a title for this conversation: {prompt}"}
        ]
    }
    system_only = {
        "messages": [{"role": "system", "content": prompt}],
        "tools": [{"type": "function", "function": {"name": "read"}}],
    }
    fingerprint = canary.hmac.new(key, prompt.encode("utf-8"), canary.hashlib.sha256).hexdigest()

    assert _classify_request_purpose(
        proposal, task_prompt=prompt, task_prompt_hmac_key=key
    ) == (
        "primary_task_workflow",
        f"task_prompt_hmac_sha256:{fingerprint}",
        "known_workload_prompt_hmac_and_task_state",
    )
    assert _classify_request_purpose(
        final, task_prompt=prompt, task_prompt_hmac_key=key
    )[0] == "primary_task_workflow"
    assert _classify_request_purpose(
        title, task_prompt=prompt, task_prompt_hmac_key=key
    ) == (
        "session_title_auxiliary",
        "opencode_session_title_v1",
        "exact_source_confirmed_prefix",
    )
    assert _classify_request_purpose(
        system_only, task_prompt=prompt, task_prompt_hmac_key=key
    )[0] == "unknown"
    assert prompt not in f"task_prompt_hmac_sha256:{fingerprint}"


def test_client_attribution_requires_one_unambiguous_process_window():
    windows = {
        "opencode": {"started_at_unix_ms": 100, "finished_at_unix_ms": 200},
        "deepseek_harness": {"started_at_unix_ms": 150, "finished_at_unix_ms": 250},
    }

    assert _client_for_timestamp(120, windows) == (
        "opencode",
        "unique_subprocess_window",
    )
    assert _client_for_timestamp(175, windows) == (
        None,
        "overlapping_subprocess_windows",
    )
    assert _client_for_timestamp(300, windows) == (
        None,
        "no_matching_subprocess_window",
    )


def test_loopback_capture_records_reordered_title_purpose_and_client_without_text():
    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            body = json.dumps(
                {
                    "id": "local-request-id",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
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
    proxy = _LoopbackAccountingProxy(
        f"http://127.0.0.1:{upstream.server_port}/v1"
    )
    proxy.start()
    try:
        requests = [
            (
                "deepseek_harness",
                {
                    "model": "test-model",
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Generate the session title from this JSON array of human messages:\n"
                                '[{"text":"PRIVATE_SESSION_TEXT_DSH"}]'
                            ),
                        }
                    ],
                },
            ),
            (
                "opencode",
                {
                    "model": "test-model",
                    "messages": [
                        {"role": "system", "content": "Generate a title for this conversation"},
                        {"role": "user", "content": "PRIVATE_SESSION_TEXT_OPENCODE"},
                    ],
                },
            ),
            (
                "opencode",
                {
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "Read README.md."}],
                    "tools": [],
                },
            ),
        ]
        for _client_name, payload in requests:
            request = urllib.request.Request(
                f"{proxy.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                assert response.status == 200
            time.sleep(0.01)

        request_times = [
            call["request_started_at_unix_ms"] for call in proxy.snapshot()["calls"]
        ]
        capture = proxy.snapshot(
            {
                "deepseek_harness": {
                    "started_at_unix_ms": request_times[0],
                    "finished_at_unix_ms": request_times[0],
                },
                "opencode": {
                    "started_at_unix_ms": request_times[1],
                    "finished_at_unix_ms": request_times[2],
                },
            }
        )
        calls = capture["calls"]
        assert capture["snapshot_complete"] is True
        assert capture["delivery_status_complete"] is True
        assert all(call["downstream_write_status"] == "server_write_completed" for call in calls)
        assert [call["client_attribution"] for call in calls] == [
            "deepseek_harness",
            "opencode",
            "opencode",
        ]
        assert [call["purpose"] for call in calls] == [
            "session_title_auxiliary",
            "session_title_auxiliary",
            "unknown",
        ]
        assert all(call["request_id"] == "local-request-id" for call in calls)
        assert all(call["usage"]["total_tokens"] == 9 for call in calls)
        assert capture["client_attribution_complete"] is True
        assert capture["purpose_attribution_complete"] is False
        assert capture["route_attribution_complete"] is True
        assert capture["accounting_complete"] is False
        serialized = json.dumps(capture)
        assert "PRIVATE_SESSION_TEXT_DSH" not in serialized
        assert "PRIVATE_SESSION_TEXT_OPENCODE" not in serialized
        assert "Generate the session title" not in serialized
        assert "Generate a title for this conversation" not in serialized
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_loopback_proxy_records_upstream_usage_once_when_client_write_fails():
    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            body = json.dumps(
                {
                    "id": "once-only-request-id",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {"prompt_tokens": 7, "completion_tokens": 2, "total_tokens": 9},
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-LiteLLM-Response-Cost", "0.125")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    class DisconnectingProxy(_LoopbackAccountingProxy):
        def _send_downstream_response(self, handler, *, status, headers, body) -> None:
            raise BrokenPipeError("deterministic downstream write failure")

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = DisconnectingProxy(f"http://127.0.0.1:{upstream.server_port}/v1")
    proxy.start()
    request = urllib.request.Request(
        f"{proxy.base_url}/chat/completions",
        data=json.dumps(
            {"model": "test-model", "messages": [{"role": "user", "content": "bounded test"}]}
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with pytest.raises((urllib.error.URLError, OSError)):
            urllib.request.urlopen(request, timeout=5)
        capture = proxy.snapshot()
        assert capture["call_count"] == 1
        assert capture["snapshot_complete"] is True
        assert capture["request_ids_complete"] is True
        assert capture["delivery_status_complete"] is True
        assert capture["frontier_tokens"] == 9
        assert capture["cost_usd"] == 0.125
        event = capture["calls"][0]
        assert event["status"] == 200
        assert event["request_id"] == "once-only-request-id"
        assert event["usage"]["total_tokens"] == 9
        assert event["cost_usd"] == 0.125
        assert event["downstream_write_status"] == "interrupted"
        assert event["downstream_write_error_type"] == "BrokenPipeError"
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_task_marker_capture_counts_two_task_states_and_persists_no_marker():
    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            body = json.dumps(
                {
                    "id": "marker-test-request",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
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
    marker = "wrench-private-marker-2fd08b"
    proxy = _LoopbackAccountingProxy(
        f"http://127.0.0.1:{upstream.server_port}/v1", task_marker=marker
    )
    proxy.start()
    client_times: dict[str, list[int]] = {"opencode": [], "deepseek_harness": []}
    try:
        for client in ("opencode", "deepseek_harness"):
            requests = [
                {
                    "messages": [
                        {"role": "user", "content": f"Generate a title for this conversation: {marker}"}
                    ]
                },
                {
                    "messages": [{"role": "user", "content": f"Read README.md. {marker}"}],
                    "tools": [{"type": "function", "function": {"name": "read_file"}}],
                },
                {
                    "messages": [
                        {"role": "user", "content": f"Read README.md. {marker}"},
                        {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1"}]},
                        {"role": "tool", "tool_call_id": "call-1", "content": "heading"},
                    ]
                },
            ]
            for payload in requests:
                request = urllib.request.Request(
                    f"{proxy.base_url}/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    assert response.status == 200
                client_times[client].append(proxy.snapshot()["calls"][-1]["request_started_at_unix_ms"])
                time.sleep(0.01)

        windows = {
            client: {
                "started_at_unix_ms": min(timestamps),
                "finished_at_unix_ms": max(timestamps),
            }
            for client, timestamps in client_times.items()
        }
        capture = proxy.snapshot(windows)
        assert [call["purpose"] for call in capture["calls"]] == [
            "session_title_auxiliary", "primary_task_workflow", "primary_task_workflow",
            "session_title_auxiliary", "primary_task_workflow", "primary_task_workflow",
        ]
        assert capture["task_marker_validation"]["exact_two_matches_per_client"] is True
        assert capture["task_marker_validation"]["non_title_matches_per_client"] == {
            "opencode": 2,
            "deepseek_harness": 2,
        }
        serialized = json.dumps(capture)
        assert marker not in serialized
        assert "Generate a title for this conversation" not in serialized
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_two_state_local_stub_emits_only_whitelisted_read_tool_call():
    marker = "wrench-two-state-test-8a0b"
    server, calls = canary._baseline_server(
        two_state_read_tool=True,
        task_marker=marker,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        def post(payload):
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.read().decode("utf-8")

        title_stream = post({
            "stream": True,
            "messages": [{"role": "user", "content": f"Generate a title for this conversation: {marker}"}],
        })
        title_chunks = [json.loads(line[6:]) for line in title_stream.splitlines() if line.startswith("data: {")]
        assert not any(chunk.get("choices", [{}])[0].get("delta", {}).get("tool_calls") for chunk in title_chunks)

        proposal_stream = post({
            "stream": True,
            "messages": [{"role": "user", "content": f"Read README.md. {marker}"}],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "read",
                    "parameters": {
                        "type": "object",
                        "properties": {"file_path": {"type": "string"}, "offset": {"type": "number"}, "limit": {"type": "number"}},
                        "required": ["file_path"],
                    },
                },
            }],
        })
        proposal_chunks = [json.loads(line[6:]) for line in proposal_stream.splitlines() if line.startswith("data: {")]
        tool_deltas = [
            tool
            for chunk in proposal_chunks
            for tool in chunk.get("choices", [{}])[0].get("delta", {}).get("tool_calls", [])
        ]
        assert len(tool_deltas) == 1
        assert tool_deltas[0]["function"]["name"] == "read"
        assert json.loads(tool_deltas[0]["function"]["arguments"]) == {
            "file_path": "README.md",
            "offset": 0,
            "limit": 12,
        }

        final_stream = post({
            "stream": True,
            "messages": [
                {"role": "user", "content": f"Read README.md. {marker}"},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "call-local-readme-heading"}]},
                {"role": "tool", "tool_call_id": "call-local-readme-heading", "content": "# Wrench SLM"},
            ],
        })
        final_chunks = [json.loads(line[6:]) for line in final_stream.splitlines() if line.startswith("data: {")]
        assert any(
            chunk.get("choices", [{}])[0].get("delta", {}).get("content") == canary.BASELINE_TEXT
            for chunk in final_chunks
        )
        assert len(calls) == 3
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_known_prompt_capture_requires_ordered_two_state_protocol_per_client():
    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            body = json.dumps(
                {
                    "id": "known-prompt-request",
                    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
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
    prompt = "Read README.md and report its first heading."
    proxy = _LoopbackAccountingProxy(
        f"http://127.0.0.1:{upstream.server_port}/v1", task_prompt=prompt
    )
    proxy.start()
    client_times: dict[str, list[int]] = {"opencode": [], "deepseek_harness": []}
    try:
        title_requests = {
            "opencode": {
                "messages": [
                    {"role": "system", "content": "Generate a title for this conversation"},
                    {"role": "user", "content": prompt},
                ]
            },
            "deepseek_harness": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Generate the session title from this JSON array of human messages:\n"
                        + json.dumps([{"text": prompt}]),
                    }
                ]
            },
        }
        for client in ("opencode", "deepseek_harness"):
            proposal_user = f"  {prompt}  " if client == "opencode" else prompt
            requests = [
                title_requests[client],
                {
                    "messages": [{"role": "user", "content": proposal_user}],
                    "tools": [{"type": "function", "function": {"name": "read"}}],
                },
                {
                    "messages": [
                        {"role": "user", "content": proposal_user},
                        {"role": "assistant", "content": None, "tool_calls": [{"id": f"{client}-call"}]},
                        {"role": "tool", "tool_call_id": f"{client}-call", "content": "heading"},
                    ]
                },
            ]
            for payload in requests:
                request = urllib.request.Request(
                    f"{proxy.base_url}/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=5) as response:
                    assert response.status == 200
                client_times[client].append(
                    proxy.snapshot()["calls"][-1]["request_started_at_unix_ms"]
                )
                time.sleep(0.01)

        windows = {
            client: {
                "started_at_unix_ms": min(timestamps),
                "finished_at_unix_ms": max(timestamps),
            }
            for client, timestamps in client_times.items()
        }
        capture = proxy.snapshot(windows)
        validation = capture["task_prompt_validation"]
        assert [call["purpose"] for call in capture["calls"]] == [
            "session_title_auxiliary", "primary_task_workflow", "primary_task_workflow",
            "session_title_auxiliary", "primary_task_workflow", "primary_task_workflow",
        ]
        assert validation["fingerprint_scheme"] == "per_run_hmac_sha256"
        assert validation["exact_ordered_two_state_protocol_per_client"] is True
        assert validation["observed_state_order_per_client"] == {
            "opencode": ["proposal_tool_definitions", "final_tool_result"],
            "deepseek_harness": ["proposal_tool_definitions", "final_tool_result"],
        }
        assert capture["purpose_attribution_complete"] is True
        assert capture["accounting_complete"] is False
        serialized = json.dumps(capture)
        assert prompt not in serialized
        assert proxy._task_prompt_hmac_key.hex() not in serialized
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_client_latency_comparison_is_diagnostic_and_pairs_only_correct_results():
    result = _compare_client_latencies(
        {
            "opencode": {"correct": True, "elapsed_ms": 1000},
            "deepseek_harness": {"correct": True, "elapsed_ms": 800},
        },
        {
            "client_answers": {
                "opencode": {"correct": True},
                "deepseek_harness": {"correct": False},
            },
            "client_elapsed_ms": {"opencode": 400, "deepseek_harness": 300},
        },
        baseline_correct=True,
    )

    assert result["status"] == "DIAGNOSTIC_ONLY_INSUFFICIENT_TASK_PAIRS"
    assert result["successful_paired_task_count"] == 1
    assert result["client_observations"]["opencode"]["latency_reduction_percent"] == 60
    assert result["client_observations"]["deepseek_harness"]["hybrid_elapsed_ms"] is None
    assert result["confidence_interval_95"] is None
    assert result["gate_c_claim"] is False


def test_client_latency_comparison_rejects_invalid_timings_and_unsuccessful_baseline():
    result = _compare_client_latencies(
        {"opencode": {"correct": True, "elapsed_ms": True}},
        {
            "client_answers": {"opencode": {"correct": True}},
            "client_elapsed_ms": {"opencode": 10},
        },
        baseline_correct=False,
    )

    assert result["successful_paired_task_count"] == 0
    assert result["client_observations"]["opencode"]["baseline_elapsed_ms"] is None


def test_bounded_subprocess_records_timeout(monkeypatch, tmp_path):
    def run_timeout(*args, **kwargs):
        return {
            "exit_code": None,
            "timed_out": True,
            "timeout_seconds": 7,
            "elapsed_ms": 7,
            "stdout": b"partial",
            "stderr": b"timed out",
            "tree_cleanup_complete": True,
        }

    if os.name == "nt":
        monkeypatch.setattr(canary, "_run_windows_job_subprocess", run_timeout)
    else:
        class FakeProcess:
            pid = 123
            returncode = None

            def communicate(self, timeout=None):
                if timeout == 7:
                    raise subprocess.TimeoutExpired(
                        "fake-client", timeout, output=b"partial", stderr=b"timed out"
                    )
                self.returncode = -9
                return b"partial", b"timed out"

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                self.returncode = -9
                return self.returncode

        monkeypatch.setattr(canary.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
        monkeypatch.setattr(canary, "_terminate_process_tree", lambda process: True)
    result = canary._run_bounded_subprocess(
        ["fake-client"],
        cwd=tmp_path,
        env={},
        timeout_seconds=7,
    )

    assert result["timed_out"] is True
    assert result["exit_code"] is None
    assert result["timeout_seconds"] == 7
    assert result["stdout"] == "partial"
    assert result["stderr"] == "timed out"
    assert result["tree_cleanup_complete"] is True


def test_bounded_subprocess_timeout_terminates_spawned_child(tmp_path):
    child_code = "import time; time.sleep(60)"
    parent_code = (
        "import subprocess,sys,time; "
        f"child=subprocess.Popen([sys.executable,'-c',{child_code!r}], "
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
        "print(child.pid,flush=True); time.sleep(60)"
    )
    result = canary._run_bounded_subprocess(
        [sys.executable, "-c", parent_code],
        cwd=tmp_path,
        env=dict(os.environ),
        timeout_seconds=1,
    )
    child_pid = int(result["stdout"].strip())

    def process_exists(pid):
        if os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                return not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    try:
        assert result["timed_out"] is True
        assert not process_exists(child_pid), f"timed-out subprocess left child {child_pid} alive"
    finally:
        if process_exists(child_pid):
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(child_pid), "/T", "/F"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            else:
                os.kill(child_pid, 9)


def test_bounded_subprocess_timeout_cleans_child_after_parent_exits(tmp_path):
    child_code = "import time; time.sleep(60)"
    child_pid_file = tmp_path / "spawned-child.pid"
    parent_code = (
        "import pathlib,subprocess,sys; "
        f"child=subprocess.Popen([sys.executable,'-c',{child_code!r}]); "
        f"pathlib.Path({str(child_pid_file)!r}).write_text(str(child.pid))"
    )
    result = canary._run_bounded_subprocess(
        [sys.executable, "-c", parent_code],
        cwd=tmp_path,
        env=dict(os.environ),
        timeout_seconds=1,
    )
    child_pid = int(child_pid_file.read_text(encoding="utf-8"))

    def process_exists(pid):
        if os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            try:
                exit_code = wintypes.DWORD()
                return not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    try:
        assert result["timed_out"] is True
        assert result["tree_cleanup_complete"] is True
        assert result["elapsed_ms"] < 7000
        assert not process_exists(child_pid), (
            "timed-out subprocess left child "
            f"{child_pid} alive after its root exited; "
            f"tree cleanup status: {result['tree_cleanup_complete']}"
        )
    finally:
        if process_exists(child_pid):
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(child_pid), "/T", "/F"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
            else:
                os.kill(child_pid, 9)


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object behavior")
def test_windows_job_assignment_failure_never_resumes_suspended_root(monkeypatch, tmp_path):
    marker = tmp_path / "root-was-resumed.txt"
    command = [
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({str(marker)!r}).write_text('resumed')",
    ]
    resumed = []
    root_pids = []

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetProcessId.argtypes = [wintypes.HANDLE]
    kernel32.GetProcessId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    def fail_assignment(kernel32, job, process_handle):
        root_pids.append(kernel32.GetProcessId(process_handle))
        raise OSError("injected AssignProcessToJobObject failure")

    monkeypatch.setattr(windows_job_process, "_assign_windows_process", fail_assignment)
    monkeypatch.setattr(
        windows_job_process,
        "_resume_windows_thread",
        lambda *args: resumed.append(True),
    )

    with pytest.raises(OSError, match="injected AssignProcessToJobObject failure"):
        canary._run_bounded_subprocess(
            command,
            cwd=tmp_path,
            env=dict(os.environ),
            timeout_seconds=5,
        )

    assert resumed == []
    assert not marker.exists()
    assert len(root_pids) == 1
    root_handle = kernel32.OpenProcess(0x1000, False, root_pids[0])
    if root_handle:
        try:
            exit_code = wintypes.DWORD()
            assert kernel32.GetExitCodeProcess(root_handle, ctypes.byref(exit_code))
            assert exit_code.value != 259, "assignment failure left the suspended root alive"
        finally:
            kernel32.CloseHandle(root_handle)


def test_windows_job_launcher_maps_script_shim_to_sibling_powershell(monkeypatch, tmp_path):
    command_shim = tmp_path / "named-client.cmd"
    powershell_script = tmp_path / "named-client.ps1"
    command_shim.write_text("@echo off\n", encoding="utf-8")
    powershell_script.write_text("exit 0\n", encoding="utf-8")
    powershell = tmp_path / "powershell.exe"
    monkeypatch.setattr(
        windows_job_process.shutil,
        "which",
        lambda name: str(powershell) if name == "powershell.exe" else None,
    )

    resolved, prepared_env = windows_job_process._prepare_windows_command(
        [str(command_shim), "run", "prompt with spaces"], {}
    )

    assert resolved[:7] == [
        str(powershell),
        "-NoProfile",
        "-NonInteractive",
        "-OutputFormat",
        "Text",
        "-ExecutionPolicy",
        "Bypass",
    ]
    assert resolved[7] == "-EncodedCommand"
    dispatcher = base64.b64decode(resolved[8]).decode("utf-16le")
    assert "$scriptPath = [string]$data.script" in dispatcher
    payload = json.loads(
        base64.b64decode(prepared_env["WRENCH_JOB_LAUNCH_PAYLOAD"]).decode("utf-8")
    )
    assert payload == {
        "script": str(powershell_script),
        "arguments": ["run", "prompt with spaces"],
    }


def test_windows_job_launcher_rejects_unsupported_script_shim(monkeypatch, tmp_path):
    command_shim = tmp_path / "missing-wrapper.cmd"
    monkeypatch.setattr(windows_job_process.shutil, "which", lambda name: "powershell.exe")

    with pytest.raises(RuntimeError, match="No PowerShell wrapper exists"):
        windows_job_process._prepare_windows_command([str(command_shim), "run"], {})


def test_windows_job_launcher_resolves_native_executable_from_npm_shim(tmp_path):
    command_shim = tmp_path / "named-client.cmd"
    native_executable = tmp_path / "node_modules" / "sample-client" / "bin" / "sample.exe"
    native_executable.parent.mkdir(parents=True)
    native_executable.write_bytes(b"fixture")
    command_shim.write_text(
        '@echo off\n"%dp0%\\node_modules\\sample-client\\bin\\sample.exe" %*\n',
        encoding="utf-8",
    )

    resolved, prepared_env = windows_job_process._prepare_windows_command(
        [str(command_shim), "--flag", "argument with spaces"], {"KEEP": "value"}
    )

    assert resolved == [str(native_executable), "--flag", "argument with spaces"]
    assert prepared_env == {"KEEP": "value"}


def test_windows_job_launcher_resolves_node_script_from_npm_shim(monkeypatch, tmp_path):
    command_shim = tmp_path / "named-client.cmd"
    node_executable = tmp_path / "node.exe"
    script_path = tmp_path / "node_modules" / "sample-client" / "bin.js"
    node_executable.write_bytes(b"fixture")
    script_path.parent.mkdir(parents=True)
    script_path.write_text("", encoding="utf-8")
    command_shim.write_text(
        '@echo off\n"%dp0%\\node.exe" "%dp0%\\node_modules\\sample-client\\bin.js" %*\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(windows_job_process.shutil, "which", lambda name: None)

    resolved, prepared_env = windows_job_process._prepare_windows_command(
        [str(command_shim), "--flag", "argument with spaces"], {}
    )

    assert resolved == [
        str(node_executable), str(script_path), "--flag", "argument with spaces"
    ]
    assert prepared_env == {}


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object launcher integration")
def test_windows_job_launcher_runs_powershell_shim_with_literal_arguments(tmp_path):
    command_shim = tmp_path / "named-client.cmd"
    powershell_script = tmp_path / "named-client.ps1"
    command_shim.write_text("@echo off\n", encoding="utf-8")
    powershell_script.write_text(
        '& $env:WRENCH_TEST_PYTHON -c "import sys; print(\'|\'.join(sys.argv[1:]))" $args\n',
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["WRENCH_TEST_PYTHON"] = sys.executable
    result = canary._run_bounded_subprocess(
        [str(command_shim), "--option", "argument with spaces", "literal&value"],
        cwd=tmp_path,
        env=env,
        timeout_seconds=5,
    )

    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert result["tree_cleanup_complete"] is True
    assert result["stdout"] == "--option|argument with spaces|literal&value"


@pytest.mark.skipif(os.name != "nt", reason="Installed Windows client shims")
def test_windows_job_launcher_runs_installed_opencode_and_dsh_help():
    client_paths = {
        name: windows_job_process.shutil.which(name)
        for name in ("opencode.cmd", "dsh.cmd")
    }
    if not all(client_paths.values()):
        pytest.skip("OpenCode and DSH command shims are not both installed")
    keep = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}

    for client_name, expected in (("opencode.cmd", "opencode"), ("dsh.cmd", "Usage: dsh")):
        result = canary._run_bounded_subprocess(
            [client_paths[client_name], "--help"],
            cwd=Path.cwd(),
            env=env,
            timeout_seconds=10,
        )

        assert result["exit_code"] == 0, client_name
        assert result["timed_out"] is False, client_name
        assert result["tree_cleanup_complete"] is True, client_name
        assert expected in (result["stdout"] + result["stderr"]), client_name


def test_bounded_subprocess_captures_utf8_with_replacement(monkeypatch, tmp_path):
    result_record = {
            "exit_code": 0,
            "timed_out": False,
            "timeout_seconds": 7,
            "elapsed_ms": 1,
            "stdout": b"# Wrench SLM",
            "stderr": b"",
            "tree_cleanup_complete": True,
        }
    if os.name == "nt":
        monkeypatch.setattr(
            canary, "_run_windows_job_subprocess", lambda *args, **kwargs: result_record
        )
    else:
        class FakeProcess:
            pid = 123
            returncode = 0

            def communicate(self, timeout=None):
                return b"# Wrench SLM", b""

        monkeypatch.setattr(canary.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    result = canary._run_bounded_subprocess(
        ["fake-client"],
        cwd=tmp_path,
        env={},
        timeout_seconds=7,
    )

    assert result["stdout"] == "# Wrench SLM"
    assert result["tree_cleanup_complete"] is True


def test_bounded_subprocess_decodes_windows_code_page_output(monkeypatch, tmp_path):
    class FakeProcess:
        pid = 123
        returncode = 0

        def communicate(self, timeout=None):
            return "The first heading is **“Wrench SLM”**.".encode("cp1252"), b""

    result_record = {
            "exit_code": 0,
            "timed_out": False,
            "timeout_seconds": 7,
            "elapsed_ms": 1,
            "stdout": "The first heading is **“Wrench SLM”**.".encode("cp1252"),
            "stderr": b"",
            "tree_cleanup_complete": True,
        }
    if os.name == "nt":
        monkeypatch.setattr(
            canary, "_run_windows_job_subprocess", lambda *args, **kwargs: result_record
        )
    else:
        class FakeProcess:
            pid = 123
            returncode = 0

            def communicate(self, timeout=None):
                return result_record["stdout"], b""

        monkeypatch.setattr(canary.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    result = canary._run_bounded_subprocess(
        ["fake-client"],
        cwd=tmp_path,
        env={},
        timeout_seconds=7,
    )

    assert result["stdout"] == "The first heading is **“Wrench SLM”**."


def test_canary_status_requires_net_savings_beyond_arm_accounting():
    common = {
        "baseline_correct": True,
        "hybrid_correct": True,
        "hybrid_frontier_tokens": 0,
        "hybrid_model_calls": 0,
    }
    assert _classify_canary_status(**common, accounting_complete=True) == "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED"
    inconclusive = _classify_canary_status(**common, accounting_complete=False)
    assert inconclusive == "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE"
    assert _canary_process_exit_code(inconclusive) == 1
    assert _canary_process_exit_code("PASS_PAIRED_REAL_CLIENT_HYBRID_CANARY") == 0


@pytest.mark.parametrize(
    ("frontier_tokens", "model_calls"),
    [(1, 0), (0, 1), (1, 1)],
)
def test_nonzero_hybrid_calls_require_threshold_evaluation_before_failure(frontier_tokens, model_calls):
    assert _classify_canary_status(
        baseline_correct=True,
        hybrid_correct=True,
        hybrid_frontier_tokens=frontier_tokens,
        hybrid_model_calls=model_calls,
        accounting_complete=True,
    ) == "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED"


def test_failed_answer_remains_fail_even_if_accounting_is_incomplete():
    assert _classify_canary_status(
        baseline_correct=True,
        hybrid_correct=False,
        hybrid_frontier_tokens=0,
        hybrid_model_calls=0,
        accounting_complete=False,
    ) == "FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY"


@pytest.mark.parametrize(
    ("baseline_correct", "hybrid_correct", "expected"),
    [
        (True, True, "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED"),
        (True, False, "FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY"),
        (False, True, "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_COMPARATOR_INVALID"),
        (False, False, "FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY"),
    ],
)
def test_teacher_comparator_failure_is_not_misattributed_to_correct_wrench(
    baseline_correct, hybrid_correct, expected
):
    status = _classify_canary_status(
        baseline_correct=baseline_correct,
        hybrid_correct=hybrid_correct,
        hybrid_frontier_tokens=0,
        hybrid_model_calls=0,
        accounting_complete=True,
    )
    assert status == expected
    if status.startswith("INCONCLUSIVE"):
        assert _canary_process_exit_code(status) == 1


def test_missing_direct_baseline_client_cannot_count_as_a_correct_comparator():
    assert not _baseline_clients_correct({})
    assert not _baseline_clients_correct({"opencode": {"correct": True}})
    assert not _baseline_clients_correct({
        "opencode": {"correct": True},
        "deepseek_harness": {"correct": False},
    })
    assert _baseline_clients_correct({
        "opencode": {"correct": True},
        "deepseek_harness": {"correct": True},
    })


def test_nonzero_model_activity_does_not_exit_as_canary_pass_without_savings_result():
    status = _classify_canary_status(
        baseline_correct=True,
        hybrid_correct=True,
        hybrid_frontier_tokens=1,
        hybrid_model_calls=1,
        accounting_complete=True,
    )
    assert status == "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED"
    assert _canary_process_exit_code(status) == 1


def test_external_baseline_requires_explicit_workload_authorization():
    with pytest.raises(RuntimeError, match="external baseline requires workload authorization"):
        _validate_external_baseline_guard(
            "https://provider.example/v1",
            workload_authorization="local_stub_only",
            allow_external_baseline=True,
            api_key="redacted-test-key",
        )

    with pytest.raises(RuntimeError, match="--allow-external-baseline"):
        _validate_external_baseline_guard(
            "https://provider.example/v1",
            workload_authorization="approved_real_workflow",
            allow_external_baseline=False,
            api_key="redacted-test-key",
        )

    with pytest.raises(RuntimeError, match="https URL"):
        _validate_external_baseline_guard(
            "http://provider.example/v1",
            workload_authorization="approved_real_workflow",
            allow_external_baseline=True,
            api_key="redacted-test-key",
        )

    assert _effective_baseline_api_key("http://localhost:4000/v1", "") == "local-gateway"
    assert _effective_baseline_api_key("https://provider.example/v1", "") == ""


def test_configured_loopback_baseline_requires_exact_approved_child_contract():
    parent_contract_sha256 = "a" * 64
    parent_contract = {
        "contract_id": canary.PARENT_CONTRACT_ID,
        "collaboration": {
            "bounds": {
                "monetary_budget": 0.10,
                "paid_canary_route_allowance": _test_parent_route_allowance(
                    endpoint="http://localhost:4000/v1",
                    alias="minimax-guided",
                    provider_model="provider/minimax-guided",
                ),
            }
        },
    }
    contract = {
        "schema": canary.CHILD_CONTRACT_SCHEMA,
        "parent_contract_id": "wrench-slm-productive-value-2026-09-22",
        "parent_contract_sha256": parent_contract_sha256,
        "decision": "human.approve_commit",
        "status": "APPROVED",
        "approved_by": "test-human",
        "approval_reference": "test-only-approval",
        "workload_sha256": "a" * 64,
        "endpoint": "http://localhost:4000/v1",
        "model": "minimax-guided",
        "expected_provider_model": "provider/minimax-guided",
        "repetitions": 1,
        "max_spend_usd": 0.10,
        "spend_cap_kind": "provider_hard_cap",
        "spend_cap_reference": "test-only-provider-cap",
        "cost_accounting": _test_cost_accounting_binding(),
    }
    assert canary._validate_paid_baseline_child_contract(
        contract,
        parent_contract=parent_contract,
        parent_contract_sha256=parent_contract_sha256,
        baseline_url="http://localhost:4000/v1",
        baseline_model="minimax-guided",
        workload_sha256="a" * 64,
        workload_authorization="approved_real_workflow",
    )["max_spend_usd"] == 0.10

    missing_allowance = json.loads(json.dumps(parent_contract))
    del missing_allowance["collaboration"]["bounds"]["paid_canary_route_allowance"]
    with pytest.raises(RuntimeError, match="paid_canary_route_allowance missing"):
        canary._validate_paid_baseline_child_contract(
            contract,
            parent_contract=missing_allowance,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="minimax-guided",
            workload_sha256="a" * 64,
            workload_authorization="approved_real_workflow",
        )

    for change, requested_endpoint, requested_alias in (
        ({"endpoint": "http://localhost:4001/v1"}, "http://localhost:4001/v1", "minimax-guided"),
        ({"model": "openrouter"}, "http://localhost:4000/v1", "openrouter"),
        ({"expected_provider_model": "another/provider-model"}, "http://localhost:4000/v1", "minimax-guided"),
    ):
        mismatched_child = {**contract, **change}
        with pytest.raises(RuntimeError, match="not authorized by parent Q4 route allowance"):
            canary._validate_paid_baseline_child_contract(
                mismatched_child,
                parent_contract=parent_contract,
                parent_contract_sha256=parent_contract_sha256,
                baseline_url=requested_endpoint,
                baseline_model=requested_alias,
                workload_sha256="a" * 64,
                workload_authorization="approved_real_workflow",
            )

    with pytest.raises(RuntimeError, match="approved child contract required"):
        canary._validate_paid_baseline_child_contract(
            None,
            parent_contract=parent_contract,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="minimax-guided",
            workload_sha256="a" * 64,
            workload_authorization="approved_real_workflow",
        )
    for change in (
        {"template": True},
        {"workload_sha256": "b" * 64},
        {"parent_contract_sha256": "b" * 64},
        {"endpoint": "http://localhost:4001/v1"},
        {"model": "minimax"},
        {"repetitions": 2},
        {"max_spend_usd": 0},
        {"max_spend_usd": float("inf")},
        {"max_spend_usd": "unlimited"},
        {"max_spend_usd": 0.11},
        {"schema": "wrench.paid-canary-child-contract.v2"},
        {"cost_accounting": None},
        {"spend_cap_kind": "soft_estimate"},
        {"spend_cap_reference": ""},
        {"expected_provider_model": ""},
        {"status": "PENDING"},
    ):
        with pytest.raises(RuntimeError, match="child contract"):
            canary._validate_paid_baseline_child_contract(
                {**contract, **change},
                parent_contract=parent_contract,
                parent_contract_sha256=parent_contract_sha256,
                baseline_url="http://localhost:4000/v1",
                baseline_model="minimax-guided",
                workload_sha256="a" * 64,
                workload_authorization="approved_real_workflow",
            )
    with pytest.raises(RuntimeError, match="workload authorization"):
        canary._validate_paid_baseline_child_contract(
            contract,
            parent_contract=parent_contract,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="minimax-guided",
            workload_sha256="a" * 64,
            workload_authorization="local_stub_only",
        )
    zero_budget_parent = {
        "contract_id": canary.PARENT_CONTRACT_ID,
        "collaboration": {"bounds": {"monetary_budget": 0}},
    }
    with pytest.raises(RuntimeError, match="parent monetary_budget is zero"):
        canary._validate_paid_baseline_child_contract(
            contract,
            parent_contract=zero_budget_parent,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="minimax-guided",
            workload_sha256="a" * 64,
            workload_authorization="approved_real_workflow",
        )


def test_openai_aggregate_child_preflight_requires_isolation_and_spend_headroom():
    parent_contract_sha256 = "a" * 64
    parent_contract = {
        "contract_id": canary.PARENT_CONTRACT_ID,
        "collaboration": {
            "bounds": {
                "monetary_budget": 0.10,
                "paid_canary_route_allowance": _test_parent_route_allowance(
                    endpoint="http://localhost:4000/v1",
                    alias="openai-current-test",
                    provider_model="gpt-6-test",
                ),
            }
        },
    }
    start = 1730419200
    contract = {
        "schema": canary.CHILD_CONTRACT_SCHEMA,
        "parent_contract_id": canary.PARENT_CONTRACT_ID,
        "parent_contract_sha256": parent_contract_sha256,
        "decision": "human.approve_commit",
        "status": "APPROVED",
        "approved_by": "test-human",
        "approval_reference": "test-only-approval",
        "workload_sha256": "a" * 64,
        "endpoint": "http://localhost:4000/v1",
        "model": "openai-current-test",
        "expected_provider_model": "gpt-6-test",
        "repetitions": 1,
        "max_spend_usd": 0.10,
        "spend_cap_kind": "provider_hard_cap",
        "spend_cap_reference": "test-only-provider-cap",
        "cost_accounting": {
            "schema": "wrench.provider-cost-accounting-binding.v1",
            "provider": "openai",
            "mode": "openai_organization_costs_daily_aggregate",
            "export_endpoint": "https://api.openai.com/v1/organization/costs",
            "project_id": "proj-test",
            "api_key_id": "key-test",
            "bucket_start_time": start,
            "bucket_end_time": start + 86400,
            "dedicated_project": True,
            "exclusive_api_key": True,
            "exclusive_for_entire_interval": True,
            "isolation_evidence_reference": "test-only-isolation",
            "current_project_spend_usd": 0.02,
            "project_hard_limit_usd": 0.08,
            "hard_limit_overshoot_reserve_usd": 0.01,
            "spend_headroom_evidence_reference": "test-only-headroom",
        },
    }

    approved = canary._validate_paid_baseline_child_contract(
        contract,
        parent_contract=parent_contract,
        parent_contract_sha256=parent_contract_sha256,
        baseline_url="http://localhost:4000/v1",
        baseline_model="openai-current-test",
        workload_sha256="a" * 64,
        workload_authorization="approved_real_workflow",
    )
    assert approved["cost_accounting"]["mode"] == "openai_organization_costs_daily_aggregate"

    excessive_limit = json.loads(json.dumps(contract))
    excessive_limit["cost_accounting"]["project_hard_limit_usd"] = 0.12
    with pytest.raises(RuntimeError, match="lacks approved spend headroom"):
        canary._validate_paid_baseline_child_contract(
            excessive_limit,
            parent_contract=parent_contract,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="openai-current-test",
            workload_sha256="a" * 64,
            workload_authorization="approved_real_workflow",
        )

    unisolated = json.loads(json.dumps(contract))
    unisolated["cost_accounting"]["exclusive_api_key"] = False
    with pytest.raises(RuntimeError, match="exclusive_api_key not approved"):
        canary._validate_paid_baseline_child_contract(
            unisolated,
            parent_contract=parent_contract,
            parent_contract_sha256=parent_contract_sha256,
            baseline_url="http://localhost:4000/v1",
            baseline_model="openai-current-test",
            workload_sha256="a" * 64,
            workload_authorization="approved_real_workflow",
        )

def test_zero_parent_budget_blocks_configured_baseline_before_output_or_network(tmp_path, monkeypatch):
    parent_path = tmp_path / "COLLABORATION_CONTRACT.json"
    parent_path.write_text(
        json.dumps({
            "contract_id": canary.PARENT_CONTRACT_ID,
            "collaboration": {"bounds": {"monetary_budget": 0}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(canary, "PARENT_CONTRACT_PATH", parent_path)
    workload_path = _write_synthetic_test_workload(tmp_path)
    workload = load_workload(workload_path)
    child_path = tmp_path / "child-contract.json"
    parent_contract_sha256 = canary.hashlib.sha256(parent_path.read_bytes()).hexdigest()
    child_path.write_text(
        json.dumps({
            "schema": canary.CHILD_CONTRACT_SCHEMA,
            "parent_contract_id": canary.PARENT_CONTRACT_ID,
            "parent_contract_sha256": parent_contract_sha256,
            "decision": "human.approve_commit",
            "status": "APPROVED",
            "approved_by": "test-human",
            "approval_reference": "test-only-approval",
            "workload_sha256": workload["workload_sha256"],
            "endpoint": "http://localhost:4000/v1",
            "model": "minimax-guided",
            "expected_provider_model": "provider/minimax-guided",
            "repetitions": 1,
            "max_spend_usd": 0.10,
            "spend_cap_kind": "provider_hard_cap",
            "spend_cap_reference": "test-only-provider-cap",
            "cost_accounting": _test_cost_accounting_binding(),
        }),
        encoding="utf-8",
    )
    output = tmp_path / "blocked-output" / "receipt.json"
    monkeypatch.setattr(sys, "argv", [
        "probe_paired_real_client_canary.py",
        "--package-dir", str(tmp_path / "package"),
        "--output", str(output),
        "--baseline-url", "http://localhost:4000/v1",
        "--baseline-model", "minimax-guided",
        "--child-contract", str(child_path),
        "--capture-gateway-accounting",
        "--workload", str(workload_path),
    ])
    monkeypatch.setattr(
        canary.urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("network request reached before parent budget check"),
    )
    with pytest.raises(RuntimeError, match="parent monetary_budget is zero"):
        canary.main()
    assert not output.parent.exists()


def test_configured_baseline_fails_before_output_or_gateway_request_without_child_contract(tmp_path, monkeypatch):
    output = tmp_path / "new-output" / "receipt.json"
    workload = _write_synthetic_test_workload(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "probe_paired_real_client_canary.py",
        "--package-dir", str(tmp_path / "package"),
        "--output", str(output),
        "--baseline-url", "http://localhost:4000/v1",
        "--baseline-model", "minimax-guided",
        "--workload", str(workload),
    ])
    with pytest.raises(RuntimeError, match="approved child contract required"):
        canary.main()
    assert not output.parent.exists()


def test_child_contract_template_cannot_authorize_configured_baseline(tmp_path, monkeypatch):
    parent_path = tmp_path / "COLLABORATION_CONTRACT.json"
    parent = {
        "contract_id": canary.PARENT_CONTRACT_ID,
        "collaboration": {"bounds": {"monetary_budget": 500}},
    }
    parent_path.write_text(json.dumps(parent), encoding="utf-8")
    monkeypatch.setattr(canary, "PARENT_CONTRACT_PATH", parent_path)
    template_path = (
        canary.REPO_ROOT
        / "phases"
        / "phase-439-openai-cost-export-compatibility"
        / "child-contract-v3.template.json"
    )
    workload_path = _write_synthetic_test_workload(tmp_path)
    output = tmp_path / "blocked-template-output" / "receipt.json"
    monkeypatch.setattr(sys, "argv", [
        "probe_paired_real_client_canary.py",
        "--package-dir", str(tmp_path / "package"),
        "--output", str(output),
        "--baseline-url", "http://localhost:4000/v1",
        "--baseline-model", "minimax-guided",
        "--child-contract", str(template_path),
        "--capture-gateway-accounting",
        "--workload", str(workload_path),
    ])
    monkeypatch.setattr(
        canary.urllib.request,
        "urlopen",
        lambda *args, **kwargs: pytest.fail("gateway request reached with a template contract"),
    )

    with pytest.raises(RuntimeError, match="child contract template cannot authorize"):
        canary.main()

    assert not output.parent.exists()


def test_loopback_spend_probe_records_empty_uncorrelated_logs(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"[]"

    monkeypatch.setattr(canary.urllib.request, "urlopen", lambda request, timeout: Response())
    result = _probe_loopback_spend_logs("http://localhost:4000/v1")

    assert result["status"] == "observed"
    assert result["row_count"] == 0
    assert result["request_correlation_observed"] is False


def test_loopback_spend_probe_does_not_touch_non_loopback_endpoint():
    result = _probe_loopback_spend_logs("https://provider.example/v1")

    assert result == {"status": "not_attempted", "reason": "non_loopback_endpoint"}


def test_usage_capture_handles_json_and_streaming_responses():
    assert _usage_from_response(
        b'{"usage":{"prompt_tokens":4,"completion_tokens":3,"total_tokens":7}}',
        "application/json",
    ) == {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7}
    assert _usage_from_response(
        b'data: {"usage":{"prompt_tokens":8,"completion_tokens":2,"total_tokens":10}}\n\ndata: [DONE]\n\n',
        "text/event-stream",
    ) == {"prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10}


@pytest.mark.parametrize(
    "usage",
    [
        {"prompt_tokens": True, "completion_tokens": 1, "total_tokens": 2},
        {"prompt_tokens": -1, "completion_tokens": 1, "total_tokens": 0},
        {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 4},
        {"prompt_tokens": 2, "total_tokens": 2},
    ],
)
def test_usage_capture_rejects_malformed_or_inconsistent_accounting(usage):
    body = json.dumps({"usage": usage}).encode("utf-8")
    assert _usage_from_response(body, "application/json") is None


def test_trace_jsonl_malformed_or_non_object_rows_fail_closed(tmp_path):
    path = tmp_path / "trace.jsonl"
    valid_accounting_row = {
        "request_id": "r1",
        "client_workflow_id": "w1",
        "client_attempt": 1,
        "model_calls": 0,
        "raw_input_tokens_estimate": 7,
        "cost_accounting": {
            "schema": "wrench.cost-accounting-receipt.v1",
            "token_usage_complete": True,
            "frontier_tokens": 0,
            "local_model_tokens": 0,
            "total_workflow_tokens": 0,
            "repair_passes": 0,
            "local_model_calls": 0,
            "frontier_model_calls": 0,
        },
    }
    path.write_text(json.dumps(valid_accounting_row) + "\nnot-json\n[]\n", encoding="utf-8")

    rows, well_formed = _read_trace_jsonl(path)

    assert rows == [valid_accounting_row]
    assert well_formed is False
    assert _trace_token_accounting_complete(rows, trace_jsonl_well_formed=well_formed) is False


def test_trace_identity_requires_unique_request_and_present_attempt_ids():
    valid = [
        {"request_id": "r1", "client_workflow_id": "w1", "client_attempt": 1},
        {"request_id": "r2", "client_workflow_id": "w1", "client_attempt": 2},
    ]
    assert _trace_identity_accounting(valid) == (True, True)
    assert _trace_identity_accounting([valid[0], {**valid[1], "request_id": "r1"}]) == (False, True)
    assert _trace_identity_accounting([{**valid[0], "request_id": " "}]) == (False, True)
    assert _trace_identity_accounting([{**valid[0], "client_attempt": None}]) == (True, False)
    assert _trace_identity_accounting([{**valid[0], "client_attempt": True}]) == (True, False)
    assert _trace_identity_accounting([valid[0], {**valid[1], "client_attempt": 1}]) == (True, False)


def test_run_hybrid_malformed_trace_fails_closed_without_losing_client_outcome(tmp_path, monkeypatch):
    clients = {name: {"exit_code": 0} for name in ("opencode", "deepseek_harness", "claude_code")}
    (tmp_path / "receipt.json").write_text(json.dumps({"status": "PASSED", "clients": clients}))
    for filename in ("opencode.stdout.txt", "dsh.stdout.txt", "claude.stdout.txt"):
        (tmp_path / filename).write_text("The first heading is # Wrench SLM.", encoding="utf-8")
    (tmp_path / "wrench-client.trace.jsonl").write_text(
        '{"raw_input_tokens_estimate":7}\nnot-json\n', encoding="utf-8"
    )
    monkeypatch.setattr(canary.shutil, "which", lambda _: "powershell.exe")
    monkeypatch.setattr(canary, "_run_bounded_subprocess", lambda *args, **kwargs: {
        "exit_code": 0, "timed_out": False, "timeout_seconds": 180,
        "elapsed_ms": 2, "stdout": "", "stderr": "",
    })

    result = canary._run_hybrid(tmp_path, tmp_path, 29120, prompt=canary.PROMPT, expected=canary.EXPECTED)

    assert result["correct"] is True
    assert result["accounting"]["trace_jsonl_well_formed"] is False
    assert result["accounting"]["token_accounting_complete"] is False
    assert result["accounting"]["frontier_tokens"] is None
    assert result["accounting"]["local_model_tokens"] is None
    assert result["accounting"]["local_input_tokens_estimate"] is None
    assert result["accounting"]["accounting_complete"] is False


@pytest.mark.parametrize("cost_header", ["nan", "inf", "-0.01", "invalid"])
def test_gateway_cost_capture_rejects_nonfinite_negative_or_invalid_values(cost_header):
    class UpstreamHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            body = json.dumps({
                "id": "request-1",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("x-litellm-response-cost", cost_header)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
    upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    upstream_thread.start()
    proxy = _LoopbackAccountingProxy(f"http://127.0.0.1:{upstream.server_port}/v1")
    proxy.start()
    try:
        request = urllib.request.Request(
            f"{proxy.base_url}/chat/completions",
            data=b'{"model":"test","messages":[]}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5):
            pass
        capture = proxy.snapshot()
        assert capture["calls"][0]["cost_usd"] is None
        assert capture["costs_complete"] is False
        assert capture["accounting_complete"] is False
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
        upstream_thread.join(timeout=5)


def test_default_canary_workload_is_hash_bound():
    workload = load_workload(None)
    assert workload["schema"] == "wrench.paired-canary-workload.v1"
    assert workload["workload_id"] == "local-single-readme-heading-v1"
    assert workload["authorization"] == "local_stub_only"
    assert len(workload["workload_sha256"]) == 64
    assert workload["workload_sha256"] == load_workload(None)["workload_sha256"]


def test_canary_workload_rejects_multiple_cases(tmp_path):
    path = tmp_path / "workload.json"
    path.write_text(
        json.dumps(
            {
                "schema": "wrench.paired-canary-workload.v1",
                "workload_id": "invalid",
                "cases": [
                    {"case_id": "a", "prompt": "a", "expected_observation": "a"},
                    {"case_id": "b", "prompt": "b", "expected_observation": "b"},
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="workload_must_contain_exactly_one_case"):
        load_workload(path)
