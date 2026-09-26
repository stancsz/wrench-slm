"""Synthetic mechanics only. These fixtures are not task or utility data."""

import hashlib
import json

import pytest

from wrench_harness.outcome_receipt import build_outcome_receipt
from tools.report_paired_frontier_savings import InputError, SCHEMA, summarize


COMPARISON = {
    "protocol_id": "synthetic-protocol-v1",
    "client_id": "synthetic-client-v1",
    "frontier_model_id": "synthetic-model-v1",
    "token_convention_id": "tok-v1",
}


def _receipt(
    task_id, input_tokens, output_tokens, *, outcome="completed", provenance="user_reported",
    verifier_result="unknown", usage_status="exact", cost_known=None, snapshot="a" * 64,
):
    known = usage_status == "exact"
    cost_known = known if cost_known is None else cost_known
    return build_outcome_receipt({
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": task_id,
        "run_id": f"{task_id}-run",
        "snapshot_sha256": snapshot,
        "context_receipt_sha256": "b" * 64,
        "selected_evidence_ids": ["evidence-a"],
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "actual_route": "frontier",
        "attempts": [{
            "attempt_id": "call-1", "route": "frontier", "result": "failed" if outcome == "failed" else "success",
            "retry_of": None, "fallback": False, "call_made": True,
            "usage": {
                "status": usage_status, "counter_id": "tok-v1" if known else None,
                "local_input_tokens": 0 if known else None,
                "local_output_tokens": 0 if known else None,
                "frontier_input_tokens": input_tokens if known else None,
                "frontier_output_tokens": output_tokens if known else None,
                "local_cost_microunits": 0 if cost_known else None,
                "frontier_cost_microunits": 0 if cost_known else None,
                "cost_status": "known" if cost_known else "unknown",
            },
        }],
        "work_calls": ([{
            "call_id": "verification-1", "kind": "verifier", "route": "none",
            "result": "passed" if verifier_result == "passed" else "failed",
            "usage": {
                "status": "not_applicable", "counter_id": None,
                "local_input_tokens": 0, "local_output_tokens": 0,
                "frontier_input_tokens": 0, "frontier_output_tokens": 0,
                "local_cost_microunits": 0, "frontier_cost_microunits": 0,
                "cost_status": "known",
            },
        }] if provenance == "independently_verified" else []),
        "verifier": {
            "identity": "verifier-v1" if provenance == "independently_verified" else None,
            "result": verifier_result,
            "evidence_ids": ["evidence-a"] if provenance == "independently_verified" else [],
        },
        "outcome": {"status": outcome, "provenance": provenance, "evidence_ids": ["evidence-a"]},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": 1, "retries": 0, "fallback_calls": 0,
            "verifier_calls": 1 if provenance == "independently_verified" else 0,
            "tool_calls": 0, "local_tokens": 0 if known else None,
            "frontier_tokens": input_tokens + output_tokens if known else None,
            "local_token_counter_id": None, "frontier_token_counter_id": "tok-v1" if known else None,
            "token_count_status": "exact" if known else "unknown",
            "local_cost_microunits": 0 if cost_known else None,
            "frontier_cost_microunits": 0 if cost_known else None,
            "cost_status": "known" if cost_known else "unknown",
        },
        "completeness": "complete" if known and cost_known and snapshot is not None else "incomplete",
        "missing_fields": ([] if known else ["usage", "costs"])
        + ([] if cost_known or not known else ["costs"])
        + ([] if snapshot is not None else ["snapshot_sha256"]),
    })


def _arm(
    task_id, total, *, outcome="completed", provenance="user_reported", verifier_result="unknown",
    usage_status="exact", cost_known=None, snapshot="a" * 64,
):
    result = _receipt(
        task_id, total, 0, outcome=outcome, provenance=provenance,
        verifier_result=verifier_result, usage_status=usage_status,
        cost_known=cost_known, snapshot=snapshot,
    )
    assert result.receipt is not None
    return {
        "comparison": dict(COMPARISON),
        "receipt": {"payload_json": result.receipt.payload_json, "sha256": result.receipt.sha256},
    }


