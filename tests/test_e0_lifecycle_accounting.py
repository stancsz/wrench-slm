from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_lifecycle_accounting import (
    ENVELOPE_SCHEMA,
    ENVELOPE_SCHEMA_WITH_CONTEXT_HOOK_OBSERVATION,
    PartialTraceStatus,
    build_partial_lifecycle_trace,
)
from wrench_harness.e0_request_record import finalize_opencode_preparation_outcome
from wrench_harness.e0_route_preparation import (
    RoutePreparationStatus,
    route_and_prepare_e0_context,
    verify_route_preparation_accounting_receipt,
)
from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.namespace_registry import NamespaceDescriptor, NamespaceRegistry, OperationDescriptor
from wrench_harness.opencode_context import prepare_opencode_e0_context
from wrench_harness.prompt_compiler import materialize_prompt_messages
from wrench_harness.opencode_hook_projection import (
    CONTEXT_HOOK_OBSERVATION_SCHEMA,
    OpenCodeContextHookObserver,
    OPENCODE_CONTEXT_HOOK_VERSION,
    OpenCodeProjectionResult,
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)
from wrench_harness.outcome_receipt import ReceiptStatus, build_outcome_receipt
from wrench_harness.snapshot import bind_source_root, create_snapshot


def _prepare(
    tmp_path,
    *,
    extra_files=(),
    sample_source="def target():\n    return 1\n",
):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    (root / "sample.py").write_text(sample_source, encoding="utf-8")
    for relative_path in extra_files:
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def unrelated():\n    return 'other fixture'\n", encoding="utf-8")
    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, ("sample.py", *extra_files))
    registry = NamespaceRegistry([
        NamespaceDescriptor("files", "File metadata", (
            OperationDescriptor("inspect", "Inspect one path", {
                "type": "object", "properties": {"path": {"type": "string"}},
            }),
        )),
    ])
    join = prepare_opencode_e0_context(
        "ses_partial_trace_fixture",
        {"id": "ses_partial_trace_fixture", "location": {"directory": str(root)}},
        snapshot=snapshot,
        paths=["sample.py"],
        store=ArtifactStore(tmp_path / "store"),
        query="target",
        source_order_start=0,
        context_token_budget=64,
        prompt_token_budget=4096,
        namespace_registry=registry,
        schema_lookups=(),
        base_messages=({"role": "system", "content": [{"type": "text", "text": "Use evidence."}]},),
        context_position=1,
        serializer=lambda messages: json.dumps(materialize_prompt_messages(messages), sort_keys=True, separators=(",", ":")),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )
    preparation = join.preparation
    return preparation, join


