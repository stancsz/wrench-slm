#!/usr/bin/env python3
"""Run a bounded operational shadow against the portable Wrench package.

This is a local, no-mutation Gate E probe. It starts the downloaded package in
mechanical-only mode, sends a small counterbalanced request set concurrently,
and records recovery after a deliberately cancelled client request. It does
not claim production readiness or model quality.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


REQUESTS = (
    ("read_file", "Read wrench-package.json with a 4096 byte limit."),
    ("read_lines", "Read lines 1 through 12 from README.md."),
    ("literal_search", "Search the repository for the literal Wrench."),
    ("git_read_status", "Read git status for this repository."),
    ("health_read", "Read http://127.0.0.1:1/health with a 1 second timeout and a 1024 byte response cap."),
    (
        "patch_draft",
        "Draft a review-only patch for README.md changing no files. Show a bounded diff only.",
    ),
)


def _memory_snapshot() -> dict[str, Any]:
    try:
        import psutil

        memory = psutil.virtual_memory()
        result: dict[str, Any] = {
            "ram_total_bytes": int(memory.total),
            "ram_available_bytes": int(memory.available),
            "ram_available_ratio": round(memory.available / memory.total, 4),
        }
    except Exception as exc:  # pragma: no cover - optional host dependency
        result = {"memory_probe_error": type(exc).__name__}
    try:
        import torch

        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            result.update(
                {
                    "vram_total_bytes": int(total),
                    "vram_free_bytes": int(free),
                    "vram_free_ratio": round(free / total, 4),
                }
            )
        else:
            result["vram_available"] = False
    except Exception as exc:  # pragma: no cover - optional host dependency
        result["vram_probe_error"] = type(exc).__name__
    result["ram_reserve_pass"] = result.get("ram_available_ratio", 0) >= 0.10
    result["vram_reserve_pass"] = (
        result.get("vram_available") is False
        or result.get("vram_free_ratio", 0) >= 0.10
    )
    return result


def _post(endpoint: str, prompt: str, timeout: float) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": "wrench-operational-shadow",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 64,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elapsed_ms = (time.perf_counter() - started) * 1000
    wrench = payload.get("wrench") if isinstance(payload, dict) else None
    if not isinstance(wrench, dict):
        raise ValueError("missing_wrench_receipt")
    return {
        "elapsed_ms": round(elapsed_ms, 3),
        "status": wrench.get("status"),
        "backend": wrench.get("backend"),
        "mechanical_fast_path": wrench.get("mechanical_fast_path"),
        "model_calls": wrench.get("model_calls"),
        "cost_accounting": wrench.get("cost_accounting"),
    }


def _wait_ready(endpoint: str) -> None:
    deadline = time.perf_counter() + 15
    last_error = "not_started"
    while time.perf_counter() < deadline:
        try:
            result = _post(endpoint, "Read wrench-package.json with a 4096 byte limit.", 2)
            if result["status"] == "accepted":
                return
            last_error = "readiness_not_accepted"
        except Exception as exc:
            last_error = type(exc).__name__
        time.sleep(0.1)
    raise RuntimeError(f"server_not_ready:{last_error}")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return round(ordered[index], 3)


def _latency_by_action(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for row in rows:
        action = row.get("action")
        elapsed = row.get("elapsed_ms")
        if not isinstance(action, str) or not isinstance(elapsed, (int, float)):
            continue
        grouped.setdefault(action, []).append(float(elapsed))
    return {
        action: {
            "count": len(values),
            "p50": _percentile(values, 0.50),
            "p95": _percentile(values, 0.95),
            "max": max(values),
        }
        for action, values in sorted(grouped.items())
        if values
    }


def _receipt_digest(rows: list[dict[str, Any]], recovery: dict[str, Any], errors: list[str]) -> str:
    seed = json.dumps({"rows": rows, "recovery": recovery, "errors": errors}, sort_keys=True).encode()
    return hashlib.sha256(seed).hexdigest()


def run(args: argparse.Namespace) -> dict[str, Any]:
    package_dir = args.package_dir.resolve()
    server_script = package_dir / "wrench_server.py"
    if not server_script.is_file():
        raise FileNotFoundError(server_script)
    port = args.port or _free_port()
    endpoint = f"http://127.0.0.1:{port}/v1/chat/completions"
    before = _memory_snapshot()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_dir) + os.pathsep + env.get("PYTHONPATH", "")
    process = subprocess.Popen(
        [sys.executable, str(server_script), "--model-dir", str(package_dir), "--port", str(port), "--mechanical-only"],
        cwd=str(package_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        _wait_ready(endpoint)
        tasks = [REQUESTS[index % len(REQUESTS)] for index in range(args.rounds * args.concurrency)]
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {
                pool.submit(_post, endpoint, prompt, args.timeout): action
                for action, prompt in tasks
            }
            for future in concurrent.futures.as_completed(futures):
                action = futures[future]
                try:
                    result = future.result()
                    result["action"] = action
                    rows.append(result)
                except Exception as exc:
                    errors.append(f"{action}:{type(exc).__name__}")
        burst_elapsed_ms = (time.perf_counter() - started) * 1000

        # Deliberately close a client socket while the server is reading a
        # request. The next normal request must still complete successfully.
        cancelled = False
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=2)
            sock.sendall(b"POST /v1/chat/completions HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 999999\r\n\r\n")
            sock.close()
            cancelled = True
        except OSError as exc:
            errors.append(f"cancel_probe:{type(exc).__name__}")
        recovery = _post(endpoint, "Read wrench-package.json with a 4096 byte limit.", args.timeout)
        after = _memory_snapshot()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    latencies = [float(row["elapsed_ms"]) for row in rows]
    accepted_latencies = [
        float(row["elapsed_ms"])
        for row in rows
        if row.get("status") == "accepted"
    ]
    accepted = sum(row.get("status") == "accepted" for row in rows)
    abstained = sum(row.get("status") == "abstain" for row in rows)
    mechanical = sum(row.get("mechanical_fast_path") is True for row in rows)
    model_calls = sum(int(row.get("model_calls") or 0) for row in rows)
    bounded_statuses = {"accepted", "abstain"}
    status_histogram: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status"))
        status_histogram[status] = status_histogram.get(status, 0) + 1
    receipt = {
        "schema": "wrench.operational-shadow-receipt.v1",
        "status": "PENDING_CHECKS",
        "scope": "local mechanical-only portable package; no tool execution; no production approval",
        "package_dir": str(package_dir),
        "concurrency": args.concurrency,
        "rounds": args.rounds,
        "requests_expected": len(tasks),
        "requests_completed": len(rows),
        "errors": errors,
        "rows": rows,
        "accepted": accepted,
        "abstained": abstained,
        "status_histogram": status_histogram,
        "mechanical_fast_path": mechanical,
        "model_calls": model_calls,
        "latency_ms": {
            "p50": _percentile(latencies, 0.50) if latencies else None,
            "p95": _percentile(latencies, 0.95) if latencies else None,
            "max": max(latencies) if latencies else None,
            "burst_elapsed": round(burst_elapsed_ms, 3),
            "accepted_only_p50": _percentile(accepted_latencies, 0.50) if accepted_latencies else None,
            "accepted_only_p95": _percentile(accepted_latencies, 0.95) if accepted_latencies else None,
        },
        "latency_by_action_ms": _latency_by_action(rows),
        "cancel_probe": {"client_closed_mid_request": cancelled, "recovery": recovery},
        "resource_before": before,
        "resource_after": after,
        "checks": {
            "all_expected_requests_completed": len(rows) == len(tasks),
            "all_responses_bounded": all(row.get("status") in bounded_statuses for row in rows),
            "mechanical_fast_path_coverage_recorded": True,
            "zero_model_calls": model_calls == 0,
            "cancel_recovery_accepted": cancelled and recovery.get("status") == "accepted",
            "ram_reserve_before": before.get("ram_reserve_pass") is True,
            "ram_reserve_after": after.get("ram_reserve_pass") is True,
            "vram_reserve_before": before.get("vram_reserve_pass") is True,
            "vram_reserve_after": after.get("vram_reserve_pass") is True,
        },
    }
    receipt["all_checks_pass"] = all(receipt["checks"].values())
    receipt["status"] = (
        "PASS_BOUNDED_OPERATIONAL_SHADOW"
        if receipt["all_checks_pass"]
        else "FAIL_BOUNDED_OPERATIONAL_SHADOW"
    )
    receipt["receipt_sha256"] = _receipt_digest(rows, recovery, errors)
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if args.concurrency < 1 or args.rounds < 1 or args.timeout <= 0:
        raise SystemExit("concurrency, rounds, and timeout must be positive")
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "all_checks_pass": receipt["all_checks_pass"], "output": str(args.output.resolve())}))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