def _document(pairs):
    return {
        "schema": SCHEMA,
        "comparison": dict(COMPARISON),
        "tasks": [
            {"task_id": task_id, "snapshot_sha256": "a" * 64,
             "baseline": _arm(task_id, baseline, outcome=outcome),
             "wrench": _arm(task_id, wrench, outcome=outcome)}
            for task_id, baseline, wrench, outcome in pairs
        ],
    }


def test_reports_arithmetic_mean_and_ratio_of_sums_separately_and_keeps_failures_in_costs():
    report = summarize(_document([
        ("task-a", 100, 50, "completed"),
        ("task-b", 900, 900, "failed"),
    ]))
    assert report["valid_pair_count"] == 2
    assert report["frontier_token_totals"] == {"baseline": 1000, "wrench": 950}
    assert report["average_per_task_savings_percent"] == 25.0
    assert report["ratio_of_sums_savings_percent"] == 5.0
    assert report["task_outcome_counts_by_arm"]["baseline"] == {"completed": 1, "failed": 1}
    assert report["excluded_pair_count"] == 0
    assert report["per_task"] == [
        {
            "task_ref_sha256": hashlib.sha256(b"task-a").hexdigest(),
            "status": "valid",
            "baseline_frontier_tokens": 100,
            "wrench_frontier_tokens": 50,
            "savings_percent": 50.0,
            "excluded_reason": None,
            "successful_task_eligible": False,
            "successful_task_excluded_reason": "baseline+wrench_arm_not_independently_verified_success",
        },
        {
            "task_ref_sha256": hashlib.sha256(b"task-b").hexdigest(),
            "status": "valid",
            "baseline_frontier_tokens": 900,
            "wrench_frontier_tokens": 900,
            "savings_percent": 0.0,
            "excluded_reason": None,
            "successful_task_eligible": False,
            "successful_task_excluded_reason": "baseline+wrench_arm_not_independently_verified_success",
        },
    ]
    assert all("task_id" not in row for row in report["per_task"])


def test_success_metric_includes_only_pairs_completed_and_independently_verified_in_both_arms():
    document = _document([
        ("success", 100, 40, "completed"),
        ("verified-failure", 300, 300, "failed"),
        ("unverified-completion", 100, 10, "completed"),
    ])
    success = document["tasks"][0]
    for arm in ("baseline", "wrench"):
        success[arm] = _arm(
            "success", 100 if arm == "baseline" else 40,
            provenance="independently_verified", verifier_result="passed",
        )
    failed = document["tasks"][1]
    for arm in ("baseline", "wrench"):
        failed[arm] = _arm(
            "verified-failure", 300, outcome="failed",
            provenance="independently_verified", verifier_result="failed",
        )

    report = summarize(document)

    # The all-usage diagnostic still includes failed and user-reported pairs.
    assert report["valid_pair_count"] == 3
    assert report["average_per_task_savings_percent"] == 50.0
    assert report["ratio_of_sums_savings_percent"] == 30.0
    # The primary successful-task metric includes only the independently
    # verified completed pair, and gives failed/unverified rows reasons.
    assert report["successful_pair_count"] == 1
    assert report["successful_frontier_token_totals"] == {"baseline": 100, "wrench": 40}
    assert report["average_per_successful_task_savings_percent"] == 60.0
    assert report["ratio_of_sums_successful_task_savings_percent"] == 60.0
    assert report["excluded_from_successful_pairs_count"] == 2
    assert report["per_task"][0]["successful_task_eligible"] is True
    assert report["per_task"][0]["successful_task_excluded_reason"] is None
    assert report["per_task"][1]["successful_task_eligible"] is False
    assert report["per_task"][2]["successful_task_eligible"] is False


