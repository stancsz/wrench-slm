"""Bounded, evidence-backed execution-state patch validation.

The controller may propose small task-state facts. Host code supplies the
field schema and current evidence manifest, validates every patch, and returns
a new immutable state. This module does not persist state, retrieve evidence,
route requests, execute tools, or grant permission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping


STATE_SCHEMA = "wrench.execution-state.v1"
PATCH_SCHEMA = "wrench.execution-state-patch.v1"
MAX_SESSION_ID_CHARS = 128
MAX_EVIDENCE_ID_CHARS = 128
MAX_PATCH_CHANGES = 32
MAX_PATCH_EVIDENCE_REFS = 8
MAX_PATCH_BYTES = 16 * 1024
MAX_EXECUTION_STATE_BYTES = 64 * 1024
MAX_FIELD_SPECS = 128
MAX_EVIDENCE_MANIFEST_ITEMS = 10_000
MAX_EVIDENCE_SOURCE_PATH_CHARS = 1_024
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_FIELD_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VALUE_TYPES = {"string", "integer", "boolean", "string_list"}
_CONTROL_FIELD_PARTS = {
    "authority",
    "authorize",
    "authorization",
    "budget",
    "budgets",
    "command",
    "commands",
    "credential",
    "credentials",
    "policy",
    "policies",
    "provider",
    "providers",
    "route",
    "routes",
    "routing",
    "shell",
    "spend",
    "tool",
    "tools",
    "permission",
    "permissions",
}


class ExecutionStateError(ValueError):
    """A bounded execution-state proposal failed validation."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class StateFieldSpec:
    """Host-owned schema for one non-authoritative state fact."""

    value_type: Literal["string", "integer", "boolean", "string_list"]
    required: bool = False
    max_chars: int = 512
    max_items: int = 16

    def __post_init__(self) -> None:
        if not isinstance(self.value_type, str) or self.value_type not in _VALUE_TYPES:
            raise ValueError("invalid_state_field_type")
        if not isinstance(self.required, bool):
            raise ValueError("invalid_state_field_required_flag")
        if (
            not isinstance(self.max_chars, int)
            or isinstance(self.max_chars, bool)
            or self.max_chars < 1
            or self.max_chars > 4096
        ):
            raise ValueError("invalid_state_field_char_limit")
        if (
            not isinstance(self.max_items, int)
            or isinstance(self.max_items, bool)
            or self.max_items < 1
            or self.max_items > 64
        ):
            raise ValueError("invalid_state_field_item_limit")


@dataclass(frozen=True)
class EvidenceSource:
    """Host-owned path and namespace for reacquiring one source reference."""

    source_namespace_sha256: str
    source_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_namespace_sha256, str) or not _SHA256_RE.fullmatch(
            self.source_namespace_sha256
        ):
            raise ValueError("invalid_evidence_source_namespace")
        if not _valid_evidence_source_path(self.source_path):
            raise ValueError("invalid_evidence_source_path")


@dataclass(frozen=True)
class EvidenceRef:
    """Content-free pointer to an exact, caller-owned evidence item."""

    evidence_id: str
    sha256: str
    source: EvidenceSource | None = None

    def __post_init__(self) -> None:
        if not _valid_id(self.evidence_id, MAX_EVIDENCE_ID_CHARS):
            raise ValueError("invalid_evidence_id")
        if not isinstance(self.sha256, str) or not _SHA256_RE.fullmatch(self.sha256):
            raise ValueError("invalid_evidence_sha256")
        if self.evidence_id.startswith("stable-source-") and self.source is None:
            raise ValueError("stable_evidence_source_metadata_required")
        if self.source is not None:
            if not isinstance(self.source, EvidenceSource):
                raise ValueError("invalid_evidence_source")
            if stable_source_evidence_id(
                self.source.source_namespace_sha256, self.source.source_path, self.sha256
            ) != self.evidence_id:
                raise ValueError("evidence_source_identity_mismatch")


