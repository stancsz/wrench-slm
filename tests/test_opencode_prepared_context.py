import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from wrench_harness.context import ContextLedger
from wrench_harness.e0_context_pipeline import PreparationResult, PreparationStatus
from wrench_harness.opencode_context import OpenCodePreparationJoin
from wrench_harness.opencode_hook_projection import (
    MAX_HOOK_MESSAGES,
    verify_opencode_prepared_transition_receipt,
)
from wrench_harness.opencode_prepared_context import (
    PreparedContextStatus,
    materialize_opencode_prepared_context,
)
from wrench_harness.outcome_receipt import build_outcome_receipt
from wrench_harness.prompt_compiler import PromptGateStatus, compile_prompt


def _message(role, text):
    return {"role": role, "content": [{"type": "text", "text": text}]}


def _event(session_id="ses_fixture123", messages=None):
    return {
        "sessionID": session_id,
        "agent": "build",
        "model": {"providerID": "fixture-provider", "id": "fixture-model"},
        "system": [{"type": "text", "text": "fixture system"}],
        "messages": messages if messages is not None else [
            _message("system", "fixture rules"),
            _message("user", "fixture request"),
        ],
        "tools": {},
        "options": {"temperature": 0},
    }


def _ready_join(*, context_message_json=None, gate=None, status=PreparationStatus.READY,
                route="none", retrieval_misses=()):
    ledger = ContextLedger(max_logical_tokens=100)
    ledger.add_segment("fixture-evidence", "authored synthetic context", 1, token_count=2)
    assembly = ledger.assemble("synthetic query", active_token_budget=16)
    base = [_message("system", "fixture rules"), _message("user", "fixture request")]

    def serializer(messages):
        from wrench_harness.prompt_compiler import materialize_prompt_messages
        return json.dumps(materialize_prompt_messages(messages), sort_keys=True, separators=(",", ":"))

    compiled = compile_prompt(
        assembly, base, context_position=1, serializer=serializer,
        tokenizer_counter=len, serializer_id="authored-fixture-serializer-v1",
        tokenizer_id="authored-fixture-character-counter-v1", hard_budget=100_000,
        message_format="opencode-2.0.15",
    )
    assert compiled.receipt.status is PromptGateStatus.READY
    aggregate_hash = "a" * 64
    snapshot_hash = "b" * 64
    receipt = build_outcome_receipt({
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "e0-context-preparation",
        "run_id": aggregate_hash,
        "snapshot_sha256": snapshot_hash,
        "context_receipt_sha256": aggregate_hash,
        "selected_evidence_ids": list(compiled.receipt.selected_evidence_ids),
        "omitted_evidence_ids": [],
        "retrieval_misses": [],
        "actual_route": "none",
        "attempts": [], "work_calls": [],
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
        "completeness": "incomplete", "missing_fields": ["outcome"],
    })
    preparation = PreparationResult(
        status=status, route=route, prompt=compiled.prompt,
        prompt_gate=gate or compiled.receipt, outcome_receipt=receipt,
        aggregate_sha256=aggregate_hash, sources=(),
        selected_evidence_ids=compiled.receipt.selected_evidence_ids,
        omitted_evidence=(), retrieval_misses=retrieval_misses, schema_digests=(),
        structural_status="ready",
        context_message_json=(
            compiled.context_message_json
            if context_message_json is None else context_message_json
        ),
    )
    return OpenCodePreparationJoin(
        session_id="ses_fixture123", configured_root=Path("C:/fixture"),
        snapshot_sha256=snapshot_hash, root_location_sha256="c" * 64,
        root_identity="fixture-root", preparation=preparation,
    ), compiled


