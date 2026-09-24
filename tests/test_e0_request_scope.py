"""Synthetic checks for the offline E0/E3 request scope coordinator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_context_pipeline import (
    PREPARATION_ACCOUNTING_COUNTER_FIELDS,
    PREPARATION_ACCOUNTING_SCHEMA,
    PreparationAccountingReceipt,
    PreparationResult,
    PreparationStatus,
)
from wrench_harness.e0_request_scope import (
    RequestScopeCoordinator,
    RequestScopeError,
    RequestScopeStatus,
)
from wrench_harness.model_lifecycle import ModelLifecycle
from wrench_harness.outcome_receipt import ReceiptStatus, build_outcome_receipt
from wrench_harness.prompt_compiler import PromptGateReceipt, PromptGateStatus


FACTORY = {
    "foundation": b"synthetic-foundation-v1",
    "core": b"synthetic-core-v1",
    "runtime": b"synthetic-runtime-v1",
    "tokenizer": b"synthetic-tokenizer-v1",
    "compatibility": b"synthetic-compatibility-v1",
}
PREPARATION_SHA = "a" * 64


def _preparation() -> PreparationResult:
    counters = {name: 0 for name in PREPARATION_ACCOUNTING_COUNTER_FIELDS}
    for name in (
        "caller_path_count", "structural_index_candidate_count", "schema_discover_results",
        "ledger_selected_count", "ledger_omitted_count", "prompt_serialized_bytes",
        "prompt_token_count", "ledger_logical_token_count", "ledger_selected_token_count",
        "ledger_retrieval_candidate_count", "ledger_search_limit", "structural_index_file_count",
        "structural_index_symbol_count", "structural_index_serialized_bytes",
        "artifact_pin_scope_duration_ns", "structural_index_status", "structural_index_query_status",
        "outcome_receipt_status", "ledger_token_count_mode", "ledger_token_counter_name",
        "callback_external_activity", "process_cpu_ns", "process_rss_bytes", "energy_joules",
        "os_cache_bytes", "request_page_faults",
        "ledger_retrieval_truncated",
    ):
        counters[name] = None
    for name in (
        "exact_source_retrieval_status_counts", "structural_index_exact_read_status_counts",
        "schema_lookup_status_counts",
    ):
        counters[name] = []
    counters["unmeasured_dimensions"] = [
        "callback_external_activity", "process_cpu", "process_rss", "energy",
        "os_cache", "request_page_faults",
    ]
    counters["facade_model_call_sites"] = 0
    counters["facade_provider_call_sites"] = 0
    counters["facade_verifier_call_sites"] = 0
    counters["facade_tool_call_sites"] = 0
    account_payload = {
        "schema": PREPARATION_ACCOUNTING_SCHEMA,
        "preparation_sha256": PREPARATION_SHA,
        "counters": counters,
    }
    account_json = json.dumps(account_payload, sort_keys=True, separators=(",", ":"))
    accounting = PreparationAccountingReceipt(
        PREPARATION_ACCOUNTING_SCHEMA,
        PREPARATION_SHA,
        hashlib.sha256(account_json.encode()).hexdigest(),
        account_json,
    )
    preparation_outcome = build_outcome_receipt({
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "e0-context-preparation",
        "run_id": PREPARATION_SHA,
        "snapshot_sha256": "b" * 64,
        "context_receipt_sha256": PREPARATION_SHA,
        "selected_evidence_ids": [],
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "actual_route": "none",
        "attempts": [],
        "work_calls": [],
        "verifier": {"identity": None, "result": "not_run", "evidence_ids": []},
        "outcome": {"status": "unknown", "provenance": "unknown", "evidence_ids": []},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": 0, "retries": 0,
            "fallback_calls": 0, "verifier_calls": 0, "tool_calls": 0,
            "local_tokens": 0, "frontier_tokens": 0,
            "local_token_counter_id": None, "frontier_token_counter_id": None,
            "token_count_status": "not_applicable", "local_cost_microunits": 0,
            "frontier_cost_microunits": 0, "cost_status": "known",
        },
        "completeness": "incomplete",
        "missing_fields": ["outcome"],
    })
    assert preparation_outcome.status is ReceiptStatus.INCOMPLETE
    prompt = b"synthetic-gated-prompt"
    prompt_gate = PromptGateReceipt(
        PromptGateStatus.READY, "synthetic-session", (), (), (),
        hashlib.sha256(prompt).hexdigest(), 1, 64, "synthetic-tokenizer-v1",
        "synthetic-serializer-v1", len(prompt),
    )
    return PreparationResult(
        PreparationStatus.READY, "none", prompt, prompt_gate,
        preparation_outcome, PREPARATION_SHA,
        (), (), (), (), (), None, accounting_receipt=accounting,
    )


def _outcome(*, run_id: str = "synthetic-run", status: str = "completed", completeness: str = "complete",
             snapshot_hash: str = "b" * 64):
    payload = {
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "synthetic-task",
        "run_id": run_id,
        "snapshot_sha256": snapshot_hash,
        "context_receipt_sha256": PREPARATION_SHA,
        "selected_evidence_ids": [],
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "actual_route": "none",
        "attempts": [],
        "work_calls": [],
        "verifier": {"identity": None, "result": "not_run", "evidence_ids": []},
        "outcome": {"status": status, "provenance": "user_reported", "evidence_ids": []},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": 0, "retries": 0,
            "fallback_calls": 0, "verifier_calls": 0, "tool_calls": 0,
            "local_tokens": 0, "frontier_tokens": 0,
            "local_token_counter_id": None, "frontier_token_counter_id": None,
            "token_count_status": "not_applicable", "local_cost_microunits": 0,
            "frontier_cost_microunits": 0, "cost_status": "known",
        },
        "completeness": completeness,
        "missing_fields": [] if completeness == "complete" else ["outcome"],
    }
    return build_outcome_receipt(payload)


def _candidate(lifecycle: ModelLifecycle) -> None:
    payloads = dict(FACTORY)
    payloads["personal"] = b"synthetic-personal-v2"
    lifecycle.stage_candidate("personal-2", parent_version_id="factory", payloads=payloads)
    lifecycle.admit_candidate("personal-2")


def test_request_scope_keeps_starting_version_and_next_scope_sees_activation(tmp_path):
    artifact_store = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifact_store, lifecycle)
    content = b"synthetic-context"
    handle = artifact_store.put(
        snapshot_sha256="c" * 64, source_path="fixture.txt",
        expected_content_sha256=hashlib.sha256(content).hexdigest(), data=content,
    )
    prep = _preparation()
    terminal = _outcome(run_id="scope-1")
    assert terminal.status is ReceiptStatus.VALID

    with coordinator.open_scope("scope-1") as scope:
        first_pin = scope.version_pin

        def prepare(request):
            assert request is scope.artifact_request
            assert request.pin(handle).data == content
            return prep

        scope.prepare(prepare)
        _candidate(lifecycle)
        lifecycle.activate_candidate("personal-2")
        assert scope.version_pin.version_id == "factory"
        assert lifecycle.read_payload(first_pin, "core") == FACTORY["core"]
        scope.finish(terminal.receipt)

    assert scope.status is RequestScopeStatus.READY
    assert scope.envelope is not None
    envelope = json.loads(scope.envelope.payload_json)
    assert envelope["version_id"] == "factory"
    assert envelope["context_receipt_sha256"] == PREPARATION_SHA
    assert envelope["snapshot_sha256"] == "b" * 64
    assert envelope["preparation_accounting_sha256"] == prep.accounting_receipt.accounting_sha256
    assert envelope["preparation_outcome_receipt_sha256"] == prep.outcome_receipt.receipt.sha256
    assert envelope["artifact_pin_scope_duration_ns"] >= 0
    assert artifact_store._pins == {}

    with coordinator.open_scope("scope-2") as following:
        assert following.version_pin.version_id == "personal-2"
        following.prepare(lambda request: prep)
        following.finish(_outcome(run_id="scope-2").receipt)
    assert following.status is RequestScopeStatus.READY


def test_complete_receipt_with_failed_task_outcome_is_bound_as_failed(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)
    failed = _outcome(run_id="failed-scope", status="failed")
    assert failed.status is ReceiptStatus.VALID
    with coordinator.open_scope("failed-scope") as scope:
        scope.prepare(lambda request: _preparation())
        scope.finish(failed.receipt)
    assert scope.status is RequestScopeStatus.FAILED
    assert scope.envelope is not None
    assert json.loads(scope.envelope.payload_json)["outcome_status"] == "failed"


def test_incomplete_outcome_and_exception_never_leave_request_pins(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)
    data = b"synthetic-pin"
    handle = artifacts.put(
        snapshot_sha256="d" * 64, source_path="pin.txt",
        expected_content_sha256=hashlib.sha256(data).hexdigest(), data=data,
    )

    with coordinator.open_scope("incomplete-scope") as scope:
        scope.prepare(lambda request: (request.pin(handle), _preparation())[1])
        incomplete = _outcome(run_id="incomplete-scope", status="unknown", completeness="incomplete")
        assert incomplete.status is ReceiptStatus.INCOMPLETE
        with pytest.raises(RequestScopeError, match="incomplete_or_invalid"):
            scope.finish(incomplete.receipt)
    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None
    assert artifacts._pins == {}

    with pytest.raises(RuntimeError, match="synthetic failure"):
        with coordinator.open_scope("exception-scope") as failed_scope:
            failed_scope.prepare(lambda request: (request.pin(handle), _preparation())[1])
            raise RuntimeError("synthetic failure")
    assert failed_scope.status is RequestScopeStatus.FAILED
    assert failed_scope.envelope is None
    assert artifacts._pins == {}


def test_scope_without_explicit_terminal_receipt_is_incomplete(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    with RequestScopeCoordinator(artifacts, lifecycle).open_scope("no-terminal") as scope:
        scope.prepare(lambda request: _preparation())
    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None


def test_preparer_cannot_close_artifact_pins_before_terminal_receipt(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)
    content = b"synthetic-early-close"
    handle = artifacts.put(
        snapshot_sha256="e" * 64, source_path="early-close.txt",
        expected_content_sha256=hashlib.sha256(content).hexdigest(), data=content,
    )

    with coordinator.open_scope("early-close") as scope:
        def close_during_prepare(request):
            assert request.pin(handle).data == content
            request.__exit__(None, None, None)
            return _preparation()

        with pytest.raises(RequestScopeError, match="artifact_request_scope_inactive"):
            scope.prepare(close_during_prepare)

    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None
    assert artifacts._pins == {}


def test_terminal_receipt_with_mismatched_snapshot_fails_closed(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)

    with coordinator.open_scope("snapshot-mismatch") as scope:
        scope.prepare(lambda request: _preparation())
        with pytest.raises(RequestScopeError, match="preparation_outcome_join_mismatch"):
            scope.finish(_outcome(run_id="snapshot-mismatch", snapshot_hash="c" * 64).receipt)

    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None
    assert artifacts._pins == {}


def test_terminal_receipt_from_another_request_fails_closed(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)

    with coordinator.open_scope("request-a") as scope:
        scope.prepare(lambda request: _preparation())
        with pytest.raises(RequestScopeError, match="request_run_join_mismatch"):
            scope.finish(_outcome(run_id="request-b").receipt)

    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None
    assert artifacts._pins == {}


def test_ready_preparation_without_matching_preparation_receipt_fails_closed(tmp_path):
    artifacts = ArtifactStore(tmp_path / "artifacts")
    lifecycle = ModelLifecycle.create(tmp_path / "versions", factory_version_id="factory", payloads=FACTORY)
    coordinator = RequestScopeCoordinator(artifacts, lifecycle)
    malformed = replace(_preparation(), outcome_receipt=None)

    with coordinator.open_scope("missing-prep-receipt") as scope:
        with pytest.raises(RequestScopeError, match="preparation_outcome_receipt_invalid"):
            scope.bind_preparation(malformed)

    assert scope.status is RequestScopeStatus.INCOMPLETE
    assert scope.envelope is None
    assert artifacts._pins == {}
