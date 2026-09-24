"""Bounded, provider-free projection of the pinned OpenCode context hook."""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from .prompt_compiler import (
    MAX_INPUT_DEPTH,
    MAX_INPUT_NODES,
    PromptGateReceipt,
    PromptGateStatus,
    _bounded_canonical_json,
)


MAX_OPENCODE_CONTEXT_HOOK_BYTES = 1024 * 1024
MAX_HOOK_MESSAGES = 128
MAX_HOOK_SYSTEM_PARTS = 128
MAX_HOOK_TOOLS = 256
OPENCODE_CONTEXT_HOOK_VERSION = "2.0.15"
PROJECTION_SCHEMA = "wrench.opencode.context-hook-projection.v1"
CONTEXT_HOOK_OBSERVATION_SCHEMA = "wrench.opencode.context-hook-observation.v1"
PREPARED_TRANSITION_RECEIPT_SCHEMA = "wrench.opencode.prepared-context-transition-receipt.v1"
MAX_PREPARED_TRANSITION_RECEIPT_BYTES = 4096
_CONTEXT_FIELDS = frozenset({
    "sessionID", "agent", "model", "system", "messages", "tools", "options",
})


class OpenCodeProjectionStatus(str, Enum):
    READY = "ready"
    INVALID_INPUT = "invalid_input"
    INVALID_FIELDS = "invalid_fields"
    INVALID_SHAPE = "invalid_shape"
    INPUT_LIMIT_EXCEEDED = "input_limit_exceeded"


class OpenCodeTransitionStatus(str, Enum):
    READY = "ready"
    INVALID_INPUT = "invalid_input"
    INVALID_PROJECTION = "invalid_projection"
    SESSION_MISMATCH = "session_mismatch"
    PROTECTED_CONTEXT_CHANGED = "protected_context_changed"
    MESSAGE_SEQUENCE_MISMATCH = "message_sequence_mismatch"
    INSERTION_POSITION_INVALID = "insertion_position_invalid"


class OpenCodePreparedTransitionStatus(str, Enum):
    READY = "ready"
    INVALID_PREPARATION = "invalid_preparation"
    INVALID_PROMPT_GATE = "invalid_prompt_gate"
    INSERTION_BINDING_MISSING = "insertion_binding_missing"
    INSERTION_BINDING_INVALID = "insertion_binding_invalid"
    INSERTION_BINDING_MISMATCH = "insertion_binding_mismatch"
    TRANSITION_REJECTED = "transition_rejected"


@dataclass(frozen=True)
class OpenCodeContextHookProjection:
    """Bounded copy of every semantic field exposed by SessionHooks.context.

    ``payload_json`` preserves array order and object insertion order from the
    input snapshot. ``projection_sha256`` hashes the canonical JSON projection
    so object-key ordering does not change semantic identity. This is not the
    provider's final request serialization or a prompt-token measurement.
    """

    session_id: str
    agent_id: str
    provider_id: str
    model_id: str
    model_variant: str | None
    projection_schema: str
    opencode_context_hook_version: str
    payload_json: str
    projection_sha256: str
    serialized_bytes: int


@dataclass(frozen=True)
class OpenCodeProjectionResult:
    status: OpenCodeProjectionStatus
    projection: OpenCodeContextHookProjection | None
    reason: str


@dataclass(frozen=True)
class OpenCodeContextTransitionReceipt:
    """Content-free local receipt for one validated context-message insertion."""

    session_id: str
    opencode_context_hook_version: str
    projection_schema: str
    before_projection_sha256: str
    after_projection_sha256: str
    inserted_message_sha256: str
    insertion_position: int


@dataclass(frozen=True)
class OpenCodeTransitionResult:
    status: OpenCodeTransitionStatus
    receipt: OpenCodeContextTransitionReceipt | None
    reason: str


@dataclass(frozen=True)
class OpenCodePreparedTransitionReceipt:
    """Content-free receipt joining preparation identity to a hook transition."""

    preparation_sha256: str
    transition: OpenCodeContextTransitionReceipt
    receipt_sha256: str
    schema: str = PREPARED_TRANSITION_RECEIPT_SCHEMA


