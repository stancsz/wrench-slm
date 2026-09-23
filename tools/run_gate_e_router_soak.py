"""Run the one approved, local-only Gate E fake-callback soak."""

from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
import csv
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
from urllib.parse import urlsplit
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "phases" / "phase-435-router-soak"
FIRST_RECEIPT_PATH = PHASE_DIR / "router-soak-receipt.json"
REQUEST_COUNT = 200
CONCURRENCY = 8
SOAK_LIMIT_SECONDS = 300.0
PROPOSAL_TIMEOUT_SECONDS = 20.0
REQUEST_TIMEOUT_SECONDS = 30.0
RESOURCE_SAMPLE_SECONDS = 2.0
MINIMUM_RESERVE_FRACTION = 0.10
MODEL_NAME = "wrench-phase-435-test-only"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from wrench_harness.router import ProposalRouter, RouterConfig  # noqa: E402
from wrench_harness.server import WrenchHTTPServer  # noqa: E402
from wrench_harness.worker import WrenchWorker  # noqa: E402


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _accepted_fake_callback() -> dict[str, str]:
    return {"status": "accepted", "test_marker": "phase-435-deterministic"}


def _resource_snapshot() -> dict[str, Any]:
    if os.name != "nt":
        raise RuntimeError("resource_monitor_requires_windows")

    memory = MEMORYSTATUSEX()
    memory.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    global_memory_status = ctypes.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx
    global_memory_status.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
    global_memory_status.restype = ctypes.c_bool
    if not global_memory_status(ctypes.byref(memory)):
        raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed")

    gpu_result = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
    )
    gpus = []
    for index, row in enumerate(csv.reader(gpu_result.stdout.splitlines())):
        if len(row) != 3:
            raise RuntimeError("resource_monitor_gpu_output_invalid")
        total_mib = int(row[1].strip())
        free_mib = int(row[2].strip())
        if total_mib <= 0 or free_mib < 0:
            raise RuntimeError("resource_monitor_gpu_values_invalid")
        gpus.append(
            {
                "index": index,
                "name": row[0].strip(),
                "total_bytes": total_mib * 1024 * 1024,
                "free_bytes": free_mib * 1024 * 1024,
                "free_fraction": free_mib / total_mib,
            }
        )
    if not gpus:
        raise RuntimeError("resource_monitor_no_gpu_reported")

    total_ram = int(memory.ullTotalPhys)
    free_ram = int(memory.ullAvailPhys)
    if total_ram <= 0 or free_ram < 0:
        raise RuntimeError("resource_monitor_ram_values_invalid")
    return {
        "ram": {
            "total_bytes": total_ram,
            "free_bytes": free_ram,
            "free_fraction": free_ram / total_ram,
        },
        "gpus": gpus,
    }


def _reserve_is_safe(snapshot: dict[str, Any]) -> bool:
    return snapshot["ram"]["free_fraction"] >= MINIMUM_RESERVE_FRACTION and all(
        gpu["free_fraction"] >= MINIMUM_RESERVE_FRACTION for gpu in snapshot["gpus"]
    )


def _request(endpoint: str) -> tuple[dict[str, Any], float]:
    parsed = urlsplit(endpoint)
    try:
        target_ip = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise RuntimeError("non_loopback_target_blocked") from exc
    if (
        parsed.scheme != "http"
        or not target_ip.is_loopback
        or parsed.path != "/v1/chat/completions"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("non_loopback_target_blocked")
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "Run the approved local fake-callback soak."}],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    started = time.monotonic()
    with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = json.loads(response.read().decode("utf-8"))
        if response.status != 200:
            raise RuntimeError("request_http_status_not_200")
    return body, (time.monotonic() - started) * 1000


def _request_is_accepted(body: dict[str, Any]) -> bool:
    if not isinstance(body, dict):
        return False
    wrench = body.get("wrench")
    if not isinstance(wrench, dict):
        return False
    router = wrench.get("test_only_proposal_router")
    return (
        wrench.get("status") == "accepted"
        and wrench.get("backend") == "test-only-proposal-router"
        and wrench.get("model_calls") == 0
        and isinstance(router, dict)
        and router.get("failures") == 0
    )


