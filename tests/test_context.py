from __future__ import annotations

import json

import pytest

from wrench_harness import ContextAdmissionError, ContextLedger, ContextSelectionError


def test_ledger_admits_two_million_logical_tokens_without_model_call():
    ledger = ContextLedger(max_logical_tokens=2_000_000)
    ledger.add_segment("part-1", "alpha project architecture", 1, token_count=1_000_000)
    ledger.add_segment("part-2", "beta project verifier", 2, token_count=1_000_000)

    assert ledger.logical_token_count == 2_000_000
    receipt = ledger.assemble("verifier", active_token_budget=1_000_000)
    assert receipt["logical_token_count"] == 2_000_000
    assert receipt["selected_token_count"] == 1_000_000
    assert receipt["token_count_mode"] == "explicit"
    assert receipt["omitted_segments"]


def test_admission_is_atomic_and_rejects_duplicates():
    ledger = ContextLedger(max_logical_tokens=10)
    ledger.add_segment("one", "one", 1, token_count=9)

    with pytest.raises(ContextAdmissionError, match="logical_context_limit_exceeded"):
        ledger.add_segment("two", "two", 2, token_count=2)
    with pytest.raises(ContextAdmissionError, match="duplicate segment_id"):
        ledger.add_segment("one", "replacement", 3, token_count=1)

    assert ledger.segment_count == 1
    assert ledger.logical_token_count == 9


def test_tool_call_and_result_are_selected_as_one_atomic_unit():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("request", "inspect the deployment status", 1, token_count=4, role="user")
    ledger.add_segment("call", '{"action":"health_read"}', 2, token_count=4, role="assistant", kind="tool_call", unit_id="u1")
    ledger.add_segment("result", '{"status":200}', 3, token_count=4, role="tool", kind="tool_result", unit_id="u1")
    ledger.add_segment("unrelated", "a different topic", 4, token_count=3)

    receipt = ledger.assemble("health status", active_token_budget=8, preserve_ids=["call"])
    selected = [item["segment_id"] for item in receipt["selected_segments"]]
    assert selected == ["call", "result"]
    assert receipt["selected_token_count"] == 8


def test_preserved_unit_that_does_not_fit_fails_closed():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("call", "tool call", 1, token_count=6, unit_id="u1", kind="tool_call")
    ledger.add_segment("result", "tool result", 2, token_count=6, unit_id="u1", kind="tool_result")

    with pytest.raises(ContextSelectionError, match="preserved_unit_exceeds_active_budget"):
        ledger.assemble("tool", active_token_budget=8, preserve_ids=["call"])


def test_receipt_is_hash_bound_and_has_no_silent_omission():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("old", "historical compiler output", 1, token_count=5)
    ledger.add_segment("new", "current compiler error", 2, token_count=5)
    receipt = ledger.assemble("current error", active_token_budget=5)

    assert receipt["schema"] == "wrench.context-assembly.v1"
    assert len(receipt["session_hash"]) == 64
    omitted = {item["segment_id"]: item["reason"] for item in receipt["omitted_segments"]}
    assert omitted["old"] in {"active_token_budget", "not_selected", "unit_exceeds_active_budget"}
    json.dumps(receipt, ensure_ascii=False)


def test_reference_context_is_not_forwarded_without_explicit_preservation():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("recent", "current deployment request", 2, token_count=4, retention="hot")
    ledger.add_segment("old-lookup", "historical deployment lookup", 1, token_count=4, retention="reference")

    default_receipt = ledger.assemble("deployment", active_token_budget=4)
    assert [item["segment_id"] for item in default_receipt["selected_segments"]] == ["recent"]
    assert default_receipt["omitted_reason_counts"] == {"not_selected": 1}

    preserved_receipt = ledger.assemble(
        "deployment",
        active_token_budget=8,
        preserve_ids=("old-lookup",),
    )
    assert [item["segment_id"] for item in preserved_receipt["selected_segments"]] == ["old-lookup", "recent"]


def test_invalid_retention_tier_fails_closed():
    ledger = ContextLedger(max_logical_tokens=100)
    with pytest.raises(ContextAdmissionError, match="invalid_retention_tier"):
        ledger.add_segment("bad", "content", 1, token_count=1, retention="discard")


def test_summary_receipt_is_compact_but_hash_bound():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("old", "historical compiler output", 1, token_count=5)
    ledger.add_segment("new", "current compiler error", 2, token_count=5)
    receipt = ledger.assemble("current error", active_token_budget=5, receipt_detail="summary")

    assert receipt["receipt_detail"] == "summary"
    assert receipt["omitted_segment_count"] == 1
    assert receipt["omitted_segments"] == []
    assert len(receipt["omitted_segments_digest"]) == 64


def test_derived_summary_is_retrievable_without_double_counting_source_tokens():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("source-a", "raw build logs", 1, token_count=45)
    ledger.add_segment("source-b", "raw deployment notes", 2, token_count=45)
    summary = ledger.add_summary(
        "task-summary",
        "release incident summary says deployment rolled back safely",
        3,
        summary_of=("source-a", "source-b"),
        token_count=8,
        level="task",
    )

    assert summary.kind == "summary"
    assert ledger.logical_token_count == 90
    receipt = ledger.assemble("release incident", active_token_budget=8)
    selected = receipt["selected_segments"]
    assert selected[0]["segment_id"] == "task-summary"
    assert selected[0]["counts_toward_logical_limit"] is False


def test_custom_token_counter_is_named_in_receipt():
    ledger = ContextLedger(
        max_logical_tokens=20,
        token_counter=lambda text: len(text.split()) * 2,
        token_counter_name="test_exact_counter_v1",
    )
    ledger.add_segment("one", "alpha beta", 1)

    assert ledger.logical_token_count == 4
    receipt = ledger.assemble("alpha", active_token_budget=4)
    assert receipt["token_count_mode"] == "custom"
    assert receipt["token_counter_name"] == "test_exact_counter_v1"


def test_explicit_counts_are_not_mislabeled_as_tokenizer_counts():
    ledger = ContextLedger(max_logical_tokens=10)
    ledger.add_segment("one", "alpha", 1, token_count=4)

    receipt = ledger.assemble("alpha", active_token_budget=4)
    assert receipt["token_count_mode"] == "explicit"
    assert receipt["token_counter_name"] == "caller_explicit_counts"
