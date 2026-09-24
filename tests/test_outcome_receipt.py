from __future__ import annotations

from copy import deepcopy

import pytest

import wrench_harness.outcome_receipt as receipt_module
from wrench_harness.outcome_receipt import (
    MAX_ATTEMPTS,
    MAX_ID_CHARS,
    MAX_RECEIPT_BYTES,
    MAX_REFERENCES,
    ReceiptStatus,
    build_outcome_receipt,
    validate_outcome_receipt,
)


def _attempt(attempt_id="call-1", *, route="frontier", retry_of=None, result="success", fallback=False, usage_status="exact", counter="tok-v1"):
    known = usage_status in {"exact", "estimated"}
    return {
        "attempt_id": attempt_id,
        "route": route,
        "result": result,
        "retry_of": retry_of,
        "fallback": fallback,
        "call_made": route != "none",
        "usage": {
            "status": usage_status,
            "counter_id": counter if known else None,
            "local_input_tokens": 0 if known else None,
            "local_output_tokens": 0 if known else None,
            "frontier_input_tokens": 10 if known else None,
            "frontier_output_tokens": 4 if known else None,
            "local_cost_microunits": 0 if known else None,
            "frontier_cost_microunits": 100 if known else None,
            "cost_status": "known" if known else "unknown",
        },
    }


def _payload():
    return {
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "task-1",
        "run_id": "run-1",
        "snapshot_sha256": "a" * 64,
        "context_receipt_sha256": "b" * 64,
        "selected_evidence_ids": ["evidence-a"],
        "omitted_evidence_ids": ["evidence-b"],
        "retrieval_misses": [{"evidence_id": "evidence-b", "status": "stale"}],
        "actual_route": "frontier",
        "attempts": [_attempt()],
        "work_calls": [{
            "call_id": "verify-1",
            "kind": "verifier",
            "route": "none",
            "result": "passed",
            "usage": {
                "status": "not_applicable", "counter_id": None,
                "local_input_tokens": 0, "local_output_tokens": 0,
                "frontier_input_tokens": 0, "frontier_output_tokens": 0,
                "local_cost_microunits": 0, "frontier_cost_microunits": 0,
                "cost_status": "known",
            },
        }],
        "verifier": {"identity": "verifier-v1", "result": "passed", "evidence_ids": ["evidence-a"]},
        "outcome": {"status": "completed", "provenance": "independently_verified", "evidence_ids": ["evidence-a"]},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0,
            "frontier_model_calls": 1,
            "retries": 0,
            "fallback_calls": 0,
            "verifier_calls": 1,
            "tool_calls": 0,
            "local_tokens": 0,
            "frontier_tokens": 14,
            "local_token_counter_id": None,
            "frontier_token_counter_id": "tok-v1",
            "token_count_status": "exact",
            "local_cost_microunits": 0,
            "frontier_cost_microunits": 100,
            "cost_status": "known",
        },
        "completeness": "complete",
        "missing_fields": [],
    }


def _v3_payload():
    payload = _payload()
    payload.update({
        "schema": "wrench.e0.outcome-receipt.v3",
        "session_id": "session-v3",
        "preparation_accounting_sha256": "c" * 64,
        "post_task_evidence_refs": [{
            "evidence_id": "post-result-v3", "kind": "test_result", "sha256": "d" * 64,
        }],
    })
    payload["verifier"]["evidence_ids"] = ["post-result-v3"]
    payload["outcome"]["evidence_ids"] = ["post-result-v3"]
    return payload


def test_receipt_hash_binds_selected_omitted_and_snapshot_context_identities():
    result = build_outcome_receipt(_payload())
    assert result.status is ReceiptStatus.VALID
    checked = validate_outcome_receipt(result.receipt)
    assert checked.status is ReceiptStatus.VALID
    assert checked.receipt.sha256 == result.receipt.sha256

    changed = deepcopy(_payload())
    changed["selected_evidence_ids"] = []
    changed["omitted_evidence_ids"] = ["evidence-a", "evidence-b"]
    changed["retrieval_misses"] = [
        {"evidence_id": "evidence-a", "status": "stale"},
        {"evidence_id": "evidence-b", "status": "missing"},
    ]
    changed["verifier"] = {"identity": None, "result": "not_run", "evidence_ids": []}
    changed["work_calls"] = []
    changed["accounting"]["verifier_calls"] = 0
    changed["outcome"] = {"status": "completed", "provenance": "user_reported", "evidence_ids": []}
    altered = build_outcome_receipt(changed)
    assert altered.status is ReceiptStatus.VALID
    assert altered.receipt.sha256 != result.receipt.sha256