def test_one_unverified_arm_excludes_pair_from_success_metric():
    document = _document([("one-sided", 100, 40, "completed")])
    document["tasks"][0]["baseline"] = _arm(
        "one-sided", 100,
        provenance="independently_verified", verifier_result="passed",
    )
    report = summarize(document)

    assert report["valid_pair_count"] == 1
    assert report["successful_pair_count"] == 0
    assert report["excluded_from_successful_pairs_by_reason"] == {
        "wrench_arm_not_independently_verified_success": 1,
    }
    assert report["per_task"][0]["successful_task_excluded_reason"] == (
        "wrench_arm_not_independently_verified_success"
    )


def test_independently_verified_exact_usage_remains_eligible_when_cost_is_unknown():
    document = _document([("cost-unknown", 100, 40, "completed")])
    for arm in ("baseline", "wrench"):
        document["tasks"][0][arm] = _arm(
            "cost-unknown", 100 if arm == "baseline" else 40,
            provenance="independently_verified", verifier_result="passed",
            cost_known=False,
        )
    report = summarize(document)

    assert report["valid_pair_count"] == 1
    assert report["cost_unknown_valid_pair_count"] == 1
    assert report["successful_pair_count"] == 1
    assert report["average_per_successful_task_savings_percent"] == 60.0
    assert report["excluded_from_successful_pairs_count"] == 0


def test_missing_usage_is_unavailable_and_pair_is_excluded_by_reason():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["wrench"] = _arm("task-a", 50, usage_status="unknown")
    report = summarize(document)
    assert report["valid_pair_count"] == 0
    assert report["average_per_task_savings_percent"] is None
    assert report["ratio_of_sums_savings_percent"] is None
    assert report["excluded_by_reason"] == {"incomplete_receipt": 1}
    assert report["per_task"][0]["status"] == "excluded"
    assert report["per_task"][0]["savings_percent"] is None
    assert report["per_task"][0]["excluded_reason"] == "incomplete_receipt"


def test_invalid_arm_shape_has_a_per_task_exclusion_row():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["baseline"] = None
    report = summarize(document)
    assert report["per_task"] == [{
        "task_ref_sha256": hashlib.sha256(b"task-a").hexdigest(),
        "status": "excluded",
        "baseline_frontier_tokens": None,
        "wrench_frontier_tokens": None,
        "savings_percent": None,
        "excluded_reason": "invalid_arm_record_shape",
        "successful_task_eligible": False,
        "successful_task_excluded_reason": "invalid_arm_record_shape",
    }]


def test_invalid_receipt_shape_has_a_per_task_exclusion_row():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["baseline"]["receipt"] = {"payload_json": "missing-digest"}
    report = summarize(document)
    assert report["per_task"][0]["status"] == "excluded"
    assert report["per_task"][0]["excluded_reason"] == "invalid_receipt_shape"


