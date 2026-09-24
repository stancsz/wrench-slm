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
from contextlib import nullcontext
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .artifact_store import ArtifactHandle, ArtifactReadStatus, ArtifactRequest, ArtifactStore, ArtifactStoreError
from .context import ContextAdmissionError, ContextLedger, ContextSelectionError
from .namespace_registry import NamespaceRegistry, SchemaLookupStatus
from .outcome_receipt import ReceiptResult, ReceiptStatus, build_outcome_receipt
from .prompt_compiler import (
    MAX_BASE_MESSAGES, MAX_BASE_MESSAGES_BYTES, PromptGateReceipt,
    PromptGateStatus, _bounded_canonical_json, compile_prompt,
)
from .snapshot import RetrievalStatus, SourceRootBinding, SourceSnapshot, retrieve_exact
from .snapshot_structure import (
    StructuralStatus, build_snapshot_symbol_index, query_snapshot_symbols,
)


MAX_PATHS = 16
MAX_SCHEMA_LOOKUPS = 4
MAX_SOURCE_BYTES = 64 * 1024
MAX_AGGREGATE_SOURCE_BYTES = 512 * 1024
MAX_REFERENCES = 256
MAX_RECEIPT_REFERENCE_BYTES = 64 * 1024
MAX_QUERY_CHARS = 256
MAX_CONTEXT_TOKENS = 8192
MAX_PROMPT_TOKENS = 8192
PREPARATION_ACCOUNTING_SCHEMA = "wrench.e0.preparation-accounting.v1"
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


