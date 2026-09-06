"""Held-out evaluation and canary tests."""
from __future__ import annotations

from pathlib import Path

from wrench import ProductionDataBaseline, evaluate_baseline, iter_jsonl, run_canary


def test_baseline_evaluation_on_held_out_is_bounded():
    summary = evaluate_baseline("data/held_out.jsonl", limit=200)
    assert summary.total == 200
    assert 0.0 <= summary.schema_valid_rate <= 1.0
    assert 0.0 <= summary.arg_exact_rate <= summary.schema_valid_rate


def test_canary_reports_local_speedup():
    canary = run_canary(ProductionDataBaseline(), "data/held_out.jsonl", limit=200)
    assert canary.samples == 200
    assert canary.avg_local_latency_ms < canary.avg_cloud_latency_ms
    assert canary.cloud_tokens_saved > 0


def test_held_out_records_have_required_fields():
    path = Path("data/held_out.jsonl")
    for record in iter_jsonl(str(path)):
        assert {"tool", "args", "prompt"}.issubset(record)
        break
