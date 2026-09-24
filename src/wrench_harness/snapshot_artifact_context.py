"""Verified snapshot-to-artifact-to-context roundtrip bridge."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum

from .artifact_store import (
    ArtifactHandle,
    ArtifactIdentityError,
    ArtifactReadStatus,
    ArtifactStore,
    ArtifactStoreError,
)
from .context import ContextAdmissionError, ContextLedger
from .snapshot import RetrievalStatus, SourceRootBinding, SourceSnapshot, retrieve_exact


class SnapshotArtifactContextStatus(str, Enum):
    ADMITTED = "admitted"
    UNKNOWN_SNAPSHOT = "unknown_snapshot"
    UNKNOWN_SOURCE = "unknown_source"
    MISSING = "missing"
    STALE = "stale"
    UNSAFE = "unsafe"
    STORE_ERROR = "store_error"
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_EVICTED = "artifact_evicted"
    ARTIFACT_CORRUPT = "artifact_corrupt"
    ROUNDTRIP_MISMATCH = "roundtrip_mismatch"
    NON_TEXT = "non_text"
    CONTEXT_REJECTED = "context_rejected"


@dataclass(frozen=True)
class SnapshotArtifactContextReceipt:
    """Outcome and identity fields only; never contains source bytes."""

    status: SnapshotArtifactContextStatus
    segment_id: str | None = None
    snapshot_sha256: str | None = None
    source_path: str | None = None
    content_sha256: str | None = None
    artifact_handle_id: str | None = None
    reason: str | None = None


def _identity_hash(snapshot_sha256: str, source_path: str, content_sha256: str) -> str:
    raw = json.dumps(
        [snapshot_sha256, source_path, content_sha256],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _segment_id(snapshot_sha256: str, source_path: str, content_sha256: str) -> str:
    return "source-" + _identity_hash(snapshot_sha256, source_path, content_sha256)


def _artifact_status(status: ArtifactReadStatus) -> SnapshotArtifactContextStatus:
    return {
        ArtifactReadStatus.MISSING: SnapshotArtifactContextStatus.ARTIFACT_MISSING,
        ArtifactReadStatus.EVICTED: SnapshotArtifactContextStatus.ARTIFACT_EVICTED,
        ArtifactReadStatus.CORRUPT: SnapshotArtifactContextStatus.ARTIFACT_CORRUPT,
    }.get(status, SnapshotArtifactContextStatus.ROUNDTRIP_MISMATCH)


def admit_snapshot_artifact_source(
    *,
    source_root: str | os.PathLike[str] | SourceRootBinding,
    snapshot: SourceSnapshot,
    path: str | os.PathLike[str],
    store: ArtifactStore,
    ledger: ContextLedger,
    source_order: int,
) -> SnapshotArtifactContextReceipt:
    """Verify a current source, persist it, pin/read it, then admit text.

    The caller owns and supplies the artifact store. If text is rejected by the
    ledger after a successful store roundtrip, the verified object remains in
    that store; no compensating delete is attempted.
    """
    if not isinstance(ledger, ContextLedger):
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.CONTEXT_REJECTED, reason="invalid_context_ledger"
        )
    if not isinstance(store, ArtifactStore):
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.STORE_ERROR, reason="invalid_artifact_store"
        )

    retrieved = retrieve_exact(source_root, snapshot, path)
    retrieval_outcomes = {
        RetrievalStatus.UNKNOWN_SNAPSHOT: SnapshotArtifactContextStatus.UNKNOWN_SNAPSHOT,
        RetrievalStatus.UNKNOWN_SOURCE: SnapshotArtifactContextStatus.UNKNOWN_SOURCE,
        RetrievalStatus.MISSING: SnapshotArtifactContextStatus.MISSING,
        RetrievalStatus.CHANGED: SnapshotArtifactContextStatus.STALE,
        RetrievalStatus.UNSAFE: SnapshotArtifactContextStatus.UNSAFE,
    }
    if retrieved.status in retrieval_outcomes:
        return SnapshotArtifactContextReceipt(retrieval_outcomes[retrieved.status], source_path=retrieved.path)
    if retrieved.status is not RetrievalStatus.OK or not isinstance(retrieved.data, bytes):
        return SnapshotArtifactContextReceipt(SnapshotArtifactContextStatus.UNSAFE, source_path=retrieved.path)

    assert isinstance(snapshot, SourceSnapshot)
    assert retrieved.path is not None
    source_bytes = retrieved.data
    content_sha256 = hashlib.sha256(source_bytes).hexdigest()
    expected_handle_id = _identity_hash(snapshot.snapshot_sha256, retrieved.path, content_sha256)
    handle: ArtifactHandle | None = None
    try:
        handle = store.put(
            snapshot_sha256=snapshot.snapshot_sha256,
            source_path=retrieved.path,
            expected_content_sha256=content_sha256,
            data=source_bytes,
        )
        if not isinstance(handle, ArtifactHandle) or (
            handle.snapshot_sha256 != snapshot.snapshot_sha256
            or handle.source_path != retrieved.path
            or handle.content_sha256 != content_sha256
            or handle.size_bytes != len(source_bytes)
            or handle.handle_id != expected_handle_id
        ):
            return SnapshotArtifactContextReceipt(
                SnapshotArtifactContextStatus.ROUNDTRIP_MISMATCH,
                snapshot_sha256=snapshot.snapshot_sha256,
                source_path=retrieved.path,
                content_sha256=content_sha256,
                artifact_handle_id=getattr(handle, "handle_id", None),
                reason="artifact_handle_identity_mismatch",
            )

        with store.request() as request:
            pinned = request.pin(handle)
            if pinned.status is not ArtifactReadStatus.OK:
                return SnapshotArtifactContextReceipt(
                    _artifact_status(pinned.status), snapshot_sha256=snapshot.snapshot_sha256,
                    source_path=retrieved.path, content_sha256=content_sha256,
                    artifact_handle_id=handle.handle_id,
                )
            roundtrip = request.read(handle)
            if roundtrip.status is not ArtifactReadStatus.OK:
                return SnapshotArtifactContextReceipt(
                    _artifact_status(roundtrip.status), snapshot_sha256=snapshot.snapshot_sha256,
                    source_path=retrieved.path, content_sha256=content_sha256,
                    artifact_handle_id=handle.handle_id,
                )
            if (
                pinned.data != source_bytes
                or roundtrip.data != source_bytes
                or not isinstance(roundtrip.data, bytes)
                or hashlib.sha256(roundtrip.data).hexdigest() != content_sha256
            ):
                return SnapshotArtifactContextReceipt(
                    SnapshotArtifactContextStatus.ROUNDTRIP_MISMATCH,
                    snapshot_sha256=snapshot.snapshot_sha256,
                    source_path=retrieved.path,
                    content_sha256=content_sha256,
                    artifact_handle_id=handle.handle_id,
                )
    except (ArtifactStoreError, ArtifactIdentityError, OSError, ValueError) as exc:
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.STORE_ERROR,
            snapshot_sha256=snapshot.snapshot_sha256,
            source_path=retrieved.path,
            content_sha256=content_sha256,
            artifact_handle_id=getattr(handle, "handle_id", None),
            reason=str(exc),
        )

    try:
        text = source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.NON_TEXT, snapshot_sha256=snapshot.snapshot_sha256,
            source_path=retrieved.path, content_sha256=content_sha256,
            artifact_handle_id=handle.handle_id,
        )
    if not text:
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.NON_TEXT, snapshot_sha256=snapshot.snapshot_sha256,
            source_path=retrieved.path, content_sha256=content_sha256,
            artifact_handle_id=handle.handle_id, reason="empty_text",
        )

    segment_id = _segment_id(snapshot.snapshot_sha256, retrieved.path, content_sha256)
    metadata = {
        "source_snapshot_sha256": snapshot.snapshot_sha256,
        "source_path": retrieved.path,
        "source_content_sha256": content_sha256,
        "artifact_handle_id": handle.handle_id,
    }
    try:
        ledger.add_segment(
            segment_id,
            text,
            source_order,
            role="context",
            kind="source_snapshot",
            retention="reference",
            metadata=metadata,
        )
    except ContextAdmissionError as exc:
        return SnapshotArtifactContextReceipt(
            SnapshotArtifactContextStatus.CONTEXT_REJECTED,
            segment_id=segment_id,
            snapshot_sha256=snapshot.snapshot_sha256,
            source_path=retrieved.path,
            content_sha256=content_sha256,
            artifact_handle_id=handle.handle_id,
            reason=str(exc),
        )

    return SnapshotArtifactContextReceipt(
        SnapshotArtifactContextStatus.ADMITTED,
        segment_id=segment_id,
        snapshot_sha256=snapshot.snapshot_sha256,
        source_path=retrieved.path,
        content_sha256=content_sha256,
        artifact_handle_id=handle.handle_id,
    )


__all__ = [
    "SnapshotArtifactContextReceipt",
    "SnapshotArtifactContextStatus",
    "admit_snapshot_artifact_source",
]