@dataclass(frozen=True)
class OpenCodePreparedTransitionResult:
    status: OpenCodePreparedTransitionStatus
    receipt: OpenCodePreparedTransitionReceipt | None
    reason: str


@dataclass(frozen=True)
class OpenCodeContextHookObservation:
    """Content-free local counters for observed callback executions."""

    schema: str
    opencode_context_hook_version: str
    invocation_count: int
    completed_count: int
    returned_count: int
    error_count: int
    timing_error_count: int
    elapsed_ns: int
    calls: tuple["OpenCodeContextHookCall", ...]
    calls_capped: bool
    saturated: bool


@dataclass(frozen=True)
class OpenCodeContextHookCall:
    """One bounded, content-free callback completion row."""

    invocation_index: int
    elapsed_ns: int | None
    result: str


_MAX_OBSERVATION_COUNT = (1 << 31) - 1
_MAX_OBSERVATION_ELAPSED_NS = (1 << 63) - 1
MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS = 128


class OpenCodeContextHookObserver:
    """Measure callback execution locally without retaining callback content.

    The wrapper is async to match OpenCode's awaited Promise callback boundary.
    Synchronous callbacks are accepted too. Exceptions propagate unchanged;
    only the bounded result category is stored in the observation.
    """

    def __init__(
        self,
        callback: Callable[..., Any],
        *,
        monotonic_ns: Callable[[], Any] = time.monotonic_ns,
    ) -> None:
        if not callable(callback) or not callable(monotonic_ns):
            raise TypeError("callback_and_clock_must_be_callable")
        self._callback = callback
        self._monotonic_ns = monotonic_ns
        self._lock = threading.Lock()
        self._invocation_count = 0
        self._completed_count = 0
        self._returned_count = 0
        self._error_count = 0
        self._timing_error_count = 0
        self._elapsed_ns = 0
        self._calls: list[OpenCodeContextHookCall] = []
        self._calls_capped = False
        self._saturated = False

    @property
    def observation(self) -> OpenCodeContextHookObservation | None:
        """Return an immutable summary, or ``None`` before any invocation."""
        with self._lock:
            if self._invocation_count == 0:
                return None
            return OpenCodeContextHookObservation(
                schema=CONTEXT_HOOK_OBSERVATION_SCHEMA,
                opencode_context_hook_version=OPENCODE_CONTEXT_HOOK_VERSION,
                invocation_count=self._invocation_count,
                completed_count=self._completed_count,
                returned_count=self._returned_count,
                error_count=self._error_count,
                timing_error_count=self._timing_error_count,
                elapsed_ns=self._elapsed_ns,
                calls=tuple(self._calls),
                calls_capped=self._calls_capped,
                saturated=self._saturated,
            )

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            self._invocation_count, did_saturate = _saturating_add(
                self._invocation_count, 1, _MAX_OBSERVATION_COUNT
            )
            self._saturated |= did_saturate
            invocation_index = self._invocation_count

        started_ns, timing_errors = _safe_monotonic_ns(self._monotonic_ns)
        result = "returned"
        try:
            callback_result = self._callback(*args, **kwargs)
            if inspect.isawaitable(callback_result):
                callback_result = await callback_result
            return callback_result
        except BaseException:
            result = "error"
            raise
        finally:
            elapsed: int | None = None
            call_elapsed_saturated = False
            if started_ns is not None:
                ended_ns, end_timing_errors = _safe_monotonic_ns(self._monotonic_ns)
                timing_errors += end_timing_errors
                if ended_ns is not None:
                    if ended_ns < started_ns:
                        timing_errors += 1
                    else:
                        raw_elapsed = ended_ns - started_ns
                        elapsed = min(raw_elapsed, _MAX_OBSERVATION_ELAPSED_NS)
                        call_elapsed_saturated = raw_elapsed > _MAX_OBSERVATION_ELAPSED_NS
            with self._lock:
                self._completed_count, completed_saturated = _saturating_add(
                    self._completed_count, 1, _MAX_OBSERVATION_COUNT
                )
                if result == "returned":
                    self._returned_count, returned_saturated = _saturating_add(
                        self._returned_count, 1, _MAX_OBSERVATION_COUNT
                    )
                    error_saturated = False
                else:
                    self._error_count, error_saturated = _saturating_add(
                        self._error_count, 1, _MAX_OBSERVATION_COUNT
                    )
                    returned_saturated = False
                aggregate_elapsed_saturated = False
                if elapsed is not None:
                    self._elapsed_ns, aggregate_elapsed_saturated = _saturating_add(
                        self._elapsed_ns, elapsed, _MAX_OBSERVATION_ELAPSED_NS
                    )
                self._timing_error_count, timing_saturated = _saturating_add(
                    self._timing_error_count, timing_errors, _MAX_OBSERVATION_COUNT
                )
                if invocation_index <= MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS:
                    self._calls.append(OpenCodeContextHookCall(
                        invocation_index=invocation_index,
                        elapsed_ns=elapsed,
                        result=result,
                    ))
                    self._calls.sort(key=lambda call: call.invocation_index)
                else:
                    self._calls_capped = True
                self._saturated |= (
                    completed_saturated or returned_saturated
                    or error_saturated or call_elapsed_saturated
                    or aggregate_elapsed_saturated or timing_saturated
                )


