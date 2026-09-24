"""Provider-free materialization of compiler-bound context into a hook event.

This offline seam validates the supplied OpenCode event and local preparation.
It does not register a plugin, authenticate a runtime callback, or veto dispatch.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum

from .opencode_context import (
    check_opencode_preparation_admission,
)
from .opencode_hook_projection import (
    MAX_HOOK_MESSAGES,
    MAX_OPENCODE_CONTEXT_HOOK_BYTES,
    OpenCodeProjectionStatus,
    OpenCodePreparedTransitionReceipt,
    OpenCodePreparedTransitionStatus,
    _ProjectionFailure,
    _bounded_canonical_json,
    _copy_json_bounded,
    project_opencode_context_hook,
    validate_opencode_preparation_context_transition,
    verify_opencode_prepared_transition_receipt,
)
from .prompt_compiler import PromptGateReceipt, PromptGateStatus


class PreparedContextStatus(str, Enum):
    READY = "ready"
    INVALID_EVENT = "invalid_event"
    ADMISSION_REJECTED = "admission_rejected"
    CONTEXT_BINDING_MISSING = "context_binding_missing"
    CONTEXT_BINDING_INVALID = "context_binding_invalid"
    CONTEXT_BINDING_MISMATCH = "context_binding_mismatch"
    MESSAGE_ALREADY_PRESENT = "message_already_present"
    INSERTION_POSITION_INVALID = "insertion_position_invalid"
    OUTPUT_INVALID = "output_invalid"


@dataclass(frozen=True)
class PreparedContextResult:
    """Bounded result; failure metadata contains no prepared context text."""

    status: PreparedContextStatus
    event: dict[str, object] | None = field(repr=False, compare=False)
    reason: str
    transition_receipt: OpenCodePreparedTransitionReceipt | None = None


def materialize_opencode_prepared_context(
    join: object,
    event: object,
) -> PreparedContextResult:
    """Insert the exact prompt-gate context message into one pinned hook event.

    The READY local admission predicate binds ``event.sessionID`` to the
    preparation join. The message comes only from the compiler's immutable
    ephemeral bridge and is verified against the gate receipt before insertion.
    No value is recovered from or parsed out of ``preparation.prompt``.
    """
    projected = project_opencode_context_hook(event)
    if projected.status is not OpenCodeProjectionStatus.READY or projected.projection is None:
        return PreparedContextResult(PreparedContextStatus.INVALID_EVENT, None, "event_invalid")

    admission = check_opencode_preparation_admission(
        projected.projection.session_id, join  # type: ignore[arg-type]
    )
    if admission.join is None:
        return PreparedContextResult(
            PreparedContextStatus.ADMISSION_REJECTED, None, admission.status.value
        )

    preparation = admission.join.preparation
    gate = preparation.prompt_gate
    if type(gate) is not PromptGateReceipt or gate.status is not PromptGateStatus.READY:
        return PreparedContextResult(
            PreparedContextStatus.ADMISSION_REJECTED, None, "prompt_gate_not_ready"
        )
    bound_digest = gate.context_message_sha256
    position = gate.context_insertion_position
    if preparation.context_message_json is None and bound_digest is None and position is None:
        return PreparedContextResult(
            PreparedContextStatus.CONTEXT_BINDING_MISSING, None, "context_binding_missing"
        )
    if preparation.context_message_json is None:
        return PreparedContextResult(
            PreparedContextStatus.CONTEXT_BINDING_MISSING, None, "context_message_missing"
        )
    if (
        type(bound_digest) is not str
        or len(bound_digest) != 64
        or any(char not in "0123456789abcdef" for char in bound_digest)
        or type(position) is not int
        or type(preparation.context_message_json) is not str
        or len(preparation.context_message_json) > MAX_OPENCODE_CONTEXT_HOOK_BYTES
    ):
        return PreparedContextResult(
            PreparedContextStatus.CONTEXT_BINDING_INVALID, None, "context_binding_invalid"
        )

    try:
        raw_message = json.loads(preparation.context_message_json)
        message = _copy_json_bounded(raw_message)
        if (
            type(message) is not dict
            or message.get("role") != "user"
            or type(message.get("content")) is not list
            or len(message["content"]) != 1
            or type(message["content"][0]) is not dict
            or message["content"][0].get("type") != "text"
            or type(message["content"][0].get("text")) is not str
        ):
            raise _ProjectionFailure("context_message_shape_invalid")
        message_bytes = _bounded_canonical_json(message, MAX_OPENCODE_CONTEXT_HOOK_BYTES)
    except (_ProjectionFailure, TypeError, ValueError, OverflowError, RecursionError):
        return PreparedContextResult(
            PreparedContextStatus.CONTEXT_BINDING_INVALID, None, "context_binding_invalid"
        )
    if hashlib.sha256(message_bytes).hexdigest() != bound_digest:
        return PreparedContextResult(
            PreparedContextStatus.CONTEXT_BINDING_MISMATCH, None, "context_binding_mismatch"
        )

    try:
        payload = json.loads(projected.projection.payload_json)
    except (TypeError, ValueError, RecursionError):
        return PreparedContextResult(PreparedContextStatus.INVALID_EVENT, None, "event_invalid")
    messages = payload.get("messages")
    if type(messages) is not list:
        return PreparedContextResult(PreparedContextStatus.INVALID_EVENT, None, "event_invalid")
    try:
        for existing in messages:
            if _bounded_canonical_json(existing, MAX_OPENCODE_CONTEXT_HOOK_BYTES) == message_bytes:
                return PreparedContextResult(
                    PreparedContextStatus.MESSAGE_ALREADY_PRESENT, None, "message_already_present"
                )
    except (TypeError, ValueError, OverflowError, RecursionError):
        return PreparedContextResult(PreparedContextStatus.INVALID_EVENT, None, "event_invalid")

    if (
        type(position) is not int
        or not 0 <= position <= len(messages)
        or len(messages) >= MAX_HOOK_MESSAGES
    ):
        return PreparedContextResult(
            PreparedContextStatus.INSERTION_POSITION_INVALID, None, "insertion_position_invalid"
        )

    materialized = list(messages)
    materialized.insert(position, message)
    payload["messages"] = materialized
    output_projection = project_opencode_context_hook(payload)
    if (
        output_projection.status is not OpenCodeProjectionStatus.READY
        or output_projection.projection is None
    ):
        return PreparedContextResult(
            PreparedContextStatus.OUTPUT_INVALID, None, "materialized_event_invalid"
        )
    transition = validate_opencode_preparation_context_transition(
        preparation,
        projected.projection,
        output_projection.projection,
        expected_message=message,
    )
    if (
        transition.status is not OpenCodePreparedTransitionStatus.READY
        or transition.receipt is None
        or not verify_opencode_prepared_transition_receipt(transition.receipt)
    ):
        return PreparedContextResult(
            PreparedContextStatus.OUTPUT_INVALID, None, "prepared_transition_invalid"
        )
    return PreparedContextResult(
        PreparedContextStatus.READY, payload, "ready", transition.receipt
    )


__all__ = [
    "PreparedContextResult",
    "PreparedContextStatus",
    "materialize_opencode_prepared_context",
]
