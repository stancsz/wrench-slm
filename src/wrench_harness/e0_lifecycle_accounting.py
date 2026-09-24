"""Reference-only partial trace for offline E0 preparation and hook evidence.

This binds local record identities structurally. It does not authenticate the
caller, measure client/provider activity, or establish task identity or truth.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum

from .e0_context_pipeline import (
    PreparationResult,
    PreparationStatus,
    verify_preparation_accounting_receipt,
)
from .e0_rule_route import RuleRouteEvidence, RuleRouteResult, RuleRouteStatus
from .e0_route_preparation import (
    RoutePreparationResult,
    RoutePreparationStatus,
    verify_route_preparation_accounting_receipt,
)
from .opencode_context import OpenCodePreparationJoin
from .opencode_hook_projection import (
    MAX_OPENCODE_CONTEXT_HOOK_BYTES,
    OPENCODE_CONTEXT_HOOK_VERSION,
    PROJECTION_SCHEMA,
    OpenCodeContextHookProjection,
    OpenCodeProjectionResult,
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)
from .outcome_receipt import (
    OutcomeReceipt,
    ReceiptResult,
    ReceiptStatus,
    validate_outcome_receipt,
)


ENVELOPE_SCHEMA = "wrench.e0.partial-lifecycle-trace.v3"
MAX_ENVELOPE_BYTES = 16 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ROUTE_ACTIONS = frozenset({"read_file", "read_lines", "literal_search"})
_ROUTE_REASONS = frozenset({
    "invalid_input", "snapshot_manifest_invalid", "ambiguous_or_unsupported_request",
    "read_intent_denied_or_constrained", "rule_abstained", "proposal_schema_invalid",
    "action_not_allowlisted", "read_file_proposal_shape_invalid", "source_not_in_snapshot",
    "file_size_limit_invalid", "file_size_limit", "non_text_source",
    "read_lines_proposal_shape_invalid", "invalid_line_bounds", "line_end_out_of_range",
    "literal_search_proposal_shape_invalid", "search_root_invalid", "invalid_literal",
    "invalid_match_limit", "search_scope_has_no_snapshot_sources", "route_file_limit_exceeded",
    "source_size_limit_exceeded", "route_byte_limit_exceeded", "match_limit_reached",
    "search_result_line_limit_exceeded", "snapshot_read_unknown_snapshot",
    "snapshot_read_unknown_source", "snapshot_read_missing", "snapshot_read_changed",
    "snapshot_read_unsafe",
})
_ROUTE_EVIDENCE_STATUSES = frozenset({
    "ok", "unknown", "unknown_snapshot", "unknown_source", "missing", "changed",
    "unsafe", "non_text", "result_line_too_long", "match_limit_reached",
})
_UNAVAILABLE_DIMENSIONS = (
    "opencode_dispatch_and_veto",
    "provider_final_serialization_and_tokenizer_parity",
    "provider_requests_responses_usage_and_cost",
    "tool_execution_and_transmitted_tool_schemas",
    "auxiliary_title_calls_retries_fallbacks_and_rebuilds",
    "runtime_hook_event_provenance_and_atomic_capture",
    "verifier_independence_and_task_truth",
    "runtime_cpu_memory_energy_cache_and_page_faults",
    "cancellation_and_timeouts",
    "measurement_authenticity_and_task_consent_provenance",
)


class PartialTraceStatus(str, Enum):
    READY = "ready"
    INVALID_INPUT = "invalid_input"
    INVALID_PROJECTION = "invalid_projection"
    INVALID_RECEIPT = "invalid_receipt"
    INVALID_ROUTE_RESULT = "invalid_route_result"
    JOIN_MISMATCH = "join_mismatch"


@dataclass(frozen=True)
class PartialTraceEnvelope:
    """Bounded references and dimensions; never includes hook or prompt text."""

    schema: str
    payload_json: str
    sha256: str


@dataclass(frozen=True)
class PartialTraceResult:
    status: PartialTraceStatus
    envelope: PartialTraceEnvelope | None
    reason: str


def build_partial_lifecycle_trace(
    join: OpenCodePreparationJoin,
    projection_result: OpenCodeProjectionResult,
    finalized_receipt: OutcomeReceipt,
    *,
    rule_route_result: RuleRouteResult | None = None,
    route_preparation_result: RoutePreparationResult | None = None,
) -> PartialTraceResult:
    """Bind a READY hook projection to a valid outcome and preparation join.

    ``run_id`` is copied as caller correlation metadata only. Session equality
    is not a unique task/run identity, and all input objects remain caller
    supplied and unauthenticated.
    """
    if type(join) is not OpenCodePreparationJoin:
        return _failure(PartialTraceStatus.INVALID_INPUT, "join_type_invalid")
    preparation = join.preparation
    if (
        type(preparation) is not PreparationResult
        or preparation.status is not PreparationStatus.READY
    ):
        return _failure(PartialTraceStatus.INVALID_INPUT, "preparation_type_invalid")
    if (
        type(join.session_id) is not str
        or not join.session_id
        or type(join.snapshot_sha256) is not str
        or not _DIGEST.fullmatch(join.snapshot_sha256)
        or type(preparation.aggregate_sha256) is not str
        or not _DIGEST.fullmatch(preparation.aggregate_sha256)
    ):
        return _failure(PartialTraceStatus.INVALID_INPUT, "join_identity_invalid")

    if (
        type(projection_result) is not OpenCodeProjectionResult
        or projection_result.status is not OpenCodeProjectionStatus.READY
        or type(projection_result.projection) is not OpenCodeContextHookProjection
    ):
        return _failure(PartialTraceStatus.INVALID_PROJECTION, "projection_not_ready")
    projection = projection_result.projection
    if not _projection_is_self_consistent(projection):
        return _failure(PartialTraceStatus.INVALID_PROJECTION, "projection_integrity_invalid")

    if type(finalized_receipt) is not OutcomeReceipt:
        return _failure(PartialTraceStatus.INVALID_RECEIPT, "receipt_type_invalid")
    checked = validate_outcome_receipt(finalized_receipt)
    if checked.status is not ReceiptStatus.VALID or checked.receipt is None:
        return _failure(PartialTraceStatus.INVALID_RECEIPT, "receipt_not_valid")
    try:
        payload = json.loads(checked.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        return _failure(PartialTraceStatus.INVALID_RECEIPT, "receipt_payload_invalid")

    accounting = preparation.accounting_receipt
    if (
        accounting is None
        or not verify_preparation_accounting_receipt(
            accounting, aggregate_sha256=preparation.aggregate_sha256
        )
    ):
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "preparation_accounting_invalid")

    preparation_result = preparation.outcome_receipt
    if (
        type(preparation_result) is not ReceiptResult
        or preparation_result.status is not ReceiptStatus.INCOMPLETE
        or preparation_result.receipt is None
    ):
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "preparation_receipt_invalid")
    checked_preparation = validate_outcome_receipt(preparation_result.receipt)
    if checked_preparation.status is not ReceiptStatus.INCOMPLETE or checked_preparation.receipt is None:
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "preparation_receipt_invalid")
    try:
        preparation_payload = json.loads(checked_preparation.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "preparation_receipt_payload_invalid")
    if (
        preparation_payload.get("schema") != "wrench.e0.outcome-receipt.v1"
        or preparation_payload.get("context_receipt_sha256") != preparation.aggregate_sha256
        or preparation_payload.get("snapshot_sha256") != join.snapshot_sha256
        or preparation_payload.get("actual_route") != "none"
        or preparation_payload.get("outcome", {}).get("status") != "unknown"
    ):
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "preparation_identity_mismatch")

    expected = {
        "session_id": join.session_id,
        "snapshot_sha256": join.snapshot_sha256,
        "context_receipt_sha256": preparation.aggregate_sha256,
        "preparation_accounting_sha256": accounting.accounting_sha256,
    }
    if any(payload.get(name) != value for name, value in expected.items()):
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "receipt_join_mismatch")
    if projection.session_id != join.session_id:
        return _failure(PartialTraceStatus.JOIN_MISMATCH, "projection_session_mismatch")

    route_summary = None
    route_preparation_accounting_sha256 = None
    if rule_route_result is not None and route_preparation_result is not None:
        return _failure(PartialTraceStatus.INVALID_ROUTE_RESULT, "route_inputs_ambiguous")
    if route_preparation_result is not None:
        if (
            type(route_preparation_result) is not RoutePreparationResult
            or route_preparation_result.status is not RoutePreparationStatus.JOINED
            or type(route_preparation_result.route_result) is not RuleRouteResult
            or type(route_preparation_result.preparation) is not PreparationResult
            or route_preparation_result.preparation is not preparation
            or route_preparation_result.accounting_receipt is None
            or not verify_route_preparation_accounting_receipt(
                route_preparation_result.accounting_receipt,
                route_result=route_preparation_result.route_result,
                preparation=route_preparation_result.preparation,
            )
        ):
            return _failure(
                PartialTraceStatus.INVALID_ROUTE_RESULT,
                "route_preparation_join_invalid",
            )
        route_summary = _route_summary(
            route_preparation_result.route_result, join.snapshot_sha256
        )
        if route_summary is None:
            return _failure(
                PartialTraceStatus.INVALID_ROUTE_RESULT,
                "route_preparation_snapshot_or_evidence_invalid",
            )
        route_preparation_accounting_sha256 = (
            route_preparation_result.accounting_receipt.accounting_sha256
        )
    elif rule_route_result is not None:
        if rule_route_result.status is RuleRouteStatus.COMPLETED:
            return _failure(PartialTraceStatus.INVALID_ROUTE_RESULT, "route_result_invalid_or_snapshot_mismatch")
        route_summary = _route_summary(rule_route_result, join.snapshot_sha256)
        if route_summary is None:
            return _failure(PartialTraceStatus.INVALID_ROUTE_RESULT, "route_result_invalid_or_snapshot_mismatch")

    run_id = payload.get("run_id")
    task_id = payload.get("task_id")
    if not _bounded_opaque_id(run_id) or not _bounded_opaque_id(task_id):
        return _failure(PartialTraceStatus.INVALID_RECEIPT, "receipt_correlation_id_invalid")

    envelope_payload = {
        "schema": ENVELOPE_SCHEMA,
        "provenance": "caller_supplied_structural_join_untrusted",
        "run_id": {"value": run_id, "meaning": "caller_correlation_only"},
        "task_id_ref": task_id,
        "session_id_ref": join.session_id,
        "snapshot_sha256": join.snapshot_sha256,
        "preparation_sha256": preparation.aggregate_sha256,
        "preparation_accounting_sha256": accounting.accounting_sha256,
        "projection_sha256": projection.projection_sha256,
        "projection_schema": projection.projection_schema,
        "opencode_context_hook_version": projection.opencode_context_hook_version,
        "projection_serialized_bytes": projection.serialized_bytes,
        "outcome_receipt_sha256": checked.receipt.sha256,
        "rule_route": route_summary,
        "route_preparation_accounting_sha256": route_preparation_accounting_sha256,
        "measured_dimensions": [
            "preparation_facade_counters_by_accounting_receipt_reference",
            "locally_serialized_projection_input_bytes",
        ],
        "unavailable_dimensions": list(_UNAVAILABLE_DIMENSIONS),
    }
    try:
        raw = json.dumps(
            envelope_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return _failure(PartialTraceStatus.INVALID_INPUT, "envelope_serialization_failed")
    if len(raw) > MAX_ENVELOPE_BYTES:
        return _failure(PartialTraceStatus.INVALID_INPUT, "envelope_size_limit_exceeded")
    envelope = PartialTraceEnvelope(
        schema=ENVELOPE_SCHEMA,
        payload_json=raw.decode("utf-8"),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    return PartialTraceResult(PartialTraceStatus.READY, envelope, "ready")


def _route_summary(result: RuleRouteResult, expected_snapshot_sha256: str) -> dict[str, object] | None:
    """Return a bounded, content-free route reference for an untrusted join."""
    if (
        type(result) is not RuleRouteResult
        or type(result.status) is not RuleRouteStatus
        or type(result.route) is not str
        or result.route != "none"
        or type(result.snapshot_sha256) is not str
        or result.snapshot_sha256 != expected_snapshot_sha256
        or type(result.action) not in (str, type(None))
        or (result.action is not None and len(result.action) > 64)
        or type(result.exact_read_attempts) is not int
        or type(result.exact_read_successes) is not int
        or type(result.exact_read_bytes) is not int
        or not 0 <= result.exact_read_successes <= result.exact_read_attempts <= 16
        or not 0 <= result.exact_read_bytes <= 512 * 1024
        or type(result.reason) not in (str, type(None))
        or (result.reason is not None and len(result.reason) > 128)
        or type(result.evidence) is not tuple
        or type(result.unknown_evidence) is not tuple
        or len(result.evidence) > 16
        or len(result.unknown_evidence) > 16
    ):
        return None
    evidence = []
    unknown = []
    for source, target in ((result.evidence, evidence), (result.unknown_evidence, unknown)):
        for item in source:
            if (
                type(item) is not RuleRouteEvidence
                or type(item.path) not in (str, type(None))
                or (item.path is not None and len(item.path) > 1024)
                or type(item.status) is not str
                or len(item.status) > 64
                or type(item.content_sha256) not in (str, type(None))
                or (item.content_sha256 is not None and not _DIGEST.fullmatch(item.content_sha256))
                or type(item.size_bytes) not in (int, type(None))
                or (item.size_bytes is not None and not 0 <= item.size_bytes <= 256 * 1024)
            ):
                return None
            try:
                path_ref_sha256 = (
                    hashlib.sha256(item.path.encode("utf-8")).hexdigest()
                    if item.path is not None else None
                )
            except UnicodeError:
                return None
            target.append({
                "path_ref_sha256": path_ref_sha256,
                "status": item.status if item.status in _ROUTE_EVIDENCE_STATUSES else "other",
                "content_sha256": item.content_sha256,
                "size_bytes": item.size_bytes,
            })
    summary = {
        "provenance": "caller_supplied_component_result_untrusted",
        "snapshot_sha256": result.snapshot_sha256,
        "status": result.status.value,
        "route": result.route,
        "action": result.action if result.action in _ROUTE_ACTIONS else ("other" if result.action is not None else None),
        "reason": result.reason if result.reason in _ROUTE_REASONS else ("other" if result.reason is not None else None),
        "caller_reported_exact_read_attempts": result.exact_read_attempts,
        "caller_reported_exact_read_successes": result.exact_read_successes,
        "caller_reported_exact_read_bytes": result.exact_read_bytes,
        "evidence": evidence,
        "unknown_evidence": unknown,
        "observation_included": False,
    }
    raw = json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    summary["summary_sha256"] = hashlib.sha256(raw).hexdigest()
    return summary


def _projection_is_self_consistent(projection: OpenCodeContextHookProjection) -> bool:
    if (
        projection.projection_schema != PROJECTION_SCHEMA
        or projection.opencode_context_hook_version != OPENCODE_CONTEXT_HOOK_VERSION
        or type(projection.payload_json) is not str
        or len(projection.payload_json) > MAX_OPENCODE_CONTEXT_HOOK_BYTES
        or type(projection.serialized_bytes) is not int
        or not 0 <= projection.serialized_bytes <= MAX_OPENCODE_CONTEXT_HOOK_BYTES
        or type(projection.projection_sha256) is not str
        or not _DIGEST.fullmatch(projection.projection_sha256)
    ):
        return False
    try:
        encoded = projection.payload_json.encode("utf-8")
        if len(encoded) != projection.serialized_bytes:
            return False
        event = json.loads(projection.payload_json)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return False
    result = project_opencode_context_hook(event)
    return (
        result.status is OpenCodeProjectionStatus.READY
        and result.projection is not None
        and result.projection.session_id == projection.session_id
        and result.projection.agent_id == projection.agent_id
        and result.projection.provider_id == projection.provider_id
        and result.projection.model_id == projection.model_id
        and result.projection.model_variant == projection.model_variant
        and result.projection.projection_sha256 == projection.projection_sha256
        and result.projection.serialized_bytes == projection.serialized_bytes
    )


def _bounded_opaque_id(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= 128
        and all(char.isascii() and (char.isalnum() or char in "._:-") for char in value)
    )


def _failure(status: PartialTraceStatus, reason: str) -> PartialTraceResult:
    return PartialTraceResult(status, None, reason)


__all__ = [
    "ENVELOPE_SCHEMA",
    "MAX_ENVELOPE_BYTES",
    "PartialTraceEnvelope",
    "PartialTraceResult",
    "PartialTraceStatus",
    "build_partial_lifecycle_trace",
]