def test_inserts_exact_compiler_message_once_and_preserves_hook_fields_and_order():
    join, compiled = _ready_join()
    event = _event()
    original = copy.deepcopy(event)

    result = materialize_opencode_prepared_context(join, event)

    assert result.status is PreparedContextStatus.READY
    assert result.event is not None
    assert result.transition_receipt is not None
    assert verify_opencode_prepared_transition_receipt(result.transition_receipt)
    inserted = result.event["messages"][compiled.receipt.context_insertion_position]
    assert json.dumps(inserted, sort_keys=True, separators=(",", ":")) == compiled.context_message_json
    assert hashlib.sha256(
        json.dumps(inserted, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest() == compiled.receipt.context_message_sha256
    assert result.event["messages"] == (
        original["messages"][:compiled.receipt.context_insertion_position]
        + [inserted]
        + original["messages"][compiled.receipt.context_insertion_position:]
    )
    assert {key: result.event[key] for key in original if key != "messages"} == {
        key: original[key] for key in original if key != "messages"
    }
    assert event == original
    assert "authored synthetic context" not in repr(result)
    assert "authored synthetic context" not in repr(result.transition_receipt)
    redacted_prompt_preparation = replace(join.preparation, prompt="<redacted>")
    assert "authored synthetic context" not in repr(redacted_prompt_preparation)


def test_fails_closed_on_session_mismatch_and_non_ready_admission():
    join, _ = _ready_join()
    assert materialize_opencode_prepared_context(join, _event("ses_other123")).status is PreparedContextStatus.ADMISSION_REJECTED
    not_ready = replace(join, preparation=replace(join.preparation, status=PreparationStatus.PROMPT_REJECTED))
    assert materialize_opencode_prepared_context(not_ready, _event()).status is PreparedContextStatus.ADMISSION_REJECTED
    wrong_route = replace(join, preparation=replace(join.preparation, route="openrouter"))
    assert materialize_opencode_prepared_context(wrong_route, _event()).status is PreparedContextStatus.ADMISSION_REJECTED
    missed = replace(join, preparation=replace(join.preparation, retrieval_misses=(("fixture", "missing"),)))
    assert materialize_opencode_prepared_context(missed, _event()).status is PreparedContextStatus.ADMISSION_REJECTED


def test_rejects_missing_forged_or_unbound_compiler_message_without_prompt_reconstruction():
    join, compiled = _ready_join()
    missing = replace(join, preparation=replace(join.preparation, context_message_json=None))
    assert materialize_opencode_prepared_context(missing, _event()).status is PreparedContextStatus.CONTEXT_BINDING_MISSING

    forged = replace(join, preparation=replace(
        join.preparation,
        context_message_json=json.dumps(_message("user", "forged content")),
        prompt="serialized prompt containing authored synthetic context",
    ))
    result = materialize_opencode_prepared_context(forged, _event())
    assert result.status is PreparedContextStatus.CONTEXT_BINDING_MISMATCH
    assert result.event is None

    altered_gate = replace(compiled.receipt, context_message_sha256="0" * 64)
    altered = replace(join, preparation=replace(join.preparation, prompt_gate=altered_gate))
    assert materialize_opencode_prepared_context(altered, _event()).status is PreparedContextStatus.CONTEXT_BINDING_MISMATCH
    rejected_gate = replace(compiled.receipt, status=PromptGateStatus.BUDGET_EXCEEDED)
    rejected = replace(join, preparation=replace(join.preparation, prompt_gate=rejected_gate))
    assert materialize_opencode_prepared_context(rejected, _event()).status is PreparedContextStatus.ADMISSION_REJECTED


def test_rejects_preexisting_duplicate_malformed_event_and_overflow():
    join, compiled = _ready_join()
    message = json.loads(compiled.context_message_json)
    assert materialize_opencode_prepared_context(
        join, _event(messages=[message, _message("user", "request")])
    ).status is PreparedContextStatus.MESSAGE_ALREADY_PRESENT
    malformed = _event()
    del malformed["tools"]
    assert materialize_opencode_prepared_context(join, malformed).status is PreparedContextStatus.INVALID_EVENT

    full = [_message("user", f"m{i}") for i in range(MAX_HOOK_MESSAGES)]
    assert materialize_opencode_prepared_context(join, _event(messages=full)).status is PreparedContextStatus.INSERTION_POSITION_INVALID

    out_of_range_gate = replace(compiled.receipt, context_insertion_position=MAX_HOOK_MESSAGES)
    out_of_range = replace(join, preparation=replace(join.preparation, prompt_gate=out_of_range_gate))
    assert materialize_opencode_prepared_context(
        out_of_range, _event(messages=[_message("user", "only")])
    ).status is PreparedContextStatus.INSERTION_POSITION_INVALID


@pytest.mark.parametrize("bad_json", ["{", "null", "[]"])
def test_rejects_malformed_or_wrong_shaped_context_bridge(bad_json):
    join, _ = _ready_join(context_message_json=bad_json)
    result = materialize_opencode_prepared_context(join, _event())
    assert result.status in {
        PreparedContextStatus.CONTEXT_BINDING_INVALID,
        PreparedContextStatus.CONTEXT_BINDING_MISMATCH,
    }
    assert result.event is None