@dataclass(frozen=True)
class StateFact:
    """One bounded fact and the evidence hashes that support it."""

    value: str | int | bool | tuple[str, ...]
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if isinstance(self.value, list):
            object.__setattr__(self, "value", tuple(self.value))
        if isinstance(self.value, str) and not self.value:
            raise ValueError("state_fact_value_empty")
        if isinstance(self.value, int) and not isinstance(self.value, bool):
            if self.value < -(2**63) or self.value > 2**63 - 1:
                raise ValueError("state_fact_integer_out_of_range")
        if isinstance(self.value, tuple) and any(
            not isinstance(item, str) or not item for item in self.value
        ):
            raise ValueError("state_fact_string_list_invalid")
        if not isinstance(self.value, (str, int, bool, tuple)):
            raise ValueError("state_fact_value_invalid")
        if not isinstance(self.evidence, tuple):
            object.__setattr__(self, "evidence", tuple(self.evidence))
        if (
            not 1 <= len(self.evidence) <= MAX_PATCH_EVIDENCE_REFS
            or any(not isinstance(ref, EvidenceRef) for ref in self.evidence)
        ):
            raise ValueError("state_fact_requires_evidence")
        ids = [ref.evidence_id for ref in self.evidence]
        if len(set(ids)) != len(ids):
            raise ValueError("state_fact_duplicate_evidence")
        object.__setattr__(
            self, "evidence", tuple(sorted(self.evidence, key=lambda ref: ref.evidence_id))
        )