def _safe_monotonic_ns(clock: Callable[[], Any]) -> tuple[int | None, int]:
    try:
        value = clock()
    except Exception:
        return None, 1
    if type(value) is not int:
        return None, 1
    return value, 0


def _saturating_add(current: int, increment: int, maximum: int) -> tuple[int, bool]:
    total = current + increment
    return (maximum, True) if total > maximum else (total, False)


class _ProjectionFailure(Exception):
    def __init__(self, reason: str, *, limit: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.limit = limit


def _valid_text(value: object, *, max_chars: int = 256) -> bool:
    if type(value) is not str or not value or len(value) > max_chars:
        return False
    return not any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)


def _copy_json_bounded(value: object) -> object:
    nodes = 0
    string_bytes = 0
    active: set[int] = set()

    def copy(item: object, depth: int) -> object:
        nonlocal nodes, string_bytes
        nodes += 1
        if nodes > MAX_INPUT_NODES or depth > MAX_INPUT_DEPTH:
            raise _ProjectionFailure("input_shape_limit_exceeded", limit=True)
        if item is None or type(item) is bool:
            return item
        if type(item) is int:
            if item.bit_length() > 256:
                raise _ProjectionFailure("input_integer_limit_exceeded", limit=True)
            return item
        if type(item) is float:
            if not math.isfinite(item):
                raise _ProjectionFailure("nonfinite_number")
            return item
        if type(item) is str:
            # Every Unicode code point needs at least one UTF-8 byte. Reject
            # from that lower bound before allocating an encoded copy of an
            # attacker-sized string. Accepted strings are therefore at most
            # 1 MiB of characters before the exact byte count is checked.
            if len(item) > MAX_OPENCODE_CONTEXT_HOOK_BYTES - string_bytes:
                raise _ProjectionFailure("input_bytes_limit_exceeded", limit=True)
            try:
                encoded_size = len(item.encode("utf-8"))
            except UnicodeEncodeError as exc:
                raise _ProjectionFailure("invalid_unicode") from exc
            string_bytes += encoded_size
            if string_bytes > MAX_OPENCODE_CONTEXT_HOOK_BYTES:
                raise _ProjectionFailure("input_bytes_limit_exceeded", limit=True)
            return item
        if type(item) not in (dict, list):
            raise _ProjectionFailure("non_json_value")

        identity = id(item)
        if identity in active:
            raise _ProjectionFailure("cyclic_input")
        minimum_nodes = 2 * len(item) if type(item) is dict else len(item)
        if minimum_nodes > MAX_INPUT_NODES - nodes:
            raise _ProjectionFailure("input_shape_limit_exceeded", limit=True)
        active.add(identity)
        try:
            if type(item) is dict:
                try:
                    entries = tuple(item.items())
                except RuntimeError as exc:
                    raise _ProjectionFailure("mapping_changed_during_snapshot") from exc
                if len(entries) != len(item):
                    raise _ProjectionFailure("mapping_changed_during_snapshot")
                copied: dict[str, object] = {}
                for key, nested in entries:
                    if type(key) is not str:
                        raise _ProjectionFailure("invalid_mapping_key")
                    copied_key = copy(key, depth + 1)
                    copied[copied_key] = copy(nested, depth + 1)  # type: ignore[index]
                return copied

            try:
                entries = tuple(item)
            except RuntimeError as exc:
                raise _ProjectionFailure("array_changed_during_snapshot") from exc
            if len(entries) != len(item):
                raise _ProjectionFailure("array_changed_during_snapshot")
            return [copy(nested, depth + 1) for nested in entries]
        finally:
            active.remove(identity)

    return copy(value, 0)


