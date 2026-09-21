#!/usr/bin/env python3
"""Probe monster model-local input while ordinary Wrench work is in flight.

The package is started in mechanical-only mode. The probe therefore measures
raw 2M and 4M request admission, deterministic reduction metadata, and whether
small practical requests still complete while a monster request is active. It
does not claim dense native attention, retrieval quality, or production release.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from run_operational_shadow import _free_port, _memory_snapshot, _post, _wait_ready


def _build_payload(target_tokens: int) -> str:
    marker = "old reference symbol=run_worker path=src/wrench_harness/worker.py line=218\n"
    filler = "stale lookup telemetry record status observed unrelated historical reference-only data; "
    current = (
        'CURRENT INTENT: inspect the source for symbol "run_worker" and return '
        "one bounded read proposal with a 65536 byte limit."
    )
    filler_words = max(1, filler.count(" "))
    repeats = max(1, (target_tokens - marker.count(" ") - current.count(" ") - 64) // filler_words)
    return marker + filler * repeats + current


def _send_monster(endpoint: str, model: str, target_tokens: int) -> dict[str, Any]:
    admission_margin = 4_096
    content = _build_payload(max(1, target_tokens - admission_margin))
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0,
            "max_tokens": 1,
            "options": {"num_ctx": 4_000_000},
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
            http_status = response.status
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"monster_http_{exc.code}:{detail}") from exc
    elapsed_ms = (time.perf_counter() - started) * 1000
    wrench = payload.get("wrench", {})
    gate = wrench.get("context_gate") or {}
    return {
        "target_tokens": target_tokens,
        "admission_safety_margin_tokens": admission_margin,
        "request_bytes": len(body),
        "payload_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "http_status": http_status,
        "elapsed_ms": round(elapsed_ms, 3),
        "status": wrench.get("status"),
        "backend": wrench.get("backend"),
        "mechanical_fast_path": wrench.get("mechanical_fast_path"),
        "model_calls": wrench.get("model_calls"),
        "raw_input_tokens_estimate": wrench.get("raw_input_tokens_estimate"),
        "raw_input_chars": wrench.get("raw_input_chars"),
        "context_gate": {
            "raw_context_limit_tokens": gate.get("raw_context_limit_tokens"),
            "effective_working_context_tokens": gate.get("effective_working_context_tokens"),
            "working_context_budget_tokens": gate.get("working_context_budget_tokens"),
            "raw_payload_hash_bound": gate.get("raw_payload_hash_bound"),
            "gate_latency_ms": gate.get("gate_latency_ms"),
        },
    }


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
    try:
        _wait_ready(endpoint)
        monster_rows: list[dict[str, Any]] = []
        probe_rows: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            monster_futures = [pool.submit(_send_monster, endpoint, "wrench-monster-shadow", tokens) for tokens in args.tokens]
            deadline = time.perf_counter() + 180
            while time.perf_counter() < deadline and not all(future.done() for future in monster_futures):
                started = time.perf_counter()
                try:
                    result = _post(endpoint, "Read wrench-package.json with a 4096 byte limit.", 10)
                    result["probe_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
                    probe_rows.append(result)
                except Exception as exc:
                    probe_rows.append({"error": type(exc).__name__})
                time.sleep(0.02)
            for future in monster_futures:
                try:
                    monster_rows.append(future.result())
                except Exception as exc:
                    monster_rows.append({"error": str(exc)})
        after = _memory_snapshot()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    monster_pass = all(
        not row.get("error")
        and row.get("http_status") == 200
        and row.get("status") in {"accepted", "abstain"}
        and row.get("mechanical_fast_path") is True
        and row.get("model_calls") == 0
        and row.get("context_gate", {}).get("raw_payload_hash_bound") is True
        and row.get("context_gate", {}).get("effective_working_context_tokens", 0) <= 64_000
        for row in monster_rows
    )
    probe_success = [row for row in probe_rows if row.get("status") == "accepted"]
    receipt: dict[str, Any] = {
        "schema": "wrench.monster-context-shadow-receipt.v1",
        "status": "PASS_MODEL_LOCAL_2M_4M_WITH_CONCURRENT_WORK" if monster_pass and probe_success else "FAIL_MODEL_LOCAL_2M_4M_WITH_CONCURRENT_WORK",
        "scope": "local portable package mechanical route; no dense native attention or production claim",
        "package_dir": str(package_dir),
        "monster_rows": monster_rows,
        "ordinary_probe": {
            "count": len(probe_rows),
            "accepted": len(probe_success),
            "errors": sum("error" in row for row in probe_rows),
            "max_elapsed_ms": max((row.get("probe_elapsed_ms", 0) for row in probe_rows), default=None),
            "p95_elapsed_ms": sorted((row.get("probe_elapsed_ms", 0) for row in probe_rows))[max(0, int((len(probe_rows) - 1) * 0.95))] if probe_rows else None,
        },
        "resource_before": before,
        "resource_after": after,
        "checks": {
            "all_monster_points_pass": monster_pass,
            "ordinary_probe_recovered_while_monster_active": bool(probe_success),
            "zero_model_calls": all(row.get("model_calls") == 0 for row in monster_rows),
            "ram_reserve_before": before.get("ram_reserve_pass") is True,
            "ram_reserve_after": after.get("ram_reserve_pass") is True,
            "vram_reserve_before": before.get("vram_reserve_pass") is True,
            "vram_reserve_after": after.get("vram_reserve_pass") is True,
        },
    }
    receipt["all_checks_pass"] = all(receipt["checks"].values())
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tokens", type=int, nargs="+", default=[2_000_000, 4_000_000])
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if any(value < 1 for value in args.tokens):
        raise SystemExit("tokens must be positive")
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "all_checks_pass": receipt["all_checks_pass"], "output": str(args.output.resolve())}))
    return 0 if receipt["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