def test_stale_miss_must_link_to_omitted_evidence():
    payload = _payload()
    payload["retrieval_misses"] = [{"evidence_id": "not-omitted", "status": "stale"}]
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "retrieval_miss_not_omitted" in result.errors


def test_route_and_verifier_failures_are_recordable_without_success_claim():
    payload = _payload()
    payload["attempts"] = [_attempt(result="failed")]
    payload["verifier"] = {"identity": "verifier-v1", "result": "failed", "evidence_ids": ["evidence-a"]}
    payload["work_calls"][0]["result"] = "failed"
    payload["outcome"] = {"status": "failed", "provenance": "independently_verified", "evidence_ids": ["evidence-a"]}
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.VALID

    bad = deepcopy(payload)
    bad["actual_route"] = "local"
    assert build_outcome_receipt(bad).status is ReceiptStatus.INVALID


def test_independent_outcome_requires_verifier_evidence_but_user_reported_is_distinct():
    payload = _payload()
    payload["verifier"] = {"identity": "verifier-v1", "result": "not_run", "evidence_ids": []}
    payload["work_calls"] = []
    payload["accounting"]["verifier_calls"] = 0
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "independent_outcome_lacks_verification_evidence" in result.errors

    payload["outcome"] = {"status": "completed", "provenance": "user_reported", "evidence_ids": ["evidence-a"]}
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID


def test_timeout_unknown_usage_and_cost_remain_null():
    payload = _payload()
    payload["attempts"] = [_attempt(result="timeout", usage_status="unknown")]
    payload["accounting"].update({
        "local_tokens": None,
        "frontier_tokens": None,
        "local_token_counter_id": None,
        "frontier_token_counter_id": None,
        "token_count_status": "unknown",
        "local_cost_microunits": None,
        "frontier_cost_microunits": None,
        "cost_status": "unknown",
    })
    payload["outcome"] = {"status": "unknown", "provenance": "unknown", "evidence_ids": []}
    payload["completeness"] = "incomplete"
    payload["missing_fields"] = ["outcome", "usage", "costs"]
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INCOMPLETE

    payload["accounting"]["frontier_tokens"] = 0
    assert build_outcome_receipt(payload).status is ReceiptStatus.INVALID


def test_retry_fallback_and_usage_totals_reconcile_all_calls():
    payload = _payload()
    first = _attempt("call-1", result="failed")
    second = _attempt("call-2", retry_of="call-1", result="success", fallback=True)
    payload["attempts"] = [first, second]
    payload["accounting"].update({"frontier_model_calls": 2, "retries": 1, "fallback_calls": 1, "frontier_tokens": 28, "frontier_cost_microunits": 200})
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID

    payload["accounting"]["retries"] = 0
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "accounting_attempt_totals_mismatch" in result.errors


def test_no_model_route_has_explicit_zero_call_accounting():
    payload = _payload()
    payload["actual_route"] = "none"
    payload["attempts"] = []
    payload["work_calls"] = []
    payload["verifier"] = {"identity": None, "result": "not_run", "evidence_ids": []}
    payload["outcome"] = {"status": "completed", "provenance": "user_reported", "evidence_ids": ["evidence-a"]}
    payload["accounting"].update({
        "frontier_model_calls": 0,
        "local_model_calls": 0,
        "local_tokens": 0,
        "frontier_tokens": 0,
        "local_token_counter_id": None,
        "frontier_token_counter_id": None,
        "token_count_status": "not_applicable",
        "local_cost_microunits": 0,
        "frontier_cost_microunits": 0,
        "cost_status": "known",
        "verifier_calls": 0,
    })
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID


def test_verifier_and_tool_counts_reconcile_to_bounded_work_call_records():
    payload = _payload()
    tool = deepcopy(payload["work_calls"][0])
    tool.update({"call_id": "tool-1", "kind": "tool", "result": "success"})
    payload["work_calls"].append(tool)
    payload["accounting"]["tool_calls"] = 1
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID

    payload["accounting"]["tool_calls"] = 0
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "accounting_tool_calls_mismatch" in result.errors


def test_non_model_work_cannot_hide_known_positive_model_cost():
    payload = _payload()
    payload["work_calls"][0]["usage"]["frontier_cost_microunits"] = 1

    result = build_outcome_receipt(payload)

    assert result.status is ReceiptStatus.INVALID
    assert "non_model_work_cost_must_be_zero_or_unknown" in result.errors


