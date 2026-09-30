"""Caller-scoped deterministic E0 context preparation with no execution route.

This facade composes existing bounded primitives. It returns a prompt only as
an inert local result; it has no provider, model, router, subprocess, or tool
execution capability. Serializer/tokenizer callbacks are caller supplied and
their identities are copied into receipts, not independently authenticated.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence

from .artifact_store import ArtifactHandle, ArtifactReadStatus, ArtifactRequest, ArtifactStore, ArtifactStoreError
from .context import ContextAdmissionError, ContextLedger, ContextSelectionError
from .execution_state import EvidenceSource, ExecutionState, stable_source_evidence_id
from .execution_state_store import StateStoreLoadReceipt
from .namespace_registry import NamespaceRegistry, SchemaLookupStatus
from .outcome_receipt import ReceiptResult, ReceiptStatus, build_outcome_receipt
from .prompt_compiler import (
    MAX_BASE_MESSAGES, MAX_BASE_MESSAGES_BYTES, PromptGateReceipt,
    PromptGateStatus, _bounded_canonical_json, _is_opencode_message_shape,
    compile_prompt,
)
from .snapshot import (
    RetrievalStatus, SnapshotAdmissionError, SourceRootBinding, SourceSnapshot,
    create_snapshot, retrieve_exact,
)
from .snapshot_structure import (
    StructuralStatus, build_snapshot_symbol_index, query_snapshot_symbols,
)
from .toml_context_spans import extract_toml_key_spans, extract_toml_table_spans

if TYPE_CHECKING:
    from .selected_segment_sources import SelectedSourceReferenceReceipt
else:
    SelectedSourceReferenceReceipt = Any


MAX_PATHS = 16
MAX_SCHEMA_LOOKUPS = 4
MAX_SOURCE_BYTES = 64 * 1024
MAX_AGGREGATE_SOURCE_BYTES = 512 * 1024
MAX_REFERENCES = 256
MAX_RECEIPT_REFERENCE_BYTES = 64 * 1024
MAX_EXECUTION_STATE_FACTS = 128
MAX_EXECUTION_STATE_EVIDENCE_REFS = 16
MAX_QUERY_CHARS = 256
MAX_CONTEXT_TOKENS = 8192
MAX_SOURCE_INGESTION_TOKENS = 65_536
MAX_PROMPT_TOKENS = 8192
PREPARATION_ACCOUNTING_SCHEMA = "wrench.e0.preparation-accounting.v2"
PREPARATION_ACCOUNTING_COUNTER_FIELDS = (
    "caller_path_count",
    "exact_source_retrieval_attempts",
    "exact_source_retrieval_successes",
    "exact_source_retrieval_status_counts",
    "exact_source_returned_bytes",
    "source_exact_read_total_attempts",
    "source_exact_read_total_successes",
    "source_exact_read_total_returned_bytes",
    "structural_index_build_attempts",
    "structural_index_status",
    "structural_index_exact_read_attempts",
    "structural_index_exact_read_successes",
    "structural_index_exact_read_status_counts",
    "structural_index_returned_bytes",
    "structural_index_query_attempts",
    "structural_index_query_status",
    "structural_index_candidate_count",
    "artifact_put_attempts",
    "artifact_put_successes",
    "artifact_put_input_bytes",
    "artifact_put_success_bytes",
    "artifact_pin_attempts",
    "artifact_pin_successes",
    "artifact_pin_bytes",
    "artifact_pin_scope_duration_ns",
    "artifact_read_attempts",
    "artifact_read_successes",
    "artifact_read_bytes",
    "schema_discover_attempts",
    "schema_discover_results",
    "schema_lookup_attempts",
    "schema_lookup_status_counts",
    "ledger_assembly_attempts",
    "ledger_selected_count",
    "ledger_omitted_count",
    "serializer_callback_attempts",
    "tokenizer_callback_attempts",
    "prompt_serialized_bytes",
    "prompt_token_count",
    "outcome_receipt_build_attempts",
    "outcome_receipt_status",
    "facade_model_call_sites",
    "facade_provider_call_sites",
    "facade_verifier_call_sites",
    "facade_tool_call_sites",
    "callback_external_activity",
    "process_cpu_ns",
    "process_rss_bytes",
    "energy_joules",
    "os_cache_bytes",
    "request_page_faults",
    "unmeasured_dimensions",
    "ledger_logical_token_count",
    "ledger_selected_token_count",
    "ledger_retrieval_candidate_count",
    "ledger_retrieval_truncated",
    "ledger_search_limit",
    "ledger_token_count_mode",
    "ledger_token_counter_name",
    "structural_index_file_count",
    "structural_index_symbol_count",
    "structural_index_serialized_bytes",
)


class PreparationStatus(str, Enum):
    READY = "ready"
    INVALID_INPUT = "invalid_input"
    SOURCE_MISSES = "source_misses"
    STRUCTURE_FAILED = "structure_failed"
    STORE_FAILED = "store_failed"
    CONTEXT_FAILED = "context_failed"
    SCHEMA_FAILED = "schema_failed"
    PROMPT_REJECTED = "prompt_rejected"
    RECEIPT_FAILED = "receipt_failed"


@dataclass(frozen=True)
class SourceIdentity:
    evidence_id: str
    path: str
    content_sha256: str
    artifact_handle_id: str | None
    status: str


@dataclass(frozen=True)
class PreparationResult:
    status: PreparationStatus
    route: str
    prompt: str | bytes | None
    prompt_gate: PromptGateReceipt | None
    outcome_receipt: ReceiptResult | None
    aggregate_sha256: str | None
    sources: tuple[SourceIdentity, ...]
    selected_evidence_ids: tuple[str, ...]
    omitted_evidence: tuple[tuple[str, str], ...]
    retrieval_misses: tuple[tuple[str, str], ...]
    schema_digests: tuple[tuple[str, str, str], ...]
    structural_status: str | None
    reason: str | None = None
    metrics: "PreparationMetrics | None" = None
    accounting_receipt: "PreparationAccountingReceipt | None" = None
    selected_source_references: SelectedSourceReferenceReceipt | None = None
    selected_source_reference_unavailable_reasons: tuple[tuple[str, str], ...] = ()
    # Ephemeral immutable bridge for a local client adapter. Never included in
    # outcome/accounting receipts or repr output.
    context_message_json: str | None = field(default=None, repr=False, compare=False)
    execution_state_revision: int | None = None
    execution_state_sha256: str | None = None
    execution_state_event_sha256: str | None = None
    execution_state_selected_fields: tuple[str, ...] = ()
    execution_state_omitted_fields: tuple[tuple[str, str], ...] = ()
    execution_state_evidence_verified_for_prompt: bool | None = None


@dataclass(frozen=True)
class PreparationAccountingReceipt:
    """Canonical companion for facade counters, joined by preparation hash.

    The same-process pin-scope duration is run-specific. Other time/resource
    dimensions and arbitrary callback effects remain unmeasured.
    """

    schema: str
    preparation_sha256: str
    accounting_sha256: str
    payload_json: str


@dataclass(frozen=True)
class PreparationMetrics:
    """Facade call-site counters; external callback effects are unmeasured.

    Resource dimensions without a trustworthy request-scoped source are
    explicitly unmeasured (None).
    """

    elapsed_wall_ns: int
    caller_path_count: int | None
    exact_source_retrieval_attempts: int
    exact_source_retrieval_successes: int
    exact_source_retrieval_status_counts: tuple[tuple[str, int], ...]
    exact_source_returned_bytes: int
    source_exact_read_total_attempts: int
    source_exact_read_total_successes: int
    source_exact_read_total_returned_bytes: int
    structural_index_build_attempts: int
    structural_index_status: str | None
    structural_index_exact_read_attempts: int
    structural_index_exact_read_successes: int
    structural_index_exact_read_status_counts: tuple[tuple[str, int], ...]
    structural_index_returned_bytes: int
    structural_index_query_attempts: int
    structural_index_query_status: str | None
    structural_index_candidate_count: int | None
    artifact_put_attempts: int
    artifact_put_successes: int
    artifact_put_input_bytes: int
    artifact_put_success_bytes: int
    artifact_pin_attempts: int
    artifact_pin_successes: int
    artifact_pin_bytes: int
    artifact_pin_scope_duration_ns: int | None
    artifact_read_attempts: int
    artifact_read_successes: int
    artifact_read_bytes: int
    schema_discover_attempts: int
    schema_discover_results: int | None
    schema_lookup_attempts: int
    schema_lookup_status_counts: tuple[tuple[str, int], ...]
    ledger_assembly_attempts: int
    ledger_selected_count: int | None
    ledger_omitted_count: int | None
    serializer_callback_attempts: int
    tokenizer_callback_attempts: int
    prompt_serialized_bytes: int | None
    prompt_token_count: int | None
    outcome_receipt_build_attempts: int
    outcome_receipt_status: str | None
    facade_model_call_sites: int
    facade_provider_call_sites: int
    facade_verifier_call_sites: int
    facade_tool_call_sites: int
    callback_external_activity: None
    process_cpu_ns: None
    process_rss_bytes: None
    energy_joules: None
    os_cache_bytes: None
    request_page_faults: None
    unmeasured_dimensions: tuple[str, ...]
    ledger_logical_token_count: int | None = None
    ledger_selected_token_count: int | None = None
    ledger_retrieval_candidate_count: int | None = None
    ledger_retrieval_truncated: bool | None = None
    ledger_search_limit: int | None = None
    ledger_token_count_mode: str | None = None
    ledger_token_counter_name: str | None = None
    structural_index_file_count: int | None = None
    structural_index_symbol_count: int | None = None
    structural_index_serialized_bytes: int | None = None


def _accounting_receipt(
    aggregate_sha256: str | None, metrics: PreparationMetrics
) -> PreparationAccountingReceipt | None:
    """Bind facade counters to the content receipt they describe.

    Preparation wall time is excluded. The process-local artifact pin-scope
    duration is included as a diagnostic. Explicit unavailable values remain
    null, distinct from a measured zero.
    """
    if aggregate_sha256 is None:
        return None
    # Keep the v2 projection explicit. New PreparationMetrics fields do not
    # silently alter this schema's identity; intentionally extend it only with
    # a documented schema/version decision.
    metric_values = asdict(metrics)
    counter_values = {
        name: metric_values[name] for name in PREPARATION_ACCOUNTING_COUNTER_FIELDS
    }
    payload = {
        "schema": PREPARATION_ACCOUNTING_SCHEMA,
        "preparation_sha256": aggregate_sha256,
        "counters": counter_values,
    }
    raw = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(raw) > MAX_RECEIPT_REFERENCE_BYTES:
        return None
    return PreparationAccountingReceipt(
        schema=payload["schema"],
        preparation_sha256=aggregate_sha256,
        accounting_sha256=_sha(raw),
        payload_json=raw.decode("utf-8"),
    )


@contextmanager
def _capture_pin_scope_duration(scope, metrics: dict[str, object]):
    """Capture the actual closed ArtifactRequest duration after scope exit.

    Caller-owned scopes normally remain open after preparation returns, so
    their duration is unavailable here. The metric describes only this local
    preparation pin scope, never downstream/client latency.
    """
    request = None
    try:
        with scope as request:
            yield request
    finally:
        try:
            duration = request.pin_scope_duration_ns if request is not None else None
        except Exception:
            # A diagnostic read must not mask preparation failure or cleanup.
            duration = None
        if type(duration) is int and duration >= 0:
            metrics["artifact_pin_scope_duration_ns"] = duration


def verify_preparation_accounting_receipt(
    receipt: PreparationAccountingReceipt,
    *,
    aggregate_sha256: str,
) -> bool:
    """Check canonical payload integrity and its join to a preparation hash.

    This verifies structure and accidental-change integrity only. It does not
    authenticate who measured the counters or prove external callback effects.
    """
    if type(receipt) is not PreparationAccountingReceipt:
        return False
    if (
        type(aggregate_sha256) is not str
        or type(receipt.schema) is not str
        or type(receipt.preparation_sha256) is not str
        or type(receipt.accounting_sha256) is not str
        or type(receipt.payload_json) is not str
        or receipt.schema != PREPARATION_ACCOUNTING_SCHEMA
    ):
        return False
    if receipt.preparation_sha256 != aggregate_sha256:
        return False
    # Every valid Unicode code point consumes at least one UTF-8 byte. Reject
    # clearly oversized strings before making the encoded copy.
    if len(receipt.payload_json) > MAX_RECEIPT_REFERENCE_BYTES:
        return False
    try:
        payload_bytes = receipt.payload_json.encode("utf-8")
    except UnicodeError:
        return False
    if len(payload_bytes) > MAX_RECEIPT_REFERENCE_BYTES:
        return False
    try:
        payload = json.loads(receipt.payload_json)
        raw = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return False
    if len(raw) > MAX_RECEIPT_REFERENCE_BYTES or raw.decode("utf-8") != receipt.payload_json:
        return False
    if _sha(raw) != receipt.accounting_sha256:
        return False
    return (
        isinstance(payload, dict)
        and set(payload) == {"schema", "preparation_sha256", "counters"}
        and payload.get("schema") == PREPARATION_ACCOUNTING_SCHEMA
        and payload.get("preparation_sha256") == aggregate_sha256
        and isinstance(payload.get("counters"), dict)
        and set(payload["counters"]) == set(PREPARATION_ACCOUNTING_COUNTER_FIELDS)
        and _valid_preparation_accounting_counters(payload["counters"])
    )


def _valid_preparation_accounting_counters(counters: dict[str, object]) -> bool:
    """Validate v2 JSON value types, preserving null versus measured zero."""
    integer_fields = {
        "exact_source_retrieval_attempts", "exact_source_retrieval_successes",
        "exact_source_returned_bytes", "source_exact_read_total_attempts",
        "source_exact_read_total_successes", "source_exact_read_total_returned_bytes",
        "structural_index_build_attempts", "structural_index_exact_read_attempts",
        "structural_index_exact_read_successes", "structural_index_returned_bytes",
        "structural_index_query_attempts", "artifact_put_attempts", "artifact_put_successes",
        "artifact_put_input_bytes", "artifact_put_success_bytes", "artifact_pin_attempts",
        "artifact_pin_successes", "artifact_pin_bytes", "artifact_read_attempts",
        "artifact_read_successes", "artifact_read_bytes", "schema_discover_attempts",
        "schema_lookup_attempts", "ledger_assembly_attempts", "serializer_callback_attempts",
        "tokenizer_callback_attempts", "outcome_receipt_build_attempts", "facade_model_call_sites",
        "facade_provider_call_sites", "facade_verifier_call_sites", "facade_tool_call_sites",
    }
    optional_integer_fields = {
        "caller_path_count", "structural_index_candidate_count", "schema_discover_results",
        "ledger_selected_count", "ledger_omitted_count", "prompt_serialized_bytes",
        "prompt_token_count", "ledger_logical_token_count", "ledger_selected_token_count",
        "ledger_retrieval_candidate_count", "ledger_search_limit", "structural_index_file_count",
        "structural_index_symbol_count", "structural_index_serialized_bytes",
        "artifact_pin_scope_duration_ns",
    }
    null_fields = {
        "callback_external_activity", "process_cpu_ns", "process_rss_bytes", "energy_joules",
        "os_cache_bytes", "request_page_faults",
    }
    string_fields = {
        "structural_index_status", "structural_index_query_status", "outcome_receipt_status",
        "ledger_token_count_mode", "ledger_token_counter_name",
    }
    count_fields = {
        "exact_source_retrieval_status_counts", "structural_index_exact_read_status_counts",
        "schema_lookup_status_counts",
    }
    classified = integer_fields | optional_integer_fields | null_fields | string_fields | count_fields | {
        "structural_index_candidate_count", "ledger_retrieval_truncated", "unmeasured_dimensions",
    }
    if classified != set(PREPARATION_ACCOUNTING_COUNTER_FIELDS):
        return False
    for name in integer_fields:
        if type(counters[name]) is not int or counters[name] < 0:
            return False
    for name in optional_integer_fields:
        value = counters[name]
        if value is not None and (type(value) is not int or value < 0):
            return False
    for name in null_fields:
        if counters[name] is not None:
            return False
    for name in string_fields:
        value = counters[name]
        if value is not None and (type(value) is not str or len(value) > 128):
            return False
    for name in count_fields:
        rows = counters[name]
        if type(rows) is not list or any(
            type(row) is not list or len(row) != 2 or type(row[0]) is not str
            or len(row[0]) > 64 or type(row[1]) is not int or row[1] < 0
            for row in rows
        ):
            return False
        if rows != sorted(rows, key=lambda row: row[0]) or len({row[0] for row in rows}) != len(rows):
            return False
    truncated = counters["ledger_retrieval_truncated"]
    if truncated is not None and type(truncated) is not bool:
        return False
    unmeasured = counters["unmeasured_dimensions"]
    return unmeasured == [
        "callback_external_activity", "process_cpu", "process_rss", "energy",
        "os_cache", "request_page_faults",
    ]


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_RECEIPT_REFERENCE_BYTES:
        raise ValueError("aggregate_reference_limit_exceeded")
    return _sha(raw)


def _bounded_sequence(value: object, maximum: int) -> tuple[object, ...] | None:
    """Take a bounded owned view of exact built-in sequence inputs."""
    if type(value) not in (tuple, list):
        return None
    try:
        before = len(value)
        if before > maximum:
            return None
        owned = tuple(value)
        if len(owned) != before or len(value) != before:
            return None
        return owned
    except (RuntimeError, TypeError, ValueError):
        return None


def _plain_schema(value: object, depth: int = 0) -> object:
    """Copy a registry's immutable JSON value into bounded ordinary containers."""
    if depth > 32:
        raise ValueError("schema_depth_limit")
    if value is None or type(value) in (str, bool, int, float):
        return value
    if isinstance(value, Mapping):
        if len(value) > 1024:
            raise ValueError("schema_mapping_limit")
        return {key: _plain_schema(nested, depth + 1) for key, nested in value.items()}
    if type(value) in (list, tuple):
        if len(value) > 1024:
            raise ValueError("schema_sequence_limit")
        return [_plain_schema(nested, depth + 1) for nested in value]
    raise ValueError("schema_value_not_json")


