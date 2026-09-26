from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import measure_synthetic_context_token_reduction as runner


ROOT = Path(__file__).resolve().parents[1]


def _fixture():
    return json.loads((ROOT / runner.LOCALIZATION_FIXTURE_REL).read_text(encoding="utf-8"))


def test_cli_selects_legacy_by_default_and_localization_only_by_explicit_profile():
    default = runner._build_parser().parse_args([])
    selected = runner._build_parser().parse_args(["--profile", "localization-screen-02"])
    assert default.profile is None and default.output is None
    assert selected.profile == runner.LOCALIZATION_PROFILE
    assert runner.OUTPUT_DEFAULT.name == "synthetic-context-m3-reduction-05.json"
    assert runner.LOCALIZATION_OUTPUT_DEFAULT.name == "localization-screen-02-tokenizer-reduction.json"


def test_main_keeps_legacy_default_dispatch_and_explicit_profile_dispatch_separate():
    with patch.object(sys, "argv", ["measure_synthetic_context_token_reduction.py"]):
        with patch.object(runner, "measure", return_value={
            "status": "complete", "acceptance_status": "FAIL",
            "positive_context_evidence_pass_count": 0, "boundary_pass_count": 0,
            "total": {}, "frontier_token_savings_percent": None,
        }) as legacy:
            with contextlib.redirect_stdout(io.StringIO()):
                assert runner.main() == 0
        legacy.assert_called_once_with(runner.OUTPUT_DEFAULT)
    with patch.object(sys, "argv", ["measure_synthetic_context_token_reduction.py", "--profile", runner.LOCALIZATION_PROFILE]):
        with patch.object(runner, "measure_localization_profile", return_value={
            "status": "complete", "profile_id": runner.LOCALIZATION_PROFILE,
            "summary": {"eligible_count": 0, "mean_per_task_reduction_percent": None, "ratio_of_sums_reduction_percent": None},
            "boundary_pass_count": 0, "frontier_token_savings_percent": None,
        }) as localization:
            with contextlib.redirect_stdout(io.StringIO()):
                assert runner.main() == 0
        localization.assert_called_once_with(runner.LOCALIZATION_OUTPUT_DEFAULT)


def test_positive_eligibility_requires_exact_path_hash_and_complete_quote_visibility():
    case = next(row for row in _fixture()["cases"] if row["case_id"] == "loc02-positive-01")
    source = case["files"][0]
    snapshot_sha = "a" * 64
    eid = runner._evidence_id(snapshot_sha, source["path"], source["sha256"])
    row = SimpleNamespace(path=source["path"], status="ok", content_sha256=source["sha256"])
    selected = {eid}
    payload = f"[context:{eid}]\n{source['content_utf8']}"
    assert runner._localization_evidence_visible(
        case, snapshot_sha256=snapshot_sha, source_rows=[row], selected=selected, payload=payload
    ) == (True, None)
    missing_quote_payload = payload.replace("ledger.commit_settlement(invoice_id)", "ledger.commit(invoice_id)")
    visible, reason = runner._localization_evidence_visible(
        case, snapshot_sha256=snapshot_sha, source_rows=[row], selected=selected, payload=missing_quote_payload
    )
    assert visible is False
    assert reason == "required_quote_not_visible_in_bound_context"
    other_row = SimpleNamespace(path=source["path"], status="ok", content_sha256="b" * 64)
    visible, reason = runner._localization_evidence_visible(
        case, snapshot_sha256=snapshot_sha, source_rows=[other_row], selected=selected, payload=payload
    )
    assert visible is False
    assert reason == "required_path_identity_missing_or_mismatched"


def test_route_boundaries_match_only_the_frozen_mechanics():
    manifest = _fixture()
    cases = {case["case_id"]: case for case in manifest["cases"]}
    for case_id in runner.LOCALIZATION_BOUNDARY_IDS[:3]:
        case = cases[case_id]
        expected = case["expected_route"]
        route = SimpleNamespace(
            status=SimpleNamespace(value=expected["status"]), action=expected["action"],
            reason=expected["reason"], evidence=(),
        )
        assert runner._localization_boundary_matches(case, route, None, snapshot_sha256="a" * 64)[0] is True
    case = cases["loc02-boundary-context-budget"]
    expected = case["expected_route"]
    evidence = SimpleNamespace(path=expected["paths"][0], status="ok")
    route = SimpleNamespace(
        status=SimpleNamespace(value=expected["status"]), action=expected["action"],
        reason=expected["reason"], evidence=(evidence,),
    )
    snapshot_sha = "d" * 64
    target = case["required_evidence"][0]
    source = next(source for source in case["files"] if source["path"] == target["path"])
    evidence_id = runner._evidence_id(snapshot_sha, target["path"], source["sha256"])
    omitted = ((evidence_id, "preserved_unit_exceeds_active_budget"),)
    gate = SimpleNamespace(
        status=SimpleNamespace(value="required_evidence_omitted"),
        prompt_sha256=None, exact_token_count=None, serialized_bytes=None,
        required_evidence_reasons=omitted, omitted_evidence=omitted,
        selected_evidence_ids=(), reason="required_evidence_not_selected", hard_budget=8192,
    )
    preparation = SimpleNamespace(
        status=SimpleNamespace(value="prompt_rejected"), prompt_gate=gate,
        prompt=None, context_message_json=None, omitted_evidence=omitted,
    )
    assert runner._localization_boundary_matches(case, route, preparation, snapshot_sha256=snapshot_sha)[0] is True
    wrong_id = (("source-" + "c" * 64, "preserved_unit_exceeds_active_budget"),)
    gate.required_evidence_reasons = wrong_id
    gate.omitted_evidence = wrong_id
    preparation.omitted_evidence = wrong_id
    assert runner._localization_boundary_matches(case, route, preparation, snapshot_sha256=snapshot_sha)[0] is False


def test_profile_aggregate_reports_distinct_mean_and_ratio_of_sums():
    rows = [
        {"eligibility": "eligible", "baseline_input_tokens": 100, "e0_prepared_input_tokens": 50, "reduction_percent": 50.0},
        {"eligibility": "eligible", "baseline_input_tokens": 300, "e0_prepared_input_tokens": 240, "reduction_percent": 20.0},
        {"eligibility": "excluded", "baseline_input_tokens": None, "e0_prepared_input_tokens": None, "reduction_percent": None},
    ]
    summary = runner._localization_summary(rows)
    assert summary["eligible_count"] == 2
    assert summary["excluded_count"] == 1
    assert summary["mean_per_task_reduction_percent"] == 35.0
    assert abs(summary["ratio_of_sums_reduction_percent"] - 27.5) < 1e-9
