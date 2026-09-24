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
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .artifact_store import ArtifactHandle, ArtifactReadStatus, ArtifactStore, ArtifactStoreError
from .context import ContextAdmissionError, ContextLedger, ContextSelectionError
from .namespace_registry import NamespaceRegistry, SchemaLookupStatus
from .outcome_receipt import ReceiptResult, ReceiptStatus, build_outcome_receipt
from .prompt_compiler import (
    MAX_BASE_MESSAGES, MAX_BASE_MESSAGES_BYTES, PromptGateReceipt,
    PromptGateStatus, _bounded_canonical_json, compile_prompt,
)
from .snapshot import RetrievalStatus, SourceSnapshot, retrieve_exact
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


def prepare_e0_context(
    *,
    source_root: str | os.PathLike[str],
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
) -> PreparationResult:
    """Prepare verified, pinned context and a gated prompt; never executes it.

    Source snapshots bind bytes, not caller authority. Paths are finite and
    explicit. Store objects may persist after this request and are not rolled
    back if later context/prompt admission fails. Pins last through receipt
    construction and are process-local to the supplied ArtifactStore instance.
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
    with store.request() as request:
        seen: set[str] = set()
        admitted_source_bytes = 0
        for raw_path in paths:
            retrieved = retrieve_exact(source_root, snapshot, raw_path)
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
                handle = store.put(snapshot_sha256=snapshot.snapshot_sha256, source_path=path, expected_content_sha256=digest, data=raw)
                if (
                    handle.snapshot_sha256 != snapshot.snapshot_sha256 or handle.source_path != path
                    or handle.content_sha256 != digest or handle.size_bytes != len(raw)
                ):
                    raise ArtifactStoreError("artifact_handle_identity_mismatch")
                pinned = request.pin(handle)
                roundtrip = request.read(handle)
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
            indexed = build_snapshot_symbol_index(source_root, snapshot, valid_paths)
            structural_status = indexed.status.value
            if indexed.status is not StructuralStatus.OK or indexed.index is None:
                final_status = PreparationStatus.STRUCTURE_FAILED
                reason = indexed.status.value
            else:
                candidate_result = query_snapshot_symbols(indexed.index, query, limit=max_candidates)
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
                        discovered = namespace_registry.discover()
                        discovered_namespace_ids = [item.namespace_id for item in discovered]
                        schema_data: list[dict[str, object]] = []
                        for namespace_id, operation_id in schema_lookups:
                            lookup = namespace_registry.lookup(namespace_id, operation_id)
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
                                assembly = ledger.assemble(query, active_token_budget=context_token_budget, preserve_ids=preserve_ids, search_limit=32, receipt_detail="full")
                                prompt_result = compile_prompt(assembly, messages, context_position=context_position, serializer=serializer, tokenizer_counter=tokenizer_counter, serializer_id=serializer_id, tokenizer_id=tokenizer_id, hard_budget=prompt_token_budget, required_evidence_ids=required_ids)
                            except (ContextSelectionError, ContextAdmissionError, TypeError, ValueError, OverflowError, UnicodeError) as exc:
                                return PreparationResult(PreparationStatus.CONTEXT_FAILED, "none", None, None, None, None, tuple(source_rows), (), (), tuple(misses), tuple(schema_rows), structural_status, type(exc).__name__)
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
                            receipt_result = build_outcome_receipt(_receipt_payload(snapshot_hash=snapshot.snapshot_sha256, aggregate_hash=aggregate_hash, selected=selected, omitted=receipt_omitted, misses=receipt_misses))
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
        receipt_result = build_outcome_receipt(_receipt_payload(
            snapshot_hash=snapshot.snapshot_sha256, aggregate_hash=aggregate_hash,
            selected=(), omitted=miss_omitted, misses=receipt_misses,
        ))
        return PreparationResult(final_status, "none", None, None, receipt_result, aggregate_hash, tuple(source_rows), (), miss_omitted, tuple(misses), (), structural_status, reason)
    return PreparationResult(final_status, "none", None, None, None, None, tuple(source_rows), selected, omitted, tuple(misses), tuple(schema_rows), structural_status, reason)


__all__ = ["MAX_PATHS", "MAX_SCHEMA_LOOKUPS", "PreparationResult", "PreparationStatus", "SourceIdentity", "prepare_e0_context"]