def _evidence_id(snapshot_hash: str, path: str, digest: str) -> str:
    return "source-" + _canonical_digest([snapshot_hash, path, digest])


def _retrieval_label(status: RetrievalStatus) -> str:
    return {
        RetrievalStatus.UNKNOWN_SNAPSHOT: "unknown_snapshot",
        RetrievalStatus.UNKNOWN_SOURCE: "unknown_source",
        RetrievalStatus.MISSING: "missing",
        RetrievalStatus.CHANGED: "stale",
        RetrievalStatus.UNSAFE: "unsafe",
    }.get(status, "unsafe")


def _receipt_payload(
    *, snapshot_hash: str, aggregate_hash: str, selected: Sequence[str],
    omitted: Sequence[tuple[str, str]], misses: Sequence[tuple[str, str]],
) -> dict[str, object]:
    return {
        "schema": "wrench.e0.outcome-receipt.v1",
        "task_id": "e0-context-preparation",
        "run_id": aggregate_hash,
        "snapshot_sha256": snapshot_hash,
        "context_receipt_sha256": aggregate_hash,
        "selected_evidence_ids": list(selected),
        "omitted_evidence_ids": [item[0] for item in omitted],
        "retrieval_misses": [{"evidence_id": item[0], "status": item[1]} for item in misses],
        "actual_route": "none",
        "attempts": [],
        "work_calls": [],
        "verifier": {"identity": None, "result": "not_run", "evidence_ids": []},
        "outcome": {"status": "unknown", "provenance": "unknown", "evidence_ids": []},
        "correction_refs": [],
        "accounting": {
            "local_model_calls": 0, "frontier_model_calls": 0,
            "retries": 0, "fallback_calls": 0, "verifier_calls": 0, "tool_calls": 0,
            "local_tokens": 0, "frontier_tokens": 0,
            "local_token_counter_id": None, "frontier_token_counter_id": None,
            "token_count_status": "not_applicable",
            "local_cost_microunits": 0, "frontier_cost_microunits": 0,
            "cost_status": "known",
        },
        "completeness": "incomplete",
        "missing_fields": ["outcome"],
    }


def _valid_execution_state_receipt(value: object) -> bool:
    if type(value) is not StateStoreLoadReceipt:
        return False
    state = value.state
    if (
        type(state) is not ExecutionState
        or type(value.event_count) is not int
        or value.event_count != state.revision
        or type(value.last_event_sha256) is not str
        or len(value.last_event_sha256) != 64
        or any(char not in "0123456789abcdef" for char in value.last_event_sha256)
        or type(value.recovered_staged_event) is not bool
        or type(value.current_evidence_verified) is not bool
        or type(value.ignored_staging_files) is not tuple
        or len(value.ignored_staging_files) > 16
        or any(type(name) is not str or not name or len(name) > 128 for name in value.ignored_staging_files)
        or len(state.facts or {}) > MAX_EXECUTION_STATE_FACTS
    ):
        return False
    evidence_ids = {
        ref.evidence_id
        for fact in (state.facts or {}).values()
        for ref in fact.evidence
    }
    if len(evidence_ids) > MAX_EXECUTION_STATE_EVIDENCE_REFS:
        return False
    return True


def _execution_state_source_namespace(snapshot: SourceSnapshot) -> str | None:
    if (
        type(snapshot.root_location_sha256) is not str
        or len(snapshot.root_location_sha256) != 64
        or type(snapshot.root_identity) is not str
    ):
        return None
    return _canonical_digest([
        "wrench.e0-source-namespace.v1",
        snapshot.root_location_sha256,
        snapshot.root_identity,
    ])


