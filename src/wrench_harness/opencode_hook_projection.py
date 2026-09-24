"""Bounded, provider-free projection of the pinned OpenCode context hook."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum

from .prompt_compiler import (
    MAX_INPUT_DEPTH,
    MAX_INPUT_NODES,
    _bounded_canonical_json,
)


MAX_OPENCODE_CONTEXT_HOOK_BYTES = 1024 * 1024
MAX_HOOK_MESSAGES = 128
MAX_HOOK_SYSTEM_PARTS = 128
MAX_HOOK_TOOLS = 256
OPENCODE_CONTEXT_HOOK_VERSION = "2.0.15"
PROJECTION_SCHEMA = "wrench.opencode.context-hook-projection.v1"
_CONTEXT_FIELDS = frozenset({
    "sessionID", "agent", "model", "system", "messages", "tools", "options",
})


class OpenCodeProjectionStatus(str, Enum):
    READY = "ready"
    INVALID_INPUT = "invalid_input"
    INVALID_FIELDS = "invalid_fields"
    INVALID_SHAPE = "invalid_shape"
    INPUT_LIMIT_EXCEEDED = "input_limit_exceeded"


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
    if variant is not None and not _valid_text(variant):
        raise _ProjectionFailure("model_variant_invalid")

    system = payload["system"]
    messages = payload["messages"]
    options = payload["options"]
    tools = payload["tools"]
    if type(system) is not list or len(system) > MAX_HOOK_SYSTEM_PARTS:
        raise _ProjectionFailure("system_parts_invalid")
    if (
        type(messages) is not list
        or len(messages) > MAX_HOOK_MESSAGES
        or any(type(message) is not dict for message in messages)
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


def project_opencode_context_hook(event: object) -> OpenCodeProjectionResult:
    """Copy and hash the pinned context-hook fields under a 1 MiB bound.

    The projection is ephemeral data. This function does not persist, log,
    dispatch, authorize tools, or claim final provider serialization parity.
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


__all__ = [
    "MAX_HOOK_MESSAGES",
    "MAX_HOOK_SYSTEM_PARTS",
    "MAX_HOOK_TOOLS",
    "MAX_OPENCODE_CONTEXT_HOOK_BYTES",
    "OPENCODE_CONTEXT_HOOK_VERSION",
    "PROJECTION_SCHEMA",
    "OpenCodeContextHookProjection",
    "OpenCodeProjectionResult",
    "OpenCodeProjectionStatus",
    "project_opencode_context_hook",
]
