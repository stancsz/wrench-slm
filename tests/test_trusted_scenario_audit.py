import hashlib
import json

import pytest

from scripts.trusted_scenario_audit import audit, build_schedule, calculate_cost, validate_row


def _row(source_class="synthetic"):
    return {
        "id": "scenario-1",
        "source_class": source_class,
        "source_ref_sha256": hashlib.sha256(b"approved-source").hexdigest(),
        "redaction": {"status": "complete", "method": "operator-review-v1"},
        "prompt": "Read the visible configuration region.",
        "context": {"platform": "windows", "tool": "read_file"},
        "replay_eligible": True,
    }


def _ledger():
    return {
        "version": "price-v1",
        "provider": "example-provider",
        "model": "example-model",
        "currency": "USD",
        "effective_from": "2026-01-01",
        "source": "operator-approved-price-sheet",
        "input_price_per_million": 1.0,
        "cached_input_price_per_million": 0.25,
        "output_price_per_million": 2.0,
    }


def test_schema_only_audit_does_not_make_a_production_claim(tmp_path):
    scenarios = tmp_path / "scenarios.jsonl"
    scenarios.write_text(json.dumps(_row()) + "\n", encoding="utf-8")
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(_ledger()), encoding="utf-8")
    result = audit(scenarios, ledger, tmp_path / "receipt", allow_no_production=True)
    assert result["status"] == "SCHEMA_VALID_NO_PRODUCTION"
    assert not result["production_claim_allowed"]


def test_audit_requires_observed_production_rows_for_production_claim(tmp_path):
    scenarios = tmp_path / "scenarios.jsonl"
    scenarios.write_text(json.dumps(_row()) + "\n", encoding="utf-8")
    ledger = tmp_path / "ledger.json"
    ledger.write_text(json.dumps(_ledger()), encoding="utf-8")
    result = audit(scenarios, ledger, tmp_path / "receipt")
    assert result["status"] == "REJECTED"
    assert any("no observed_production_replay" in error for error in result["errors"])


def test_secret_and_private_gold_fields_are_rejected():
    row = _row()
    row["expected_answer"] = "do not use this"
    row["prompt"] = "Use api_key=supersecretvalue"
    errors = validate_row(row, 1)
    assert any("private evaluator fields" in error for error in errors)
    assert any("possible secret" in error for error in errors)


def test_audit_requires_explicit_replay_eligibility():
    row = _row()
    del row["replay_eligible"]
    errors = validate_row(row, 1)
    assert any("replay_eligible must be explicitly boolean" in error for error in errors)


def test_cost_ledger_calculates_cached_input_separately():
    cost = calculate_cost({"prompt_tokens": 1000, "cached_tokens": 400, "completion_tokens": 200}, _ledger())
    assert cost == pytest.approx((600 * 1.0 + 400 * 0.25 + 200 * 2.0) / 1_000_000)


def test_replay_schedule_is_deterministic_and_stratified():
    rows = [_row("observed_production_replay"), {**_row("synthetic"), "id": "scenario-2"},
            {**_row("adversarial"), "id": "scenario-3"}]
    first = build_schedule(rows, 3, 7)
    second = build_schedule(rows, 3, 7)
    assert first == second
    assert {row["source_class"] for row in first} == {"observed_production_replay", "synthetic", "adversarial"}


def test_replay_schedule_rejects_oversampling():
    with pytest.raises(ValueError, match="exceeds replay-eligible"):
        build_schedule([_row()], 2, 7)
