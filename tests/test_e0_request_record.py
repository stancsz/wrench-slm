from __future__ import annotations

import json

import pytest

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import prepare_e0_context
from wrench_harness.e0_request_record import (
    finalize_opencode_preparation_outcome,
    finalize_preparation_outcome,
)
from wrench_harness.namespace_registry import NamespaceDescriptor, NamespaceRegistry, OperationDescriptor
from wrench_harness.opencode_context import OpenCodePreparationJoin
from wrench_harness.outcome_receipt import ReceiptStatus
from wrench_harness.snapshot import create_snapshot


def _prepare(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "sample.py").write_text("def target():\n    return 1\n", encoding="utf-8")
    snapshot = create_snapshot(root, ["sample.py"])
    registry = NamespaceRegistry([
        NamespaceDescriptor("files", "File metadata", (
            OperationDescriptor("inspect", "Inspect one path", {
                "type": "object", "properties": {"path": {"type": "string"}},
            }),
        )),
    ])
    return prepare_e0_context(
        source_root=root,
        snapshot=snapshot,
        paths=["sample.py"],
        store=ArtifactStore(tmp_path / "store"),
        query="target",
        source_order_start=0,
        context_token_budget=64,
        prompt_token_budget=4096,
        namespace_registry=registry,
        schema_lookups=(),
        base_messages=({"role": "system", "content": "Use evidence."},),
        context_position=1,
        serializer=lambda messages: json.dumps(messages, sort_keys=True, separators=(",", ":")),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )


