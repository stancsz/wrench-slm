from __future__ import annotations

import json
from pathlib import Path

from tools.simulate_5060ti_worker_claim import simulate_claim


def _manifest() -> dict:
    return {
        "schema": "wrench.worker-job.v1",
        "job_id": "mock-5060-job",
        "execution": {"script": "tools/run_5060ti_hf_preflight.ps1"},
        "resource_requirements": {
            "minimum_host_ram_free_fraction": 0.1,
            "minimum_host_vram_free_fraction": 0.1,
        },
        "state": "pending",
        "queue_contract": "jobs/pending -> jobs/running -> jobs/completed or jobs/failed",
    }


def test_mock_claim_is_atomic_and_never_claims_hardware(tmp_path: Path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    queue_root = tmp_path / "queue"

    result = simulate_claim(manifest_path, queue_root)

    assert result["status"] == "BLOCKED_MOCK_ONLY"
    assert result["independent_5060_claim"] is False
    assert result["pending_entries"] == 0
    assert result["running_entries"] == 0
    assert result["completed_entries"] == 0
    assert result["failed_entries"] == 3

    receipt = json.loads(Path(result["terminal_receipt"]).read_text(encoding="utf-8"))
    assert receipt["actual_execution"] is False
    assert receipt["gpu_identity"] is None
    assert [item["to"] for item in receipt["state_transitions"]] == ["pending", "running", "failed"]
    assert receipt["state_transitions"][1]["atomic"] is True