def _postrun(session_id):
    return {
        "task_id": "task-fixture",
        "run_id": "run-fixture-1",
        "session_id": session_id,
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
            "evidence_id": "test-result-1", "kind": "test_result", "sha256": "c" * 64,
        }],
        "verifier": {
            "identity": "fixture-verifier-v1", "result": "passed", "evidence_ids": ["test-result-1"],
        },
        "outcome": {
            "status": "completed", "provenance": "independently_verified", "evidence_ids": ["test-result-1"],
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


def _projection(session_id="ses_partial_trace_fixture"):
    event = {
        "sessionID": session_id,
        "model": {"id": "model-fixture", "providerID": "provider-fixture"},
        "system": [],
        "messages": [{"role": "user", "content": [{"type": "text", "text": "synthetic fixture"}]}],
        "options": {},
        "agent": "build",
        "tools": {},
    }
    return project_opencode_context_hook(event)


def _prepared_transition(preparation, *, insertion_position=None, message_override=None):
    """Build fixture hook projections from the exact prepared prompt message list."""
    prompt = preparation.prompt
    if type(prompt) is bytes:
        prompt = prompt.decode("utf-8")
    prepared_messages = json.loads(prompt)
    assert type(prepared_messages) is list
    gate = preparation.prompt_gate
    position = gate.context_insertion_position
    assert type(position) is int
    assert gate.context_message_sha256 is not None
    inserted_message = prepared_messages[position]
    expected_message = inserted_message if message_override is None else message_override
    before_messages = list(prepared_messages)
    del before_messages[position]
    after_messages = list(before_messages)
    actual_position = position if insertion_position is None else insertion_position
    after_messages.insert(actual_position, inserted_message)

    base_event = json.loads(_projection().projection.payload_json)
    before_event = dict(base_event)
    before_event["messages"] = before_messages
    after_event = dict(base_event)
    after_event["messages"] = after_messages
    return (
        project_opencode_context_hook(before_event),
        project_opencode_context_hook(after_event),
        expected_message,
        position,
    )


def _finalized(join, preparation):
    result = finalize_opencode_preparation_outcome(join, _postrun(join.session_id))
    assert result.receipt is not None
    return result.receipt


def _route_preparation(
    tmp_path,
    join,
    *,
    prompt="Read sample.py with a 64 byte limit.",
    snapshot_paths=("sample.py",),
    system_content="Use evidence.",
):
    binding = bind_source_root(join.configured_root)
    snapshot = create_snapshot(binding, snapshot_paths)
    assert snapshot.snapshot_sha256 == join.snapshot_sha256
    result = route_and_prepare_e0_context(
        prompt,
        root_binding=binding,
        snapshot=snapshot,
        store=ArtifactStore(tmp_path / "route-preparation-store"),
        query="target",
        source_order_start=0,
        context_token_budget=64,
        prompt_token_budget=4096,
        namespace_registry=NamespaceRegistry([]),
        schema_lookups=(),
        base_messages=({"role": "system", "content": [{"type": "text", "text": system_content}]},),
        context_position=1,
        message_format="opencode-2.0.15",
        serializer=lambda messages: json.dumps(materialize_prompt_messages(messages), sort_keys=True, separators=(",", ":")),
        tokenizer_counter=lambda value: len(value),
        serializer_id="fixture-json-v1",
        tokenizer_id="fixture-char-count-v1",
    )
    assert result.preparation is not None
    return replace(join, preparation=result.preparation), result


def test_partial_trace_joins_valid_references_without_copying_hook_content(tmp_path):
    preparation, join = _prepare(tmp_path)
    projection = _projection()

    result = build_partial_lifecycle_trace(join, projection, _finalized(join, preparation))

    assert result.status is PartialTraceStatus.READY
    assert result.envelope is not None
    payload = json.loads(result.envelope.payload_json)
    assert result.envelope.schema == ENVELOPE_SCHEMA
    assert payload["schema"] == ENVELOPE_SCHEMA
    assert payload["provenance"] == "caller_supplied_structural_join_untrusted"
    assert payload["run_id"] == {"value": "run-fixture-1", "meaning": "caller_correlation_only"}
    assert payload["session_id_ref"] == join.session_id
    assert payload["snapshot_sha256"] == join.snapshot_sha256
    assert payload["preparation_accounting_sha256"] == preparation.accounting_receipt.accounting_sha256
    assert payload["projection_sha256"] == projection.projection.projection_sha256
    assert payload["projection_serialized_bytes"] == projection.projection.serialized_bytes
    assert payload["measured_dimensions"] == [
        "preparation_facade_counters_by_accounting_receipt_reference",
        "locally_serialized_projection_input_bytes",
    ]
    assert "runtime_hook_event_provenance_and_atomic_capture" in payload["unavailable_dimensions"]
    assert "provider_final_serialization_and_tokenizer_parity" in payload["unavailable_dimensions"]
    assert "synthetic fixture" not in result.envelope.payload_json
    assert len(result.envelope.sha256) == 64
    assert "context_hook_observation" not in payload


def _scoped_observation(session_id="ses_partial_trace_fixture"):
    observer = OpenCodeContextHookObserver(
        lambda _event: None,
        monotonic_ns=iter((10, 15)).__next__,
        session_id_getter=lambda event: event["sessionID"],
    )
    asyncio.run(observer({"sessionID": session_id, "messages": [{"text": "secret"}]}))
    return observer.observation


def test_partial_trace_joins_complete_scoped_hook_observation(tmp_path):
    preparation, join = _prepare(tmp_path)
    observation = _scoped_observation()

    result = build_partial_lifecycle_trace(
        join, _projection(), _finalized(join, preparation),
        context_hook_observation=observation,
    )

    assert result.status is PartialTraceStatus.READY
    assert result.envelope.schema == ENVELOPE_SCHEMA_WITH_CONTEXT_HOOK_OBSERVATION
    payload = json.loads(result.envelope.payload_json)
    assert payload["schema"] == ENVELOPE_SCHEMA_WITH_CONTEXT_HOOK_OBSERVATION
    summary = payload["context_hook_observation"]
    assert summary["provenance"] == "caller_supplied_unauthenticated_structural_observation"
    assert summary["schema"] == CONTEXT_HOOK_OBSERVATION_SCHEMA
    assert summary["opencode_context_hook_version"] == OPENCODE_CONTEXT_HOOK_VERSION
    assert summary["session_id_sha256"] == hashlib.sha256(
        join.session_id.encode("utf-8")
    ).hexdigest()
    assert summary["all_rows_bound_to_session"] is True
    assert summary["calls"] == [{
        "invocation_index": 1, "elapsed_ns": 5, "result": "returned",
    }]
    assert "ses_partial_trace_fixture" not in json.dumps(summary)
    assert "secret" not in result.envelope.payload_json


def test_partial_trace_rejects_unscoped_or_mixed_session_observation(tmp_path):
    preparation, join = _prepare(tmp_path)
    unscoped = _scoped_observation()
    unscoped = replace(
        unscoped,
        calls=(replace(unscoped.calls[0], scope_sha256=None),),
    )
    mixed_observer = OpenCodeContextHookObserver(
        lambda _event: None,
        monotonic_ns=iter((10, 15, 20, 28)).__next__,
        session_id_getter=lambda event: event["sessionID"],
    )
    asyncio.run(mixed_observer({"sessionID": join.session_id}))
    asyncio.run(mixed_observer({"sessionID": "ses_other_session"}))
    mixed = mixed_observer.observation

    for observation in (unscoped, mixed):
        result = build_partial_lifecycle_trace(
            join, _projection(), _finalized(join, preparation),
            context_hook_observation=observation,
        )
        assert result.status is PartialTraceStatus.INVALID_OBSERVATION
        assert result.envelope is None


def test_partial_trace_rejects_incomplete_capped_saturated_or_mismatched_observation(tmp_path):
    preparation, join = _prepare(tmp_path)
    observation = _scoped_observation()

    class _HostileEquality:
        def __eq__(self, _other):
            raise AssertionError("untrusted equality must not run")

    invalid = (
        replace(observation, completed_count=0),
        replace(observation, calls_capped=True),
        replace(observation, saturated=True),
        replace(observation, schema="wrench.opencode.context-hook-observation.v1"),
        replace(observation, opencode_context_hook_version="wrong-version"),
        replace(observation, schema=_HostileEquality()),
        replace(observation, opencode_context_hook_version=_HostileEquality()),
    )

    for candidate in invalid:
        result = build_partial_lifecycle_trace(
            join, _projection(), _finalized(join, preparation),
            context_hook_observation=candidate,
        )
        assert result.status is PartialTraceStatus.INVALID_OBSERVATION
        assert result.envelope is None


def test_partial_trace_rejects_impossible_observation_timing_error_count(tmp_path):
    preparation, join = _prepare(tmp_path)
    observation = _scoped_observation()
    impossible = replace(observation, timing_error_count=3)

    result = build_partial_lifecycle_trace(
        join, _projection(), _finalized(join, preparation),
        context_hook_observation=impossible,
    )

    assert result.status is PartialTraceStatus.INVALID_OBSERVATION
    assert result.envelope is None


def test_partial_trace_requires_ready_projection(tmp_path):
    preparation, join = _prepare(tmp_path)
    projection = OpenCodeProjectionResult(OpenCodeProjectionStatus.INVALID_INPUT, None, "fixture")

    result = build_partial_lifecycle_trace(join, projection, _finalized(join, preparation))

    assert result.status is PartialTraceStatus.INVALID_PROJECTION
    assert result.envelope is None


def test_partial_trace_rejects_projection_session_mismatch(tmp_path):
    preparation, join = _prepare(tmp_path)

    result = build_partial_lifecycle_trace(
        join, _projection("ses_other_fixture"), _finalized(join, preparation)
    )

    assert result.status is PartialTraceStatus.JOIN_MISMATCH
    assert result.reason == "projection_session_mismatch"


def test_partial_trace_rejects_receipt_snapshot_mismatch(tmp_path):
    preparation, join = _prepare(tmp_path)
    receipt = _finalized(join, preparation)
    payload = json.loads(receipt.payload_json)
    payload["snapshot_sha256"] = "f" * 64
    mismatched_receipt = build_outcome_receipt(payload)
    assert mismatched_receipt.receipt is not None

    result = build_partial_lifecycle_trace(join, _projection(), mismatched_receipt.receipt)

    assert result.status is PartialTraceStatus.JOIN_MISMATCH
    assert result.reason == "receipt_join_mismatch"


def test_partial_trace_binds_join_back_to_preparation_snapshot(tmp_path):
    preparation, join = _prepare(tmp_path)
    mismatched_join = replace(join, snapshot_sha256="f" * 64)
    payload = json.loads(_finalized(join, preparation).payload_json)
    payload["snapshot_sha256"] = mismatched_join.snapshot_sha256
    mismatched_receipt = build_outcome_receipt(payload)
    assert mismatched_receipt.status is ReceiptStatus.VALID
    assert mismatched_receipt.receipt is not None

    result = build_partial_lifecycle_trace(
        mismatched_join, _projection(), mismatched_receipt.receipt
    )

    assert result.status is PartialTraceStatus.JOIN_MISMATCH
    assert result.reason == "preparation_identity_mismatch"


def test_partial_trace_rejects_invalid_or_tampered_final_receipt(tmp_path):
    preparation, join = _prepare(tmp_path)
    receipt = _finalized(join, preparation)
    payload = json.loads(receipt.payload_json)
    payload["preparation_accounting_sha256"] = "0" * 64
    invalid_receipt = build_outcome_receipt(payload)

    result = build_partial_lifecycle_trace(join, _projection(), receipt)
    assert result.status is PartialTraceStatus.READY

    rejected = build_partial_lifecycle_trace(join, _projection(), invalid_receipt.receipt)
    assert rejected.status is PartialTraceStatus.JOIN_MISMATCH
    assert rejected.reason == "receipt_join_mismatch"


def test_partial_trace_joins_route_owned_preparation_receipt(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    assert route_preparation.status is RoutePreparationStatus.JOINED
    assert route_preparation.route_result.status is RuleRouteStatus.COMPLETED
    assert route_preparation.preparation is join.preparation
    assert verify_route_preparation_accounting_receipt(
        route_preparation.accounting_receipt,
        route_result=route_preparation.route_result,
        preparation=join.preparation,
    )
    before, after, expected_message, insertion_position = _prepared_transition(join.preparation)

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["provenance"] == "caller_supplied_component_result_untrusted"
    assert payload["rule_route"]["snapshot_sha256"] == join.snapshot_sha256
    assert payload["rule_route"]["caller_reported_exact_read_bytes"] == route_preparation.route_result.exact_read_bytes
    assert payload["route_preparation_accounting_sha256"] == route_preparation.accounting_receipt.accounting_sha256
    assert payload["rule_route"]["observation_included"] is False
    transition = payload["prepared_context_transition"]
    assert transition["preparation_sha256"] == join.preparation.aggregate_sha256
    assert transition["insertion_position"] == insertion_position
    assert transition["inserted_message_sha256"] == join.preparation.prompt_gate.context_message_sha256
    assert transition["before_projection_sha256"] == before.projection.projection_sha256
    assert transition["after_projection_sha256"] == after.projection.projection_sha256
    assert len(transition["receipt_sha256"]) == 64
    assert expected_message["content"][0]["text"] not in result.envelope.payload_json
    assert "sample.py" not in result.envelope.payload_json
    assert "def target" not in result.envelope.payload_json


def test_partial_trace_rejects_route_preparation_without_transition(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
    )

    assert result.status is not PartialTraceStatus.READY
    assert result.envelope is None


def test_partial_trace_rejects_incomplete_transition_arguments(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    before, after, expected_message, _ = _prepared_transition(join.preparation)
    finalized = _finalized(join, join.preparation)

    missing_expected = build_partial_lifecycle_trace(
        join,
        after,
        finalized,
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
    )
    missing_before = build_partial_lifecycle_trace(
        join,
        after,
        finalized,
        route_preparation_result=route_preparation,
        transition_expected_message=expected_message,
    )

    assert missing_expected.status is not PartialTraceStatus.READY
    assert missing_expected.envelope is None
    assert missing_before.status is not PartialTraceStatus.READY
    assert missing_before.envelope is None


def test_partial_trace_rejects_transition_with_wrong_prepared_message(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    before, after, expected_message, _ = _prepared_transition(join.preparation)
    wrong_message = dict(expected_message)
    wrong_message["content"] += " changed"

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=wrong_message,
    )

    assert result.status is not PartialTraceStatus.READY
    assert result.envelope is None


def test_partial_trace_rejects_transition_at_wrong_prepared_position(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    prepared_position = join.preparation.prompt_gate.context_insertion_position
    before, after, expected_message, _ = _prepared_transition(
        join.preparation, insertion_position=0 if prepared_position else 1
    )

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is not PartialTraceStatus.READY
    assert result.envelope is None


def test_partial_trace_rejects_after_projection_changed_after_transition(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    before, after, expected_message, _ = _prepared_transition(join.preparation)
    after_event = json.loads(after.projection.payload_json)
    after_event["messages"].append({"role": "user", "content": [{"type": "text", "text": "unaccounted addition"}]})
    changed_after = project_opencode_context_hook(after_event)
    assert changed_after.status is OpenCodeProjectionStatus.READY

    result = build_partial_lifecycle_trace(
        join,
        changed_after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is not PartialTraceStatus.READY
    assert result.envelope is None


def test_partial_trace_rejects_transition_bound_to_another_preparation(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    other_preparation, _ = _prepare(
        tmp_path / "other",
        sample_source="def target():\n    return 'different prepared evidence with a distinct payload'\n",
    )
    assert other_preparation.aggregate_sha256 != join.preparation.aggregate_sha256
    assert other_preparation.prompt_gate.context_message_sha256 != join.preparation.prompt_gate.context_message_sha256
    before, after, expected_message, _ = _prepared_transition(other_preparation)

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is not PartialTraceStatus.READY
    assert result.envelope is None


def test_partial_trace_rejects_standalone_completed_route_result(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        rule_route_result=route_preparation.route_result,
    )

    assert result.status is PartialTraceStatus.INVALID_ROUTE_RESULT
    assert result.reason == "route_result_invalid_or_snapshot_mismatch"
    assert result.envelope is None


def test_partial_trace_retains_actual_rule_route_abstention(tmp_path):
    preparation, join = _prepare(tmp_path)
    binding = bind_source_root(join.configured_root)
    snapshot = create_snapshot(binding, ["sample.py"])
    route = run_e0_rule_route(
        "Summarize sample.py.", root_binding=binding, snapshot=snapshot
    )
    assert route.status is RuleRouteStatus.ABSTAIN

    result = build_partial_lifecycle_trace(
        join, _projection(), _finalized(join, preparation), rule_route_result=route
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["status"] == "abstain"
    assert payload["rule_route"]["route"] == "none"
    assert payload["rule_route"]["unknown_evidence"]
    assert payload["rule_route"]["caller_reported_exact_read_attempts"] == 0


def test_partial_trace_retains_stale_snapshot_route_abstention(tmp_path):
    preparation, join = _prepare(tmp_path)
    binding = bind_source_root(join.configured_root)
    snapshot = create_snapshot(binding, ["sample.py"])
    (join.configured_root / "sample.py").write_text("def target():\n    return 2\n", encoding="utf-8")
    route = run_e0_rule_route(
        "Read sample.py with a 64 byte limit.", root_binding=binding, snapshot=snapshot
    )
    assert route.status is RuleRouteStatus.ABSTAIN
    assert route.reason == "snapshot_read_changed"

    result = build_partial_lifecycle_trace(
        join, _projection(), _finalized(join, preparation), rule_route_result=route
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["status"] == "abstain"
    assert payload["rule_route"]["reason"] == "snapshot_read_changed"
    assert payload["rule_route"]["unknown_evidence"]


def test_partial_trace_rejects_route_result_for_different_snapshot(tmp_path):
    preparation, join = _prepare(tmp_path)
    (join.configured_root / "other.py").write_text("other\n", encoding="utf-8")
    binding = bind_source_root(join.configured_root)
    snapshot = create_snapshot(binding, ["sample.py", "other.py"])
    route = run_e0_rule_route(
        "Read sample.py with a 64 byte limit.", root_binding=binding, snapshot=snapshot
    )

    result = build_partial_lifecycle_trace(
        join, _projection(), _finalized(join, preparation), rule_route_result=route
    )

    assert result.status is PartialTraceStatus.INVALID_ROUTE_RESULT
    assert result.envelope is None


def test_partial_trace_rejects_same_snapshot_route_with_mismatched_path_and_content(tmp_path):
    _, original_join = _prepare(tmp_path, extra_files=("other.py",))
    join, route_preparation = _route_preparation(
        tmp_path, original_join, snapshot_paths=("sample.py", "other.py")
    )
    binding = bind_source_root(join.configured_root)
    snapshot = create_snapshot(binding, ("sample.py", "other.py"))
    mismatched_route = run_e0_rule_route(
        "Read other.py with a 64 byte limit.",
        root_binding=binding,
        snapshot=snapshot,
    )
    assert mismatched_route.status is RuleRouteStatus.COMPLETED
    assert mismatched_route.snapshot_sha256 == join.snapshot_sha256
    assert tuple(row.path for row in mismatched_route.evidence) == ("other.py",)
    prepared_rows = tuple(row for row in join.preparation.sources if row.status == "ok")
    assert tuple(row.path for row in prepared_rows) == ("sample.py",)
    assert mismatched_route.evidence[0].content_sha256 != prepared_rows[0].content_sha256
    mismatched = replace(route_preparation, route_result=mismatched_route)
    before, after, expected_message, _ = _prepared_transition(join.preparation)

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=mismatched,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is PartialTraceStatus.INVALID_ROUTE_RESULT
    assert result.reason == "route_preparation_join_invalid"
    assert result.envelope is None


def test_partial_trace_rejects_invalid_or_tampered_route_preparation_receipts(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    tampered_receipt = replace(
        route_preparation.accounting_receipt,
        accounting_sha256="0" * 64,
    )
    tampered = replace(route_preparation, accounting_receipt=tampered_receipt)
    before, after, expected_message, _ = _prepared_transition(join.preparation)

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=tampered,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is PartialTraceStatus.INVALID_ROUTE_RESULT
    assert result.reason == "route_preparation_join_invalid"
    assert result.envelope is None


def test_partial_trace_sanitizes_route_owned_preparation_summary(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)
    before, after, expected_message, _ = _prepared_transition(join.preparation)

    result = build_partial_lifecycle_trace(
        join,
        after,
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
        transition_before_projection_result=before,
        transition_expected_message=expected_message,
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["provenance"] == "caller_supplied_component_result_untrusted"
    assert payload["rule_route"]["evidence"][0]["path_ref_sha256"]
    assert payload["rule_route"]["evidence"][0]["content_sha256"]
    assert payload["prepared_context_transition"]["preparation_sha256"] == join.preparation.aggregate_sha256
    assert "sample.py" not in result.envelope.payload_json
    assert "def target" not in result.envelope.payload_json