def _postrun(**overrides):
    value = {
        "task_id": "task-fixture",
        "run_id": "run-fixture-1",
        "session_id": "session-fixture",
        "actual_route": "none",
        "attempts": [],
        "work_calls": [{
            "call_id": "verify-fixture-1",
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
        "post_task_evidence_refs": [{
            "evidence_id": "test-result-1",
            "kind": "test_result",
            "sha256": "c" * 64,
        }],
        "verifier": {
            "identity": "fixture-verifier-v1",
            "result": "passed",
            "evidence_ids": ["test-result-1"],
        },
        "outcome": {
            "status": "completed",
            "provenance": "independently_verified",
            "evidence_ids": ["test-result-1"],
        },
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": 0,
            "retries": 0, "fallback_calls": 0, "verifier_calls": 1, "tool_calls": 0,
            "local_tokens": 0, "frontier_tokens": 0,
            "local_token_counter_id": None, "frontier_token_counter_id": None,
            "token_count_status": "not_applicable",
            "local_cost_microunits": 0, "frontier_cost_microunits": 0,
            "cost_status": "known",
        },
        "completeness": "complete",
        "missing_fields": [],
    }
    value.update(overrides)
    return value


def test_final_outcome_joins_preparation_accounting_and_post_task_evidence(tmp_path):
    preparation = _prepare(tmp_path)

    result = finalize_preparation_outcome(preparation, _postrun())

    assert result.status is ReceiptStatus.VALID
    payload = json.loads(result.receipt.payload_json)
    assert payload["schema"] == "wrench.e0.outcome-receipt.v2"
    assert payload["context_receipt_sha256"] == preparation.aggregate_sha256
    assert payload["preparation_accounting_sha256"] == preparation.accounting_receipt.accounting_sha256
    assert payload["selected_evidence_ids"] == list(preparation.selected_evidence_ids)
    assert payload["outcome"]["evidence_ids"] == ["test-result-1"]
    assert "test-result-1" not in payload["selected_evidence_ids"]


def test_final_outcome_rejects_context_ids_as_post_task_verifier_evidence(tmp_path):
    preparation = _prepare(tmp_path)
    context_id = preparation.selected_evidence_ids[0]
    postrun = _postrun(
        verifier={"identity": "fixture-verifier-v1", "result": "passed", "evidence_ids": [context_id]},
        outcome={"status": "completed", "provenance": "independently_verified", "evidence_ids": [context_id]},
    )

    result = finalize_preparation_outcome(preparation, postrun)

    assert result.status is ReceiptStatus.INVALID
    assert "verifier_evidence_not_post_task" in result.errors
    assert "outcome_evidence_not_post_task" in result.errors


def test_final_outcome_rejects_colliding_context_and_post_task_ids(tmp_path):
    preparation = _prepare(tmp_path)
    context_id = preparation.selected_evidence_ids[0]
    postrun = _postrun(
        post_task_evidence_refs=[{
            "evidence_id": context_id, "kind": "test_result", "sha256": "c" * 64,
        }],
        verifier={"identity": "fixture-verifier-v1", "result": "passed", "evidence_ids": [context_id]},
        outcome={"status": "completed", "provenance": "independently_verified", "evidence_ids": [context_id]},
    )

    result = finalize_preparation_outcome(preparation, postrun)

    assert result.status is ReceiptStatus.INVALID
    assert "context_post_task_evidence_id_overlap" in result.errors


def test_final_outcome_rejects_raw_post_task_content_and_bad_preparation_accounting(tmp_path):
    preparation = _prepare(tmp_path)
    bad_content = _postrun(post_task_evidence_refs=[{
        "evidence_id": "test-result-1", "kind": "test_result",
        "sha256": "c" * 64, "content": "raw test output",
    }])
    assert "forbidden_raw_content_key" in finalize_preparation_outcome(preparation, bad_content).errors

    tampered = preparation.accounting_receipt
    object.__setattr__(tampered, "accounting_sha256", "0" * 64)
    result = finalize_preparation_outcome(preparation, _postrun())
    assert result.status is ReceiptStatus.INVALID
    assert result.errors == ("preparation_accounting_invalid",)


def test_v2_requires_session_identity_for_complete_receipts(tmp_path):
    preparation = _prepare(tmp_path)
    complete_without_session = _postrun(session_id=None)
    result = finalize_preparation_outcome(preparation, complete_without_session)
    assert result.status is ReceiptStatus.INVALID
    assert "incomplete_receipt_missing_field_list_inconsistent" in result.errors
    assert "complete_receipt_missing_session_identity" in result.errors

    incomplete_without_session = _postrun(
        session_id=None,
        completeness="incomplete",
        missing_fields=["session_id"],
    )
    result = finalize_preparation_outcome(preparation, incomplete_without_session)
    assert result.status is ReceiptStatus.INCOMPLETE
    assert result.receipt is not None
    assert json.loads(result.receipt.payload_json)["missing_fields"] == ["session_id"]


def test_v2_rejects_prose_in_opaque_identity_fields(tmp_path):
    preparation = _prepare(tmp_path)
    bad_task = finalize_preparation_outcome(preparation, _postrun(task_id="task with embedded raw text"))
    assert bad_task.status is ReceiptStatus.INVALID
    assert "task_id_invalid" in bad_task.errors

    bad_evidence = _postrun(post_task_evidence_refs=[{
        "evidence_id": "test result contains output", "kind": "test_result",
        "sha256": "c" * 64,
    }])
    result = finalize_preparation_outcome(preparation, bad_evidence)
    assert result.status is ReceiptStatus.INVALID
    assert "post_task_evidence_ref_id_invalid" in result.errors


def test_opencode_finalizer_binds_postrun_session_to_preparation_join(tmp_path):
    preparation = _prepare(tmp_path)
    prep_payload = json.loads(preparation.outcome_receipt.receipt.payload_json)
    join = OpenCodePreparationJoin(
        session_id="session-fixture",
        configured_root=tmp_path / "repo",
        snapshot_sha256=prep_payload["snapshot_sha256"],
        root_location_sha256=None,
        root_identity=None,
        preparation=preparation,
    )

    result = finalize_opencode_preparation_outcome(
        join, _postrun(session_id="session-fixture")
    )

    assert result.status is ReceiptStatus.VALID
    assert json.loads(result.receipt.payload_json)["session_id"] == join.session_id


@pytest.mark.parametrize("session_id", ["other-session", None])
def test_opencode_finalizer_rejects_missing_or_mismatched_postrun_session(tmp_path, session_id):
    preparation = _prepare(tmp_path)
    join = OpenCodePreparationJoin(
        session_id="session-fixture",
        configured_root=tmp_path / "repo",
        snapshot_sha256="b" * 64,
        root_location_sha256=None,
        root_identity=None,
        preparation=preparation,
    )

    result = finalize_opencode_preparation_outcome(
        join, _postrun(session_id=session_id)
    )

    assert result.status is ReceiptStatus.INVALID
    assert result.errors == ("opencode_session_id_mismatch",)
