from __future__ import annotations

import json
from dataclasses import replace

import pytest

import wrench_harness.context as context_module
from wrench_harness import ContextAdmissionError, ContextLedger, ContextSelectionError
from wrench_harness.context import RetrievalDecision, RetrievalPageStatus


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


def test_opt_in_preserved_overflow_receipt_marks_later_mandatory_units():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("fits", "first required region", 1, token_count=3)
    ledger.add_segment("overflows", "second required region", 2, token_count=2)

    receipt = ledger.assemble(
        "regions", active_token_budget=3, preserve_ids=("fits", "overflows"),
        on_preserved_overflow="omit",
    )

    assert [row["segment_id"] for row in receipt["selected_segments"]] == ["fits"]
    assert receipt["omitted_segments"] == [{
        "segment_id": "overflows",
        "reason": "preserved_unit_exceeds_active_budget",
    }]


def test_default_preserved_overflow_fails_when_earlier_unit_fills_budget():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("fits", "first required region", 1, token_count=3)
    ledger.add_segment("overflows", "second required region", 2, token_count=2)

    with pytest.raises(ContextSelectionError, match="preserved_unit_exceeds_active_budget"):
        ledger.assemble(
            "regions", active_token_budget=3, preserve_ids=("fits", "overflows"),
        )


def test_receipt_is_hash_bound_and_has_no_silent_omission():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("old", "historical compiler output", 1, token_count=5)
    ledger.add_segment("new", "current compiler error", 2, token_count=5)
    receipt = ledger.assemble("current error", active_token_budget=5)

    assert receipt["schema"] == "wrench.context-assembly.v2"
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


def test_query_retrieves_ranked_reference_segments_within_budget():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("hot", "current deployment request", 3, token_count=3, retention="hot")
    ledger.add_segment("matching", "deployment rollback commands", 2, token_count=3, retention="reference")
    ledger.add_segment("unrelated", "database schema changes", 1, token_count=3, retention="reference")

    receipt = ledger.assemble("deployment rollback", active_token_budget=6, search_limit=2)

    assert [item["segment_id"] for item in receipt["selected_segments"]] == ["matching", "hot"]
    assert receipt["retrieval_candidate_ids"] == ["matching", "hot"]
    assert receipt["search_limit"] == 2
    omitted = {item["segment_id"]: item["reason"] for item in receipt["omitted_segments"]}
    assert omitted["unrelated"] == "not_selected"


def _retrieval_ledger(count: int = 65) -> ContextLedger:
    ledger = ContextLedger(max_logical_tokens=10_000)
    for index in range(count):
        ledger.add_segment(
            f"evidence-{index:03}", "needle deployment evidence", index,
            token_count=1, retention="reference",
        )
    return ledger


def test_retrieval_pages_are_stable_bounded_and_return_only_known_ids():
    ledger = _retrieval_ledger()

    first = ledger.retrieve_page("needle", RetrievalDecision.RETRIEVE_MORE)
    second = ledger.retrieve_page(
        "needle", RetrievalDecision.RETRIEVE_MORE, cursor=first.cursor
    )

    assert first.status is RetrievalPageStatus.MORE_AVAILABLE
    assert len(first.candidate_ids) == context_module.MAX_RETRIEVAL_PAGE_SIZE == 32
    assert first.candidate_ids[0] == "evidence-064"
    assert first.candidate_ids[-1] == "evidence-033"
    assert second.status is RetrievalPageStatus.CANDIDATE_LIMIT
    assert len(second.candidate_ids) == 32
    assert second.candidate_ids[0] == "evidence-032"
    assert second.candidate_ids[-1] == "evidence-001"
    assert set(first.candidate_ids + second.candidate_ids).issubset(ledger._segments)
    assert not hasattr(first, "assembled_text")
    assert second.cursor is None


def test_retrieval_enough_stops_without_search_or_candidate_ids(monkeypatch):
    ledger = _retrieval_ledger()

    def forbidden_search(*args, **kwargs):
        raise AssertionError("ENOUGH must stop without searching")

    monkeypatch.setattr(ledger, "_search_candidates", forbidden_search)
    result = ledger.retrieve_page("needle", RetrievalDecision.ENOUGH)

    assert result.status is RetrievalPageStatus.STOPPED
    assert result.candidate_ids == ()
    assert result.cursor is None


@pytest.mark.parametrize("mutation", ["query", "session"])
def test_retrieval_cursor_rejects_other_query_or_changed_ledger(mutation):
    ledger = _retrieval_ledger()
    first = ledger.retrieve_page("needle", RetrievalDecision.RETRIEVE_MORE)
    assert first.cursor is not None

    if mutation == "query":
        result = ledger.retrieve_page(
            "deployment", RetrievalDecision.RETRIEVE_MORE, cursor=first.cursor
        )
    else:
        ledger.add_segment("new-evidence", "needle deployment", 100, token_count=1)
        result = ledger.retrieve_page(
            "needle", RetrievalDecision.RETRIEVE_MORE, cursor=first.cursor
        )

    assert result.status is RetrievalPageStatus.INVALID_CURSOR
    assert result.candidate_ids == ()
    assert result.cursor is None