@dataclass(frozen=True)
class ExecutionState:
    """Immutable bounded state for one task and one logical session."""

    session_id: str
    task_spec_sha256: str
    revision: int = 0
    facts: Mapping[str, StateFact] | None = None
    schema: str = STATE_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != STATE_SCHEMA:
            raise ValueError("execution_state_schema_mismatch")
        if not _valid_id(self.session_id, MAX_SESSION_ID_CHARS):
            raise ValueError("invalid_execution_session_id")
        if not isinstance(self.task_spec_sha256, str) or not _SHA256_RE.fullmatch(
            self.task_spec_sha256
        ):
            raise ValueError("invalid_task_spec_sha256")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 0
        ):
            raise ValueError("invalid_execution_state_revision")
        if self.facts is not None and not isinstance(self.facts, Mapping):
            raise ValueError("execution_state_facts_invalid")
        if self.facts is not None and len(self.facts) > MAX_FIELD_SPECS:
            raise ValueError("execution_state_field_limit_exceeded")
        raw_facts = {} if self.facts is None else dict(self.facts)
        if len(raw_facts) > MAX_FIELD_SPECS:
            raise ValueError("execution_state_field_limit_exceeded")
        for field, fact in raw_facts.items():
            if not _valid_field(field) or _is_control_field(field):
                raise ValueError("invalid_execution_state_field")
            if not isinstance(fact, StateFact):
                raise ValueError("invalid_execution_state_fact")
        object.__setattr__(self, "facts", MappingProxyType(raw_facts))
        try:
            state_bytes = _canonical_json(self.to_dict())
        except (TypeError, ValueError, OverflowError) as exc:
            raise ExecutionStateError("execution_state_not_json_safe") from exc
        if len(state_bytes) > MAX_EXECUTION_STATE_BYTES:
            raise ExecutionStateError("execution_state_byte_limit_exceeded")

    def to_dict(self) -> dict[str, Any]:
        facts: dict[str, Any] = {}
        for field in sorted(self.facts or {}):
            fact = (self.facts or {})[field]
            value: Any = list(fact.value) if isinstance(fact.value, tuple) else fact.value
            facts[field] = {
                "value": value,
                "evidence": [
                    _evidence_ref_to_dict(ref)
                    for ref in fact.evidence
                ],
            }
        return {
            "schema": self.schema,
            "session_id": self.session_id,
            "task_spec_sha256": self.task_spec_sha256,
            "revision": self.revision,
            "facts": facts,
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()


@dataclass(frozen=True)
class StatePatchResult:
    state: ExecutionState
    changed_fields: tuple[str, ...]
    patch_sha256: str
    normalized_patch_json: bytes


def new_execution_state(session_id: str, task_spec_sha256: str) -> ExecutionState:
    """Create an empty state bound to the immutable task specification."""

    return ExecutionState(session_id=session_id, task_spec_sha256=task_spec_sha256)


def apply_state_patch(
    current: ExecutionState,
    proposal: object,
    *,
    field_specs: Mapping[str, StateFieldSpec],
    evidence_hashes: Mapping[str, str],
    evidence_sources: Mapping[str, EvidenceSource] | None = None,
) -> StatePatchResult:
    """Validate a model proposal and return a new state without mutating input.

    The caller owns persistence and must commit the returned transition to its
    event log before using the new state. All facts require evidence references
    present in the caller's current evidence manifest. Routing, tools, policy,
    credentials, commands, and permissions cannot be state fields.
    """

    if not isinstance(current, ExecutionState):
        raise ExecutionStateError("current_state_invalid")
    specs = _validate_field_specs(field_specs)
    evidence = _validate_evidence_manifest(evidence_hashes)
    _validate_current_facts(current, specs, evidence)
    patch = _validate_proposal(proposal, current=current, specs=specs, evidence=evidence)
    sources = _validate_evidence_sources(evidence_sources, evidence=evidence, patch=patch)

    facts = dict(current.facts or {})
    changed: list[str] = []
    for change in patch["changes"]:
        field = change["field"]
        operation = change["op"]
        if operation == "delete":
            if specs[field].required:
                raise ExecutionStateError("required_state_field_cannot_be_deleted")
            if field not in facts:
                raise ExecutionStateError("state_field_to_delete_missing")
            del facts[field]
        else:
            value = _validate_value(change["value"], specs[field])
            refs = tuple(
                EvidenceRef(evidence_id=item, sha256=evidence[item], source=sources.get(item))
                for item in sorted(change["evidence_ids"])
            )
            facts[field] = StateFact(value=value, evidence=refs)
        changed.append(field)

    for field, spec in specs.items():
        if spec.required and field not in facts:
            raise ExecutionStateError("required_state_field_missing")

    new_state = ExecutionState(
        session_id=current.session_id,
        task_spec_sha256=current.task_spec_sha256,
        revision=current.revision + 1,
        facts=facts,
    )
    try:
        encoded = _canonical_json(patch)
        state_encoded = _canonical_json(new_state.to_dict())
    except (TypeError, ValueError, OverflowError) as exc:
        raise ExecutionStateError("state_patch_not_json_safe") from exc
    if len(encoded) > MAX_PATCH_BYTES:
        raise ExecutionStateError("state_patch_byte_limit_exceeded")
    if len(state_encoded) > MAX_EXECUTION_STATE_BYTES:
        raise ExecutionStateError("execution_state_byte_limit_exceeded")
    return StatePatchResult(
        state=new_state,
        changed_fields=tuple(sorted(changed)),
        patch_sha256=hashlib.sha256(encoded).hexdigest(),
        normalized_patch_json=encoded,
    )


def _validate_proposal(
    proposal: object,
    *,
    current: ExecutionState,
    specs: Mapping[str, StateFieldSpec],
    evidence: Mapping[str, str],
) -> dict[str, Any]:
    if type(proposal) is not dict or len(proposal) != 4 or set(proposal) != {
        "schema",
        "session_id",
        "base_revision",
        "changes",
    }:
        raise ExecutionStateError("state_patch_shape_invalid")
    if proposal["schema"] != PATCH_SCHEMA:
        raise ExecutionStateError("state_patch_schema_mismatch")
    if proposal["session_id"] != current.session_id:
        raise ExecutionStateError("state_patch_session_mismatch")
    revision = proposal["base_revision"]
    if not isinstance(revision, int) or isinstance(revision, bool):
        raise ExecutionStateError("state_patch_revision_invalid")
    if revision != current.revision:
        raise ExecutionStateError("state_patch_stale")
    changes = proposal["changes"]
    if type(changes) is not list or not 1 <= len(changes) <= MAX_PATCH_CHANGES:
        raise ExecutionStateError("state_patch_change_count_invalid")

    seen: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for change in changes:
        if type(change) is not dict or len(change) > 4:
            raise ExecutionStateError("state_patch_change_shape_invalid")
        operation = change.get("op")
        expected = {"op", "field", "evidence_ids"}
        if operation == "set":
            expected.add("value")
        elif operation != "delete":
            raise ExecutionStateError("state_patch_operation_invalid")
        if set(change) != expected:
            raise ExecutionStateError("state_patch_change_shape_invalid")
        field = change.get("field")
        if not _valid_field(field) or _is_control_field(field):
            raise ExecutionStateError("state_patch_field_invalid")
        if field not in specs:
            raise ExecutionStateError("state_patch_field_not_allowed")
        if field in seen:
            raise ExecutionStateError("state_patch_duplicate_field")
        seen.add(field)
        evidence_ids = change.get("evidence_ids")
        if (
            type(evidence_ids) is not list
            or not 1 <= len(evidence_ids) <= MAX_PATCH_EVIDENCE_REFS
            or any(not _valid_id(item, MAX_EVIDENCE_ID_CHARS) for item in evidence_ids)
            or len(set(evidence_ids)) != len(evidence_ids)
        ):
            raise ExecutionStateError("state_patch_evidence_refs_invalid")
        if any(item not in evidence for item in evidence_ids):
            raise ExecutionStateError("state_patch_evidence_missing")
        normalized_change: dict[str, Any] = {
            "op": operation,
            "field": field,
            "evidence_ids": sorted(evidence_ids),
        }
        if operation == "set":
            if specs[field].value_type == "string_list" and type(change.get("value")) is not list:
                raise ExecutionStateError("state_patch_value_invalid")
            normalized_change["value"] = _validate_value(change["value"], specs[field])
            if isinstance(normalized_change["value"], tuple):
                normalized_change["value"] = list(normalized_change["value"])
        normalized.append(normalized_change)
    return {
        "schema": PATCH_SCHEMA,
        "session_id": current.session_id,
        "base_revision": current.revision,
        "changes": sorted(normalized, key=lambda item: item["field"]),
    }


def _validate_field_specs(
    field_specs: Mapping[str, StateFieldSpec],
) -> Mapping[str, StateFieldSpec]:
    if not isinstance(field_specs, Mapping) or len(field_specs) > MAX_FIELD_SPECS:
        raise ExecutionStateError("state_field_schema_invalid")
    copied: dict[str, StateFieldSpec] = {}
    for field, spec in field_specs.items():
        if not _valid_field(field) or _is_control_field(field):
            raise ExecutionStateError("state_field_schema_invalid")
        if not isinstance(spec, StateFieldSpec):
            raise ExecutionStateError("state_field_schema_invalid")
        copied[field] = spec
    return MappingProxyType(copied)


def _validate_current_facts(
    current: ExecutionState,
    specs: Mapping[str, StateFieldSpec],
    evidence: Mapping[str, str],
) -> None:
    for field, fact in (current.facts or {}).items():
        if field not in specs:
            raise ExecutionStateError("current_state_schema_mismatch")
        _validate_value(fact.value, specs[field])
        for ref in fact.evidence:
            if evidence.get(ref.evidence_id) != ref.sha256:
                raise ExecutionStateError("current_state_evidence_stale")


def _validate_evidence_manifest(evidence_hashes: Mapping[str, str]) -> Mapping[str, str]:
    if not isinstance(evidence_hashes, Mapping) or len(evidence_hashes) > MAX_EVIDENCE_MANIFEST_ITEMS:
        raise ExecutionStateError("state_evidence_manifest_invalid")
    copied: dict[str, str] = {}
    for evidence_id, digest in evidence_hashes.items():
        if not _valid_id(evidence_id, MAX_EVIDENCE_ID_CHARS):
            raise ExecutionStateError("state_evidence_manifest_invalid")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise ExecutionStateError("state_evidence_manifest_invalid")
        copied[evidence_id] = digest
    return MappingProxyType(copied)


def _validate_evidence_sources(
    evidence_sources: Mapping[str, EvidenceSource] | None,
    *,
    evidence: Mapping[str, str],
    patch: Mapping[str, Any],
) -> Mapping[str, EvidenceSource]:
    if evidence_sources is None:
        evidence_sources = {}
    if not isinstance(evidence_sources, Mapping) or len(evidence_sources) > MAX_EVIDENCE_MANIFEST_ITEMS:
        raise ExecutionStateError("state_evidence_sources_invalid")
    patched_ids = {
        evidence_id
        for change in patch["changes"]
        if change["op"] == "set"
        for evidence_id in change["evidence_ids"]
    }
    copied: dict[str, EvidenceSource] = {}
    for evidence_id, source in evidence_sources.items():
        if (
            not _valid_id(evidence_id, MAX_EVIDENCE_ID_CHARS)
            or evidence_id not in patched_ids
            or evidence_id not in evidence
            or not isinstance(source, EvidenceSource)
            or stable_source_evidence_id(
                source.source_namespace_sha256, source.source_path, evidence[evidence_id]
            ) != evidence_id
        ):
            raise ExecutionStateError("state_evidence_sources_invalid")
        copied[evidence_id] = source
    required_stable_ids = {
        evidence_id
        for evidence_id in patched_ids
        if evidence_id.startswith("stable-source-")
    }
    if not required_stable_ids.issubset(copied):
        raise ExecutionStateError("state_evidence_sources_missing")
    return MappingProxyType(copied)


def _validate_value(value: object, spec: StateFieldSpec) -> str | int | bool | tuple[str, ...]:
    if spec.value_type == "string":
        if not isinstance(value, str) or not value or len(value) > spec.max_chars:
            raise ExecutionStateError("state_patch_value_invalid")
        return value
    if spec.value_type == "integer":
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < -(2**63)
            or value > 2**63 - 1
        ):
            raise ExecutionStateError("state_patch_value_invalid")
        return value
    if spec.value_type == "boolean":
        if not isinstance(value, bool):
            raise ExecutionStateError("state_patch_value_invalid")
        return value
    if spec.value_type == "string_list":
        if (
            not isinstance(value, (list, tuple))
            or len(value) > spec.max_items
            or any(not isinstance(item, str) or not item or len(item) > spec.max_chars for item in value)
        ):
            raise ExecutionStateError("state_patch_value_invalid")
        return tuple(value)
    raise ExecutionStateError("state_field_schema_invalid")


