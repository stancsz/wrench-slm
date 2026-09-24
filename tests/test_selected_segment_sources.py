import hashlib
import json
from dataclasses import replace

import pytest

from wrench_harness.e0_context_pipeline import SourceIdentity
from wrench_harness.selected_segment_sources import (
    SelectedSourceReferenceError,
    build_selected_segment_source_references,
)
from wrench_harness.snapshot_structure import StructuralCandidate


SNAPSHOT = "a" * 64
CONTENT = "b" * 64
HANDLE = "c" * 64


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _source(path="src/example.py"):
    source_id = "source-" + _digest([SNAPSHOT, path, CONTENT])
    return SourceIdentity(source_id, path, CONTENT, HANDLE, "ok")


def _candidate(path="src/example.py", start=8, end=13):
    return StructuralCandidate(
        name="render_panel",
        kind="function",
        path=path,
        start_line=start,
        end_line=end,
        signature="def render_panel(value): ...",
        match_score=17,
        snapshot_sha256=SNAPSHOT,
        source_sha256=CONTENT,
        parser="python_ast_v1",
        language="python",
    )


def _symbol_id(candidate):
    return "symbol-" + _digest([
        SNAPSHOT,
        candidate.path,
        CONTENT,
        candidate.name,
        candidate.start_line,
        candidate.end_line,
    ])


def test_selected_source_joins_identity_and_marks_whole_file_and_missing_summary_lineage():
    source = _source()
    receipt = build_selected_segment_source_references(
        snapshot_sha256=SNAPSHOT,
        selected_segment_ids=(source.evidence_id,),
        sources=(source,),
    ).as_dict()

    row = receipt["references"][0]
    assert row["segment_kind"] == "source"
    assert row["source_path"] == "src/example.py"
    assert row["content_sha256"] == CONTENT
    assert row["artifact_handle_id"] == HANDLE
    assert row["span_status"] == "whole_file"
    assert row["start_line"] is None and row["end_line"] is None
    assert row["summary_lineage_status"] == "unavailable"
    assert row["summary_of"] is None
    assert receipt["receipt_sha256"] == _digest({key: receipt[key] for key in (
        "schema", "snapshot_sha256", "selected_segment_ids", "references"
    )})


def test_receipt_reference_rows_cannot_be_mutated_after_digesting():
    source = _source()
    result = build_selected_segment_source_references(
        snapshot_sha256=SNAPSHOT,
        selected_segment_ids=(source.evidence_id,),
        sources=(source,),
    )
    with pytest.raises(TypeError):
        result.references[0]["span_status"] = "changed"

    exported = result.as_dict()
    assert exported["references"][0]["span_status"] == "whole_file"
    assert exported["receipt_sha256"] == _digest({key: exported[key] for key in (
        "schema", "snapshot_sha256", "selected_segment_ids", "references"
    )})


def test_selected_symbol_gets_exact_parser_reported_span_when_candidate_row_is_supplied():
    candidate = _candidate()
    receipt = build_selected_segment_source_references(
        snapshot_sha256=SNAPSHOT,
        selected_segment_ids=(_symbol_id(candidate),),
        sources=(_source(),),
        candidates=(candidate,),
    ).as_dict()

    row = receipt["references"][0]
    assert row["segment_kind"] == "symbol"
    assert (row["start_line"], row["end_line"]) == (8, 13)
    assert row["span_status"] == "parser_reported_exact"
    assert row["parser"] == "python_ast_v1"
    assert row["language"] == "python"


def test_selected_symbol_without_candidate_lineage_stays_unavailable():
    candidate = _candidate()
    receipt = build_selected_segment_source_references(
        snapshot_sha256=SNAPSHOT,
        selected_segment_ids=(_symbol_id(candidate),),
        sources=(_source(),),
    ).as_dict()

    row = receipt["references"][0]
    assert row["segment_kind"] == "unresolved"
    assert row["span_status"] == "unavailable"
    assert row["start_line"] is None and row["end_line"] is None
    assert row["summary_lineage_status"] == "unavailable"


def test_candidate_must_match_the_snapshot_and_successful_source_identity():
    candidate = _candidate()
    wrong_snapshot = StructuralCandidate(
        **{**candidate.__dict__, "snapshot_sha256": "d" * 64}
    )
    with pytest.raises(SelectedSourceReferenceError, match="candidate_snapshot_mismatch"):
        build_selected_segment_source_references(
            snapshot_sha256=SNAPSHOT,
            selected_segment_ids=(_symbol_id(candidate),),
            sources=(_source(),),
            candidates=(wrong_snapshot,),
        )


def test_oversized_source_path_is_rejected_before_receipt_encoding():
    source = _source(path="a" * 1025)
    with pytest.raises(SelectedSourceReferenceError, match="source_identity_fields_invalid"):
        build_selected_segment_source_references(
            snapshot_sha256=SNAPSHOT,
            selected_segment_ids=(source.evidence_id,),
            sources=(source,),
        )


@pytest.mark.parametrize("metadata", ["p" * 129, object()])
def test_invalid_candidate_parser_metadata_is_rejected(metadata):
    candidate = replace(_candidate(), parser=metadata)
    with pytest.raises(SelectedSourceReferenceError, match="candidate_metadata_invalid"):
        build_selected_segment_source_references(
            snapshot_sha256=SNAPSHOT,
            selected_segment_ids=(_symbol_id(_candidate()),),
            sources=(_source(),),
            candidates=(candidate,),
        )


def test_duplicate_selected_ids_are_rejected():
    source = _source()
    with pytest.raises(SelectedSourceReferenceError, match="duplicate_selected_segment_id"):
        build_selected_segment_source_references(
            snapshot_sha256=SNAPSHOT,
            selected_segment_ids=(source.evidence_id, source.evidence_id),
            sources=(source,),
        )
