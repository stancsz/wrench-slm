from __future__ import annotations

import json
from dataclasses import replace

from wrench_harness.artifact_store import ArtifactStore
from wrench_harness.e0_lifecycle_accounting import (
    ENVELOPE_SCHEMA,
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
from wrench_harness.opencode_hook_projection import (
    OpenCodeProjectionResult,
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)
from wrench_harness.outcome_receipt import ReceiptStatus, build_outcome_receipt
from wrench_harness.snapshot import bind_source_root, create_snapshot


def _prepare(tmp_path, *, extra_files=()):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "sample.py").write_text("def target():\n    return 1\n", encoding="utf-8")
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
        base_messages=({"role": "system", "content": "Use evidence."},),
        context_position=1,
        serializer=lambda messages: json.dumps(messages, sort_keys=True, separators=(",", ":")),
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
        "messages": [{"role": "user", "content": "synthetic fixture"}],
        "options": {},
        "agent": "build",
        "tools": {},
    }
    return project_opencode_context_hook(event)


def _finalized(join, preparation):
    result = finalize_opencode_preparation_outcome(join, _postrun(join.session_id))
    assert result.receipt is not None
    return result.receipt


def _route_preparation(tmp_path, join, *, prompt="Read sample.py with a 64 byte limit.", snapshot_paths=("sample.py",)):
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
        base_messages=({"role": "system", "content": "Use evidence."},),
        context_position=1,
        serializer=lambda messages: json.dumps(list(messages), sort_keys=True, separators=(",", ":")),
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

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["provenance"] == "caller_supplied_component_result_untrusted"
    assert payload["rule_route"]["snapshot_sha256"] == join.snapshot_sha256
    assert payload["rule_route"]["caller_reported_exact_read_bytes"] == route_preparation.route_result.exact_read_bytes
    assert payload["route_preparation_accounting_sha256"] == route_preparation.accounting_receipt.accounting_sha256
    assert payload["rule_route"]["observation_included"] is False
    assert "sample.py" not in result.envelope.payload_json
    assert "def target" not in result.envelope.payload_json


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

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        route_preparation_result=mismatched,
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

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        route_preparation_result=tampered,
    )

    assert result.status is PartialTraceStatus.INVALID_ROUTE_RESULT
    assert result.reason == "route_preparation_join_invalid"
    assert result.envelope is None


def test_partial_trace_sanitizes_route_owned_preparation_summary(tmp_path):
    _, original_join = _prepare(tmp_path)
    join, route_preparation = _route_preparation(tmp_path, original_join)

    result = build_partial_lifecycle_trace(
        join,
        _projection(),
        _finalized(join, join.preparation),
        route_preparation_result=route_preparation,
    )

    assert result.status is PartialTraceStatus.READY
    payload = json.loads(result.envelope.payload_json)
    assert payload["rule_route"]["provenance"] == "caller_supplied_component_result_untrusted"
    assert payload["rule_route"]["evidence"][0]["path_ref_sha256"]
    assert payload["rule_route"]["evidence"][0]["content_sha256"]
    assert "sample.py" not in result.envelope.payload_json
    assert "def target" not in result.envelope.payload_json