def _validate_context_shape(payload: object) -> tuple[str, str, str, str, str | None]:
    if type(payload) is not dict:
        raise _ProjectionFailure("context_must_be_object")
    fields = set(payload)
    if fields != _CONTEXT_FIELDS:
        missing = sorted(_CONTEXT_FIELDS - fields)
        extra = sorted(fields - _CONTEXT_FIELDS)
        raise _ProjectionFailure(f"context_fields_mismatch:{','.join(missing)}:{','.join(extra)}")

    session_id = payload["sessionID"]
    agent_id = payload["agent"]
    if not _valid_text(session_id) or not session_id.startswith("ses"):
        raise _ProjectionFailure("session_id_invalid")
    if not _valid_text(agent_id):
        raise _ProjectionFailure("agent_id_invalid")

    model = payload["model"]
    if type(model) is not dict or not {"id", "providerID"}.issubset(model):
        raise _ProjectionFailure("model_ref_invalid")
    if set(model) - {"id", "providerID", "variant"}:
        raise _ProjectionFailure("model_ref_fields_invalid")
    if not _valid_text(model["id"]) or not _valid_text(model["providerID"]):
        raise _ProjectionFailure("model_ref_identity_invalid")
    variant = model.get("variant")
    if "variant" in model and not _valid_text(variant):
        raise _ProjectionFailure("model_variant_invalid")

    system = payload["system"]
    messages = payload["messages"]
    options = payload["options"]
    tools = payload["tools"]
    if (
        type(system) is not list
        or len(system) > MAX_HOOK_SYSTEM_PARTS
        or any(
            type(part) is not dict
            or part.get("type") != "text"
            or type(part.get("text")) is not str
            for part in system
        )
    ):
        raise _ProjectionFailure("system_parts_invalid")
    if (
        type(messages) is not list
        or len(messages) > MAX_HOOK_MESSAGES
        or any(
            type(message) is not dict
            or message.get("role") not in ("system", "user", "assistant", "tool")
            or type(message.get("content")) is not list
            or any(
                type(part) is not dict
                or type(part.get("type")) is not str
                or not part.get("type")
                or (part.get("type") == "text" and type(part.get("text")) is not str)
                for part in message.get("content", ())
            )
            for message in messages
        )
    ):
        raise _ProjectionFailure("messages_invalid")
    if type(options) is not dict:
        raise _ProjectionFailure("options_invalid")
    if type(tools) is not dict or len(tools) > MAX_HOOK_TOOLS:
        raise _ProjectionFailure("tools_invalid")
    for name, tool in tools.items():
        if not _valid_text(name) or type(tool) is not dict or set(tool) != {"description", "input"}:
            raise _ProjectionFailure("tool_schema_invalid")
        if type(tool["description"]) is not str or type(tool["input"]) not in (dict, bool):
            raise _ProjectionFailure("tool_schema_invalid")

    return session_id, agent_id, model["providerID"], model["id"], variant