def _response_failure_observation(body: Any) -> dict[str, Any]:
    """Keep only bounded response metadata, never messages or arbitrary details."""

    if not isinstance(body, dict):
        return {"kind": "non_object_response", "response_type": type(body).__name__}
    wrench = body.get("wrench")
    if not isinstance(wrench, dict):
        return {"kind": "wrench_metadata_missing"}
    router = wrench.get("test_only_proposal_router")
    if not isinstance(router, dict):
        router = {}
    allowed_statuses = {"accepted", "abstain"}
    allowed_fallbacks = {
        "cancelled",
        "router_disabled",
        "router_invocation_error",
        "router_queue_timeout",
        "router_result_invalid",
        "router_timeout",
        "router_worker_did_not_exit",
        "router_worker_exited_without_result",
        "router_worker_result_invalid",
    }
    status = wrench.get("status")
    fallback = wrench.get("fallback_reason")
    backend = wrench.get("backend")
    model_calls = wrench.get("model_calls")
    attempts = router.get("attempts")
    failures = router.get("failures")
    circuit_open = router.get("circuit_open")
    return {
        "kind": "response_check_failed",
        "status": status
        if isinstance(status, str) and status in allowed_statuses
        else "other",
        "backend": backend if backend == "test-only-proposal-router" else "other",
        "fallback_reason": fallback
        if isinstance(fallback, str) and fallback in allowed_fallbacks
        else "other",
        "model_calls": model_calls if type(model_calls) is int and 0 <= model_calls <= 1000 else None,
        "router_attempts": attempts if type(attempts) is int and 0 <= attempts <= REQUEST_COUNT else None,
        "router_failures": failures if type(failures) is int and 0 <= failures <= REQUEST_COUNT else None,
        "circuit_open": circuit_open if type(circuit_open) is bool else None,
    }