def _valid_id(value: object, max_chars: int) -> bool:
    return isinstance(value, str) and len(value) <= max_chars and bool(_ID_RE.fullmatch(value))


def _valid_evidence_source_path(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_EVIDENCE_SOURCE_PATH_CHARS
        or "\x00" in value
        or "\\" in value
        or value.startswith("/")
        or (len(value) >= 2 and value[1] == ":")
    ):
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") or ":" in part for part in parts):
        return False
    if any(part.endswith((".", " ")) for part in parts):
        return False
    return True


def stable_source_evidence_id(
    source_namespace_sha256: str, source_path: str, source_sha256: str
) -> str:
    """Build a snapshot-independent ID bound to one host namespace and file hash."""

    source = EvidenceSource(source_namespace_sha256, source_path)
    if not isinstance(source_sha256, str) or not _SHA256_RE.fullmatch(source_sha256):
        raise ValueError("invalid_evidence_source_sha256")
    payload = {
        "schema": "wrench.state-source-identity.v1",
        "source_namespace_sha256": source.source_namespace_sha256,
        "source_path": source.source_path,
        "source_sha256": source_sha256,
    }
    return "stable-source-" + hashlib.sha256(_canonical_json(payload)).hexdigest()


def _evidence_ref_to_dict(ref: EvidenceRef) -> dict[str, Any]:
    result: dict[str, Any] = {"evidence_id": ref.evidence_id, "sha256": ref.sha256}
    if ref.source is not None:
        result["source"] = {
            "source_namespace_sha256": ref.source.source_namespace_sha256,
            "source_path": ref.source.source_path,
        }
    return result


def _valid_field(value: object) -> bool:
    return isinstance(value, str) and bool(_FIELD_RE.fullmatch(value))


def _is_control_field(field: str) -> bool:
    return bool(_CONTROL_FIELD_PARTS.intersection(field.split("_")))


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
