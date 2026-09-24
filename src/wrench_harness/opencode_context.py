"""Provider-free binding from an OpenCode session record to E0 preparation.

This is an offline adapter seam. It does not register an OpenCode plugin,
query the OpenCode API, or authorize downstream dispatch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .artifact_store import ArtifactRequest, ArtifactStore
from .e0_context_pipeline import PreparationResult, PreparationStatus, prepare_e0_context
from .namespace_registry import NamespaceRegistry
from .outcome_receipt import (
    OutcomeReceipt,
    ReceiptResult,
    ReceiptStatus,
    validate_outcome_receipt,
)
from .opencode_session_root import resolve_opencode_session_root
from .prompt_compiler import PromptGateReceipt, PromptGateStatus
from .snapshot import SourceSnapshot


@dataclass(frozen=True)
class OpenCodePreparationJoin:
    """Keep the session/root/snapshot identity alongside local preparation."""

    session_id: str
    configured_root: Path
    snapshot_sha256: str
    root_location_sha256: str | None
    root_identity: str | None
    preparation: PreparationResult


class OpenCodeAdmissionStatus(str, Enum):
    """Local preparation classification, not an OpenCode dispatch decision."""

    READY = "ready"
    INVALID_JOIN = "invalid_join"
    SESSION_MISMATCH = "session_mismatch"
    PREPARATION_NOT_READY = "preparation_not_ready"
    ROUTE_UNEXPECTED = "route_unexpected"
    PROMPT_MISSING = "prompt_missing"
    PROMPT_GATE_NOT_READY = "prompt_gate_not_ready"
    PREPARATION_RECEIPT_INVALID = "preparation_receipt_invalid"
    RETRIEVAL_MISSES = "retrieval_misses"


@dataclass(frozen=True)
class OpenCodePreparationAdmission:
    """Result of checking whether a local preparation join is internally ready.

    A READY result carries the original join for inspection. It does not bind
    an OpenCode hook, prevent dispatch, authenticate caller-supplied callback
    identities, or establish prompt/tokenizer parity with a client runtime.
    """

    status: OpenCodeAdmissionStatus
    join: OpenCodePreparationJoin | None
    reason: str


def check_opencode_preparation_admission(
    event_session_id: str,
    join: OpenCodePreparationJoin,
) -> OpenCodePreparationAdmission:
    """Fail closed on an incomplete or mismatched offline preparation join.

    This typed predicate is an inert local check. A caller can ignore its
    result, so it is not a client dispatch veto or runtime authority boundary.
    """
    if (
        type(event_session_id) is not str
        or not event_session_id
        or type(join) is not OpenCodePreparationJoin
    ):
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.INVALID_JOIN, None, "invalid_join"
        )
    if type(join.session_id) is not str or join.session_id != event_session_id:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.SESSION_MISMATCH, None, "session_mismatch"
        )
    preparation = join.preparation
    if type(preparation) is not PreparationResult:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.INVALID_JOIN, None, "invalid_preparation"
        )
    if type(preparation.status) is not PreparationStatus or preparation.status is not PreparationStatus.READY:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PREPARATION_NOT_READY, None, "preparation_not_ready"
        )
    if type(preparation.route) is not str or preparation.route != "none":
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.ROUTE_UNEXPECTED, None, "route_unexpected"
        )
    if type(preparation.prompt) not in (str, bytes) or not preparation.prompt:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PROMPT_MISSING, None, "prompt_missing"
        )
    if (
        type(preparation.prompt_gate) is not PromptGateReceipt
        or type(preparation.prompt_gate.status) is not PromptGateStatus
        or preparation.prompt_gate.status is not PromptGateStatus.READY
    ):
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PROMPT_GATE_NOT_READY, None, "prompt_gate_not_ready"
        )
    receipt_result = preparation.outcome_receipt
    if (
        type(receipt_result) is not ReceiptResult
        or type(receipt_result.status) is not ReceiptStatus
        or receipt_result.status is not ReceiptStatus.INCOMPLETE
        or type(receipt_result.receipt) is not OutcomeReceipt
    ):
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
            None,
            "preparation_receipt_invalid",
        )
    validated_receipt = validate_outcome_receipt(receipt_result.receipt)
    if validated_receipt.status is not ReceiptStatus.INCOMPLETE or validated_receipt.receipt is None:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
            None,
            "preparation_receipt_invalid",
        )
    try:
        receipt_payload = json.loads(validated_receipt.receipt.payload_json)
    except (TypeError, ValueError, RecursionError):
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
            None,
            "preparation_receipt_invalid",
        )
    if (
        receipt_payload.get("schema") != "wrench.e0.outcome-receipt.v1"
        or receipt_payload.get("snapshot_sha256") != join.snapshot_sha256
        or receipt_payload.get("context_receipt_sha256") != preparation.aggregate_sha256
        or receipt_payload.get("actual_route") != "none"
        or receipt_payload.get("outcome", {}).get("status") != "unknown"
        or receipt_payload.get("completeness") != "incomplete"
        or receipt_payload.get("missing_fields") != ["outcome"]
    ):
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.PREPARATION_RECEIPT_INVALID,
            None,
            "preparation_receipt_identity_mismatch",
        )
    if type(preparation.retrieval_misses) is not tuple or preparation.retrieval_misses:
        return OpenCodePreparationAdmission(
            OpenCodeAdmissionStatus.RETRIEVAL_MISSES, None, "retrieval_misses"
        )
    return OpenCodePreparationAdmission(OpenCodeAdmissionStatus.READY, join, "ready")


def prepare_opencode_e0_context(
    event_session_id: str,
    session_record: object,
    *,
    snapshot: SourceSnapshot,
    paths: Sequence[str | PathLike[str]],
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
) -> OpenCodePreparationJoin:
    """Resolve one session root and prepare only against that configured root.

    The signature mirrors the bounded E0 preparation surface except that the
    caller cannot supply or override ``source_root``. Preparation itself
    checks that the snapshot identity matches this root during exact reads.
    Pass an active caller-owned ``artifact_request`` to retain pins after this
    helper returns, and keep its scope open through downstream completion or
    failure cleanup. The default remains preparation-only.
    """
    if type(snapshot) is not SourceSnapshot:
        raise ValueError("invalid_source_snapshot")
    resolved = resolve_opencode_session_root(event_session_id, session_record)
    result = prepare_e0_context(
        source_root=resolved.configured_root,
        snapshot=snapshot,
        paths=paths,
        store=store,
        query=query,
        source_order_start=source_order_start,
        context_token_budget=context_token_budget,
        prompt_token_budget=prompt_token_budget,
        namespace_registry=namespace_registry,
        schema_lookups=schema_lookups,
        base_messages=base_messages,
        context_position=context_position,
        serializer=serializer,
        tokenizer_counter=tokenizer_counter,
        serializer_id=serializer_id,
        tokenizer_id=tokenizer_id,
        required_evidence_ids=required_evidence_ids,
        preserve_evidence_ids=preserve_evidence_ids,
        required_source_paths=required_source_paths,
        preserve_source_paths=preserve_source_paths,
        max_candidates=max_candidates,
        artifact_request=artifact_request,
    )
    return OpenCodePreparationJoin(
        session_id=resolved.session_id,
        configured_root=resolved.configured_root,
        snapshot_sha256=snapshot.snapshot_sha256,
        root_location_sha256=snapshot.root_location_sha256,
        root_identity=snapshot.root_identity,
        preparation=result,
    )


__all__ = [
    "OpenCodeAdmissionStatus",
    "OpenCodePreparationAdmission",
    "OpenCodePreparationJoin",
    "check_opencode_preparation_admission",
    "prepare_opencode_e0_context",
]