def test_model_routed_verifier_call_joins_local_frontier_accounting():
    payload = _payload()
    payload["actual_route"] = "mixed"
    verify = payload["work_calls"][0]
    verify["route"] = "local"
    verify["usage"].update({
        "status": "exact", "counter_id": "tok-v1",
        "local_input_tokens": 1, "local_output_tokens": 1,
        "frontier_input_tokens": 0, "frontier_output_tokens": 0,
        "local_cost_microunits": 5, "frontier_cost_microunits": 0,
    })
    payload["accounting"].update({
        "local_model_calls": 1,
        "local_tokens": 2,
        "local_token_counter_id": "tok-v1",
        "local_cost_microunits": 5,
    })
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID


def test_mixed_local_frontier_tokenizer_identities_are_kept_separate():
    payload = _payload()
    payload["actual_route"] = "mixed"
    work = payload["work_calls"][0]
    work["route"] = "local"
    work["usage"].update({
        "status": "exact", "counter_id": "local-tok-v3",
        "local_input_tokens": 2, "local_output_tokens": 3,
        "frontier_input_tokens": 0, "frontier_output_tokens": 0,
        "local_cost_microunits": 7, "frontier_cost_microunits": 0,
    })
    payload["accounting"].update({
        "local_model_calls": 1,
        "local_tokens": 5,
        "local_token_counter_id": "local-tok-v3",
        "frontier_token_counter_id": "tok-v1",
        "local_cost_microunits": 7,
    })
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID


def test_no_call_and_fallback_attempt_cannot_report_positive_usage():
    payload = _payload()
    attempt = payload["attempts"][0]
    attempt.update({"call_made": False, "fallback": True})
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "fallback_without_call" in result.errors
    assert "no_call_has_positive_usage" in result.errors

    attempt["fallback"] = False
    result = build_outcome_receipt(payload)
    assert "no_call_has_positive_usage" in result.errors
    for key in ("frontier_input_tokens", "frontier_output_tokens"):
        attempt["usage"][key] = 0
    result = build_outcome_receipt(payload)
    assert "no_call_has_positive_usage" in result.errors


def test_retry_must_reference_prior_actual_call():
    payload = _payload()
    first = _attempt("call-1", result="not_run")
    first["call_made"] = False
    first["usage"] = {
        "status": "not_applicable", "counter_id": None,
        "local_input_tokens": 0, "local_output_tokens": 0,
        "frontier_input_tokens": 0, "frontier_output_tokens": 0,
        "local_cost_microunits": 0, "frontier_cost_microunits": 0,
        "cost_status": "known",
    }
    payload["attempts"] = [first, _attempt("call-2", retry_of="call-1")]
    payload["accounting"].update({"frontier_model_calls": 1, "retries": 1, "frontier_tokens": 14, "frontier_cost_microunits": 100})
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "retry_order_or_call_mismatch" in result.errors


@pytest.mark.parametrize(("verifier_result", "outcome_status"), [
    ("passed", "failed"),
    ("failed", "completed"),
    ("inconclusive", "completed"),
])
def test_independent_verifier_and_outcome_status_must_match(verifier_result, outcome_status):
    payload = _payload()
    payload["verifier"]["result"] = verifier_result
    payload["work_calls"][0]["result"] = verifier_result
    payload["outcome"]["status"] = outcome_status
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "independent_outcome_verifier_status_mismatch" in result.errors


def test_inconclusive_verifier_maps_only_to_partial_outcome():
    payload = _payload()
    payload["verifier"]["result"] = "inconclusive"
    payload["work_calls"][0]["result"] = "inconclusive"
    payload["outcome"]["status"] = "partial"
    assert build_outcome_receipt(payload).status is ReceiptStatus.VALID


def test_malformed_enum_values_return_structured_invalid_result():
    payload = _payload()
    payload["actual_route"] = []
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert result.receipt is None
    assert result.errors


def test_tokenizer_identity_mismatch_is_rejected():
    payload = _payload()
    payload["attempts"][0]["usage"]["counter_id"] = "tok-other"
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert "frontier_token_counter_identity_mismatch" in result.errors


