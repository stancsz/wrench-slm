from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import multiprocessing
import os
import threading
import time
import urllib.request
from pathlib import Path

import pytest

from wrench_harness.router import CancellationToken, ProposalRouter, RouterConfig
from wrench_harness.server import WrenchHTTPServer
from wrench_harness.worker import WrenchWorker


def _accepted_invoker() -> dict[str, object]:
    return {"status": "accepted", "test_marker": "accepted"}


def _abstaining_invoker() -> dict[str, object]:
    return {"status": "abstain", "fallback_reason": "deterministic_test_failure"}


def _raising_invoker() -> dict[str, object]:
    raise RuntimeError("deterministic callback failure")


def _abrupt_exit_invoker() -> dict[str, object]:
    os._exit(23)


def _invalid_status_invoker() -> dict[str, object]:
    return {"status": "successful", "test_marker": "malformed"}


def _abstain_without_reason_invoker() -> dict[str, object]:
    return {"status": "abstain"}


def _signal_then_wait(started: object) -> dict[str, object]:
    started.set()  # type: ignore[attr-defined]
    time.sleep(30)
    return {"status": "accepted"}


@pytest.fixture
def serving_server(tmp_path: Path):
    servers: list[tuple[WrenchHTTPServer, threading.Thread]] = []

    def start(
        invoker,
        *,
        config: RouterConfig | None = None,
        timeout_seconds: float = 5.0,
        cancellation: CancellationToken | None = None,
        address: tuple[str, int] = ("127.0.0.1", 0),
        upstream_url: str | None = None,
        trace_log: Path | None = None,
    ) -> WrenchHTTPServer:
        server = WrenchHTTPServer(
            address,
            WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
            model_name="wrench-gate-e-test",
            max_request_bytes=1024 * 1024,
            use_mechanical_route=False,
            upstream_url=upstream_url,
            trace_log=trace_log,
            test_only_proposal_router=ProposalRouter(config or RouterConfig()),
            test_only_proposal_invoker=invoker,
            test_only_proposal_timeout_seconds=timeout_seconds,
            test_only_cancellation_token=cancellation,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append((server, thread))
        return server

    yield start

    for server, thread in reversed(servers):
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()
        assert server.test_only_active_child_pids == ()


def _post(server: WrenchHTTPServer, *, timeout: float = 12) -> dict[str, object]:
    payload = {
        "model": "wrench-gate-e-test",
        "messages": [{"role": "user", "content": "Run the deterministic router test."}],
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def test_real_handler_routes_success_through_injected_proposal_router(serving_server):
    server = serving_server(
        _accepted_invoker,
        config=RouterConfig(max_attempts=4, failure_threshold=2),
    )

    body = _post(server)

    assert body["wrench"]["status"] == "accepted"
    assert body["wrench"]["backend"] == "test-only-proposal-router"
    assert body["wrench"]["model_calls"] == 0
    assert body["wrench"]["test_only_proposal_router"]["attempts"] == 1
    assert server.test_only_child_launches == 1
    assert server.test_only_active_child_pids == ()


def test_test_only_trace_and_cost_metadata_are_explicit_and_prompt_free(
    serving_server,
    tmp_path: Path,
):
    trace_path = tmp_path / "test-only-router-trace.jsonl"
    server = serving_server(_accepted_invoker, trace_log=trace_path)

    body = _post(server)
    trace = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
    accounting = body["wrench"]["cost_accounting"]

    assert body["wrench"]["test_only_proposal_router"]["attempts"] == 1
    assert trace["test_only_proposal_router"]["attempts"] == 1
    assert trace["status"] == "accepted"
    assert "Run the deterministic router test." not in json.dumps(trace)
    assert accounting["model_calls"] == 0
    assert accounting["frontier_tokens"] == 0
    assert accounting["usd_cost"] is None
    assert accounting["usd_cost_status"] == "not_priced_local_runtime"


def test_default_server_path_exposes_no_test_only_metadata(tmp_path: Path):
    trace_path = tmp_path / "default-router-trace.jsonl"
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-gate-e-test",
        max_request_bytes=1024 * 1024,
        use_mechanical_route=False,
        trace_log=trace_path,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body = _post(server)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)

    assert not thread.is_alive()
    trace = json.loads(trace_path.read_text(encoding="utf-8").splitlines()[0])
    assert body["wrench"]["fallback_reason"] == "model_not_loaded"
    assert "test_only_proposal_router" not in body["wrench"]
    assert "test_only_proposal_router" not in trace


def test_concurrent_handler_requests_keep_router_state_race_free(serving_server):
    request_count = 5
    server = serving_server(
        _accepted_invoker,
        config=RouterConfig(max_attempts=request_count, failure_threshold=2),
    )

    with ThreadPoolExecutor(max_workers=request_count) as pool:
        bodies = list(pool.map(lambda _: _post(server), range(request_count)))

    assert all(body["wrench"]["status"] == "accepted" for body in bodies)
    assert server.test_only_proposal_router.status()["attempts"] == request_count
    assert server.test_only_child_launches == request_count
    assert server.test_only_active_child_pids == ()


def test_concurrent_failures_open_circuit_once_at_configured_threshold(serving_server):
    request_count = 6
    failure_threshold = 2
    server = serving_server(
        _abstaining_invoker,
        config=RouterConfig(max_attempts=request_count, failure_threshold=failure_threshold),
        timeout_seconds=15,
    )

    with ThreadPoolExecutor(max_workers=request_count) as pool:
        bodies = list(pool.map(lambda _: _post(server), range(request_count)))

    reasons = [body["wrench"]["fallback_reason"] for body in bodies]
    assert reasons.count("deterministic_test_failure") == failure_threshold
    assert reasons.count("router_disabled") == request_count - failure_threshold
    assert all(body["wrench"]["status"] == "abstain" for body in bodies)
    status = server.test_only_proposal_router.status()
    assert status["attempts"] == failure_threshold
    assert status["failures"] == failure_threshold
    assert status["circuit_open"] is True
    assert server.test_only_child_launches == failure_threshold
    assert server.test_only_active_child_pids == ()


def test_router_queue_wait_does_not_scale_with_lifetime_attempt_ceiling(serving_server):
    server = serving_server(
        _accepted_invoker,
        config=RouterConfig(max_attempts=1_000_000, failure_threshold=2),
        timeout_seconds=0.1,
    )
    assert server._test_only_router_lock.acquire(blocking=False)
    started = time.monotonic()
    try:
        body = _post(server, timeout=3)
    finally:
        server._test_only_router_lock.release()

    assert time.monotonic() - started < 2
    assert body["wrench"]["fallback_reason"] == "router_queue_timeout"
    assert server.test_only_child_launches == 0


@pytest.mark.parametrize(
    ("invoker", "expected_reason"),
    [
        (_abstaining_invoker, "deterministic_test_failure"),
        (_raising_invoker, "router_invocation_error"),
    ],
)
def test_failure_opens_circuit_and_later_request_does_not_spawn(
    serving_server,
    invoker,
    expected_reason,
):
    server = serving_server(
        invoker,
        config=RouterConfig(max_attempts=4, failure_threshold=2),
    )

    first = _post(server)
    second = _post(server)
    third = _post(server)

    assert first["wrench"]["fallback_reason"] == expected_reason
    assert second["wrench"]["test_only_proposal_router"]["circuit_open"] is True
    assert second["wrench"]["test_only_proposal_router"]["attempts"] == 2
    assert third["wrench"]["fallback_reason"] == "router_disabled"
    assert server.test_only_child_launches == 2
    assert server.test_only_active_child_pids == ()


@pytest.mark.parametrize(
    "invoker",
    [_invalid_status_invoker, _abstain_without_reason_invoker],
    ids=["invalid-status", "missing-abstain-reason"],
)
def test_malformed_callback_result_abstains_and_opens_circuit(serving_server, invoker):
    server = serving_server(
        invoker,
        config=RouterConfig(max_attempts=3, failure_threshold=1),
    )

    malformed = _post(server)
    rejected = _post(server)

    assert malformed["wrench"]["status"] == "abstain"
    assert malformed["wrench"]["fallback_reason"] == "router_worker_result_invalid"
    assert malformed["wrench"]["test_only_proposal_router"]["circuit_open"] is True
    assert rejected["wrench"]["fallback_reason"] == "router_disabled"
    assert server.test_only_proposal_router.status()["failures"] == 1
    assert server.test_only_child_launches == 1
    assert server.test_only_active_child_pids == ()


def test_abrupt_child_failure_opens_circuit_and_reset_recovers(serving_server):
    server = serving_server(
        _abrupt_exit_invoker,
        config=RouterConfig(max_attempts=4, failure_threshold=1),
    )
    router = server.test_only_proposal_router

    failed = _post(server)
    blocked = _post(server)
    server.test_only_proposal_invoker = _accepted_invoker
    assert router.reset(router.config.config_hash)
    recovered = _post(server)

    assert failed["wrench"]["fallback_reason"] == "router_worker_exited_without_result"
    assert blocked["wrench"]["fallback_reason"] == "router_disabled"
    assert recovered["wrench"]["status"] == "accepted"
    assert recovered["wrench"]["test_only_proposal_router"]["attempts"] == 1
    assert server.test_only_child_launches == 2
    assert server.test_only_active_child_pids == ()


def test_server_shutdown_terminates_inflight_callback_child(tmp_path: Path):
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    server = WrenchHTTPServer(
        ("127.0.0.1", 0),
        WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
        model_name="wrench-gate-e-test",
        max_request_bytes=1024 * 1024,
        use_mechanical_route=False,
        test_only_proposal_router=ProposalRouter(),
        test_only_proposal_invoker=partial(_signal_then_wait, started),
        test_only_proposal_timeout_seconds=30,
    )
    serve_thread = threading.Thread(target=server.serve_forever, daemon=True)
    serve_thread.start()
    request_pool = ThreadPoolExecutor(max_workers=1)
    server_closed = False
    try:
        pending = request_pool.submit(_post, server)
        assert started.wait(timeout=12), "fake callback did not start within its bound"
        assert len(server.test_only_active_child_pids) == 1

        server.shutdown()
        server.server_close()
        server_closed = True
        serve_thread.join(timeout=3)
        body = pending.result(timeout=5)

        assert not serve_thread.is_alive()
        assert body["wrench"]["fallback_reason"] == "router_worker_exited_without_result"
        assert server.test_only_active_child_pids == ()
    finally:
        if not server_closed:
            if serve_thread.is_alive():
                server.shutdown()
            server.server_close()
        serve_thread.join(timeout=3)
        request_pool.shutdown(wait=True)


def test_cancellation_terminates_child_and_returns_through_handler(serving_server):
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    cancellation = CancellationToken()
    server = serving_server(
        partial(_signal_then_wait, started),
        timeout_seconds=8,
        cancellation=cancellation,
    )

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(_post, server)
        assert started.wait(timeout=12), "fake callback did not start within its bound"
        cancellation.cancel()
        body = pending.result(timeout=5)

    assert body["wrench"]["fallback_reason"] == "cancelled"
    assert server.test_only_proposal_router.status()["failures"] == 0
    assert server.test_only_active_child_pids == ()


def test_deadline_opens_circuit_and_terminates_child(serving_server):
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    server = serving_server(
        partial(_signal_then_wait, started),
        config=RouterConfig(max_attempts=2, failure_threshold=1),
        timeout_seconds=3,
    )

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(_post, server)
        assert started.wait(timeout=12), "fake callback did not start within its bound"
        body = pending.result(timeout=8)

    assert body["wrench"]["fallback_reason"] == "router_timeout"
    assert body["wrench"]["test_only_proposal_router"]["circuit_open"] is True
    launches_before_rejected_call = server.test_only_child_launches
    rejected = _post(server)
    assert rejected["wrench"]["fallback_reason"] == "router_disabled"
    assert server.test_only_child_launches == launches_before_rejected_call == 1
    assert server.test_only_active_child_pids == ()


@pytest.mark.parametrize(
    ("address", "upstream_url"),
    [
        (("0.0.0.0", 0), None),
        (("127.0.0.1", 0), "http://127.0.0.1:4000/v1"),
    ],
)
def test_test_only_integration_rejects_nonlocal_or_upstream_binding(
    tmp_path: Path,
    address: tuple[str, int],
    upstream_url: str | None,
):
    with pytest.raises(ValueError):
        WrenchHTTPServer(
            address,
            WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path),
            model_name="wrench-gate-e-test",
            max_request_bytes=1024 * 1024,
            upstream_url=upstream_url,
            test_only_proposal_router=ProposalRouter(),
            test_only_proposal_invoker=_accepted_invoker,
        )