def test_estimated_frontier_usage_is_reported_as_unavailable_for_that_task():
    document = _document([("task-a", 100, 50, "completed")])
    arm = document["tasks"][0]["wrench"]
    receipt = arm["receipt"]
    payload = json.loads(receipt["payload_json"])
    payload["accounting"]["token_count_status"] = "estimated"
    payload["attempts"][0]["usage"]["status"] = "estimated"
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    receipt["payload_json"] = canonical
    receipt["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    report = summarize(document)
    assert report["valid_pair_count"] == 0
    assert report["per_task"][0]["status"] == "excluded"
    assert report["per_task"][0]["baseline_frontier_tokens"] is None
    assert report["per_task"][0]["wrench_frontier_tokens"] is None
    assert report["per_task"][0]["savings_percent"] is None
    assert report["per_task"][0]["excluded_reason"] == "usage_not_exact"


def test_zero_baseline_is_excluded_instead_of_dividing_by_zero():
    report = summarize(_document([("task-a", 0, 0, "completed")]))
    assert report["excluded_by_reason"] == {"zero_baseline_frontier_tokens": 1}
    assert report["frontier_token_totals"] == {"baseline": None, "wrench": None}


def test_invalid_receipt_digest_excludes_pair():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["baseline"]["receipt"]["sha256"] = "0" * 64
    report = summarize(document)
    assert report["valid_pair_count"] == 0
    assert report["excluded_by_reason"] == {"invalid_receipt_hash_or_schema": 1}


def test_boolean_token_count_is_rejected_even_when_receipt_hash_is_recomputed():
    document = _document([("task-a", 100, 50, "completed")])
    receipt = document["tasks"][0]["wrench"]["receipt"]
    payload = json.loads(receipt["payload_json"])
    payload["attempts"][0]["usage"]["frontier_input_tokens"] = True
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    receipt["payload_json"] = canonical
    receipt["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    report = summarize(document)
    assert report["excluded_by_reason"] == {"invalid_receipt_hash_or_schema": 1}


def test_duplicate_task_ids_reject_entire_input():
    document = _document([("task-a", 100, 50, "completed"), ("task-a", 100, 50, "completed")])
    with pytest.raises(InputError, match="duplicate_task_id"):
        summarize(document)


def test_schema_identity_must_be_complete():
    document = _document([("task-a", 100, 50, "completed")])
    document["comparison"]["client_id"] = ""
    with pytest.raises(InputError, match="comparison_identity_invalid"):
        summarize(document)


def test_receipt_task_id_must_match_pair_key():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["wrench"] = _arm("task-other", 50)
    report = summarize(document)
    assert report["excluded_by_reason"] == {"receipt_task_id_mismatch": 1}


def test_counter_identity_mismatch_is_unavailable():
    document = _document([("task-a", 100, 50, "completed")])
    # The common comparison identity is required and applied to every exact call.
    document["comparison"]["token_convention_id"] = "tok-other"
    for arm in ("baseline", "wrench"):
        document["tasks"][0][arm]["comparison"]["token_convention_id"] = "tok-other"
    report = summarize(document)
    assert report["excluded_by_reason"] == {"token_convention_mismatch": 1}


def test_each_arm_must_match_frozen_comparison_identity():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["wrench"]["comparison"]["frontier_model_id"] = "different-model"
    report = summarize(document)
    assert report["excluded_by_reason"] == {"comparison_identity_mismatch": 1}


def test_paired_receipts_must_bind_to_same_task_snapshot():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["wrench"] = _arm("task-a", 50, snapshot="c" * 64)
    report = summarize(document)
    assert report["valid_pair_count"] == 0
    assert report["unresolved_or_excluded_by_reason"] == {"task_snapshot_mismatch": 1}


def test_both_arms_sharing_the_same_wrong_snapshot_are_excluded():
    document = _document([("task-a", 100, 50, "completed")])
    for arm in ("baseline", "wrench"):
        document["tasks"][0][arm] = _arm("task-a", 100 if arm == "baseline" else 50, snapshot="c" * 64)
    report = summarize(document)
    assert report["excluded_by_reason"] == {"task_snapshot_mismatch": 1}


def test_null_snapshot_in_either_receipt_is_excluded():
    document = _document([("task-a", 100, 50, "completed")])
    document["tasks"][0]["baseline"] = _arm("task-a", 100, snapshot=None)
    report = summarize(document)
    assert report["excluded_by_reason"] == {"task_snapshot_mismatch": 1}


def test_both_null_receipt_snapshots_are_excluded():
    document = _document([("task-a", 100, 50, "completed")])
    for arm in ("baseline", "wrench"):
        document["tasks"][0][arm] = _arm("task-a", 100 if arm == "baseline" else 50, snapshot=None)
    report = summarize(document)
    assert report["excluded_by_reason"] == {"task_snapshot_mismatch": 1}