def test_retrieval_cursor_checksum_rejects_accidental_edit():
    ledger = _retrieval_ledger()
    first = ledger.retrieve_page("needle", RetrievalDecision.RETRIEVE_MORE)
    assert first.cursor is not None
    edited = replace(first.cursor, cursor_sha256="0" * 64)

    result = ledger.retrieve_page(
        "needle", RetrievalDecision.RETRIEVE_MORE, cursor=edited
    )

    assert result.status is RetrievalPageStatus.INVALID_CURSOR
    assert result.candidate_ids == ()


def test_retrieval_second_page_reports_exhaustion_without_more_candidates():
    ledger = _retrieval_ledger(40)
    first = ledger.retrieve_page("needle", RetrievalDecision.RETRIEVE_MORE)
    second = ledger.retrieve_page(
        "needle", RetrievalDecision.RETRIEVE_MORE, cursor=first.cursor
    )

    assert first.status is RetrievalPageStatus.MORE_AVAILABLE
    assert second.status is RetrievalPageStatus.EXHAUSTED
    assert second.candidate_ids == tuple(f"evidence-{i:03}" for i in range(7, -1, -1))
    assert second.cursor is None


def test_retrieval_fails_closed_when_bm25_work_is_truncated(monkeypatch):
    monkeypatch.setattr(context_module, "MAX_SEARCH_TERM_DOCUMENT_CHECKS", 1)
    ledger = _retrieval_ledger(4)

    result = ledger.retrieve_page("needle", RetrievalDecision.RETRIEVE_MORE)

    assert result.status is RetrievalPageStatus.WORK_LIMIT
    assert result.candidate_ids == ()
    assert result.cursor is None


def test_retrieval_page_rejects_untyped_action():
    ledger = _retrieval_ledger(1)

    with pytest.raises(ContextSelectionError, match="invalid retrieval decision"):
        ledger.retrieve_page("needle", "retrieve_more")


def test_hot_context_precedes_retrieved_context_when_budget_is_tight():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("hot-old", "current deployment request", 1, token_count=2, retention="hot")
    ledger.add_segment("hot-new", "deployment failure output", 2, token_count=2, retention="hot")
    ledger.add_segment("reference", "deployment rollback notes", 0, token_count=2, retention="reference")

    first = ledger.assemble("deployment rollback", active_token_budget=4)
    second = ledger.assemble("deployment rollback", active_token_budget=4)

    assert first == second
    assert [item["segment_id"] for item in first["selected_segments"]] == ["hot-old", "hot-new"]
    assert first["retrieval_candidate_ids"][0] == "reference"


def test_invalid_search_limit_fails_before_context_selection():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("one", "deployment", 1, token_count=1)

    with pytest.raises(ContextSelectionError, match="invalid search limit"):
        ledger.assemble("deployment", active_token_budget=10, search_limit=0)


def test_receipt_marks_search_work_truncated_at_posting_cap(monkeypatch):
    monkeypatch.setattr(context_module, "MAX_SEARCH_TERM_DOCUMENT_CHECKS", 1)
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("newer", "common deployment failure", 2, token_count=1, retention="reference")
    ledger.add_segment("older", "common compiler message", 1, token_count=1, retention="reference")

    receipt = ledger.assemble("common", active_token_budget=1)

    assert receipt["retrieval_truncated"] is True
    assert receipt["retrieval_candidate_ids"] == ["newer"]


def test_query_character_limit_rejects_repeated_terms_before_tokenization():
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("one", "common evidence", 1, token_count=1)
    query = "x " * (context_module.MAX_SEARCH_QUERY_CHARS // 2 + 1)

    with pytest.raises(ContextSelectionError, match="query_character_limit_exceeded"):
        ledger.assemble(query, active_token_budget=10)


def test_text_byte_limit_cannot_be_bypassed_with_explicit_token_counts(monkeypatch):
    monkeypatch.setattr(context_module, "MAX_CONTEXT_TEXT_BYTES", 3)
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("one", "aa", 1, token_count=1)

    with pytest.raises(ContextAdmissionError, match="context_text_byte_limit_exceeded"):
        ledger.add_segment("two", "bb", 2, token_count=1)


def test_metadata_and_summary_references_have_independent_admission_limits():
    ledger = ContextLedger(max_logical_tokens=100)

    with pytest.raises(ContextAdmissionError, match="context_metadata_byte_limit_exceeded"):
        ledger.add_segment("large-metadata", "text", 1, token_count=1, metadata={"note": "x" * 1025})
    with pytest.raises(ContextAdmissionError, match="summary_reference_limit_exceeded"):
        ledger.add_segment(
            "many-references",
            "text",
            2,
            token_count=1,
            summary_of=(f"source-{index}" for index in range(context_module.MAX_CONTEXT_SUMMARY_REFS + 1)),
        )


def test_auxiliary_bytes_are_capped_and_returned_metadata_is_immutable(monkeypatch):
    monkeypatch.setattr(context_module, "MAX_CONTEXT_AUX_BYTES", 40)
    ledger = ContextLedger(max_logical_tokens=100)
    segment = ledger.add_segment("a", "text", 1, token_count=1, metadata={"source": "local"})

    with pytest.raises(TypeError):
        segment.metadata["extra"] = "x"
    with pytest.raises(ContextAdmissionError, match="context_auxiliary_byte_limit_exceeded"):
        ledger.add_segment("b", "text", 2, token_count=1)


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
