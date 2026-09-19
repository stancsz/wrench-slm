from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.run_workflow_arm_replay import assemble


def _row(identifier: str, family: str, *, tokens: int, cost: float, latency: int, retries: int = 0) -> dict:
    return {
        "id": identifier,
        "family": family,
        "final_success": True,
        "prohibited_accept": False,
        "unexpected_mutation": False,
        "stronger_model_tokens": tokens,
        "total_tokens": tokens + 20,
        "cost_usd": cost,
        "latency_ms": latency,
        "retry_count": retries,
        "provider_requests": 1 + retries,
    }


def _write(path: Path, rows: list[dict]) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_replay_assembler_blocks_by_default_and_records_metrics(tmp_path: Path):
    cloud = _write(tmp_path / "cloud.jsonl", [_row("one", "read_file", tokens=100, cost=0.02, latency=1000)])
    rules = _write(tmp_path / "rules.jsonl", [_row("one", "read_file", tokens=90, cost=0.018, latency=800, retries=1)])
    learned = _write(tmp_path / "learned.jsonl", [_row("one", "read_file", tokens=70, cost=0.012, latency=500)])

    manifest, evaluation = assemble(cloud, rules, learned)

    assert manifest["schema"] == "wrench.workflow-arm-traces.v1"
    assert evaluation["status"] == "BLOCKED_TRACE_AUTHORIZATION"
    assert evaluation["arms"]["cloud_only"]["total_cost_usd"] == 0.02
    assert evaluation["arms"]["rules_plus_identical_fallback"]["total_retries"] == 1
    assert evaluation["paired_savings"] == []


def test_replay_assembler_scores_authorized_matched_receipts(tmp_path: Path):
    cloud_rows = [_row(f"case-{index}", "read_file", tokens=100, cost=0.02, latency=1000) for index in range(20)]
    rules_rows = [_row(f"case-{index}", "read_file", tokens=90, cost=0.018, latency=800) for index in range(20)]
    learned_rows = [_row(f"case-{index}", "read_file", tokens=70, cost=0.012, latency=500) for index in range(20)]
    cloud = _write(tmp_path / "cloud.jsonl", cloud_rows)
    rules = _write(tmp_path / "rules.jsonl", rules_rows)
    learned = _write(tmp_path / "learned.jsonl", learned_rows)

    _, evaluation = assemble(
        cloud,
        rules,
        learned,
        authorization="approved_real_workflow",
        capture_id="capture-001",
        captured_at="2026-09-19T00:00:00Z",
        reviewer="test-reviewer",
        source_scope="test-fixture",
    )

    assert evaluation["status"] == "PASS_WORKFLOW_ARM_METRICS"
    assert evaluation["paired_cost_savings"][0]["mean_cost_savings_rate"] == pytest.approx(0.4)
    assert evaluation["latency_comparison"]["cloud_only"]["learned_p95_ms"] == 500.0


def test_replay_assembler_rejects_unmatched_ids(tmp_path: Path):
    cloud = _write(tmp_path / "cloud.jsonl", [_row("one", "read_file", tokens=100, cost=0.02, latency=1000)])
    rules = _write(tmp_path / "rules.jsonl", [_row("two", "read_file", tokens=90, cost=0.018, latency=800)])
    learned = _write(tmp_path / "learned.jsonl", [_row("one", "read_file", tokens=70, cost=0.012, latency=500)])

    with pytest.raises(ValueError, match="matched trace IDs differ"):
        assemble(cloud, rules, learned)