def _is_opencode_text_message(value: object) -> bool:
    """Validate the exact user-text Message subset Wrench inserts."""
    return (
        type(value) is dict
        and value.get("role") == "user"
        and type(value.get("content")) is list
        and len(value["content"]) == 1
        and type(value["content"][0]) is dict
        and value["content"][0].get("type") == "text"
        and type(value["content"][0].get("text")) is str
    )


def project_opencode_context_hook(event: object) -> OpenCodeProjectionResult:
    """Copy and hash the pinned context-hook fields under a 1 MiB bound.

    The projection is ephemeral data. This function does not persist, log,
    dispatch, authorize tools, or claim final provider serialization parity.
    The caller must supply a stable event object for the duration of this call.
    Length changes observed during container copying are rejected, but same-
    length or nested concurrent mutations cannot be detected atomically.
    """
    try:
        payload = _copy_json_bounded(event)
        session_id, agent_id, provider_id, model_id, variant = _validate_context_shape(payload)
        canonical = _bounded_canonical_json({
            "schema": PROJECTION_SCHEMA,
            "opencode_context_hook_version": OPENCODE_CONTEXT_HOOK_VERSION,
            "payload": payload,
        }, MAX_OPENCODE_CONTEXT_HOOK_BYTES)
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > MAX_OPENCODE_CONTEXT_HOOK_BYTES:
            raise _ProjectionFailure("input_bytes_limit_exceeded", limit=True)
    except _ProjectionFailure as exc:
        status = (
            OpenCodeProjectionStatus.INPUT_LIMIT_EXCEEDED
            if exc.limit
            else OpenCodeProjectionStatus.INVALID_SHAPE
        )
        if exc.reason == "context_must_be_object":
            status = OpenCodeProjectionStatus.INVALID_INPUT
        elif exc.reason.startswith("context_fields_mismatch:"):
            status = OpenCodeProjectionStatus.INVALID_FIELDS
        return OpenCodeProjectionResult(status, None, exc.reason)
    except OverflowError:
        return OpenCodeProjectionResult(
            OpenCodeProjectionStatus.INPUT_LIMIT_EXCEEDED, None, "input_bytes_limit_exceeded"
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return OpenCodeProjectionResult(
            OpenCodeProjectionStatus.INVALID_SHAPE, None, "projection_serialization_failed"
        )

    projection = OpenCodeContextHookProjection(
        session_id=session_id,
        agent_id=agent_id,
        provider_id=provider_id,
        model_id=model_id,
        model_variant=variant,
        projection_schema=PROJECTION_SCHEMA,
        opencode_context_hook_version=OPENCODE_CONTEXT_HOOK_VERSION,
        payload_json=encoded.decode("utf-8"),
        projection_sha256=hashlib.sha256(canonical).hexdigest(),
        serialized_bytes=len(encoded),
    )
    return OpenCodeProjectionResult(OpenCodeProjectionStatus.READY, projection, "ready")


def _validated_projection_payload(
    projection: object,
) -> tuple[dict[str, object], OpenCodeContextHookProjection] | None:
    if type(projection) is not OpenCodeContextHookProjection:
        return None
    if (
        type(projection.session_id) is not str
        or type(projection.agent_id) is not str
        or type(projection.provider_id) is not str
        or type(projection.model_id) is not str
        or (projection.model_variant is not None and type(projection.model_variant) is not str)
        or type(projection.projection_schema) is not str
        or type(projection.opencode_context_hook_version) is not str
        or type(projection.payload_json) is not str
        or type(projection.projection_sha256) is not str
        or type(projection.serialized_bytes) is not int
    ):
        return None
    payload_json = projection.payload_json
    if type(payload_json) is not str or len(payload_json) > MAX_OPENCODE_CONTEXT_HOOK_BYTES:
        return None
    try:
        if len(payload_json.encode("utf-8")) > MAX_OPENCODE_CONTEXT_HOOK_BYTES:
            return None
        payload = json.loads(payload_json)
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return None
    recomputed = project_opencode_context_hook(payload)
    if (
        recomputed.status is not OpenCodeProjectionStatus.READY
        or recomputed.projection is None
        or recomputed.projection != projection
    ):
        return None
    return payload, recomputed.projection


def validate_opencode_context_hook_transition(
    before: object,
    after: object,
    *,
    expected_message: object,
    insertion_position: int,
) -> OpenCodeTransitionResult:
    """Validate that two caller-supplied projections differ by one message insertion.

    Only the ``messages`` array may change. The declared position must contain
    the exact bounded JSON object supplied as ``expected_message`` and all
    original messages must remain in their original order. This validates the
    snapshots the caller provides; it does not authenticate a client hook or
    enforce dispatch.
    """
    before_validated = _validated_projection_payload(before)
    after_validated = _validated_projection_payload(after)
    if before_validated is None or after_validated is None:
        return OpenCodeTransitionResult(
            OpenCodeTransitionStatus.INVALID_PROJECTION, None, "invalid_projection"
        )
    before_payload, before_projection = before_validated
    after_payload, after_projection = after_validated

    if before_projection.session_id != after_projection.session_id:
        return OpenCodeTransitionResult(
            OpenCodeTransitionStatus.SESSION_MISMATCH, None, "session_mismatch"
        )

    protected_fields = ("agent", "model", "system", "tools", "options")
    for field in protected_fields:
        try:
            unchanged = _bounded_canonical_json(
                before_payload[field], MAX_OPENCODE_CONTEXT_HOOK_BYTES
            ) == _bounded_canonical_json(
                after_payload[field], MAX_OPENCODE_CONTEXT_HOOK_BYTES
            )
        except (TypeError, ValueError, OverflowError, RecursionError):
            unchanged = False
        if not unchanged:
            return OpenCodeTransitionResult(
                OpenCodeTransitionStatus.PROTECTED_CONTEXT_CHANGED,
                None,
                "protected_context_changed",
            )

    before_messages = before_payload["messages"]
    after_messages = after_payload["messages"]
    if (
        type(before_messages) is not list
        or type(after_messages) is not list
        or type(insertion_position) is not int
        or not 0 <= insertion_position <= len(before_messages)
        or len(before_messages) >= MAX_HOOK_MESSAGES
        or len(after_messages) != len(before_messages) + 1
        or type(expected_message) is not dict
        or not _is_opencode_text_message(expected_message)
    ):
        return OpenCodeTransitionResult(
            OpenCodeTransitionStatus.INSERTION_POSITION_INVALID,
            None,
            "insertion_position_invalid",
        )

    try:
        expected_copy = _copy_json_bounded(expected_message)
        if type(expected_copy) is not dict:
            raise _ProjectionFailure("expected_message_must_be_object")
        unchanged_prefix = _bounded_canonical_json(
            before_messages[:insertion_position], MAX_OPENCODE_CONTEXT_HOOK_BYTES
        ) == _bounded_canonical_json(
            after_messages[:insertion_position], MAX_OPENCODE_CONTEXT_HOOK_BYTES
        )
        unchanged_suffix = _bounded_canonical_json(
            before_messages[insertion_position:], MAX_OPENCODE_CONTEXT_HOOK_BYTES
        ) == _bounded_canonical_json(
            after_messages[insertion_position + 1 :], MAX_OPENCODE_CONTEXT_HOOK_BYTES
        )
        inserted = _bounded_canonical_json(
            expected_copy, MAX_OPENCODE_CONTEXT_HOOK_BYTES
        ) == _bounded_canonical_json(
            after_messages[insertion_position], MAX_OPENCODE_CONTEXT_HOOK_BYTES
        )
        expected_digest = hashlib.sha256(
            _bounded_canonical_json(expected_copy, MAX_OPENCODE_CONTEXT_HOOK_BYTES)
        ).hexdigest()
    except (_ProjectionFailure, TypeError, ValueError, OverflowError, RecursionError):
        return OpenCodeTransitionResult(
            OpenCodeTransitionStatus.INSERTION_POSITION_INVALID,
            None,
            "expected_message_invalid",
        )
    if not unchanged_prefix or not unchanged_suffix or not inserted:
        return OpenCodeTransitionResult(
            OpenCodeTransitionStatus.MESSAGE_SEQUENCE_MISMATCH,
            None,
            "message_sequence_mismatch",
        )

    receipt = OpenCodeContextTransitionReceipt(
        session_id=before_projection.session_id,
        opencode_context_hook_version=before_projection.opencode_context_hook_version,
        projection_schema=before_projection.projection_schema,
        before_projection_sha256=before_projection.projection_sha256,
        after_projection_sha256=after_projection.projection_sha256,
        inserted_message_sha256=expected_digest,
        insertion_position=insertion_position,
    )
    return OpenCodeTransitionResult(OpenCodeTransitionStatus.READY, receipt, "ready")


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _prepared_transition_receipt_payload(
    preparation_sha256: str,
    transition: OpenCodeContextTransitionReceipt,
) -> dict[str, object]:
    return {
        "schema": PREPARED_TRANSITION_RECEIPT_SCHEMA,
        "preparation_sha256": preparation_sha256,
        "transition": {
            "session_id": transition.session_id,
            "opencode_context_hook_version": transition.opencode_context_hook_version,
            "projection_schema": transition.projection_schema,
            "before_projection_sha256": transition.before_projection_sha256,
            "after_projection_sha256": transition.after_projection_sha256,
            "inserted_message_sha256": transition.inserted_message_sha256,
            "insertion_position": transition.insertion_position,
        },
    }


def verify_opencode_prepared_transition_receipt(receipt: object) -> bool:
    """Verify the canonical hash and field shape of a prepared transition receipt."""
    if type(receipt) is not OpenCodePreparedTransitionReceipt:
        return False
    transition = receipt.transition
    if type(transition) is not OpenCodeContextTransitionReceipt:
        return False
    if (
        type(receipt.schema) is not str
        or receipt.schema != PREPARED_TRANSITION_RECEIPT_SCHEMA
        or not _is_sha256(receipt.preparation_sha256)
        or not _is_sha256(receipt.receipt_sha256)
        or type(transition.session_id) is not str
        or not _valid_text(transition.session_id)
        or type(transition.opencode_context_hook_version) is not str
        or transition.opencode_context_hook_version != OPENCODE_CONTEXT_HOOK_VERSION
        or type(transition.projection_schema) is not str
        or transition.projection_schema != PROJECTION_SCHEMA
        or not _is_sha256(transition.before_projection_sha256)
        or not _is_sha256(transition.after_projection_sha256)
        or not _is_sha256(transition.inserted_message_sha256)
        or type(transition.insertion_position) is not int
        or not 0 <= transition.insertion_position < MAX_HOOK_MESSAGES
    ):
        return False
    try:
        canonical = _bounded_canonical_json(
            _prepared_transition_receipt_payload(receipt.preparation_sha256, transition),
            MAX_PREPARED_TRANSITION_RECEIPT_BYTES,
        )
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False
    return hashlib.sha256(canonical).hexdigest() == receipt.receipt_sha256


def validate_opencode_preparation_context_transition(
    preparation: object,
    before: object,
    after: object,
    *,
    expected_message: object,
) -> OpenCodePreparedTransitionResult:
    """Bind a single hook insertion to a READY E0 preparation and prompt gate.

    The preparation type is imported locally so the context pipeline can use
    this module without introducing an import cycle. This validates supplied
    local snapshots and receipts; it does not authenticate client behavior or
    enforce request dispatch.
    """
    # Local import avoids a cycle: e0_context_pipeline itself imports the hook
    # projection layer for its offline join and verification helpers.
    from .e0_context_pipeline import PreparationResult, PreparationStatus

    if (
        type(preparation) is not PreparationResult
        or preparation.status is not PreparationStatus.READY
        or not _is_sha256(preparation.aggregate_sha256)
    ):
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INVALID_PREPARATION,
            None,
            "preparation_invalid",
        )
    gate = preparation.prompt_gate
    if (
        type(gate) is not PromptGateReceipt
        or gate.status is not PromptGateStatus.READY
    ):
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INVALID_PROMPT_GATE,
            None,
            "prompt_gate_invalid",
        )
    message_sha256 = gate.context_message_sha256
    insertion_position = gate.context_insertion_position
    if message_sha256 is None and insertion_position is None:
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INSERTION_BINDING_MISSING,
            None,
            "insertion_binding_missing",
        )
    if not _is_sha256(message_sha256) or type(insertion_position) is not int or insertion_position < 0:
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INSERTION_BINDING_INVALID,
            None,
            "insertion_binding_invalid",
        )
    try:
        expected_copy = _copy_json_bounded(expected_message)
        if type(expected_copy) is not dict:
            raise _ProjectionFailure("expected_message_must_be_object")
        expected_sha256 = hashlib.sha256(
            _bounded_canonical_json(expected_copy, MAX_OPENCODE_CONTEXT_HOOK_BYTES)
        ).hexdigest()
    except (_ProjectionFailure, TypeError, ValueError, OverflowError, RecursionError):
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INSERTION_BINDING_INVALID,
            None,
            "expected_message_invalid",
        )
    if expected_sha256 != message_sha256:
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.INSERTION_BINDING_MISMATCH,
            None,
            "expected_message_binding_mismatch",
        )

    transition_result = validate_opencode_context_hook_transition(
        before,
        after,
        expected_message=expected_copy,
        insertion_position=insertion_position,
    )
    if transition_result.status is not OpenCodeTransitionStatus.READY or transition_result.receipt is None:
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.TRANSITION_REJECTED,
            None,
            f"transition_{transition_result.status.value}",
        )
    payload = _prepared_transition_receipt_payload(
        preparation.aggregate_sha256, transition_result.receipt
    )
    try:
        canonical = _bounded_canonical_json(payload, MAX_PREPARED_TRANSITION_RECEIPT_BYTES)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return OpenCodePreparedTransitionResult(
            OpenCodePreparedTransitionStatus.TRANSITION_REJECTED,
            None,
            "receipt_serialization_failed",
        )
    receipt = OpenCodePreparedTransitionReceipt(
        preparation.aggregate_sha256,
        transition_result.receipt,
        hashlib.sha256(canonical).hexdigest(),
    )
    return OpenCodePreparedTransitionResult(
        OpenCodePreparedTransitionStatus.READY,
        receipt,
        "ready",
    )


