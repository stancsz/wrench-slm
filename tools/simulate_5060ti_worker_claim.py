#!/usr/bin/env python3
"""Dry-run the 5060 Ti queue claim and receipt protocol without hardware work."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema") != "wrench.worker-job.v1":
        raise ValueError("worker manifest schema mismatch")
    job_id = manifest.get("job_id")
    if not isinstance(job_id, str) or not job_id or any(char in job_id for char in "\\/:"):
        raise ValueError("worker manifest job_id must be a safe non-empty path component")
    if manifest.get("state") != "pending":
        raise ValueError("mock claim requires a pending manifest")
    if manifest.get("queue_contract") != "jobs/pending -> jobs/running -> jobs/completed or jobs/failed":
        raise ValueError("worker manifest queue contract mismatch")
    execution = manifest.get("execution")
    if not isinstance(execution, dict) or not isinstance(execution.get("script"), str):
        raise ValueError("worker manifest execution script is required")
    requirements = manifest.get("resource_requirements")
    if not isinstance(requirements, dict):
        raise ValueError("worker manifest resource requirements are required")
    if requirements.get("minimum_host_ram_free_fraction") != 0.1:
        raise ValueError("manifest must require the 10 percent RAM reserve")
    if requirements.get("minimum_host_vram_free_fraction") != 0.1:
        raise ValueError("manifest must require the 10 percent VRAM reserve")


def simulate_claim(manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("worker manifest must be a JSON object")
    _validate_manifest(manifest)

    job_id = str(manifest["job_id"])
    queue_root = output_dir.resolve()
    if queue_root.exists() and any(queue_root.iterdir()):
        raise ValueError(f"mock queue output must be empty: {queue_root}")
    queue_root.mkdir(parents=True, exist_ok=True)
    pending = queue_root / "jobs" / "pending"
    running = queue_root / "jobs" / "running"
    failed = queue_root / "jobs" / "failed"
    completed = queue_root / "jobs" / "completed"
    for directory in (pending, running, failed, completed):
        directory.mkdir(parents=True, exist_ok=True)

    nonce = uuid.uuid4().hex
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    transitions: list[dict[str, Any]] = []

    local_pending = pending / f"{job_id}.json"
    local_pending.write_bytes(raw)
    transitions.append({"from": None, "to": "pending", "atomic": True})

    local_running = running / local_pending.name
    os.replace(local_pending, local_running)
    transitions.append({"from": "pending", "to": "running", "atomic": True})

    liveness = {
        "schema": "wrench.worker-liveness-receipt.v1",
        "job_id": job_id,
        "claim_nonce": nonce,
        "queue_state": "running",
        "status": "MOCK_LIVENESS_ONLY",
        "manifest_sha256": manifest_sha256,
        "worker_identity": "local-mock-executor",
        "hardware_identity": None,
        "claimed_at_unix": time.time(),
        "actual_execution": False,
        "independent_5060_claim": False,
        "resource_reserve": {
            "required_host_ram_free_fraction": 0.1,
            "required_host_vram_free_fraction": 0.1,
            "measured": False,
            "status": "NOT_MEASURED_IN_MOCK",
        },
    }
    running_liveness = running / f"{job_id}.liveness.json"
    _write_json(running_liveness, liveness)

    local_failed = failed / local_running.name
    os.replace(local_running, local_failed)
    failed_liveness = failed / running_liveness.name
    os.replace(running_liveness, failed_liveness)
    transitions.append({"from": "running", "to": "failed", "atomic": True})

    terminal = {
        "schema": "wrench.worker-mock-orchestration-receipt.v1",
        "job_id": job_id,
        "claim_nonce": nonce,
        "queue_state": "failed",
        "status": "BLOCKED_MOCK_ONLY",
        "manifest_sha256": manifest_sha256,
        "state_transitions": transitions,
        "attempted_command": manifest["execution"]["script"],
        "command_started": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "worker_identity": "local-mock-executor",
        "gpu_identity": None,
        "latency_ms": None,
        "peak_memory": None,
        "resource_reserve": {
            "required_host_ram_free_fraction": 0.1,
            "required_host_vram_free_fraction": 0.1,
            "measured": False,
            "status": "NOT_MEASURED_IN_MOCK",
        },
        "actual_execution": False,
        "independent_5060_claim": False,
        "claims_not_authorized": [
            "RTX 5060 Ti execution",
            "GPU identity",
            "latency or memory performance",
            "package validation on the worker",
        ],
    }
    terminal_path = failed / f"{job_id}.mock-receipt.json"
    _write_json(terminal_path, terminal)
    transition_path = queue_root / "transitions.jsonl"
    transition_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in transitions),
        encoding="utf-8",
    )
    return {
        "status": terminal["status"],
        "job_id": job_id,
        "claim_nonce": nonce,
        "manifest_sha256": manifest_sha256,
        "queue_root": str(queue_root),
        "liveness_receipt": str(failed_liveness),
        "terminal_receipt": str(terminal_path),
        "pending_entries": len(list(pending.iterdir())),
        "running_entries": len(list(running.iterdir())),
        "failed_entries": len(list(failed.iterdir())),
        "completed_entries": len(list(completed.iterdir())),
        "independent_5060_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = simulate_claim(args.manifest, args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

