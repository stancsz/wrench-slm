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


ENVELOPE_SCHEMA = "wrench.e0.partial-lifecycle-trace.v1"
MAX_ENVELOPE_BYTES = 16 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
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
