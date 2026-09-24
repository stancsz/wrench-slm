"""Synthetic offline composition from enrolled source to fixture request.

This module joins existing Wrench preparation and the fixture-only request
boundary. It has no client, HTTP client, upstream route, or provider path.
Serializer and tokenizer identities are synthetic test identities; this does
not establish runtime token parity or dispatch authority.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence

from .artifact_store import ArtifactStore
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


SYNTHETIC_SERIALIZER_ID = "wrench-synthetic-opencode-json-v1"
SYNTHETIC_TOKENIZER_ID = "wrench-synthetic-character-counter-v1"
_FIXTURE_MODEL = "wrench-offline-fixture"
_MAX_CANONICAL_BYTES = 65_536
_ROLES = frozenset({"system", "developer", "user", "assistant"})
_HEX = frozenset("0123456789abcdef")


class CompositionStatus(str, Enum):
    READY = "ready"
    PROJECT_REJECTED = "project_rejected"
    STRUCTURE_REJECTED = "structure_rejected"
    PREPARATION_REJECTED = "preparation_rejected"
    MATERIALIZATION_REJECTED = "materialization_rejected"
    LOWERING_REJECTED = "lowering_rejected"


@dataclass(frozen=True)
class OfflineCompositionReceipt:
    """Content-free joins for one synthetic composition."""

    schema: str
    snapshot_sha256: str
    candidate_count: int
    selected_candidate_order_sha256: str
    source_hash_join_sha256: str
    preparation_sha256: str
    insertion_receipt_sha256: str
    context_message_sha256: str
    request_body_sha256: str
    serializer_id: str
    tokenizer_id: str
    exact_token_gate: str
    receipt_sha256: str


@dataclass(frozen=True)
class OfflineCompositionResult:
    """A ready fixture request and the lease that owns its artifact pins."""

    status: CompositionStatus
    reason: str
    snapshot_sha256: str | None = None
    preparation_status: str | None = None
    candidate_count: int = 0
    receipt: OfflineCompositionReceipt | None = None
    request: LoweredRequest | None = field(default=None, repr=False, compare=False)
    ticket: LeaseTicket | None = field(default=None, repr=False, compare=False)
    fixture_response: FixtureResponse | None = field(default=None, repr=False, compare=False)
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


def _fixture_serializer(messages: Sequence[Mapping[str, object]]) -> str:
    from .prompt_compiler import materialize_prompt_messages

    return _canonical(materialize_prompt_messages(messages)).decode("utf-8")


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
        or type(event) is not dict
        or event.get("sessionID") != event_session_id
        or type(event.get("messages")) is not list
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
    try:
        pin_scope = _PinScope(store)
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
            base_messages=event["messages"],
            context_position=context_position,
            serializer=_fixture_serializer,
            tokenizer_counter=_fixture_tokenizer,
            serializer_id=SYNTHETIC_SERIALIZER_ID,
            tokenizer_id=SYNTHETIC_TOKENIZER_ID,
            max_candidates=max_candidates,
            artifact_request=pin_scope.request,
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
            return OfflineCompositionResult(
                CompositionStatus.PREPARATION_REJECTED,
                preparation.reason or preparation.status.value,
                snapshot_sha256=project_snapshot.snapshot.snapshot_sha256,
                preparation_status=preparation.status.value,
                candidate_count=(preparation.metrics.structural_index_candidate_count or 0)
                if preparation.metrics is not None else 0,
            )

        candidate_count = preparation.metrics.structural_index_candidate_count
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

        materialized = materialize_opencode_prepared_context(join, event)
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
        receipt_payload = {
            "schema": "wrench.e0-offline-composition-receipt.v1",
            "snapshot_sha256": project_snapshot.snapshot.snapshot_sha256,
            "candidate_count": candidate_count,
            "selected_candidate_order_sha256": candidate_digest,
            "source_hash_join_sha256": source_join_digest,
            "preparation_sha256": preparation.aggregate_sha256,
            "insertion_receipt_sha256": materialized.transition_receipt.receipt_sha256,
            "context_message_sha256": preparation.prompt_gate.context_message_sha256,
            "request_body_sha256": body_digest,
            "serializer_id": SYNTHETIC_SERIALIZER_ID,
            "tokenizer_id": SYNTHETIC_TOKENIZER_ID,
            "exact_token_gate": ExactTokenGateStatus.UNAVAILABLE.value,
        }
        receipt = OfflineCompositionReceipt(
            schema=receipt_payload["schema"],
            snapshot_sha256=receipt_payload["snapshot_sha256"],
            candidate_count=receipt_payload["candidate_count"],
            selected_candidate_order_sha256=receipt_payload["selected_candidate_order_sha256"],
            source_hash_join_sha256=receipt_payload["source_hash_join_sha256"],
            preparation_sha256=receipt_payload["preparation_sha256"],
            insertion_receipt_sha256=receipt_payload["insertion_receipt_sha256"],
            context_message_sha256=receipt_payload["context_message_sha256"],
            request_body_sha256=receipt_payload["request_body_sha256"],
            serializer_id=SYNTHETIC_SERIALIZER_ID,
            tokenizer_id=SYNTHETIC_TOKENIZER_ID,
            exact_token_gate=ExactTokenGateStatus.UNAVAILABLE.value,
            receipt_sha256=_sha256(_canonical(receipt_payload)),
        )
        # Register the lease only after all content validation, lowering, and
        # digest construction have succeeded. No fallible user callback runs
        # after registration.
        ticket = boundary.prepare(lease_id, pin_scope.release_once)
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
            candidate_count=candidate_count,
            receipt=receipt,
            request=lowered_request,
            ticket=ticket,
            fixture_response=fixture_response,
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


__all__ = [
    "CompositionStatus",
    "OfflineCompositionReceipt",
    "OfflineCompositionResult",
    "SYNTHETIC_SERIALIZER_ID",
    "SYNTHETIC_TOKENIZER_ID",
    "prepare_offline_e0_request",
]