def execution_state_evidence_manifest(
    snapshot: SourceSnapshot,
) -> tuple[dict[str, str], dict[str, EvidenceSource]]:
    """Return path-and-content identities for validated caller-owned sources.

    The source namespace is stable across snapshots of the same bound root.
    An evidence ID changes when either its relative path or bytes change.
    """

    if type(snapshot) is not SourceSnapshot:
        raise ValueError("execution_state_source_snapshot_invalid")
    namespace = _execution_state_source_namespace(snapshot)
    if namespace is None or type(snapshot.sources) is not tuple:
        raise ValueError("execution_state_source_snapshot_invalid")
    evidence_hashes: dict[str, str] = {}
    evidence_sources: dict[str, EvidenceSource] = {}
    for source in snapshot.sources:
        if (
            type(source.path) is not str or type(source.sha256) is not str
            or len(source.sha256) != 64
        ):
            raise ValueError("execution_state_source_snapshot_invalid")
        evidence_id = stable_source_evidence_id(namespace, source.path, source.sha256)
        evidence_hashes[evidence_id] = source.sha256
        evidence_sources[evidence_id] = EvidenceSource(namespace, source.path)
    return evidence_hashes, evidence_sources


def _execution_state_fact_text(
    state: ExecutionState,
    field_name: str,
    fact: object,
    current_evidence_ids: Mapping[str, str],
) -> str:
    value = fact.value
    if isinstance(value, tuple):
        value = list(value)
    payload = {
        "schema": "wrench.execution-state-fact.v1",
        "revision": state.revision,
        "field": field_name,
        "value": value,
        "evidence": [
            {
                "evidence_id": ref.evidence_id,
                "sha256": ref.sha256,
                "source_path": ref.source.source_path if ref.source is not None else None,
                "current_evidence_id": current_evidence_ids.get(ref.evidence_id),
            }
            for ref in fact.evidence
        ],
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return "Persisted Wrench execution fact, untrusted data; retrieve its cited evidence before relying on it: " + encoded


def _prepare_e0_context_impl(
    *,
    source_root: str | os.PathLike[str] | SourceRootBinding,
    snapshot: SourceSnapshot,
    paths: Sequence[str | os.PathLike[str]],
    store: ArtifactStore,
    query: str,
    source_order_start: int,
    context_token_budget: int,
    prompt_token_budget: int,
    source_ingestion_token_limit: int,
    namespace_registry: NamespaceRegistry,
    schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]],
    context_position: int,
    message_format: str,
    context_render_mode: str,
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int],
    serializer_id: str,
    tokenizer_id: str,
    required_evidence_ids: Sequence[str] = (),
    preserve_evidence_ids: Sequence[str] = (),
    required_source_paths: Sequence[str] = (),
    preserve_source_paths: Sequence[str] = (),
    use_symbol_span_for_required_path: bool = False,
    use_toml_key_spans_for_required_path: bool = False,
    use_toml_table_spans_for_required_path: bool = False,
    toml_span_query: str | None = None,
    max_candidates: int = 8,
    artifact_request: ArtifactRequest | None = None,
    execution_state_receipt: StateStoreLoadReceipt | None = None,
    _metrics: dict[str, object],
) -> PreparationResult:
    """Prepare verified, pinned context and a gated prompt; never executes it.

    Source snapshots bind bytes, not caller authority. Paths are finite and
    explicit. Store objects may persist after this request and are not rolled
    back if later context/prompt admission fails. By default pins last through
    receipt construction; a caller-owned request may keep them through its
    downstream lifecycle. Pins are process-local to the supplied store.
    """
    empty = PreparationResult(PreparationStatus.INVALID_INPUT, "none", None, None, None, None, (), (), (), (), (), None)
    if execution_state_receipt is not None and not _valid_execution_state_receipt(execution_state_receipt):
        return replace(empty, reason="execution_state_receipt_invalid")
    source_order_limit = 2**63 - 1 - MAX_PATHS - 16
    if execution_state_receipt is not None:
        source_order_limit -= MAX_EXECUTION_STATE_FACTS + MAX_EXECUTION_STATE_EVIDENCE_REFS
    if (
        type(snapshot) is not SourceSnapshot or type(store) is not ArtifactStore
        or type(namespace_registry) is not NamespaceRegistry
        or type(paths) not in (tuple, list) or not 1 <= len(paths) <= MAX_PATHS
        or type(schema_lookups) not in (tuple, list) or len(schema_lookups) > MAX_SCHEMA_LOOKUPS
        or type(query) is not str or not query or len(query) > MAX_QUERY_CHARS
        or type(source_order_start) is not int or not 0 <= source_order_start <= source_order_limit
        or type(context_token_budget) is not int or not 1 <= context_token_budget <= MAX_CONTEXT_TOKENS
        or type(source_ingestion_token_limit) is not int
        or not context_token_budget <= source_ingestion_token_limit <= MAX_SOURCE_INGESTION_TOKENS
        or type(prompt_token_budget) is not int or not 1 <= prompt_token_budget <= MAX_PROMPT_TOKENS
        or type(max_candidates) is not int or not 1 <= max_candidates <= 16
        or type(context_position) is not int or not 0 <= context_position <= MAX_BASE_MESSAGES
        or type(message_format) is not str or message_format not in (
            "generic", "opencode-2.0.12", "opencode-2.0.15"
        )
        or type(use_symbol_span_for_required_path) is not bool
        or type(use_toml_key_spans_for_required_path) is not bool
        or type(use_toml_table_spans_for_required_path) is not bool
        or (use_toml_key_spans_for_required_path and use_toml_table_spans_for_required_path)
        or (
            toml_span_query is not None
            and (type(toml_span_query) is not str or not toml_span_query or len(toml_span_query) > MAX_QUERY_CHARS)
        )
    ):
        return empty
    if artifact_request is not None and (
        type(artifact_request) is not ArtifactRequest or not artifact_request.is_active_for(store)
    ):
        return replace(empty, reason="artifact_request_scope_invalid")
    owned_paths = _bounded_sequence(paths, MAX_PATHS)
    owned_schema_lookups = _bounded_sequence(schema_lookups, MAX_SCHEMA_LOOKUPS)
    owned_required_ids = _bounded_sequence(required_evidence_ids, MAX_REFERENCES)
    owned_preserve_ids = _bounded_sequence(preserve_evidence_ids, MAX_REFERENCES)
    owned_required_paths = _bounded_sequence(required_source_paths, MAX_PATHS)
    owned_preserve_paths = _bounded_sequence(preserve_source_paths, MAX_PATHS)
    if any(item is None for item in (owned_paths, owned_schema_lookups, owned_required_ids, owned_preserve_ids, owned_required_paths, owned_preserve_paths)):
        return empty
    paths = owned_paths
    schema_lookups = owned_schema_lookups
    required_evidence_ids = owned_required_ids
    preserve_evidence_ids = owned_preserve_ids
    required_source_paths = owned_required_paths
    preserve_source_paths = owned_preserve_paths
    symbol_targeted_query = query.startswith("symbol:")
    query_for_context = query
    if symbol_targeted_query:
        query_for_context = query[len("symbol:"):].strip()
        if not query_for_context or not query_for_context.isidentifier():
            return empty
    query_for_toml_spans = toml_span_query if toml_span_query is not None else query_for_context
    if any(type(path) is not str or not path or len(path) > 1024 for path in paths):
        return empty
    if len(set(paths)) != len(paths):
        return empty
    try:
        query.encode("utf-8")
        for path in paths:
            path.encode("utf-8")
    except UnicodeEncodeError:
        return empty
    if any(type(pair) is not tuple or len(pair) != 2 or any(type(item) is not str or not item or len(item) > 128 for item in pair) for pair in schema_lookups):
        return empty
    if len(set(schema_lookups)) != len(schema_lookups):
        return empty
    id_sequences = (required_evidence_ids, preserve_evidence_ids)
    if any(type(items) not in (tuple, list) or len(items) > MAX_REFERENCES for items in id_sequences):
        return empty
    if any(type(item) is not str or not item or len(item) > 256 for items in id_sequences for item in items):
        return empty
    path_sequences = (required_source_paths, preserve_source_paths)
    if any(type(items) not in (tuple, list) or len(items) > MAX_PATHS for items in path_sequences):
        return empty
    if any(type(item) is not str or not item or len(item) > 1024 for items in path_sequences for item in items):
        return empty
    if any(len(set(items)) != len(items) for items in id_sequences + path_sequences):
        return empty
    if not set(required_source_paths).issubset(paths) or not set(preserve_source_paths).issubset(paths):
        return empty

    execution_state_source_paths: dict[str, str] = {}
    original_snapshot = snapshot
    if execution_state_receipt is not None:
        namespace = _execution_state_source_namespace(snapshot)
        if namespace is None:
            return replace(
                empty, status=PreparationStatus.CONTEXT_FAILED,
                reason="execution_state_source_namespace_unavailable",
            )
        snapshot_sources_by_path = {source.path: source for source in snapshot.sources}
        state_source_paths: list[str] = []
        for fact in (execution_state_receipt.state.facts or {}).values():
            for ref in fact.evidence:
                if ref.source is not None:
                    if (
                        ref.source.source_namespace_sha256 != namespace
                        or stable_source_evidence_id(namespace, ref.source.source_path, ref.sha256)
                        != ref.evidence_id
                    ):
                        return replace(
                            empty, status=PreparationStatus.CONTEXT_FAILED,
                            reason="execution_state_source_namespace_mismatch",
                            execution_state_revision=execution_state_receipt.state.revision,
                            execution_state_sha256=execution_state_receipt.state.sha256,
                            execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                        )
                    path = ref.source.source_path
                else:
                    # Legacy state IDs can be resolved only against the exact
                    # snapshot that created them. New state uses stable refs.
                    legacy = next((
                        source for source in snapshot.sources
                        if source.sha256 == ref.sha256
                        and _evidence_id(snapshot.snapshot_sha256, source.path, source.sha256)
                        == ref.evidence_id
                    ), None)
                    if legacy is None:
                        return replace(
                            empty, status=PreparationStatus.CONTEXT_FAILED,
                            reason="execution_state_evidence_unavailable",
                            execution_state_revision=execution_state_receipt.state.revision,
                            execution_state_sha256=execution_state_receipt.state.sha256,
                            execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                        )
                    path = legacy.path
                execution_state_source_paths[ref.evidence_id] = path
                if path not in state_source_paths:
                    state_source_paths.append(path)

        effective_paths = tuple(dict.fromkeys((*paths, *state_source_paths)))
        if len(effective_paths) > MAX_PATHS + MAX_EXECUTION_STATE_EVIDENCE_REFS:
            return replace(
                empty, status=PreparationStatus.CONTEXT_FAILED,
                reason="execution_state_source_path_limit_exceeded",
                execution_state_revision=execution_state_receipt.state.revision,
                execution_state_sha256=execution_state_receipt.state.sha256,
                execution_state_event_sha256=execution_state_receipt.last_event_sha256,
            )
        missing_snapshot_paths = tuple(
            path for path in state_source_paths if path not in snapshot_sources_by_path
        )
        if missing_snapshot_paths:
            try:
                expanded_snapshot = create_snapshot(source_root, effective_paths)
            except (SnapshotAdmissionError, OSError, TypeError, ValueError):
                return replace(
                    empty, status=PreparationStatus.CONTEXT_FAILED,
                    reason="execution_state_evidence_unavailable",
                    execution_state_revision=execution_state_receipt.state.revision,
                    execution_state_sha256=execution_state_receipt.state.sha256,
                    execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                )
            if (
                expanded_snapshot.root_location_sha256 != original_snapshot.root_location_sha256
                or expanded_snapshot.root_identity != original_snapshot.root_identity
            ):
                return replace(
                    empty, status=PreparationStatus.CONTEXT_FAILED,
                    reason="execution_state_source_root_changed",
                    execution_state_revision=execution_state_receipt.state.revision,
                    execution_state_sha256=execution_state_receipt.state.sha256,
                    execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                )
            expanded_by_path = {source.path: source for source in expanded_snapshot.sources}
            if any(
                path not in snapshot_sources_by_path
                or path not in expanded_by_path
                or snapshot_sources_by_path[path].sha256 != expanded_by_path[path].sha256
                or snapshot_sources_by_path[path].size_bytes != expanded_by_path[path].size_bytes
                for path in paths
            ):
                return replace(
                    empty, status=PreparationStatus.CONTEXT_FAILED,
                    reason="source_snapshot_changed_during_state_reacquisition",
                    execution_state_revision=execution_state_receipt.state.revision,
                    execution_state_sha256=execution_state_receipt.state.sha256,
                    execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                )
            snapshot = expanded_snapshot
        paths = effective_paths

    if type(base_messages) not in (tuple, list) or not 1 <= len(base_messages) <= MAX_BASE_MESSAGES:
        return empty
    if context_position > len(base_messages) or any(
        type(message) is not dict
        or (message_format in ("opencode-2.0.12", "opencode-2.0.15") and not _is_opencode_message_shape(message))
        for message in base_messages
    ):
        return empty
    try:
        base_messages_owned = json.loads(_bounded_canonical_json(base_messages, MAX_BASE_MESSAGES_BYTES).decode("utf-8"))
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        return empty

    source_rows: list[SourceIdentity] = []
    misses: list[tuple[str, str]] = []
    valid_paths: list[str] = []
    source_text_by_path: dict[str, str] = {}
    # The ledger stores caller-selected bounded sources; the smaller active
    # assembly budget is applied later by assemble().
    ledger = ContextLedger(max_logical_tokens=source_ingestion_token_limit)
    schema_rows: list[tuple[str, str, str]] = []
    path_evidence: dict[str, str] = {}
    symbol_span_ids_by_path: dict[str, str] = {}
    toml_span_candidates_by_path: dict[str, tuple[object, ...]] = {}
    toml_span_ids_by_path: dict[str, tuple[str, ...]] = {}
    toml_span_candidates: list[object] = []
    selected: tuple[str, ...] = ()
    omitted: tuple[tuple[str, str], ...] = ()
    execution_state_segment_fields: dict[str, str] = {}
    execution_state_selected_fields: tuple[str, ...] = ()
    execution_state_omitted_fields: tuple[tuple[str, str], ...] = ()
    structural_status: str | None = None
    prompt_result = None
    aggregate_hash: str | None = None
    final_status = PreparationStatus.READY
    reason: str | None = None

    # One outer scope deliberately spans source admission through receipt build.
    request_scope = store.request() if artifact_request is None else nullcontext(artifact_request)
    measured_request_scope = _capture_pin_scope_duration(request_scope, _metrics)
    with measured_request_scope as request:
        seen: set[str] = set()
        admitted_source_bytes = 0
        for raw_path in paths:
            _metrics["exact_source_retrieval_attempts"] = int(_metrics["exact_source_retrieval_attempts"]) + 1
            retrieved = retrieve_exact(source_root, snapshot, raw_path)
            status_counts = _metrics["exact_source_retrieval_status_counts"]
            assert isinstance(status_counts, dict)
            status_counts[retrieved.status.value] = status_counts.get(retrieved.status.value, 0) + 1
            if type(retrieved.data) is bytes:
                _metrics["exact_source_returned_bytes"] = int(_metrics["exact_source_returned_bytes"]) + len(retrieved.data)
                if retrieved.status is RetrievalStatus.OK:
                    _metrics["exact_source_retrieval_successes"] = int(_metrics["exact_source_retrieval_successes"]) + 1
            path = retrieved.path or raw_path
            if path in seen:
                return PreparationResult(PreparationStatus.INVALID_INPUT, "none", None, None, None, None, tuple(source_rows), (), (), tuple(misses), (), None, "duplicate_normalized_path")
            seen.add(path)
            if retrieved.status is not RetrievalStatus.OK or type(retrieved.data) is not bytes:
                status = _retrieval_label(retrieved.status)
                evidence = "miss-" + _canonical_digest([snapshot.snapshot_sha256, path, status])
                misses.append((evidence, status))
                path_evidence[raw_path] = evidence
                source_rows.append(SourceIdentity(evidence, path, "", None, status))
                continue
            path = retrieved.path or ""
            raw = retrieved.data
            digest = _sha(raw)
            evidence_id = _evidence_id(snapshot.snapshot_sha256, path, digest)
            path_evidence[raw_path] = evidence_id
            if len(raw) > MAX_SOURCE_BYTES or admitted_source_bytes + len(raw) > MAX_AGGREGATE_SOURCE_BYTES:
                misses.append((evidence_id, "limit_exceeded"))
                source_rows.append(SourceIdentity(evidence_id, path, digest, None, "limit_exceeded"))
                continue
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                misses.append((evidence_id, "non_text"))
                source_rows.append(SourceIdentity(evidence_id, path, digest, None, "non_text"))
                continue
            try:
                _metrics["artifact_put_attempts"] = int(_metrics["artifact_put_attempts"]) + 1
                _metrics["artifact_put_input_bytes"] = int(_metrics["artifact_put_input_bytes"]) + len(raw)
                handle = store.put(snapshot_sha256=snapshot.snapshot_sha256, source_path=path, expected_content_sha256=digest, data=raw)
                _metrics["artifact_put_successes"] = int(_metrics["artifact_put_successes"]) + 1
                _metrics["artifact_put_success_bytes"] = int(_metrics["artifact_put_success_bytes"]) + len(raw)
                if (
                    handle.snapshot_sha256 != snapshot.snapshot_sha256 or handle.source_path != path
                    or handle.content_sha256 != digest or handle.size_bytes != len(raw)
                ):
                    raise ArtifactStoreError("artifact_handle_identity_mismatch")
                _metrics["artifact_pin_attempts"] = int(_metrics["artifact_pin_attempts"]) + 1
                pinned = request.pin(handle)
                if pinned.status is ArtifactReadStatus.OK:
                    _metrics["artifact_pin_successes"] = int(_metrics["artifact_pin_successes"]) + 1
                if type(pinned.data) is bytes:
                    _metrics["artifact_pin_bytes"] = int(_metrics["artifact_pin_bytes"]) + len(pinned.data)
                _metrics["artifact_read_attempts"] = int(_metrics["artifact_read_attempts"]) + 1
                roundtrip = request.read(handle)
                if roundtrip.status is ArtifactReadStatus.OK and type(roundtrip.data) is bytes:
                    _metrics["artifact_read_successes"] = int(_metrics["artifact_read_successes"]) + 1
                    _metrics["artifact_read_bytes"] = int(_metrics["artifact_read_bytes"]) + len(roundtrip.data)
                if (
                    pinned.status is not ArtifactReadStatus.OK or roundtrip.status is not ArtifactReadStatus.OK
                    or pinned.data != raw or roundtrip.data != raw or _sha(roundtrip.data or b"") != digest
                ):
                    raise ArtifactStoreError("artifact_roundtrip_mismatch")
            except (ArtifactStoreError, OSError, ValueError, ContextAdmissionError) as exc:
                failure_status = PreparationStatus.CONTEXT_FAILED if isinstance(exc, ContextAdmissionError) else PreparationStatus.STORE_FAILED
                return PreparationResult(failure_status, "none", None, None, None, None, tuple(source_rows), (), (), tuple(misses), (), None, type(exc).__name__)
            source_rows.append(SourceIdentity(evidence_id, path, digest, handle.handle_id, "ok"))
            valid_paths.append(path)
            source_text_by_path[path] = text
            admitted_source_bytes += len(raw)

        execution_state_evidence_ids: set[str] = set()
        execution_state_current_evidence_ids: dict[str, str] = {}
        if execution_state_receipt is not None:
            current_source_by_path = {
                row.path: row for row in source_rows if row.status == "ok"
            }
            namespace = _execution_state_source_namespace(snapshot)
            for fact in (execution_state_receipt.state.facts or {}).values():
                for ref in fact.evidence:
                    source_path = execution_state_source_paths.get(ref.evidence_id)
                    source = current_source_by_path.get(source_path or "")
                    valid_source = (
                        source is not None
                        and source.content_sha256 == ref.sha256
                        and (
                            (
                                ref.source is None
                                and _evidence_id(
                                    original_snapshot.snapshot_sha256,
                                    source_path or "",
                                    ref.sha256,
                                ) == ref.evidence_id
                            )
                            or (
                                ref.source is not None
                                and namespace is not None
                                and ref.source.source_namespace_sha256 == namespace
                                and stable_source_evidence_id(namespace, source_path or "", ref.sha256)
                                == ref.evidence_id
                            )
                        )
                    )
                    if not valid_source or source is None:
                        return PreparationResult(
                            PreparationStatus.CONTEXT_FAILED, "none", None, None, None, None,
                            tuple(source_rows), (), (), tuple(misses), (), None,
                            "execution_state_evidence_unavailable",
                            execution_state_revision=execution_state_receipt.state.revision,
                            execution_state_sha256=execution_state_receipt.state.sha256,
                            execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                        )
                    execution_state_evidence_ids.add(source.evidence_id)
                    execution_state_current_evidence_ids[ref.evidence_id] = source.evidence_id
            if len(execution_state_current_evidence_ids) > MAX_EXECUTION_STATE_EVIDENCE_REFS:
                return PreparationResult(
                    PreparationStatus.CONTEXT_FAILED, "none", None, None, None, None,
                    tuple(source_rows), (), (), tuple(misses), (), None,
                    "execution_state_evidence_reference_limit_exceeded",
                    execution_state_revision=execution_state_receipt.state.revision,
                    execution_state_sha256=execution_state_receipt.state.sha256,
                    execution_state_event_sha256=execution_state_receipt.last_event_sha256,
                )

        if not valid_paths:
            final_status = PreparationStatus.SOURCE_MISSES
            reason = "no_exact_text_sources"
        else:
            _metrics["structural_index_build_attempts"] = int(_metrics["structural_index_build_attempts"]) + 1
            indexed = build_snapshot_symbol_index(source_root, snapshot, valid_paths)
            structural_status = indexed.status.value
            _metrics["structural_index_status"] = structural_status
            _metrics["structural_index_exact_read_attempts"] = indexed.exact_read_attempts
            _metrics["structural_index_exact_read_successes"] = indexed.exact_read_successes
            _metrics["structural_index_exact_read_status_counts"] = dict(indexed.exact_read_status_counts)
            _metrics["structural_index_returned_bytes"] = indexed.exact_read_returned_bytes
            if indexed.status is not StructuralStatus.OK or indexed.index is None:
                final_status = PreparationStatus.STRUCTURE_FAILED
                reason = indexed.status.value
            else:
                _metrics["structural_index_file_count"] = len(indexed.index.files)
                _metrics["structural_index_symbol_count"] = indexed.index.symbol_count
                _metrics["structural_index_serialized_bytes"] = indexed.index.serialized_bytes
                _metrics["structural_index_query_attempts"] = int(_metrics["structural_index_query_attempts"]) + 1
                candidate_result = query_snapshot_symbols(indexed.index, query_for_context, limit=max_candidates)
                _metrics["structural_index_query_status"] = candidate_result.status.value
                _metrics["structural_index_candidate_count"] = len(candidate_result.candidates)
                if candidate_result.status not in (StructuralStatus.OK, StructuralStatus.NO_MATCHES):
                    final_status = PreparationStatus.STRUCTURE_FAILED
                    reason = candidate_result.status.value
                else:
                    # Candidate signatures are admitted only when every source identity matches.
                    source_by_path = {row.path: row for row in source_rows if row.status == "ok"}
                    if (
                        use_toml_key_spans_for_required_path
                        or use_toml_table_spans_for_required_path
                    ) and (not symbol_targeted_query or toml_span_query is not None):
                        from .snapshot_structure import StructuralCandidate

                        config_path_candidates: dict[str, tuple[object, ...]] = {}
                        for config_path in required_source_paths:
                            if config_path in preserve_source_paths or not config_path.lower().endswith(".toml"):
                                continue
                            source = source_by_path.get(config_path)
                            source_text = source_text_by_path.get(config_path)
                            if source is None or source_text is None:
                                continue
                            if use_toml_table_spans_for_required_path:
                                spans = extract_toml_table_spans(source_text, query_for_toml_spans)[:16]
                                parser_id = "tomllib-table-v1"
                                candidate_kind = "configuration_table"
                            else:
                                spans = extract_toml_key_spans(source_text, query_for_toml_spans)[:16]
                                parser_id = "tomllib-key-v1"
                                candidate_kind = "configuration_key"
                            if not spans:
                                continue
                            path_candidates = []
                            path_candidate_ids = []
                            for span in spans:
                                candidate = StructuralCandidate(
                                    name=span.name,
                                    kind=candidate_kind,
                                    path=config_path,
                                    start_line=span.start_line,
                                    end_line=span.end_line,
                                    signature=span.text,
                                    match_score=span.match_score,
                                    snapshot_sha256=snapshot.snapshot_sha256,
                                    source_sha256=source.content_sha256,
                                    parser=parser_id,
                                    language="toml",
                                )
                                candidate_id = "symbol-" + _canonical_digest([
                                    snapshot.snapshot_sha256,
                                    candidate.path,
                                    source.content_sha256,
                                    candidate.name,
                                    candidate.start_line,
                                    candidate.end_line,
                                ])
                                path_candidates.append(candidate)
                                path_candidate_ids.append(candidate_id)
                                toml_span_candidates.append(candidate)
                            config_path_candidates[config_path] = tuple(path_candidates)
                            toml_span_ids_by_path[config_path] = tuple(path_candidate_ids)
                        toml_span_candidates_by_path = config_path_candidates
                    requested_symbol_name = query_for_context
                    localized_candidate = None
                    if symbol_targeted_query:
                        exact_name_matches = tuple(
                            candidate for candidate in candidate_result.candidates
                            if candidate.name == requested_symbol_name
                        )
                        if len(exact_name_matches) == 1 and len(candidate_result.candidates) >= max_candidates:
                            final_status = PreparationStatus.STRUCTURE_FAILED
                            reason = "symbol_candidates_truncated"
                        elif len(exact_name_matches) != 1:
                            final_status = PreparationStatus.STRUCTURE_FAILED
                            reason = "symbol_name_ambiguous" if exact_name_matches else "symbol_name_missing"
                        else:
                            localized_candidate = exact_name_matches[0]
                            source = source_by_path.get(localized_candidate.path)
                            source_text = source_text_by_path.get(localized_candidate.path)
                            if (
                                source is None or source_text is None
                                or localized_candidate.snapshot_sha256 != snapshot.snapshot_sha256
                                or localized_candidate.source_sha256 != source.content_sha256
                            ):
                                final_status = PreparationStatus.STRUCTURE_FAILED
                                reason = "candidate_identity_mismatch"
                            else:
                                source_lines = source_text.splitlines(keepends=True)
                                if not (
                                    type(localized_candidate.start_line) is int
                                    and type(localized_candidate.end_line) is int
                                    and 1 <= localized_candidate.start_line
                                    <= localized_candidate.end_line <= len(source_lines)
                                ):
                                    final_status = PreparationStatus.STRUCTURE_FAILED
                                    reason = "symbol_span_unavailable"
                                else:
                                    localized_text = "".join(
                                        source_lines[localized_candidate.start_line - 1:localized_candidate.end_line]
                                    )
                                    if not localized_text or len(localized_text.encode("utf-8")) > MAX_SOURCE_BYTES:
                                        final_status = PreparationStatus.STRUCTURE_FAILED
                                        reason = "symbol_span_limit_exceeded"
                                    else:
                                        candidate_id = "symbol-" + _canonical_digest([
                                            snapshot.snapshot_sha256, localized_candidate.path,
                                            source.content_sha256, localized_candidate.name,
                                            localized_candidate.start_line, localized_candidate.end_line,
                                        ])
                                        symbol_span_ids_by_path[localized_candidate.path] = candidate_id
                                        try:
                                            ledger.add_segment(
                                                candidate_id, localized_text,
                                                source_order_start + len(paths),
                                                kind="symbol_source", retention="warm",
                                                metadata={
                                                    "snapshot_sha256": snapshot.snapshot_sha256,
                                                    "source_path": localized_candidate.path,
                                                    "content_sha256": source.content_sha256,
                                                    "artifact_handle_id": source.artifact_handle_id or "",
                                                    "symbol_name": localized_candidate.name,
                                                    "start_line": str(localized_candidate.start_line),
                                                    "end_line": str(localized_candidate.end_line),
                                                    "parser": localized_candidate.parser,
                                                    "language": localized_candidate.language,
                                                },
                                            )
                                        except ContextAdmissionError as exc:
                                            final_status = PreparationStatus.CONTEXT_FAILED
                                            reason = type(exc).__name__
                    else:
                        for source_index, source in enumerate(source_by_path.values()):
                            source_text = source_text_by_path.get(source.path)
                            if source_text is None:
                                final_status = PreparationStatus.STRUCTURE_FAILED
                                reason = "source_text_unavailable"
                                break
                            span_satisfies_required_path = (
                                source.path in toml_span_ids_by_path
                                and source.path in required_source_paths
                                and source.path not in preserve_source_paths
                                and source.evidence_id not in required_evidence_ids
                                and source.evidence_id not in preserve_evidence_ids
                                and source.evidence_id not in execution_state_evidence_ids
                            )
                            if span_satisfies_required_path:
                                continue
                            try:
                                ledger.add_segment(
                                    source.evidence_id, source_text,
                                    source_order_start + source_index,
                                    kind="source",
                                    retention="hot" if source.path in preserve_source_paths else "warm",
                                    metadata={
                                        "snapshot_sha256": snapshot.snapshot_sha256,
                                        "source_path": source.path,
                                        "content_sha256": source.content_sha256,
                                        "artifact_handle_id": source.artifact_handle_id or "",
                                    },
                                )
                            except ContextAdmissionError as exc:
                                final_status = PreparationStatus.CONTEXT_FAILED
                                reason = type(exc).__name__
                                break
                        if final_status is PreparationStatus.READY:
                            configuration_segment_order = 0
                            for config_path, candidate_rows in toml_span_candidates_by_path.items():
                                source = source_by_path[config_path]
                                source_is_preserved = (
                                    config_path in preserve_source_paths
                                    or source.evidence_id in required_evidence_ids
                                    or source.evidence_id in preserve_evidence_ids
                                    or source.evidence_id in execution_state_evidence_ids
                                )
                                if source_is_preserved:
                                    continue
                                for candidate in candidate_rows:
                                    candidate_id = "symbol-" + _canonical_digest([
                                        snapshot.snapshot_sha256,
                                        candidate.path,
                                        candidate.source_sha256,
                                        candidate.name,
                                        candidate.start_line,
                                        candidate.end_line,
                                    ])
                                    try:
                                        ledger.add_segment(
                                            candidate_id,
                                            candidate.signature,
                                            source_order_start + len(paths) + max_candidates + configuration_segment_order,
                                            kind=candidate.kind,
                                            retention="warm",
                                            metadata={
                                                "snapshot_sha256": snapshot.snapshot_sha256,
                                                "source_path": candidate.path,
                                                "content_sha256": candidate.source_sha256,
                                                "artifact_handle_id": source.artifact_handle_id or "",
                                                "table_name": candidate.name,
                                                "start_line": str(candidate.start_line),
                                                "end_line": str(candidate.end_line),
                                                "parser": candidate.parser,
                                                "language": candidate.language,
                                            },
                                        )
                                        configuration_segment_order += 1
                                    except ContextAdmissionError as exc:
                                        final_status = PreparationStatus.CONTEXT_FAILED
                                        reason = type(exc).__name__
                                        break
                                if final_status is not PreparationStatus.READY:
                                    break
                    if localized_candidate is not None and final_status is PreparationStatus.READY:
                        whole_file_ids = (
                            set(required_evidence_ids)
                            | set(preserve_evidence_ids)
                            | execution_state_evidence_ids
                        )
                        whole_file_paths = set(required_source_paths) | set(preserve_source_paths)
                        if use_symbol_span_for_required_path:
                            whole_file_paths.difference_update(
                                set(required_source_paths)
                                & set(symbol_span_ids_by_path)
                                - set(preserve_source_paths)
                            )
                        if use_toml_key_spans_for_required_path or use_toml_table_spans_for_required_path:
                            whole_file_paths.difference_update(
                                set(required_source_paths)
                                & set(toml_span_ids_by_path)
                                - set(preserve_source_paths)
                            )
                        required_sources = tuple(
                            source for source in source_by_path.values()
                            if source.path in whole_file_paths or source.evidence_id in whole_file_ids
                        )
                        for source_index, source in enumerate(required_sources):
                            source_text = source_text_by_path.get(source.path)
                            if source_text is None:
                                final_status = PreparationStatus.STRUCTURE_FAILED
                                reason = "source_text_unavailable"
                                break
                            try:
                                ledger.add_segment(
                                    source.evidence_id, source_text,
                                    source_order_start + len(paths) + max_candidates + source_index,
                                    kind="source",
                                    retention="hot" if source.path in preserve_source_paths else "warm",
                                    metadata={
                                        "snapshot_sha256": snapshot.snapshot_sha256,
                                        "source_path": source.path,
                                        "content_sha256": source.content_sha256,
                                        "artifact_handle_id": source.artifact_handle_id or "",
                                    },
                                )
                            except ContextAdmissionError as exc:
                                final_status = PreparationStatus.CONTEXT_FAILED
                                reason = type(exc).__name__
                                break
                        if final_status is PreparationStatus.READY:
                            configuration_segment_order = 0
                            for config_path, candidate_rows in toml_span_candidates_by_path.items():
                                source = source_by_path[config_path]
                                source_is_preserved = (
                                    config_path in preserve_source_paths
                                    or source.evidence_id in required_evidence_ids
                                    or source.evidence_id in preserve_evidence_ids
                                    or source.evidence_id in execution_state_evidence_ids
                                )
                                if source_is_preserved:
                                    continue
                                for candidate in candidate_rows:
                                    candidate_id = "symbol-" + _canonical_digest([
                                        snapshot.snapshot_sha256,
                                        candidate.path,
                                        candidate.source_sha256,
                                        candidate.name,
                                        candidate.start_line,
                                        candidate.end_line,
                                    ])
                                    try:
                                        ledger.add_segment(
                                            candidate_id,
                                            candidate.signature,
                                            source_order_start + len(paths) + max_candidates + configuration_segment_order,
                                            kind=candidate.kind,
                                            retention="warm",
                                            metadata={
                                                "snapshot_sha256": snapshot.snapshot_sha256,
                                                "source_path": candidate.path,
                                                "content_sha256": candidate.source_sha256,
                                                "artifact_handle_id": source.artifact_handle_id or "",
                                                "table_name": candidate.name,
                                                "start_line": str(candidate.start_line),
                                                "end_line": str(candidate.end_line),
                                                "parser": candidate.parser,
                                                "language": candidate.language,
                                            },
                                        )
                                        configuration_segment_order += 1
                                    except ContextAdmissionError as exc:
                                        final_status = PreparationStatus.CONTEXT_FAILED
                                        reason = type(exc).__name__
                                        break
                                if final_status is not PreparationStatus.READY:
                                    break
                    for index, candidate in enumerate(candidate_result.candidates):
                        if localized_candidate is candidate:
                            continue
                        if final_status is not PreparationStatus.READY:
                            break
                        source = source_by_path.get(candidate.path)
                        if (
                            source is None or candidate.snapshot_sha256 != snapshot.snapshot_sha256
                            or candidate.source_sha256 != source.content_sha256
                        ):
                            final_status = PreparationStatus.STRUCTURE_FAILED
                            reason = "candidate_identity_mismatch"
                            break
                        candidate_id = "symbol-" + _canonical_digest([snapshot.snapshot_sha256, candidate.path, source.content_sha256, candidate.name, candidate.start_line, candidate.end_line])
                        try:
                            ledger.add_segment(candidate_id, candidate.signature, source_order_start + len(paths) + index, kind="structural_signature", retention="warm", metadata={"snapshot_sha256": snapshot.snapshot_sha256, "source_path": candidate.path, "content_sha256": source.content_sha256, "artifact_handle_id": source.artifact_handle_id or ""})
                        except ContextAdmissionError as exc:
                            final_status = PreparationStatus.CONTEXT_FAILED
                            reason = type(exc).__name__
                            break
                    if final_status is PreparationStatus.READY and execution_state_receipt is not None:
                        state = execution_state_receipt.state
                        for index, (field_name, fact) in enumerate(sorted((state.facts or {}).items())):
                            evidence_ids = tuple(dict.fromkeys(
                                execution_state_current_evidence_ids[ref.evidence_id]
                                for ref in fact.evidence
                            ))
                            segment_id = "state-" + _canonical_digest(
                                [state.sha256, field_name, list(evidence_ids)]
                            )
                            try:
                                ledger.add_summary(
                                    segment_id,
                                    _execution_state_fact_text(
                                        state, field_name, fact,
                                        execution_state_current_evidence_ids,
                                    ),
                                    source_order_start + MAX_PATHS + 16 + index,
                                    summary_of=evidence_ids,
                                    level="execution_state_fact",
                                    retention="warm",
                                    metadata={
                                        "state_sha256": state.sha256,
                                        "state_event_sha256": execution_state_receipt.last_event_sha256,
                                        "state_revision": str(state.revision),
                                        "state_field": field_name,
                                    },
                                )
                                execution_state_segment_fields[segment_id] = field_name
                            except (ContextAdmissionError, TypeError, ValueError, OverflowError, UnicodeError) as exc:
                                final_status = PreparationStatus.CONTEXT_FAILED
                                reason = "execution_state_context_" + type(exc).__name__
                                break
                    if final_status is PreparationStatus.READY:
                        # Deferred schemas become inert message data and are hashed by the prompt gate.
                        messages = base_messages_owned
                        # Discovery is descriptive metadata only. It is deliberately
                        # not transformed into capabilities or executable handlers.
                        _metrics["schema_discover_attempts"] = int(_metrics["schema_discover_attempts"]) + 1
                        discovered = namespace_registry.discover()
                        _metrics["schema_discover_results"] = len(discovered)
                        discovered_namespace_ids = [item.namespace_id for item in discovered]
                        schema_data: list[dict[str, object]] = []
                        for namespace_id, operation_id in schema_lookups:
                            _metrics["schema_lookup_attempts"] = int(_metrics["schema_lookup_attempts"]) + 1
                            lookup = namespace_registry.lookup(namespace_id, operation_id)
                            lookup_counts = _metrics["schema_lookup_status_counts"]
                            assert isinstance(lookup_counts, dict)
                            lookup_counts[lookup.status.value] = lookup_counts.get(lookup.status.value, 0) + 1
                            if lookup.status is not SchemaLookupStatus.OK or lookup.schema is None or lookup.sha256 is None:
                                final_status = PreparationStatus.SCHEMA_FAILED
                                reason = lookup.status.value
                                break
                            try:
                                plain_schema = _plain_schema(lookup.schema)
                            except (ValueError, TypeError, RecursionError) as exc:
                                final_status = PreparationStatus.SCHEMA_FAILED
                                reason = type(exc).__name__
                                break
                            schema_data.append({"namespace_id": namespace_id, "operation_id": operation_id, "schema_sha256": lookup.sha256, "schema": plain_schema})
                            schema_rows.append((namespace_id, operation_id, lookup.sha256))
                        if final_status is PreparationStatus.READY:
                            if schema_data:
                                schema_blob = json.dumps(schema_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                                if len(messages) >= MAX_BASE_MESSAGES:
                                    final_status = PreparationStatus.SCHEMA_FAILED
                                    reason = "base_message_count_limit_exceeded"
                                else:
                                    schema_context = "Deferred operation schemas (inert data): " + schema_blob
                                    if message_format in ("opencode-2.0.12", "opencode-2.0.15"):
                                        schema_message = {"role": "user", "content": [{"type": "text", "text": schema_context}]}
                                    else:
                                        schema_message = {"role": "user", "content": schema_context}
                                    messages.insert(context_position, schema_message)
                                    context_position += 1
                        if final_status is PreparationStatus.READY:
                            available_source_ids = {
                                row.evidence_id for row in source_rows if row.status == "ok"
                            }
                            required_path_id_rows: list[str] = []
                            for path in required_source_paths:
                                if path not in path_evidence:
                                    continue
                                if (
                                    (use_toml_key_spans_for_required_path or use_toml_table_spans_for_required_path)
                                    and path in toml_span_candidates_by_path
                                    and path not in preserve_source_paths
                                    and path_evidence[path] not in required_evidence_ids
                                    and path_evidence[path] not in preserve_evidence_ids
                                    and path_evidence[path] not in execution_state_evidence_ids
                                ):
                                    candidates_for_path = toml_span_candidates_by_path[path]
                                    ids_for_path = toml_span_ids_by_path[path]
                                    required_path_id_rows.extend(ids_for_path)
                                elif (
                                    use_symbol_span_for_required_path
                                    and path in symbol_span_ids_by_path
                                    and path not in preserve_source_paths
                                ):
                                    required_path_id_rows.append(symbol_span_ids_by_path[path])
                                elif path_evidence[path] in available_source_ids:
                                    required_path_id_rows.append(path_evidence[path])
                            required_path_ids = tuple(dict.fromkeys(required_path_id_rows))
                            preserved_path_ids = tuple(
                                path_evidence[path] for path in preserve_source_paths
                                if path in path_evidence and path_evidence[path] in available_source_ids
                            )
                            # Required evidence must compete before optional retrieval
                            # candidates consume the active context budget. The final
                            # prompt gate remains authoritative and rejects overflow.
                            preserve_ids = tuple(dict.fromkeys((
                                *required_evidence_ids,
                                *required_path_ids,
                                *preserve_evidence_ids,
                                *preserved_path_ids,
                            )))
                            required_ids = tuple(dict.fromkeys((
                                *required_evidence_ids,
                                *required_path_ids,
                                *preserve_ids,
                            )))
                            if len(required_ids) > MAX_REFERENCES:
                                final_status = PreparationStatus.INVALID_INPUT
                                reason = "required_evidence_limit_exceeded"
                            elif any(
                                item not in {row.evidence_id for row in source_rows if row.status == "ok"}
                                and item not in {
                                    "symbol-" + _canonical_digest([
                                        snapshot.snapshot_sha256, candidate.path, candidate.source_sha256,
                                        candidate.name, candidate.start_line, candidate.end_line,
                                    ])
                                    for candidate in (
                                        *((candidate_result.candidates) if candidate_result.status is StructuralStatus.OK else ()),
                                        *toml_span_candidates,
                                    )
                                }
                                for item in preserve_ids
                            ):
                                final_status = PreparationStatus.CONTEXT_FAILED
                                reason = "preserved_evidence_unknown"
                        if final_status is PreparationStatus.READY:
                            try:
                                _metrics["ledger_assembly_attempts"] = int(_metrics["ledger_assembly_attempts"]) + 1
                                assembly = ledger.assemble(query_for_context, active_token_budget=context_token_budget, preserve_ids=preserve_ids, on_preserved_overflow="omit", search_limit=32, receipt_detail="full", include_selected_texts=context_render_mode == "compact_json_segments")
                                selected_segment_ids = {
                                    row["segment_id"] for row in assembly.get("selected_segments", ())
                                    if type(row) is dict and type(row.get("segment_id")) is str
                                }
                                omitted_segment_reasons = {
                                    row["segment_id"]: row["reason"]
                                    for row in assembly.get("omitted_segments", ())
                                    if type(row) is dict
                                    and type(row.get("segment_id")) is str
                                    and type(row.get("reason")) is str
                                }
                                execution_state_selected_fields = tuple(sorted(
                                    field_name for segment_id, field_name in execution_state_segment_fields.items()
                                    if segment_id in selected_segment_ids
                                ))
                                execution_state_omitted_fields = tuple(sorted(
                                    (field_name, omitted_segment_reasons[segment_id])
                                    for segment_id, field_name in execution_state_segment_fields.items()
                                    if segment_id in omitted_segment_reasons
                                ))
                                _metrics["ledger_selected_count"] = len(assembly.get("selected_segments", ()))
                                _metrics["ledger_omitted_count"] = int(assembly.get("omitted_segment_count", 0))
                                _metrics["ledger_logical_token_count"] = assembly.get("logical_token_count")
                                _metrics["ledger_selected_token_count"] = assembly.get("selected_token_count")
                                _metrics["ledger_retrieval_candidate_count"] = len(assembly.get("retrieval_candidate_ids", ()))
                                _metrics["ledger_retrieval_truncated"] = assembly.get("retrieval_truncated")
                                _metrics["ledger_search_limit"] = assembly.get("search_limit")
                                _metrics["ledger_token_count_mode"] = assembly.get("token_count_mode")
                                _metrics["ledger_token_counter_name"] = assembly.get("token_counter_name")

                                def measured_serializer(value):
                                    _metrics["serializer_callback_attempts"] = int(_metrics["serializer_callback_attempts"]) + 1
                                    return serializer(value)

                                def measured_tokenizer(value):
                                    _metrics["tokenizer_callback_attempts"] = int(_metrics["tokenizer_callback_attempts"]) + 1
                                    return tokenizer_counter(value)

                                prompt_result = compile_prompt(assembly, messages, context_position=context_position, message_format=message_format, context_render_mode=context_render_mode, serializer=measured_serializer, tokenizer_counter=measured_tokenizer, serializer_id=serializer_id, tokenizer_id=tokenizer_id, hard_budget=prompt_token_budget, required_evidence_ids=required_ids)
                            except (ContextSelectionError, ContextAdmissionError, TypeError, ValueError, OverflowError, UnicodeError) as exc:
                                return PreparationResult(PreparationStatus.CONTEXT_FAILED, "none", None, None, None, None, tuple(source_rows), (), (), tuple(misses), tuple(schema_rows), structural_status, type(exc).__name__)
                            if prompt_result.receipt.serialized_bytes is not None:
                                _metrics["prompt_serialized_bytes"] = prompt_result.receipt.serialized_bytes
                            if prompt_result.receipt.exact_token_count is not None:
                                _metrics["prompt_token_count"] = prompt_result.receipt.exact_token_count
                            selected = prompt_result.receipt.selected_evidence_ids
                            omitted = prompt_result.receipt.omitted_evidence
                            miss_rows = list(misses)
                            miss_rows.extend((row.evidence_id, row.status) for row in source_rows if row.status == "non_text")
                            receipt_omitted = list(omitted)
                            omitted_ids = {item[0] for item in receipt_omitted}
                            for miss_id, miss_status in miss_rows:
                                if miss_id not in omitted_ids:
                                    receipt_omitted.append((miss_id, miss_status))
                                    omitted_ids.add(miss_id)
                            # Non-text is an explicit facade omission, while the shared
                            # receipt's retrieval_misses enum intentionally excludes it.
                            for row in source_rows:
                                if row.status == "non_text" and row.evidence_id not in omitted_ids:
                                    receipt_omitted.append((row.evidence_id, "non_text"))
                                    omitted_ids.add(row.evidence_id)
                            receipt_misses = [(evidence_id, status) for evidence_id, status in miss_rows if status in {"missing", "stale", "unsafe", "unknown_snapshot", "unknown_source", "evicted"}]
                            # Import lazily: the helper's public SourceIdentity
                            # type is declared in this module. These validated
                            # source and candidate rows are the only lineage
                            # inputs used; no ledger internals are inspected.
                            from .selected_segment_sources import (
                                SelectedSourceReferenceError,
                                build_selected_segment_source_references,
                            )
                            try:
                                selected_source_references = build_selected_segment_source_references(
                                    snapshot_sha256=snapshot.snapshot_sha256,
                                    selected_segment_ids=selected,
                                    sources=tuple(source_rows),
                                    candidates=(
                                        tuple(candidate_result.candidates if candidate_result.status is StructuralStatus.OK else ())
                                        + tuple(toml_span_candidates)
                                    ),
                                    selected_segments=assembly["selected_segments"],
                                )
                            except (SelectedSourceReferenceError, TypeError, ValueError, OverflowError) as exc:
                                return PreparationResult(
                                    PreparationStatus.RECEIPT_FAILED, "none", None,
                                    prompt_result.receipt, None, None, tuple(source_rows),
                                    selected, tuple(receipt_omitted), tuple(miss_rows),
                                    tuple(schema_rows), structural_status,
                                    "selected_source_references_" + type(exc).__name__,
                                )

                            unavailable_reasons = tuple(
                                (str(row["segment_id"]), reason)
                                for row in selected_source_references.references
                                for reason in (
                                    ("source_or_symbol_lineage_unavailable",)
                                    if row["segment_kind"] == "unresolved"
                                    else ()
                                ) + (
                                    ("summary_lineage_not_exposed_by_preparation",)
                                    if row["summary_lineage_status"] == "unavailable"
                                    else ()
                                )
                            )
                            aggregate_payload = {
                                "schema": "wrench.e0-preparation-refs.v2", "snapshot_sha256": snapshot.snapshot_sha256,
                                "source_ingestion_token_limit": source_ingestion_token_limit,
                                "sources": [[r.evidence_id, r.path, r.content_sha256, r.artifact_handle_id, r.status] for r in source_rows],
                                "selected": list(selected), "omitted": [list(row) for row in receipt_omitted], "misses": [list(row) for row in miss_rows],
                                "selected_source_references_sha256": selected_source_references.receipt_sha256,
                                "selected_source_reference_unavailable_reasons": [list(row) for row in unavailable_reasons],
                                "assembly_session_hash": assembly.get("session_hash"),
                                "context_message_sha256": prompt_result.receipt.context_message_sha256,
                                "context_insertion_position": prompt_result.receipt.context_insertion_position,
                                "schemas": [list(row) for row in schema_rows],
                                "discovered_namespace_ids": discovered_namespace_ids,
                                "prompt_gate": {"status": prompt_result.receipt.status.value, "prompt_sha256": prompt_result.receipt.prompt_sha256,
                                    "exact_token_count": prompt_result.receipt.exact_token_count, "budget": prompt_result.receipt.hard_budget,
                                    "serializer_id": prompt_result.receipt.serializer_id, "tokenizer_id": prompt_result.receipt.tokenizer_id},
                            }
                            if execution_state_receipt is not None:
                                aggregate_payload["execution_state"] = {
                                    "revision": execution_state_receipt.state.revision,
                                    "state_sha256": execution_state_receipt.state.sha256,
                                    "last_event_sha256": execution_state_receipt.last_event_sha256,
                                    "selected_fields": list(execution_state_selected_fields),
                                    "omitted_fields": [list(row) for row in execution_state_omitted_fields],
                                    "source_refs_revalidated": True,
                                }
                            aggregate_hash = _canonical_digest(aggregate_payload)
                            _metrics["outcome_receipt_build_attempts"] = int(_metrics["outcome_receipt_build_attempts"]) + 1
                            receipt_result = build_outcome_receipt(_receipt_payload(snapshot_hash=snapshot.snapshot_sha256, aggregate_hash=aggregate_hash, selected=selected, omitted=receipt_omitted, misses=receipt_misses))
                            _metrics["outcome_receipt_status"] = receipt_result.status.value
                            if receipt_result.status not in (ReceiptStatus.VALID, ReceiptStatus.INCOMPLETE):
                                final_status = PreparationStatus.RECEIPT_FAILED
                                reason = ";".join(receipt_result.errors[:4])
                            elif prompt_result.receipt.status is not PromptGateStatus.READY:
                                final_status = PreparationStatus.PROMPT_REJECTED
                                reason = prompt_result.receipt.status.value
                            elif misses:
                                final_status = PreparationStatus.SOURCE_MISSES
                                reason = "some_sources_missed"
                            return PreparationResult(
                                final_status, "none",
                                prompt_result.prompt if prompt_result.receipt.status is PromptGateStatus.READY else None,
                                prompt_result.receipt, receipt_result, aggregate_hash,
                                tuple(source_rows), selected, tuple(receipt_omitted),
                                tuple(miss_rows), tuple(schema_rows), structural_status, reason,
                                selected_source_references=selected_source_references,
                                selected_source_reference_unavailable_reasons=unavailable_reasons,
                                context_message_json=(
                                    prompt_result.context_message_json
                                    if final_status is PreparationStatus.READY
                                    else None
                                ),
                                execution_state_revision=(
                                    execution_state_receipt.state.revision
                                    if execution_state_receipt is not None else None
                                ),
                                execution_state_sha256=(
                                    execution_state_receipt.state.sha256
                                    if execution_state_receipt is not None else None
                                ),
                                execution_state_event_sha256=(
                                    execution_state_receipt.last_event_sha256
                                    if execution_state_receipt is not None else None
                                ),
                                execution_state_selected_fields=execution_state_selected_fields,
                                execution_state_omitted_fields=execution_state_omitted_fields,
                                execution_state_evidence_verified_for_prompt=(
                                    final_status is PreparationStatus.READY
                                    if execution_state_receipt is not None else None
                                ),
                            )

    # Even a fully stale/missing request gets a reference-only incomplete
    # receipt. No content object or prompt is created for retrieval misses.
    if final_status is PreparationStatus.SOURCE_MISSES and snapshot.snapshot_sha256:
        miss_omitted = tuple((row.evidence_id, row.status) for row in source_rows)
        receipt_misses = tuple((evidence_id, status) for evidence_id, status in misses if status in {"missing", "stale", "unsafe", "unknown_snapshot", "unknown_source", "evicted"})
        aggregate_hash = _canonical_digest({
            "schema": "wrench.e0-preparation-refs.v2", "snapshot_sha256": snapshot.snapshot_sha256,
            "sources": [[r.evidence_id, r.path, r.content_sha256, r.artifact_handle_id, r.status] for r in source_rows],
            "selected": [], "omitted": [list(row) for row in miss_omitted], "misses": [list(row) for row in misses],
            "context_message_sha256": None, "context_insertion_position": None,
            "schemas": [], "prompt_gate": None,
        })
        _metrics["outcome_receipt_build_attempts"] = int(_metrics["outcome_receipt_build_attempts"]) + 1
        receipt_result = build_outcome_receipt(_receipt_payload(
            snapshot_hash=snapshot.snapshot_sha256, aggregate_hash=aggregate_hash,
            selected=(), omitted=miss_omitted, misses=receipt_misses,
        ))
        _metrics["outcome_receipt_status"] = receipt_result.status.value
        return PreparationResult(final_status, "none", None, None, receipt_result, aggregate_hash, tuple(source_rows), (), miss_omitted, tuple(misses), (), structural_status, reason)
    return PreparationResult(final_status, "none", None, None, None, None, tuple(source_rows), selected, omitted, tuple(misses), tuple(schema_rows), structural_status, reason)


def prepare_e0_context(
    *, source_root: str | os.PathLike[str] | SourceRootBinding, snapshot: SourceSnapshot,
    paths: Sequence[str | os.PathLike[str]], store: ArtifactStore, query: str,
    source_order_start: int, context_token_budget: int, prompt_token_budget: int,
    source_ingestion_token_limit: int = MAX_CONTEXT_TOKENS,
    namespace_registry: NamespaceRegistry, schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]], context_position: int,
    message_format: str = "generic",
    context_render_mode: str = "legacy_json_string",
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int], serializer_id: str,
    tokenizer_id: str, required_evidence_ids: Sequence[str] = (),
    preserve_evidence_ids: Sequence[str] = (), required_source_paths: Sequence[str] = (),
    preserve_source_paths: Sequence[str] = (), use_symbol_span_for_required_path: bool = False,
    use_toml_key_spans_for_required_path: bool = False,
    use_toml_table_spans_for_required_path: bool = False,
    toml_span_query: str | None = None,
    max_candidates: int = 8,
    artifact_request: ArtifactRequest | None = None,
    execution_state_receipt: StateStoreLoadReceipt | None = None,
) -> PreparationResult:
    """Prepare local context and attach non-identifying preparation metrics.

    The default scope is preparation-only and closes before return. To retain
    source pins during a downstream request, pass an already active
    ``ArtifactRequest`` and keep its surrounding ``with store.request()`` open
    until that request succeeds, fails, times out, or is cancelled. This
    facade never dispatches or observes downstream activity. A host-loaded
    execution-state receipt may add evidence-linked state summaries to the
    same bounded ledger; every cited state source must also be among the exact
    sources prepared for this request. Source ingestion has its own hard-capped
    logical-token limit; by default it remains equal to the historical 8,192
    token limit. Raising it does not raise the selected-context or prompt cap.
    """
    started_ns = time.perf_counter_ns()
    counters: dict[str, object] = {
        "caller_path_count": len(paths) if type(paths) in (tuple, list) else None,
        "exact_source_retrieval_attempts": 0, "exact_source_retrieval_successes": 0,
        "exact_source_retrieval_status_counts": {}, "exact_source_returned_bytes": 0,
        "structural_index_exact_read_attempts": 0, "structural_index_exact_read_successes": 0,
        "structural_index_exact_read_status_counts": {}, "structural_index_returned_bytes": 0,
        "structural_index_build_attempts": 0,
        "structural_index_status": None, "structural_index_query_attempts": 0,
        "structural_index_query_status": None, "structural_index_candidate_count": None,
        "artifact_put_attempts": 0, "artifact_put_successes": 0,
        "artifact_put_input_bytes": 0, "artifact_put_success_bytes": 0,
        "artifact_pin_attempts": 0, "artifact_pin_successes": 0, "artifact_pin_bytes": 0, "artifact_read_attempts": 0,
        "artifact_pin_scope_duration_ns": None,
        "artifact_read_successes": 0, "artifact_read_bytes": 0,
        "schema_discover_attempts": 0, "schema_discover_results": None,
        "schema_lookup_attempts": 0, "schema_lookup_status_counts": {},
        "ledger_assembly_attempts": 0, "ledger_selected_count": None, "ledger_omitted_count": None,
        "serializer_callback_attempts": 0, "tokenizer_callback_attempts": 0,
        "prompt_serialized_bytes": None, "prompt_token_count": None,
        "outcome_receipt_build_attempts": 0, "outcome_receipt_status": None,
        "ledger_logical_token_count": None, "ledger_selected_token_count": None,
        "ledger_retrieval_candidate_count": None, "ledger_retrieval_truncated": None,
        "ledger_search_limit": None, "ledger_token_count_mode": None, "ledger_token_counter_name": None,
        "structural_index_file_count": None, "structural_index_symbol_count": None,
        "structural_index_serialized_bytes": None,
    }
    result = _prepare_e0_context_impl(
        source_root=source_root, snapshot=snapshot, paths=paths, store=store, query=query,
        source_order_start=source_order_start, context_token_budget=context_token_budget,
        prompt_token_budget=prompt_token_budget,
        source_ingestion_token_limit=source_ingestion_token_limit,
        namespace_registry=namespace_registry,
        schema_lookups=schema_lookups, base_messages=base_messages, context_position=context_position,
        message_format=message_format,
        context_render_mode=context_render_mode,
        serializer=serializer, tokenizer_counter=tokenizer_counter, serializer_id=serializer_id,
        tokenizer_id=tokenizer_id, required_evidence_ids=required_evidence_ids,
        preserve_evidence_ids=preserve_evidence_ids, required_source_paths=required_source_paths,
        preserve_source_paths=preserve_source_paths,
        use_symbol_span_for_required_path=use_symbol_span_for_required_path,
        use_toml_key_spans_for_required_path=use_toml_key_spans_for_required_path,
        use_toml_table_spans_for_required_path=use_toml_table_spans_for_required_path,
        toml_span_query=toml_span_query,
        max_candidates=max_candidates,
        artifact_request=artifact_request, execution_state_receipt=execution_state_receipt,
        _metrics=counters,
    )
    elapsed = max(0, time.perf_counter_ns() - started_ns)
    metrics = PreparationMetrics(
        elapsed_wall_ns=elapsed, caller_path_count=counters["caller_path_count"],
        exact_source_retrieval_attempts=int(counters["exact_source_retrieval_attempts"]),
        exact_source_retrieval_successes=int(counters["exact_source_retrieval_successes"]),
        exact_source_retrieval_status_counts=tuple(sorted(counters["exact_source_retrieval_status_counts"].items())),
        exact_source_returned_bytes=int(counters["exact_source_returned_bytes"]),
        source_exact_read_total_attempts=int(counters["exact_source_retrieval_attempts"]) + int(counters["structural_index_exact_read_attempts"]),
        source_exact_read_total_successes=int(counters["exact_source_retrieval_successes"]) + int(counters["structural_index_exact_read_successes"]),
        source_exact_read_total_returned_bytes=int(counters["exact_source_returned_bytes"]) + int(counters["structural_index_returned_bytes"]),
        structural_index_build_attempts=int(counters["structural_index_build_attempts"]),
        structural_index_status=counters["structural_index_status"],
        structural_index_exact_read_attempts=int(counters["structural_index_exact_read_attempts"]),
        structural_index_exact_read_successes=int(counters["structural_index_exact_read_successes"]),
        structural_index_exact_read_status_counts=tuple(sorted(counters["structural_index_exact_read_status_counts"].items())),
        structural_index_returned_bytes=int(counters["structural_index_returned_bytes"]),
        structural_index_query_attempts=int(counters["structural_index_query_attempts"]),
        structural_index_query_status=counters["structural_index_query_status"],
        structural_index_candidate_count=counters["structural_index_candidate_count"],
        artifact_put_attempts=int(counters["artifact_put_attempts"]), artifact_put_successes=int(counters["artifact_put_successes"]),
        artifact_put_input_bytes=int(counters["artifact_put_input_bytes"]),
        artifact_put_success_bytes=int(counters["artifact_put_success_bytes"]),
        artifact_pin_attempts=int(counters["artifact_pin_attempts"]),
        artifact_pin_successes=int(counters["artifact_pin_successes"]), artifact_pin_bytes=int(counters["artifact_pin_bytes"]),
        artifact_pin_scope_duration_ns=counters["artifact_pin_scope_duration_ns"],
        artifact_read_attempts=int(counters["artifact_read_attempts"]),
        artifact_read_successes=int(counters["artifact_read_successes"]), artifact_read_bytes=int(counters["artifact_read_bytes"]),
        schema_discover_attempts=int(counters["schema_discover_attempts"]), schema_discover_results=counters["schema_discover_results"],
        schema_lookup_attempts=int(counters["schema_lookup_attempts"]),
        schema_lookup_status_counts=tuple(sorted(counters["schema_lookup_status_counts"].items())),
        ledger_assembly_attempts=int(counters["ledger_assembly_attempts"]), ledger_selected_count=counters["ledger_selected_count"],
        ledger_omitted_count=counters["ledger_omitted_count"],
        serializer_callback_attempts=int(counters["serializer_callback_attempts"]),
        tokenizer_callback_attempts=int(counters["tokenizer_callback_attempts"]),
        prompt_serialized_bytes=counters["prompt_serialized_bytes"], prompt_token_count=counters["prompt_token_count"],
        outcome_receipt_build_attempts=int(counters["outcome_receipt_build_attempts"]),
        outcome_receipt_status=counters["outcome_receipt_status"],
        facade_model_call_sites=0, facade_provider_call_sites=0,
        facade_verifier_call_sites=0, facade_tool_call_sites=0,
        callback_external_activity=None, process_cpu_ns=None, process_rss_bytes=None,
        energy_joules=None, os_cache_bytes=None, request_page_faults=None,
        unmeasured_dimensions=("callback_external_activity", "process_cpu", "process_rss", "energy", "os_cache", "request_page_faults"),
        ledger_logical_token_count=counters["ledger_logical_token_count"],
        ledger_selected_token_count=counters["ledger_selected_token_count"],
        ledger_retrieval_candidate_count=counters["ledger_retrieval_candidate_count"],
        ledger_retrieval_truncated=counters["ledger_retrieval_truncated"],
        ledger_search_limit=counters["ledger_search_limit"],
        ledger_token_count_mode=counters["ledger_token_count_mode"],
        ledger_token_counter_name=counters["ledger_token_counter_name"],
        structural_index_file_count=counters["structural_index_file_count"],
        structural_index_symbol_count=counters["structural_index_symbol_count"],
        structural_index_serialized_bytes=counters["structural_index_serialized_bytes"],
    )
    result = replace(
        result,
        metrics=metrics,
        accounting_receipt=_accounting_receipt(result.aggregate_sha256, metrics),
    )
    return result


__all__ = [
    "MAX_SOURCE_INGESTION_TOKENS",
    "MAX_PATHS",
    "MAX_SCHEMA_LOOKUPS",
    "PreparationAccountingReceipt",
    "PreparationResult",
    "PreparationStatus",
    "SourceIdentity",
    "prepare_e0_context",
    "verify_preparation_accounting_receipt",
]
