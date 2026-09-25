"""Synthetic offline composition from enrolled source to fixture request.

This module joins existing Wrench preparation and the fixture-only request
boundary. Prompt accounting covers the complete validated seven-field
OpenCode context projection in a synthetic semantic envelope. The fixture
lowerer accepts a stricter message subset and has no client, upstream route,
or provider path. Serializer and tokenizer identities are synthetic test
identities; this does not establish runtime token parity or dispatch authority.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .artifact_store import ArtifactStore
from .e0_route_preparation import (
    RoutePreparationStatus,
    route_and_prepare_e0_context,
    verify_route_preparation_accounting_receipt,
)
from .namespace_registry import NamespaceRegistry
from .opencode_context import OpenCodePreparationJoin, prepare_opencode_e0_context
from .opencode_prepared_context import (
    PreparedContextStatus,
    materialize_opencode_prepared_context,
)
from .opencode_project_registry import ExactTokenGateStatus, OpenCodeProjectRegistry
from .opencode_project_snapshot import (
    OpenCodeProjectSnapshot,
    ProjectSnapshotError,
    prepare_opencode_project_snapshot,
)
from .opencode_request_boundary import (
    CONTENT_TYPE_HEADER,
    CORRELATION_HEADER,
    FixtureResponse,
    FixtureResponseStream,
    MAX_MESSAGE_BYTES,
    MAX_MESSAGES,
    MAX_REQUEST_BYTES,
    ROUTE,
    LeaseTicket,
    LoweredRequest,
    RequestLeaseBoundary,
    StreamEnd,
)
from .opencode_hook_projection import (
    OpenCodeProjectionStatus,
    project_opencode_context_hook,
)


SYNTHETIC_SERIALIZER_ID = "wrench-synthetic-opencode-semantic-envelope-json-v1"
SYNTHETIC_TOKENIZER_ID = "wrench-synthetic-character-counter-v1"
_FIXTURE_MODEL = "wrench-offline-fixture"
_MAX_CANONICAL_BYTES = 65_536
_ROLES = frozenset({"system", "developer", "user", "assistant"})
_HEX = frozenset("0123456789abcdef")
_OMISSION_REASONS = frozenset({
    "active_token_budget", "not_selected", "preserved_unit_exceeds_active_budget",
    "unit_exceeds_active_budget", "missing", "stale", "unsafe", "unknown_snapshot",
    "unknown_source", "evicted", "limit_exceeded", "non_text",
})
_MISS_STATUSES = frozenset({
    "missing", "stale", "unsafe", "unknown_snapshot", "unknown_source",
    "evicted", "limit_exceeded", "non_text",
})


class CompositionStatus(str, Enum):
    READY = "ready"
    PROJECT_REJECTED = "project_rejected"
    STRUCTURE_REJECTED = "structure_rejected"
    PREPARATION_REJECTED = "preparation_rejected"
    MATERIALIZATION_REJECTED = "materialization_rejected"
    LOWERING_REJECTED = "lowering_rejected"
    ROUTE_REJECTED = "route_rejected"


@dataclass(frozen=True)
class OfflineCompositionReceipt:
    """Content-free joins for one synthetic composition."""

    schema: str
    snapshot_sha256: str
    accounting_state: str
    candidate_count: int
    selected_candidate_order_sha256: str | None
    source_hash_join_sha256: str | None
    preparation_sha256: str
    preparation_outcome_receipt_sha256: str
    preparation_outcome_receipt_validation_status: str
    preparation_outcome_status: str
    preparation_status: str
    selected_evidence_count: int
    omitted_evidence_count: int
    omission_reason_counts: tuple[tuple[str, int], ...]
    retrieval_miss_count: int
    retrieval_miss_status_counts: tuple[tuple[str, int], ...]
    insertion_receipt_sha256: str | None
    context_message_sha256: str | None
    semantic_projection_sha256: str | None
    request_body_sha256: str | None
    route_preparation_sha256: str | None
    serializer_id: str
    tokenizer_id: str
    exact_token_gate: str
    terminal_outcome: str | None
    receipt_sha256: str


@dataclass(frozen=True)
class OfflineCompositionResult:
    """A ready fixture request and the lease that owns its artifact pins."""

    status: CompositionStatus
    reason: str
    snapshot_sha256: str | None = None
    preparation_status: str | None = None
    route_status: str | None = None
    candidate_count: int = 0
    receipt: OfflineCompositionReceipt | None = None
    request: LoweredRequest | None = field(default=None, repr=False, compare=False)
    ticket: LeaseTicket | None = field(default=None, repr=False, compare=False)
    fixture_response: FixtureResponse | None = field(default=None, repr=False, compare=False)
    _boundary: RequestLeaseBoundary | None = field(default=None, repr=False, compare=False)
    _pin_scope: "_PinScope | None" = field(default=None, repr=False, compare=False)

    @property
    def artifact_scope_active(self) -> bool:
        """Expose lifecycle state without exposing artifact or prompt content."""
        return self._pin_scope is not None and self._pin_scope.active


class _PinScope:
    def __init__(self, store: ArtifactStore) -> None:
        self.store = store
        self.request = store.request()
        self._lock = threading.Lock()
        self._closed = False
        self.request.__enter__()

    @property
    def active(self) -> bool:
        return not self._closed and self.request.is_active_for(self.store)

    def release_once(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self.request.__exit__(None, None, None)


def _canonical(value: object) -> bytes:
    encoder = json.JSONEncoder(
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    chunks: list[bytes] = []
    size = 0
    for chunk in encoder.iterencode(value):
        encoded = chunk.encode("utf-8")
        size += len(encoded)
        if size > _MAX_CANONICAL_BYTES:
            raise ValueError("composition_receipt_limit_exceeded")
        chunks.append(encoded)
    return b"".join(chunks)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _selected_candidate_order_digest(
    snapshot_sha256: str,
    candidate_count: int,
    references: object,
    sources: Sequence[object],
) -> str:
    """Bind selected structural spans in preparation order without source text."""
    rows = getattr(references, "references", None)
    if type(rows) is not tuple:
        raise ValueError("selected_candidate_references_invalid")
    source_by_path = {
        row.path: row for row in sources
        if getattr(row, "status", None) == "ok"
    }
    selected: list[dict[str, object]] = []
    for row in rows:
        if type(row) not in (dict,):
            try:
                row = dict(row)
            except (TypeError, ValueError):
                raise ValueError("selected_candidate_reference_invalid")
        if row.get("segment_kind") != "symbol":
            continue
        path = row.get("source_path")
        content_sha = row.get("content_sha256")
        start = row.get("start_line")
        end = row.get("end_line")
        segment_id = row.get("segment_id")
        source = source_by_path.get(path) if type(path) is str else None
        if (
            source is None
            or content_sha != source.content_sha256
            or row.get("snapshot_sha256") != snapshot_sha256
            or type(start) is not int
            or type(end) is not int
            or type(segment_id) is not str
        ):
            raise ValueError("selected_candidate_source_join_invalid")
        selected.append(
            {
                "segment_id_sha256": _sha256(segment_id.encode("utf-8")),
                "path_sha256": _sha256(path.encode("utf-8")),
                "source_sha256": content_sha,
                "start_line": start,
                "end_line": end,
                "parser_sha256": _sha256(str(row.get("parser")).encode("utf-8")),
                "language_sha256": _sha256(str(row.get("language")).encode("utf-8")),
            }
        )
    if not selected:
        raise ValueError("no_selected_structural_candidates")
    return _sha256(
        _canonical(
            {
                "snapshot_sha256": snapshot_sha256,
                "candidate_count": candidate_count,
                "selected_in_preparation_order": selected,
            }
        )
    )


def _source_hash_join(snapshot_sha256: str, sources: Sequence[object]) -> str:
    rows = []
    for source in sources:
        if (
            type(getattr(source, "path", None)) is not str
            or type(getattr(source, "content_sha256", None)) is not str
            or len(source.content_sha256) != 64
            or any(char not in _HEX for char in source.content_sha256)
            or getattr(source, "status", None) != "ok"
        ):
            raise ValueError("source_hash_join_invalid")
        handle_id = getattr(source, "artifact_handle_id", None)
        if type(handle_id) is not str or len(handle_id) != 64 or any(char not in _HEX for char in handle_id):
            raise ValueError("source_hash_join_invalid")
        rows.append(
            {
                "path_sha256": _sha256(source.path.encode("utf-8")),
                "source_sha256": source.content_sha256,
                "artifact_handle_sha256": _sha256(handle_id.encode("ascii")),
            }
        )
    rows.sort(key=lambda row: (row["path_sha256"], row["source_sha256"]))
    return _sha256(_canonical({"snapshot_sha256": snapshot_sha256, "sources": rows}))


def _status_counts(rows: Sequence[tuple[str, str]]) -> tuple[tuple[str, int], ...]:
    """Aggregate content-free reason/status labels without retaining IDs."""
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for evidence_id, status in rows:
        if type(evidence_id) is not str or not evidence_id or type(status) is not str or status not in _OMISSION_REASONS:
            raise ValueError("preparation_accounting_rows_invalid")
        if evidence_id in seen:
            raise ValueError("preparation_accounting_duplicate_id")
        seen.add(evidence_id)
        counts[status] = counts.get(status, 0) + 1
    return tuple(sorted(counts.items()))


def _preparation_selection_summary(preparation: object) -> tuple[int, int, tuple[tuple[str, int], ...], int, tuple[tuple[str, int], ...]]:
    """Check the PromptGate to facade join, then retain only count aggregates."""
    selected = getattr(preparation, "selected_evidence_ids", None)
    omitted = getattr(preparation, "omitted_evidence", None)
    misses = getattr(preparation, "retrieval_misses", None)
    gate = getattr(preparation, "prompt_gate", None)
    if (
        type(selected) is not tuple or len(selected) > 256
        or any(type(item) is not str or not item for item in selected)
        or len(set(selected)) != len(selected)
        or type(omitted) is not tuple or len(omitted) > 10_000
        or type(misses) is not tuple or len(misses) > 16
    ):
        raise ValueError("preparation_selection_shape_invalid")
    omission_counts = _status_counts(omitted)
    miss_counts = _status_counts(misses)
    if gate is None:
        if selected:
            raise ValueError("preparation_selection_prompt_join_invalid")
    else:
        gate_selected = getattr(gate, "selected_evidence_ids", None)
        gate_omitted = getattr(gate, "omitted_evidence", None)
        if (
            type(gate_selected) is not tuple
            or gate_selected != selected
            or type(gate_omitted) is not tuple
        ):
            raise ValueError("preparation_selection_prompt_join_invalid")
        _status_counts(gate_omitted)
        if not set(gate_omitted).issubset(set(omitted)):
            raise ValueError("preparation_selection_prompt_join_invalid")
    return len(selected), len(omitted), omission_counts, len(misses), miss_counts


def _preparation_outcome_digest(preparation: object, snapshot_sha256: str) -> tuple[str, str]:
    """Validate the preparation's content-free outcome receipt and bind its hash."""
    from .outcome_receipt import ReceiptResult, ReceiptStatus, validate_outcome_receipt

    result = getattr(preparation, "outcome_receipt", None)
    if type(result) is not ReceiptResult or type(result.status) is not ReceiptStatus or result.receipt is None:
        raise ValueError("preparation_outcome_receipt_invalid")
    validated = validate_outcome_receipt(result.receipt)
    if (
        validated.status not in (ReceiptStatus.VALID, ReceiptStatus.INCOMPLETE)
        or result.status is not validated.status
        or validated.receipt is None
    ):
        raise ValueError("preparation_outcome_receipt_invalid")
    try:
        payload = json.loads(validated.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        raise ValueError("preparation_outcome_receipt_invalid") from None
    if (
        type(payload) is not dict
        or payload.get("schema") != "wrench.e0.outcome-receipt.v1"
        or payload.get("snapshot_sha256") != snapshot_sha256
        or payload.get("context_receipt_sha256") != getattr(preparation, "aggregate_sha256", None)
    ):
        raise ValueError("preparation_outcome_receipt_identity_invalid")
    return validated.receipt.sha256, validated.status.value


def _fixture_serializer_for_projection(
    semantic_projection: Mapping[str, object],
):
    """Account for every supported hook field in the synthetic prompt envelope.

    The compiler supplies the post-insertion message sequence. The other six
    semantic fields come from the bounded hook projection validated before
    preparation. This envelope is synthetic accounting only; it does not
    model OpenCode's final provider serializer or request lowering.
    """
    from .prompt_compiler import materialize_prompt_messages

    base = json.loads(_canonical(dict(semantic_projection)).decode("utf-8"))
    if type(base) is not dict or set(base) != {
        "sessionID", "system", "messages", "agent", "model", "tools", "options"
    }:
        raise ValueError("semantic_projection_shape_invalid")

    def serialize(messages: Sequence[Mapping[str, object]]) -> str:
        envelope = dict(base)
        envelope["messages"] = materialize_prompt_messages(messages)
        return _canonical(
            {
                "schema": "wrench.synthetic-opencode-context-envelope.v1",
                "opencode_context_hook_version": "2.0.15",
                "projection": envelope,
            }
        ).decode("utf-8")

    return serialize


def _fixture_tokenizer(value: str | bytes) -> int:
    return len(value)


def _lower_materialized_event(
    event: object,
    *,
    context_message_sha256: str,
    max_tokens: int,
) -> tuple[bytes, str]:
    if type(event) is not dict or type(event.get("messages")) is not list:
        raise ValueError("materialized_event_invalid")
    event_messages = event["messages"]
    if not 1 <= len(event_messages) <= MAX_MESSAGES:
        raise ValueError("message_count_invalid")
    lowered_messages: list[dict[str, str]] = []
    context_texts: list[str] = []
    for message in event_messages:
        if (
            type(message) is not dict
            or set(message) != {"role", "content"}
            or type(message.get("role")) is not str
            or message["role"] not in _ROLES
            or type(message.get("content")) is not list
            or len(message["content"]) != 1
        ):
            raise ValueError("event_message_shape_unsupported")
        text_block = message["content"][0]
        if (
            type(text_block) is not dict
            or set(text_block) != {"type", "text"}
            or text_block.get("type") != "text"
            or type(text_block.get("text")) is not str
            or not text_block["text"]
        ):
            raise ValueError("event_message_content_unsupported")
        text = text_block["text"]
        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("event_message_unicode_invalid") from exc
        if len(encoded) > MAX_MESSAGE_BYTES:
            raise ValueError("event_message_too_large")
        message_bytes = _canonical(message)
        if _sha256(message_bytes) == context_message_sha256:
            context_texts.append(text)
        lowered_messages.append({"role": message["role"], "content": text})
    if len(context_texts) != 1 or sum(row["content"] == context_texts[0] for row in lowered_messages) != 1:
        raise ValueError("prepared_context_message_not_unique")
    body = _canonical(
        {
            "model": _FIXTURE_MODEL,
            "messages": lowered_messages,
            "stream": True,
            "max_tokens": max_tokens,
        }
    )
    if len(body) > MAX_REQUEST_BYTES:
        raise ValueError("lowered_request_too_large")
    return body, _sha256(body)


def prepare_offline_e0_request(
    registry: OpenCodeProjectRegistry,
    event_session_id: str,
    session_record: object,
    selected_paths: Iterable[str],
    *,
    event: object,
    fixture_response: FixtureResponse,
    store: ArtifactStore,
    boundary: RequestLeaseBoundary,
    namespace_registry: NamespaceRegistry,
    query: str,
    route_prompt: str | None = None,
    lease_id: str,
    context_token_budget: int = 128,
    prompt_token_budget: int = 8_192,
    context_position: int = 1,
    max_candidates: int = 8,
    max_tokens: int = 128,
) -> OfflineCompositionResult:
    """Prepare one in-memory lowered request for a fixture-only lease.

    The caller supplies a bounded project registry, one store instance, one
    fixture boundary and one synthetic event. Any preparation or lowering
    failure returns without an issued request ticket and closes its pin scope.
    The returned pin scope is transferred to the boundary lease and remains
    open until fixture-stream completion, cancellation, failure, disconnect,
    or timeout cleanup.
    """
    hook_projection = project_opencode_context_hook(event)
    if (
        type(registry) is not OpenCodeProjectRegistry
        or type(store) is not ArtifactStore
        or type(boundary) is not RequestLeaseBoundary
        or type(fixture_response) is not FixtureResponse
        or type(namespace_registry) is not NamespaceRegistry
        or type(lease_id) is not str
        or not lease_id
        or type(max_tokens) is not int
        or not 1 <= max_tokens <= 8_192
        or hook_projection.status is not OpenCodeProjectionStatus.READY
        or hook_projection.projection is None
        or type(event) is not dict
        or (route_prompt is not None and (type(route_prompt) is not str or not route_prompt or len(route_prompt) > 8_192))
    ):
        return OfflineCompositionResult(CompositionStatus.PROJECT_REJECTED, "input_invalid")

    try:
        semantic_projection_payload = json.loads(hook_projection.projection.payload_json)
    except (TypeError, ValueError, RecursionError):
        return OfflineCompositionResult(CompositionStatus.PROJECT_REJECTED, "input_invalid")
    if (
        type(semantic_projection_payload) is not dict
        or semantic_projection_payload.get("sessionID") != event_session_id
    ):
        return OfflineCompositionResult(CompositionStatus.PROJECT_REJECTED, "input_invalid")

    try:
        project_snapshot: OpenCodeProjectSnapshot = prepare_opencode_project_snapshot(
            registry,
            event_session_id,
            session_record,
            selected_paths,
        )
    except (ProjectSnapshotError, TypeError, ValueError, OSError) as exc:
        return OfflineCompositionResult(CompositionStatus.PROJECT_REJECTED, type(exc).__name__)
    if project_snapshot.exact_token_gate is not ExactTokenGateStatus.UNAVAILABLE:
        return OfflineCompositionResult(
            CompositionStatus.PROJECT_REJECTED, "exact_token_gate_must_remain_unavailable",
            snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
        )

    pin_scope: _PinScope | None = None
    ticket: LeaseTicket | None = None
    lowered_request: LoweredRequest | None = None
    route_preparation = None
    try:
        pin_scope = _PinScope(store)
        if route_prompt is None:
            join: OpenCodePreparationJoin = prepare_opencode_e0_context(
                event_session_id,
                session_record,
                snapshot=project_snapshot.snapshot,
                paths=project_snapshot.selected_paths,
                store=store,
                query=query,
                source_order_start=0,
                context_token_budget=context_token_budget,
                prompt_token_budget=prompt_token_budget,
                namespace_registry=namespace_registry,
                schema_lookups=(),
                base_messages=semantic_projection_payload["messages"],
                context_position=context_position,
                serializer=_fixture_serializer_for_projection(semantic_projection_payload),
                tokenizer_counter=_fixture_tokenizer,
                serializer_id=SYNTHETIC_SERIALIZER_ID,
                tokenizer_id=SYNTHETIC_TOKENIZER_ID,
                max_candidates=max_candidates,
                artifact_request=pin_scope.request,
            )
        else:
            route_preparation = route_and_prepare_e0_context(
                route_prompt,
                root_binding=project_snapshot.binding,
                snapshot=project_snapshot.snapshot,
                store=store,
                query=query,
                source_order_start=0,
                context_token_budget=context_token_budget,
                prompt_token_budget=prompt_token_budget,
                namespace_registry=namespace_registry,
                schema_lookups=(),
                base_messages=semantic_projection_payload["messages"],
                context_position=context_position,
                message_format="opencode-2.0.15",
                serializer=_fixture_serializer_for_projection(semantic_projection_payload),
                tokenizer_counter=_fixture_tokenizer,
                serializer_id=SYNTHETIC_SERIALIZER_ID,
                tokenizer_id=SYNTHETIC_TOKENIZER_ID,
                max_candidates=max_candidates,
                artifact_request=pin_scope.request,
            )
            if (
                route_preparation.status is not RoutePreparationStatus.JOINED
                or route_preparation.preparation is None
                or route_preparation.accounting_receipt is None
                or not verify_route_preparation_accounting_receipt(
                    route_preparation.accounting_receipt,
                    route_result=route_preparation.route_result,
                    preparation=route_preparation.preparation,
                )
            ):
                pin_scope.release_once()
                return OfflineCompositionResult(
                    CompositionStatus.ROUTE_REJECTED,
                    route_preparation.reason,
                    snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                    route_status=route_preparation.route_result.status.value,
                )
            join = OpenCodePreparationJoin(
                session_id=project_snapshot.session_id,
                configured_root=project_snapshot.binding.configured_root,
                snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                root_location_sha256=project_snapshot.snapshot.root_location_sha256,
                root_identity=project_snapshot.snapshot.root_identity,
                preparation=route_preparation.preparation,
            )
        preparation = join.preparation
        if (
            preparation.status.value != "ready"
            or preparation.prompt_gate is None
            or preparation.prompt_gate.status.value != "ready"
            or preparation.route != "none"
            or preparation.aggregate_sha256 is None
            or preparation.context_message_json is None
            or preparation.metrics is None
            or preparation.metrics.structural_index_query_status != "ok"
            or type(preparation.metrics.structural_index_candidate_count) is not int
            or preparation.metrics.structural_index_candidate_count < 1
        ):
            pin_scope.release_once()
            incomplete_receipt = None
            # SOURCE_MISSES is the one rejected preparation outcome that has
            # a complete, validated reference-only outcome join. Preserve its
            # counts without issuing a request or claiming prompt accounting.
            if (
                preparation.status.value == "source_misses"
                and preparation.aggregate_sha256 is not None
                and preparation.outcome_receipt is not None
                and project_snapshot.snapshot.snapshot_sha256
            ):
                try:
                    outcome_digest, outcome_status = _preparation_outcome_digest(
                        preparation, project_snapshot.snapshot.snapshot_sha256
                    )
                    selected_count, omitted_count, omission_counts, miss_count, miss_counts = _preparation_selection_summary(preparation)
                    payload = {
                        "schema": "wrench.e0-offline-composition-receipt.v2",
                        "snapshot_sha256": project_snapshot.snapshot.snapshot_sha256,
                        "accounting_state": "incomplete_preparation",
                        "candidate_count": max(0, preparation.metrics.structural_index_candidate_count or 0)
                        if preparation.metrics is not None else 0,
                        "selected_candidate_order_sha256": None,
                        "source_hash_join_sha256": None,
                        "preparation_sha256": preparation.aggregate_sha256,
                        "preparation_outcome_receipt_sha256": outcome_digest,
                        "preparation_outcome_receipt_validation_status": "valid",
                        "preparation_outcome_status": outcome_status,
                        "preparation_status": preparation.status.value,
                        "selected_evidence_count": selected_count,
                        "omitted_evidence_count": omitted_count,
                        "omission_reason_counts": [list(row) for row in omission_counts],
                        "retrieval_miss_count": miss_count,
                        "retrieval_miss_status_counts": [list(row) for row in miss_counts],
                        "insertion_receipt_sha256": None,
                        "context_message_sha256": None,
                        "semantic_projection_sha256": None,
                        "request_body_sha256": None,
                        "route_preparation_sha256": None,
                        "serializer_id": SYNTHETIC_SERIALIZER_ID,
                        "tokenizer_id": SYNTHETIC_TOKENIZER_ID,
                        "exact_token_gate": ExactTokenGateStatus.UNAVAILABLE.value,
                        "terminal_outcome": None,
                    }
                    incomplete_receipt = OfflineCompositionReceipt(
                        schema=payload["schema"],
                        snapshot_sha256=payload["snapshot_sha256"],
                        accounting_state=payload["accounting_state"],
                        candidate_count=payload["candidate_count"],
                        selected_candidate_order_sha256=None,
                        source_hash_join_sha256=None,
                        preparation_sha256=payload["preparation_sha256"],
                        preparation_outcome_receipt_sha256=outcome_digest,
                        preparation_outcome_receipt_validation_status="valid",
                        preparation_outcome_status=outcome_status,
                        preparation_status=preparation.status.value,
                        selected_evidence_count=selected_count,
                        omitted_evidence_count=omitted_count,
                        omission_reason_counts=omission_counts,
                        retrieval_miss_count=miss_count,
                        retrieval_miss_status_counts=miss_counts,
                        insertion_receipt_sha256=None,
                        context_message_sha256=None,
                        semantic_projection_sha256=None,
                        request_body_sha256=None,
                        route_preparation_sha256=None,
                        serializer_id=SYNTHETIC_SERIALIZER_ID,
                        tokenizer_id=SYNTHETIC_TOKENIZER_ID,
                        exact_token_gate=ExactTokenGateStatus.UNAVAILABLE.value,
                        terminal_outcome=None,
                        receipt_sha256=_sha256(_canonical(payload)),
                    )
                    if not verify_offline_e0_composition_receipt(incomplete_receipt):
                        incomplete_receipt = None
                except (TypeError, ValueError, UnicodeError, RecursionError):
                    incomplete_receipt = None
            return OfflineCompositionResult(
                CompositionStatus.PREPARATION_REJECTED,
                preparation.reason or preparation.status.value,
                snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                preparation_status=preparation.status.value,
                route_status=(route_preparation.route_result.status.value if route_preparation else None),
                candidate_count=(preparation.metrics.structural_index_candidate_count or 0)
                if preparation.metrics is not None else 0,
                receipt=incomplete_receipt,
            )

        candidate_count = preparation.metrics.structural_index_candidate_count
        selected_count, omitted_count, omission_counts, miss_count, miss_counts = _preparation_selection_summary(preparation)
        source_join_digest = _source_hash_join(
            project_snapshot.snapshot.snapshot_sha256,
            tuple(preparation.sources),
        )
        candidate_digest = _selected_candidate_order_digest(
            project_snapshot.snapshot.snapshot_sha256,
            candidate_count,
            preparation.selected_source_references,
            preparation.sources,
        )

        # Continue from the projector's private bounded snapshot so prompt
        # accounting, insertion, lowering, and the receipt share one input.
        materialized = materialize_opencode_prepared_context(
            join, semantic_projection_payload
        )
        if materialized.status is not PreparedContextStatus.READY or materialized.event is None or materialized.transition_receipt is None:
            pin_scope.release_once()
            return OfflineCompositionResult(
                CompositionStatus.MATERIALIZATION_REJECTED,
                materialized.reason,
                snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                preparation_status=preparation.status.value,
                candidate_count=candidate_count,
            )

        body, body_digest = _lower_materialized_event(
            materialized.event,
            context_message_sha256=preparation.prompt_gate.context_message_sha256,
            max_tokens=max_tokens,
        )
        materialized_projection = project_opencode_context_hook(materialized.event)
        if (
            materialized_projection.status is not OpenCodeProjectionStatus.READY
            or materialized_projection.projection is None
        ):
            pin_scope.release_once()
            return OfflineCompositionResult(
                CompositionStatus.LOWERING_REJECTED,
                "semantic_projection_invalid",
                snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                preparation_status=preparation.status.value,
                candidate_count=candidate_count,
            )
        semantic_projection_sha256 = materialized_projection.projection.projection_sha256
        receipt_payload = {
            "schema": "wrench.e0-offline-composition-receipt.v2",
            "snapshot_sha256": project_snapshot.snapshot.snapshot_sha256,
            "accounting_state": "complete",
            "candidate_count": candidate_count,
            "selected_candidate_order_sha256": candidate_digest,
            "source_hash_join_sha256": source_join_digest,
            "preparation_sha256": preparation.aggregate_sha256,
            "preparation_outcome_receipt_sha256": _preparation_outcome_digest(
                preparation, project_snapshot.snapshot.snapshot_sha256
            )[0],
            "preparation_outcome_receipt_validation_status": "valid",
            "preparation_outcome_status": _preparation_outcome_digest(
                preparation, project_snapshot.snapshot.snapshot_sha256
            )[1],
            "preparation_status": preparation.status.value,
            "selected_evidence_count": selected_count,
            "omitted_evidence_count": omitted_count,
            "omission_reason_counts": [list(row) for row in omission_counts],
            "retrieval_miss_count": miss_count,
            "retrieval_miss_status_counts": [list(row) for row in miss_counts],
            "insertion_receipt_sha256": materialized.transition_receipt.receipt_sha256,
            "context_message_sha256": preparation.prompt_gate.context_message_sha256,
            "semantic_projection_sha256": semantic_projection_sha256,
            "request_body_sha256": body_digest,
            "route_preparation_sha256": (
                route_preparation.accounting_receipt.accounting_sha256
                if route_preparation is not None and route_preparation.accounting_receipt is not None
                else None
            ),
            "serializer_id": SYNTHETIC_SERIALIZER_ID,
            "tokenizer_id": SYNTHETIC_TOKENIZER_ID,
            "exact_token_gate": ExactTokenGateStatus.UNAVAILABLE.value,
            "terminal_outcome": None,
        }
        receipt = OfflineCompositionReceipt(
            schema=receipt_payload["schema"],
            snapshot_sha256=receipt_payload["snapshot_sha256"],
            accounting_state=receipt_payload["accounting_state"],
            candidate_count=receipt_payload["candidate_count"],
            selected_candidate_order_sha256=receipt_payload["selected_candidate_order_sha256"],
            source_hash_join_sha256=receipt_payload["source_hash_join_sha256"],
            preparation_sha256=receipt_payload["preparation_sha256"],
            preparation_outcome_receipt_sha256=receipt_payload["preparation_outcome_receipt_sha256"],
            preparation_outcome_receipt_validation_status=receipt_payload["preparation_outcome_receipt_validation_status"],
            preparation_outcome_status=receipt_payload["preparation_outcome_status"],
            preparation_status=receipt_payload["preparation_status"],
            selected_evidence_count=receipt_payload["selected_evidence_count"],
            omitted_evidence_count=receipt_payload["omitted_evidence_count"],
            omission_reason_counts=tuple(tuple(row) for row in receipt_payload["omission_reason_counts"]),
            retrieval_miss_count=receipt_payload["retrieval_miss_count"],
            retrieval_miss_status_counts=tuple(tuple(row) for row in receipt_payload["retrieval_miss_status_counts"]),
            insertion_receipt_sha256=receipt_payload["insertion_receipt_sha256"],
            context_message_sha256=receipt_payload["context_message_sha256"],
            semantic_projection_sha256=receipt_payload["semantic_projection_sha256"],
            request_body_sha256=receipt_payload["request_body_sha256"],
            route_preparation_sha256=receipt_payload["route_preparation_sha256"],
            serializer_id=SYNTHETIC_SERIALIZER_ID,
            tokenizer_id=SYNTHETIC_TOKENIZER_ID,
            exact_token_gate=ExactTokenGateStatus.UNAVAILABLE.value,
            terminal_outcome=None,
            receipt_sha256=_sha256(_canonical(receipt_payload)),
        )
        # Register the lease only after all content validation, lowering, and
        # digest construction have succeeded. No fallible user callback runs
        # after registration.
        expected_request = LoweredRequest(
            method="POST",
            url=ROUTE,
            headers=((CONTENT_TYPE_HEADER, "application/json"),),
            body=body,
        )
        ticket = boundary.prepare(
            lease_id,
            pin_scope.release_once,
            expected_request=expected_request,
        )
        lowered_request = LoweredRequest(
            method="POST",
            url=ROUTE,
            headers=(
                (CORRELATION_HEADER, ticket.nonce),
                (CONTENT_TYPE_HEADER, "application/json"),
            ),
            body=body,
        )
        return OfflineCompositionResult(
            status=CompositionStatus.READY,
            reason="ready",
            snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
            preparation_status=preparation.status.value,
            route_status=(route_preparation.route_result.status.value if route_preparation else None),
            candidate_count=candidate_count,
            receipt=receipt,
            request=lowered_request,
            ticket=ticket,
            fixture_response=fixture_response,
            _boundary=boundary,
            _pin_scope=pin_scope,
        )
    except Exception as exc:
        if ticket is not None and lowered_request is not None:
            try:
                outcome = boundary.dispatch(lowered_request, fixture_response)
                if isinstance(outcome, FixtureResponseStream):
                    outcome.close(StreamEnd.FAILED)
            except Exception:
                pass
        if pin_scope is not None:
            pin_scope.release_once()
        return OfflineCompositionResult(
            CompositionStatus.LOWERING_REJECTED,
            type(exc).__name__,
            snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
        )


def _receipt_payload(
    receipt: OfflineCompositionReceipt, *, terminal_outcome: str | None
) -> dict[str, object]:
    return {
        "schema": receipt.schema,
        "snapshot_sha256": receipt.snapshot_sha256,
        "accounting_state": receipt.accounting_state,
        "candidate_count": receipt.candidate_count,
        "selected_candidate_order_sha256": receipt.selected_candidate_order_sha256,
        "source_hash_join_sha256": receipt.source_hash_join_sha256,
        "preparation_sha256": receipt.preparation_sha256,
        "preparation_outcome_receipt_sha256": receipt.preparation_outcome_receipt_sha256,
        "preparation_outcome_receipt_validation_status": receipt.preparation_outcome_receipt_validation_status,
        "preparation_outcome_status": receipt.preparation_outcome_status,
        "preparation_status": receipt.preparation_status,
        "selected_evidence_count": receipt.selected_evidence_count,
        "omitted_evidence_count": receipt.omitted_evidence_count,
        "omission_reason_counts": [list(row) for row in receipt.omission_reason_counts],
        "retrieval_miss_count": receipt.retrieval_miss_count,
        "retrieval_miss_status_counts": [list(row) for row in receipt.retrieval_miss_status_counts],
        "insertion_receipt_sha256": receipt.insertion_receipt_sha256,
        "context_message_sha256": receipt.context_message_sha256,
        "semantic_projection_sha256": receipt.semantic_projection_sha256,
        "request_body_sha256": receipt.request_body_sha256,
        "route_preparation_sha256": receipt.route_preparation_sha256,
        "serializer_id": receipt.serializer_id,
        "tokenizer_id": receipt.tokenizer_id,
        "exact_token_gate": receipt.exact_token_gate,
        "terminal_outcome": terminal_outcome,
    }


def verify_offline_e0_composition_receipt(
    receipt: OfflineCompositionReceipt,
) -> bool:
    """Check canonical content-free receipt integrity and terminal value."""
    if (
        type(receipt) is not OfflineCompositionReceipt
        or type(receipt.terminal_outcome) not in (str, type(None))
        or (receipt.terminal_outcome is not None and receipt.terminal_outcome not in {item.value for item in StreamEnd})
        or receipt.schema != "wrench.e0-offline-composition-receipt.v2"
        or receipt.exact_token_gate != ExactTokenGateStatus.UNAVAILABLE.value
        or receipt.serializer_id != SYNTHETIC_SERIALIZER_ID
        or receipt.tokenizer_id != SYNTHETIC_TOKENIZER_ID
    ):
        return False
    try:
        if (
            type(receipt.candidate_count) is not int or not 0 <= receipt.candidate_count <= 10_000
            or type(receipt.selected_evidence_count) is not int or not 0 <= receipt.selected_evidence_count <= 256
            or type(receipt.omitted_evidence_count) is not int or not 0 <= receipt.omitted_evidence_count <= 10_000
            or type(receipt.retrieval_miss_count) is not int or not 0 <= receipt.retrieval_miss_count <= 16
            or type(receipt.omission_reason_counts) is not tuple
            or type(receipt.retrieval_miss_status_counts) is not tuple
            or any(type(row) is not tuple or len(row) != 2 or type(row[0]) is not str or not row[0] or type(row[1]) is not int or row[1] < 0 for row in (*receipt.omission_reason_counts, *receipt.retrieval_miss_status_counts))
            or any(name not in _OMISSION_REASONS for name, _ in receipt.omission_reason_counts)
            or any(name not in _MISS_STATUSES for name, _ in receipt.retrieval_miss_status_counts)
            or tuple(name for name, _ in receipt.omission_reason_counts) != tuple(sorted(dict(receipt.omission_reason_counts)))
            or tuple(name for name, _ in receipt.retrieval_miss_status_counts) != tuple(sorted(dict(receipt.retrieval_miss_status_counts)))
            or sum(count for _, count in receipt.omission_reason_counts) != receipt.omitted_evidence_count
            or sum(count for _, count in receipt.retrieval_miss_status_counts) != receipt.retrieval_miss_count
            or type(receipt.preparation_sha256) is not str or len(receipt.preparation_sha256) != 64 or any(c not in _HEX for c in receipt.preparation_sha256)
            or type(receipt.preparation_outcome_receipt_sha256) is not str or len(receipt.preparation_outcome_receipt_sha256) != 64 or any(c not in _HEX for c in receipt.preparation_outcome_receipt_sha256)
            or receipt.preparation_outcome_status not in {"valid", "incomplete"}
            or receipt.preparation_outcome_receipt_validation_status != "valid"
        ):
            return False
        digest = _sha256(_canonical(_receipt_payload(receipt, terminal_outcome=receipt.terminal_outcome)))
        if digest != receipt.receipt_sha256:
            return False
        if receipt.accounting_state == "incomplete_preparation":
            return (
                type(receipt.snapshot_sha256) is str and len(receipt.snapshot_sha256) == 64 and all(c in _HEX for c in receipt.snapshot_sha256)
                and receipt.selected_evidence_count >= 0
                and receipt.preparation_outcome_status == "incomplete"
                and receipt.preparation_status == "source_misses"
                and receipt.selected_candidate_order_sha256 is None
                and receipt.source_hash_join_sha256 is None
                and receipt.insertion_receipt_sha256 is None
                and receipt.context_message_sha256 is None
                and receipt.semantic_projection_sha256 is None
                and receipt.request_body_sha256 is None
                and receipt.route_preparation_sha256 is None
                and receipt.terminal_outcome is None
                and receipt.omitted_evidence_count > 0
                and receipt.retrieval_miss_count > 0
            )
        if receipt.accounting_state != "complete":
            return False
        required_digests = (
            receipt.snapshot_sha256, receipt.selected_candidate_order_sha256,
            receipt.source_hash_join_sha256, receipt.preparation_sha256,
            receipt.preparation_outcome_receipt_sha256, receipt.insertion_receipt_sha256,
            receipt.context_message_sha256, receipt.semantic_projection_sha256,
            receipt.request_body_sha256,
        )
        return (
            all(type(value) is str and len(value) == 64 and all(c in _HEX for c in value) for value in required_digests)
            and (receipt.route_preparation_sha256 is None or (type(receipt.route_preparation_sha256) is str and len(receipt.route_preparation_sha256) == 64))
            and receipt.selected_evidence_count > 0
            and receipt.retrieval_miss_count == 0
            and receipt.retrieval_miss_status_counts == ()
            and receipt.preparation_status == "ready"
            and receipt.preparation_outcome_status == "incomplete"
            and (receipt.terminal_outcome is None or receipt.terminal_outcome in {item.value for item in StreamEnd})
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        return False


def finalize_offline_e0_request(
    result: OfflineCompositionResult,
    stream: FixtureResponseStream,
) -> OfflineCompositionReceipt | None:
    """Bind the matching fixture stream terminal outcome into a new receipt.

    The caller can finalize only after stream cleanup has released its artifact
    request pins. This captures fixture mechanics, not client dispatch or tool
    activity.
    """
    if (
        type(result) is not OfflineCompositionResult
        or result.status is not CompositionStatus.READY
        or type(result.receipt) is not OfflineCompositionReceipt
        or not verify_offline_e0_composition_receipt(result.receipt)
        or result.receipt.terminal_outcome is not None
        or type(result.ticket) is not LeaseTicket
        or type(result._boundary) is not RequestLeaseBoundary
        or type(result._pin_scope) is not _PinScope
        or type(stream) is not FixtureResponseStream
        or stream._boundary is not result._boundary
        or stream._lease.lease_id != result.ticket.lease_id
        or stream._lease.nonce != result.ticket.nonce
        or type(stream.end) is not StreamEnd
        or result._pin_scope.active
    ):
        return None
    terminal_outcome = stream.end.value
    payload = _receipt_payload(result.receipt, terminal_outcome=terminal_outcome)
    finalized = replace(
        result.receipt,
        terminal_outcome=terminal_outcome,
        receipt_sha256=_sha256(_canonical(payload)),
    )
    return finalized if verify_offline_e0_composition_receipt(finalized) else None


__all__ = [
    "CompositionStatus",
    "OfflineCompositionReceipt",
    "OfflineCompositionResult",
    "SYNTHETIC_SERIALIZER_ID",
    "SYNTHETIC_TOKENIZER_ID",
    "finalize_offline_e0_request",
    "prepare_offline_e0_request",
    "verify_offline_e0_composition_receipt",
]