@pytest.mark.parametrize(("field", "expected_error"), [
    ("selected", "selected_evidence_ids_item_invalid"),
    ("omitted", "omitted_evidence_ids_item_invalid"),
    ("miss", "retrieval_miss_value_invalid"),
    ("attempt", "attempt_id_invalid"),
    ("retry", "retry_reference_invalid"),
    ("work_call", "work_call_id_invalid"),
    ("usage_counter", "attempt_counter_id_invalid"),
    ("work_usage_counter", "attempt_counter_id_invalid"),
    ("verifier_evidence", "verifier_evidence_ids_item_invalid"),
    ("outcome_evidence", "outcome_evidence_ids_item_invalid"),
    ("correction", "correction_refs_item_invalid"),
    ("accounting_counter", "frontier_token_counter_identity_invalid"),
    ("local_accounting_counter", "local_token_counter_identity_invalid"),
])
def test_v3_rejects_non_opaque_reference_values(field, expected_error):
    payload = _v3_payload()
    if field == "selected":
        payload["selected_evidence_ids"] = ["prompt text /tmp/private.txt"]
    elif field == "omitted":
        payload["omitted_evidence_ids"] = ["prompt text /tmp/private.txt"]
        payload["retrieval_misses"] = []
    elif field == "miss":
        payload["omitted_evidence_ids"] = ["omitted-v3"]
        payload["retrieval_misses"] = [{"evidence_id": "prompt text /tmp/private.txt", "status": "missing"}]
    elif field in {"attempt", "retry", "usage_counter"}:
        attempt = _attempt("call-1", route="none", result="not_run", usage_status="not_applicable")
        attempt["call_made"] = False
        attempt["usage"] = {
            "status": "not_applicable", "counter_id": None,
            "local_input_tokens": 0, "local_output_tokens": 0,
            "frontier_input_tokens": 0, "frontier_output_tokens": 0,
            "local_cost_microunits": 0, "frontier_cost_microunits": 0,
            "cost_status": "known",
        }
        if field == "attempt":
            attempt["attempt_id"] = "prompt text /tmp/private.txt"
        elif field == "retry":
            attempt["retry_of"] = "prompt text /tmp/private.txt"
        else:
            attempt["usage"]["counter_id"] = "prompt text /tmp/private.txt"
        payload["attempts"] = [attempt]
    elif field == "work_call":
        payload["work_calls"][0]["call_id"] = "prompt text /tmp/private.txt"
    elif field == "work_usage_counter":
        payload["work_calls"][0]["usage"]["counter_id"] = "prompt text /tmp/private.txt"
    elif field == "verifier_evidence":
        payload["verifier"]["evidence_ids"] = ["prompt text /tmp/private.txt"]
    elif field == "outcome_evidence":
        payload["outcome"]["evidence_ids"] = ["prompt text /tmp/private.txt"]
    elif field == "correction":
        payload["correction_refs"] = ["prompt text /tmp/private.txt"]
    elif field == "local_accounting_counter":
        payload["accounting"]["local_token_counter_id"] = "prompt text /tmp/private.txt"
    else:
        payload["accounting"]["frontier_token_counter_id"] = "prompt text /tmp/private.txt"

    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    assert expected_error in result.errors


def test_v2_keeps_its_legacy_reference_validation_contract():
    assert build_outcome_receipt(_legacy_reference_payload("v2")).status is ReceiptStatus.VALID


def test_v1_keeps_its_legacy_reference_validation_contract():
    assert build_outcome_receipt(_legacy_reference_payload("v1")).status is ReceiptStatus.VALID


def _legacy_reference_payload(version):
    payload = _v3_payload()
    payload["schema"] = f"wrench.e0.outcome-receipt.{version}"
    if version == "v1":
        payload["task_id"] = "legacy task / α"
        payload["run_id"] = "legacy run / β"
    payload["selected_evidence_ids"] = ["legacy selected / γ"]
    payload["omitted_evidence_ids"] = ["legacy omitted / δ"]
    payload["retrieval_misses"] = [{"evidence_id": "legacy omitted / δ", "status": "missing"}]
    payload["attempts"] = [
        _attempt("legacy attempt / ε", counter="legacy frontier counter / ζ"),
        _attempt("legacy retry / η", retry_of="legacy attempt / ε", counter="legacy frontier counter / ζ"),
    ]
    payload["work_calls"][0].update({"call_id": "legacy verifier call / θ", "route": "frontier"})
    payload["work_calls"][0]["usage"] = {
        "status": "exact", "counter_id": "legacy frontier counter / ζ",
        "local_input_tokens": 0, "local_output_tokens": 0,
        "frontier_input_tokens": 0, "frontier_output_tokens": 0,
        "local_cost_microunits": 0, "frontier_cost_microunits": 0,
        "cost_status": "known",
    }
    payload["work_calls"].append({
        "call_id": "legacy tool call / ι", "kind": "tool", "route": "local", "result": "success",
        "usage": {
            "status": "exact", "counter_id": "legacy local counter / κ",
            "local_input_tokens": 0, "local_output_tokens": 0,
            "frontier_input_tokens": 0, "frontier_output_tokens": 0,
            "local_cost_microunits": 0, "frontier_cost_microunits": 0,
            "cost_status": "known",
        },
    })
    payload["actual_route"] = "mixed"
    payload["verifier"]["evidence_ids"] = ["legacy selected / γ"] if version == "v1" else ["post-result-v3"]
    payload["outcome"]["evidence_ids"] = ["legacy selected / γ"] if version == "v1" else ["post-result-v3"]
    payload["correction_refs"] = ["legacy correction / λ"]
    payload["accounting"].update({
        "local_model_calls": 1, "frontier_model_calls": 3,
        "retries": 1, "tool_calls": 1,
        "local_tokens": 0, "frontier_tokens": 28,
        "local_token_counter_id": "legacy local counter / κ",
        "frontier_token_counter_id": "legacy frontier counter / ζ",
        "local_cost_microunits": 0, "frontier_cost_microunits": 200,
    })
    if version == "v1":
        payload.pop("session_id")
        payload.pop("preparation_accounting_sha256")
        payload.pop("post_task_evidence_refs")
    return payload