def _next_receipt_destination(phase_dir: Path) -> tuple[int, Path]:
    """Select a new receipt path without replacing evidence from an earlier run."""

    first = phase_dir / FIRST_RECEIPT_PATH.name
    if not first.exists():
        return 1, first
    attempt = 2
    while True:
        candidate = phase_dir / f"router-soak-receipt-attempt-{attempt:02d}.json"
        if not candidate.exists():
            return attempt, candidate
        attempt += 1


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_identity() -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=5,
    ).stdout
    return {"head": revision, "tracked_worktree_dirty": bool(status.strip())}


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return round(ordered[index], 3)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        action="store_true",
        help="start the bounded local fake-callback soak",
    )
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        return 0

    attempt_number, receipt_path = _next_receipt_destination(PHASE_DIR)
    start_utc = datetime.now(timezone.utc).isoformat()
    run_started = time.monotonic()
    samples: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    requests_started = 0
    requests_succeeded = 0
    requests_failed = 0
    requests_cancelled = 0
    response_failure_observations: list[dict[str, Any]] = []
    failure_code: str | None = None
    failure_type: str | None = None
    server: WrenchHTTPServer | None = None
    serve_thread: threading.Thread | None = None
    executor: concurrent.futures.ThreadPoolExecutor | None = None
    monitor_stop = threading.Event()
    reserve_breached = threading.Event()
    monitor_error: list[str] = []
    monitor_thread: threading.Thread | None = None
    active_children_before_close: tuple[int, ...] = ()
    final_router_status: dict[str, Any] | None = None
    temp_dir: tempfile.TemporaryDirectory[str] | None = None

    try:
        baseline = _resource_snapshot()
        samples.append({"seconds": 0.0, **baseline})
        if not _reserve_is_safe(baseline):
            failure_code = "resource_preflight_reserve_below_10_percent"
            raise RuntimeError(failure_code)

        def monitor_resources() -> None:
            while not monitor_stop.wait(RESOURCE_SAMPLE_SECONDS):
                try:
                    snapshot = _resource_snapshot()
                    samples.append({"seconds": round(time.monotonic() - run_started, 3), **snapshot})
                    if not _reserve_is_safe(snapshot):
                        reserve_breached.set()
                        return
                except Exception as exc:  # noqa: BLE001
                    monitor_error.append(type(exc).__name__)
                    return

        monitor_thread = threading.Thread(
            target=monitor_resources,
            name="phase-435-resource-monitor",
            daemon=True,
        )
        monitor_thread.start()

        temp_dir = tempfile.TemporaryDirectory(prefix="wrench-phase-435-")
        server = WrenchHTTPServer(
            ("127.0.0.1", 0),
            WrenchWorker(tokenizer=None, model=None, allowed_root=Path(temp_dir.name)),
            model_name=MODEL_NAME,
            max_request_bytes=1024 * 1024,
            use_mechanical_route=False,
            upstream_url=None,
            test_only_proposal_router=ProposalRouter(
                RouterConfig(max_attempts=REQUEST_COUNT, failure_threshold=2)
            ),
            test_only_proposal_invoker=_accepted_fake_callback,
            test_only_proposal_timeout_seconds=PROPOSAL_TIMEOUT_SECONDS,
        )
        server_ip = ipaddress.ip_address(server.server_address[0])
        if not server_ip.is_loopback or server.server_address[0] != "127.0.0.1":
            failure_code = "server_bind_not_exact_ipv4_loopback"
            raise RuntimeError(failure_code)
        if server.upstream_url is not None or server.test_only_proposal_router is None:
            failure_code = "test_only_isolation_configuration_invalid"
            raise RuntimeError(failure_code)

        serve_thread = threading.Thread(
            target=server.serve_forever,
            name="phase-435-loopback-http-server",
            daemon=True,
        )
        serve_thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY)
        pending: dict[concurrent.futures.Future[tuple[dict[str, Any], float]], int] = {}
        next_request_index = 0
        deadline = run_started + SOAK_LIMIT_SECONDS

        def consume(future: concurrent.futures.Future[tuple[dict[str, Any], float]]) -> bool:
            nonlocal requests_succeeded, requests_failed
            try:
                body, elapsed_ms = future.result()
            except Exception as exc:  # noqa: BLE001
                requests_failed += 1
                if failure_code is None:
                    monitor_error.append(type(exc).__name__)
                response_failure_observations.append(
                    {"kind": "request_exception", "exception_type": type(exc).__name__}
                )
                return False
            if not _request_is_accepted(body):
                requests_failed += 1
                response_failure_observations.append(_response_failure_observation(body))
                return False
            requests_succeeded += 1
            latencies_ms.append(elapsed_ms)
            return True

        while pending or next_request_index < REQUEST_COUNT:
            if reserve_breached.is_set():
                failure_code = "resource_reserve_breached"
                break
            if monitor_error:
                failure_code = "resource_monitor_or_request_exception"
                break
            if time.monotonic() >= deadline:
                failure_code = "five_minute_run_limit_reached"
                break

            while len(pending) < CONCURRENCY and next_request_index < REQUEST_COUNT:
                future = executor.submit(_request, endpoint)
                pending[future] = next_request_index
                next_request_index += 1
                requests_started += 1

            remaining = max(0.0, deadline - time.monotonic())
            done, _ = concurrent.futures.wait(
                pending,
                timeout=min(0.25, remaining),
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            for future in done:
                pending.pop(future)
                if not consume(future):
                    failure_code = failure_code or "request_or_response_check_failed"
                    break
            if failure_code is not None:
                break

        if failure_code is not None:
            for future in pending:
                if future.cancel():
                    requests_cancelled += 1

        executor.shutdown(wait=True, cancel_futures=failure_code is not None)
        executor = None
        for future in list(pending):
            if future.cancelled():
                continue
            if not consume(future) and failure_code is None:
                failure_code = "request_or_response_check_failed"
        pending.clear()

        final_router_status = server.test_only_proposal_router.status()
        active_children_before_close = server.test_only_active_child_pids
        if active_children_before_close and failure_code is None:
            failure_code = "callback_child_still_active_after_requests"
        if requests_succeeded != REQUEST_COUNT and failure_code is None:
            failure_code = "completed_request_count_not_200"
        if final_router_status.get("attempts") != requests_succeeded or final_router_status.get("failures") != 0:
            failure_code = failure_code or "router_counters_mismatch"
    except BaseException as exc:  # noqa: BLE001
        failure_type = type(exc).__name__
        failure_code = failure_code or "soak_execution_exception"
    finally:
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)
        monitor_stop.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=6)
            if monitor_thread.is_alive() and failure_code is None:
                failure_code = "resource_monitor_did_not_stop"
        if server is not None:
            try:
                if serve_thread is not None and serve_thread.is_alive():
                    server.shutdown()
                server.server_close()
                if serve_thread is not None:
                    serve_thread.join(timeout=3)
                    if serve_thread.is_alive() and failure_code is None:
                        failure_code = "http_server_did_not_stop"
            except Exception as exc:  # noqa: BLE001
                failure_type = failure_type or type(exc).__name__
                failure_code = failure_code or "server_cleanup_failed"
        if temp_dir is not None:
            temp_dir.cleanup()

    try:
        final_resources = _resource_snapshot()
        samples.append({"seconds": round(time.monotonic() - run_started, 3), **final_resources})
        if not _reserve_is_safe(final_resources) and failure_code is None:
            failure_code = "resource_reserve_breached_at_completion"
    except Exception as exc:  # noqa: BLE001
        final_resources = None
        failure_type = failure_type or type(exc).__name__
        failure_code = failure_code or "final_resource_sample_failed"

    minimum_ram_free = min(
        (sample["ram"]["free_fraction"] for sample in samples),
        default=None,
    )
    minimum_gpu_free: dict[str, float] = {}
    for sample in samples:
        for gpu in sample["gpus"]:
            name = gpu["name"]
            minimum_gpu_free[name] = min(
                minimum_gpu_free.get(name, gpu["free_fraction"]), gpu["free_fraction"]
            )

    try:
        git = _git_identity()
        source_hashes = {
            "runner_sha256": _file_sha256(Path(__file__).resolve()),
            "server_sha256": _file_sha256(ROOT / "src" / "wrench_harness" / "server.py"),
            "focused_test_sha256": _file_sha256(ROOT / "tests" / "test_gate_e_serving_path.py"),
            "q4_contract_sha256": _file_sha256(ROOT / "COLLABORATION_CONTRACT.json"),
        }
    except Exception as exc:  # noqa: BLE001
        git = {"head": None, "tracked_worktree_dirty": None}
        source_hashes = {}
        failure_type = failure_type or type(exc).__name__
        failure_code = failure_code or "source_identity_capture_failed"

    status = "PASS" if failure_code is None and requests_succeeded == REQUEST_COUNT else "FAIL"
    receipt = {
        "schema": "wrench.gate-e-router-soak.v1",
        "phase": 435,
        "attempt": attempt_number,
        "status": status,
        "authorization": "Human approved this exact test-only local soak in the active task.",
        "started_at_utc": start_utc,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.monotonic() - run_started, 3),
        "limits": {
            "requests": REQUEST_COUNT,
            "concurrency": CONCURRENCY,
            "duration_seconds": SOAK_LIMIT_SECONDS,
            "minimum_ram_and_vram_reserve_fraction": MINIMUM_RESERVE_FRACTION,
        },
        "results": {
            "requests_started": requests_started,
            "requests_succeeded": requests_succeeded,
            "requests_failed": requests_failed,
            "requests_cancelled": requests_cancelled,
            "failure_observations": response_failure_observations,
            "callback_child_launches": (
                server.test_only_child_launches if server is not None else 0
            ),
            "router_status": final_router_status,
            "active_children_before_server_close": list(active_children_before_close),
            "active_children_after_server_close": (
                list(server.test_only_active_child_pids) if server is not None else []
            ),
            "latency_ms": {
                "min": round(min(latencies_ms), 3) if latencies_ms else None,
                "median": round(statistics.median(latencies_ms), 3) if latencies_ms else None,
                "p95": _percentile(latencies_ms, 0.95),
                "max": round(max(latencies_ms), 3) if latencies_ms else None,
            },
        },
        "isolation": {
            "bind": "127.0.0.1",
            "ephemeral_port": server.server_port if server is not None else None,
            "test_only_callback_injection": True,
            "upstream_url_configured": False,
            "provider_requests": 0,
            "model_calls": 0,
            "credentials_accessed": False,
            "request_payloads_or_prompts_persisted": False,
        },
        "resources": {
            "sampling_interval_seconds": RESOURCE_SAMPLE_SECONDS,
            "minimum_observed_ram_free_fraction": round(minimum_ram_free, 4)
            if minimum_ram_free is not None
            else None,
            "minimum_observed_gpu_free_fraction_by_name": {
                name: round(fraction, 4) for name, fraction in minimum_gpu_free.items()
            },
            "final_snapshot": final_resources,
        },
        "identity": {
            "git": git,
            "source_sha256": source_hashes,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "model": "not loaded; WrenchWorker receives tokenizer=None and model=None",
            "independent_model_verifier": "not invoked; local HTTP response fields checked by this runner",
        },
        "failure": {"code": failure_code, "exception_type": failure_type}
        if failure_code is not None
        else None,
    }

    PHASE_DIR.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "receipt": str(receipt_path), "failure": receipt["failure"]}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