@dataclass(frozen=True)
class PreparationAccountingReceipt:
    """Canonical companion for stable facade counters, joined by preparation hash.

    This does not account for time, resource use, or arbitrary callback effects.
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
    """Bind deterministic facade counters to the content receipt they describe.

    Elapsed time is deliberately excluded because it is nondeterministic. The
    explicit unmeasured values remain in the payload as null, distinct from a
    measured zero.
    """
    if aggregate_sha256 is None:
        return None
    # Keep the v1 projection explicit. New PreparationMetrics fields do not
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
    """Validate v1 JSON value types, preserving null versus measured zero."""
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
    namespace_registry: NamespaceRegistry,
    schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]],
    context_position: int,
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int],
    serializer_id: str,
    tokenizer_id: str,
    required_evidence_ids: Sequence[str] = (),
    preserve_evidence_ids: Sequence[str] = (),
    required_source_paths: Sequence[str] = (),
    preserve_source_paths: Sequence[str] = (),
    max_candidates: int = 8,
    artifact_request: ArtifactRequest | None = None,
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
    if (
        type(snapshot) is not SourceSnapshot or type(store) is not ArtifactStore
        or type(namespace_registry) is not NamespaceRegistry
        or type(paths) not in (tuple, list) or not 1 <= len(paths) <= MAX_PATHS
        or type(schema_lookups) not in (tuple, list) or len(schema_lookups) > MAX_SCHEMA_LOOKUPS
        or type(query) is not str or not query or len(query) > MAX_QUERY_CHARS
        or type(source_order_start) is not int or not 0 <= source_order_start <= (2**63 - 1 - MAX_PATHS - 16)
        or type(context_token_budget) is not int or not 1 <= context_token_budget <= MAX_CONTEXT_TOKENS
        or type(prompt_token_budget) is not int or not 1 <= prompt_token_budget <= MAX_PROMPT_TOKENS
        or type(max_candidates) is not int or not 1 <= max_candidates <= 16
        or type(context_position) is not int or not 0 <= context_position <= MAX_BASE_MESSAGES
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
    if type(base_messages) not in (tuple, list) or not 1 <= len(base_messages) <= MAX_BASE_MESSAGES:
        return empty
    if context_position > len(base_messages) or any(type(message) is not dict for message in base_messages):
        return empty
    try:
        base_messages_owned = json.loads(_bounded_canonical_json(base_messages, MAX_BASE_MESSAGES_BYTES).decode("utf-8"))
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        return empty

    source_rows: list[SourceIdentity] = []
    misses: list[tuple[str, str]] = []
    valid_paths: list[str] = []
    # The ledger stores caller-selected bounded sources; the smaller active
    # assembly budget is applied later by assemble().
    ledger = ContextLedger(max_logical_tokens=MAX_CONTEXT_TOKENS)
    schema_rows: list[tuple[str, str, str]] = []
    path_evidence: dict[str, str] = {}
    selected: tuple[str, ...] = ()
    omitted: tuple[tuple[str, str], ...] = ()
    structural_status: str | None = None
    prompt_result = None
    aggregate_hash: str | None = None
    final_status = PreparationStatus.READY
    reason: str | None = None

    # One outer scope deliberately spans source admission through receipt build.
    request_scope = store.request() if artifact_request is None else nullcontext(artifact_request)
    with request_scope as request:
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
                ledger.add_segment(evidence_id, text, source_order_start + len(valid_paths), kind="source", retention="hot" if raw_path in preserve_source_paths else "warm", metadata={"snapshot_sha256": snapshot.snapshot_sha256, "source_path": path, "content_sha256": digest, "artifact_handle_id": handle.handle_id})
            except (ArtifactStoreError, OSError, ValueError, ContextAdmissionError) as exc:
                failure_status = PreparationStatus.CONTEXT_FAILED if isinstance(exc, ContextAdmissionError) else PreparationStatus.STORE_FAILED
                return PreparationResult(failure_status, "none", None, None, None, None, tuple(source_rows), (), (), tuple(misses), (), None, type(exc).__name__)
            source_rows.append(SourceIdentity(evidence_id, path, digest, handle.handle_id, "ok"))
            valid_paths.append(path)
            admitted_source_bytes += len(raw)

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
                candidate_result = query_snapshot_symbols(indexed.index, query, limit=max_candidates)
                _metrics["structural_index_query_status"] = candidate_result.status.value
                _metrics["structural_index_candidate_count"] = len(candidate_result.candidates)
                if candidate_result.status not in (StructuralStatus.OK, StructuralStatus.NO_MATCHES):
                    final_status = PreparationStatus.STRUCTURE_FAILED
                    reason = candidate_result.status.value
                else:
                    # Candidate signatures are admitted only when every source identity matches.
                    source_by_path = {row.path: row for row in source_rows if row.status == "ok"}
                    for index, candidate in enumerate(candidate_result.candidates):
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
                                    messages.insert(context_position, {"role": "user", "content": "Deferred operation schemas (inert data): " + schema_blob})
                                    context_position += 1
                        if final_status is PreparationStatus.READY:
                            required_ids = tuple(required_evidence_ids) + tuple(path_evidence[path] for path in required_source_paths if path in path_evidence)
                            preserve_ids = tuple(preserve_evidence_ids) + tuple(path_evidence[path] for path in preserve_source_paths if path in path_evidence and any(row.evidence_id == path_evidence[path] and row.status == "ok" for row in source_rows))
                            if any(item not in {row.evidence_id for row in source_rows if row.status == "ok"} and item not in {"symbol-" + _canonical_digest([snapshot.snapshot_sha256, c.path, c.source_sha256, c.name, c.start_line, c.end_line]) for c in (candidate_result.candidates if candidate_result.status is StructuralStatus.OK else ())} for item in preserve_ids):
                                final_status = PreparationStatus.CONTEXT_FAILED
                                reason = "preserved_evidence_unknown"
                        if final_status is PreparationStatus.READY:
                            try:
                                _metrics["ledger_assembly_attempts"] = int(_metrics["ledger_assembly_attempts"]) + 1
                                assembly = ledger.assemble(query, active_token_budget=context_token_budget, preserve_ids=preserve_ids, search_limit=32, receipt_detail="full")
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

                                prompt_result = compile_prompt(assembly, messages, context_position=context_position, serializer=measured_serializer, tokenizer_counter=measured_tokenizer, serializer_id=serializer_id, tokenizer_id=tokenizer_id, hard_budget=prompt_token_budget, required_evidence_ids=required_ids)
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
                            aggregate_hash = _canonical_digest({
                                "schema": "wrench.e0-preparation-refs.v1", "snapshot_sha256": snapshot.snapshot_sha256,
                                "sources": [[r.evidence_id, r.path, r.content_sha256, r.artifact_handle_id, r.status] for r in source_rows],
                                "selected": list(selected), "omitted": [list(row) for row in receipt_omitted], "misses": [list(row) for row in miss_rows],
                                "assembly_session_hash": assembly.get("session_hash"),
                                "schemas": [list(row) for row in schema_rows],
                                "discovered_namespace_ids": discovered_namespace_ids,
                                "prompt_gate": {"status": prompt_result.receipt.status.value, "prompt_sha256": prompt_result.receipt.prompt_sha256,
                                    "exact_token_count": prompt_result.receipt.exact_token_count, "budget": prompt_result.receipt.hard_budget,
                                    "serializer_id": prompt_result.receipt.serializer_id, "tokenizer_id": prompt_result.receipt.tokenizer_id},
                            })
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
                            return PreparationResult(final_status, "none", prompt_result.prompt if prompt_result.receipt.status is PromptGateStatus.READY else None, prompt_result.receipt, receipt_result, aggregate_hash, tuple(source_rows), selected, tuple(receipt_omitted), tuple(miss_rows), tuple(schema_rows), structural_status, reason)

    # Even a fully stale/missing request gets a reference-only incomplete
    # receipt. No content object or prompt is created for retrieval misses.
    if final_status is PreparationStatus.SOURCE_MISSES and snapshot.snapshot_sha256:
        miss_omitted = tuple((row.evidence_id, row.status) for row in source_rows)
        receipt_misses = tuple((evidence_id, status) for evidence_id, status in misses if status in {"missing", "stale", "unsafe", "unknown_snapshot", "unknown_source", "evicted"})
        aggregate_hash = _canonical_digest({
            "schema": "wrench.e0-preparation-refs.v1", "snapshot_sha256": snapshot.snapshot_sha256,
            "sources": [[r.evidence_id, r.path, r.content_sha256, r.artifact_handle_id, r.status] for r in source_rows],
            "selected": [], "omitted": [list(row) for row in miss_omitted], "misses": [list(row) for row in misses],
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
    namespace_registry: NamespaceRegistry, schema_lookups: Sequence[tuple[str, str]],
    base_messages: Sequence[Mapping[str, object]], context_position: int,
    serializer: Callable[[Sequence[Mapping[str, object]]], str | bytes],
    tokenizer_counter: Callable[[str | bytes], int], serializer_id: str,
    tokenizer_id: str, required_evidence_ids: Sequence[str] = (),
    preserve_evidence_ids: Sequence[str] = (), required_source_paths: Sequence[str] = (),
    preserve_source_paths: Sequence[str] = (), max_candidates: int = 8,
    artifact_request: ArtifactRequest | None = None,
) -> PreparationResult:
    """Prepare local context and attach non-identifying preparation metrics.

    The default scope is preparation-only and closes before return. To retain
    source pins during a downstream request, pass an already active
    ``ArtifactRequest`` and keep its surrounding ``with store.request()`` open
    until that request succeeds, fails, times out, or is cancelled. This
    facade never dispatches or observes downstream activity.
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
        prompt_token_budget=prompt_token_budget, namespace_registry=namespace_registry,
        schema_lookups=schema_lookups, base_messages=base_messages, context_position=context_position,
        serializer=serializer, tokenizer_counter=tokenizer_counter, serializer_id=serializer_id,
        tokenizer_id=tokenizer_id, required_evidence_ids=required_evidence_ids,
        preserve_evidence_ids=preserve_evidence_ids, required_source_paths=required_source_paths,
        preserve_source_paths=preserve_source_paths, max_candidates=max_candidates,
        artifact_request=artifact_request, _metrics=counters,
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
    "MAX_PATHS",
    "MAX_SCHEMA_LOOKUPS",
    "PreparationAccountingReceipt",
    "PreparationResult",
    "PreparationStatus",
    "SourceIdentity",
    "prepare_e0_context",
    "verify_preparation_accounting_receipt",
]