@pytest.mark.parametrize("mutation", ["duplicate_id", "oversized_id", "too_many_attempts", "too_many_references", "too_large_receipt", "raw_content_key"])
def test_duplicate_oversized_and_forbidden_inputs_fail_closed(mutation):
    payload = _payload()
    if mutation == "duplicate_id":
        payload["selected_evidence_ids"] = ["evidence-a", "evidence-a"]
    elif mutation == "oversized_id":
        payload["task_id"] = "t" * (MAX_ID_CHARS + 1)
    elif mutation == "too_many_attempts":
        payload["attempts"] = [_attempt(f"a{i}") for i in range(MAX_ATTEMPTS + 1)]
        payload["accounting"].update({"frontier_model_calls": MAX_ATTEMPTS + 1, "frontier_tokens": 14 * (MAX_ATTEMPTS + 1), "frontier_cost_microunits": 100 * (MAX_ATTEMPTS + 1)})
    elif mutation == "too_many_references":
        payload["selected_evidence_ids"] = [f"e{i}" for i in range(MAX_REFERENCES + 1)]
    elif mutation == "too_large_receipt":
        payload["correction_refs"] = ["x" * MAX_ID_CHARS for _ in range(MAX_REFERENCES)]
    else:
        payload["prompt"] = "do not retain this"
    result = build_outcome_receipt(payload)
    assert result.status is ReceiptStatus.INVALID
    if mutation == "too_large_receipt":
        assert any("OverflowError" in error for error in result.errors)
    if mutation == "raw_content_key":
        assert "forbidden_raw_content_key" in result.errors


def test_invalid_serialized_receipt_digest_is_rejected():
    result = build_outcome_receipt(_payload())
    forged = type(result.receipt)(result.receipt.payload_json, "0" * 64)
    assert validate_outcome_receipt(forged).status is ReceiptStatus.INVALID


def test_serializer_encodes_deep_owned_snapshot_after_caller_mutation(monkeypatch):
    source = {"nested": ([{"ids": ["stable"]}],)}
    original_dumps = receipt_module.json.dumps
    mutated = False

    def mutate_source_then_encode(owned, *args, **kwargs):
        nonlocal mutated
        if not mutated:
            source["nested"][0][0]["ids"].append("raced-change")
            mutated = True
        return original_dumps(owned, *args, **kwargs)

    monkeypatch.setattr(receipt_module.json, "dumps", mutate_source_then_encode)
    encoded = receipt_module._canonical_json(source)
    assert '"ids":["stable"]' in encoded
    assert "raced-change" not in encoded


def test_dict_resize_during_owned_copy_returns_typed_invalid(monkeypatch):
    payload = _payload()
    original_items = receipt_module._snapshot_dict_items
    first_call = True

    def mutate_during_items(mapping):
        nonlocal first_call
        iterator = iter(original_items(mapping))
        if first_call:
            first_call = False
            first = next(iterator)
            yield first
            mapping["controlled_mutation"] = "test"
            yield from iterator
        else:
            yield from iterator

    monkeypatch.setattr(receipt_module, "_snapshot_dict_items", mutate_during_items)
    result = build_outcome_receipt(payload)

    assert result.status is ReceiptStatus.INVALID
    assert result.receipt is None
    assert "payload_serialization_invalid:ValueError" in result.errors
