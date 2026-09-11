import json

from scripts.profile_production_usage import profile


def test_profile_reports_usage_coverage_without_inventing_cost():
    result = profile([
        {"model": "m", "route": "cheap", "prompt_tokens": 100, "completion_tokens": 20, "cached_tokens": 10, "duration": 1.0, "ts": "2026-09-10T00:00:00Z"},
        {"model": "m", "route": "frontier", "prompt_tokens": 50, "completion_tokens": 5, "duration": 2.0, "ts": "2026-09-10T01:00:00Z"},
        {"model": "m", "route": "frontier", "ts": "2026-09-10T02:00:00Z"},
    ])
    assert result["events"] == 3
    assert result["complete_usage_events"] == 2
    assert result["usage_coverage"] == 2 / 3
    assert result["cached_tokens_total"] == 10
    assert result["cost_status"] == "PRICE_LEDGER_REQUIRED"
    assert result["estimated_cost_usd"] is None


def test_profile_calculates_cost_only_for_matching_ledger_model():
    ledger = {
        "model": "m",
        "input_price_per_million": 1.0,
        "cached_input_price_per_million": 0.25,
        "output_price_per_million": 2.0,
    }
    result = profile([{"model": "m", "prompt_tokens": 1000, "completion_tokens": 200, "cached_tokens": 400}], ledger)
    assert result["cost_status"] == "CALCULATED"
    assert result["cost_rows"] == 1
    assert result["estimated_cost_usd"] == (600 + 100 + 400) / 1_000_000


def test_profile_does_not_report_mean_for_unverified_duration_outliers():
    result = profile([
        {"model": "m", "duration": 1.0},
        {"model": "m", "duration": 2.0},
        {"model": "m", "duration": 9_000_000.0},
    ])
    assert result["duration_unit_status"] == "MIXED_OR_OUTLIER"
    assert result["duration_outlier_count_over_3600"] == 1
    assert result["duration_mean"] is None
    assert result["duration_p50"] == 2.0