__all__ = [
    "CONTEXT_HOOK_OBSERVATION_SCHEMA",
    "MAX_HOOK_MESSAGES",
    "MAX_HOOK_SYSTEM_PARTS",
    "MAX_HOOK_TOOLS",
    "MAX_OPENCODE_CONTEXT_HOOK_BYTES",
    "MAX_OPENCODE_CONTEXT_HOOK_OBSERVATION_CALLS",
    "MAX_PREPARED_TRANSITION_RECEIPT_BYTES",
    "OPENCODE_CONTEXT_HOOK_VERSION",
    "PREPARED_TRANSITION_RECEIPT_SCHEMA",
    "PROJECTION_SCHEMA",
    "OpenCodeContextTransitionReceipt",
    "OpenCodeContextHookCall",
    "OpenCodeContextHookObservation",
    "OpenCodeContextHookObserver",
    "OpenCodeContextHookProjection",
    "OpenCodeProjectionResult",
    "OpenCodeProjectionStatus",
    "OpenCodeTransitionResult",
    "OpenCodeTransitionStatus",
    "OpenCodePreparedTransitionReceipt",
    "OpenCodePreparedTransitionResult",
    "OpenCodePreparedTransitionStatus",
    "project_opencode_context_hook",
    "validate_opencode_context_hook_transition",
    "validate_opencode_preparation_context_transition",
    "verify_opencode_prepared_transition_receipt",
]
