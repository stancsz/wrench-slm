"""Bridge exact source snapshot reads into the in-memory context ledger."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum

from .context import ContextAdmissionError, ContextLedger
from .snapshot import RetrievalStatus, SourceRootBinding, SourceSnapshot, retrieve_exact


class SnapshotContextStatus(str, Enum):
    ADMITTED = "admitted"
    UNKNOWN_SNAPSHOT = "unknown_snapshot"
    UNKNOWN_SOURCE = "unknown_source"
    MISSING = "missing"
    STALE = "stale"
    UNSAFE = "unsafe"
    NON_TEXT = "non_text"
    CONTEXT_REJECTED = "context_rejected"


@dataclass(frozen=True)
class SnapshotContextReceipt:
    """Admission outcome without retaining or returning source bytes."""

    status: SnapshotContextStatus
    segment_id: str | None = None
    snapshot_sha256: str | None = None
    source_path: str | None = None
    content_sha256: str | None = None
    reason: str | None = None


def _segment_id(snapshot_sha256: str, source_path: str, content_sha256: str) -> str:
    encoded = json.dumps(
        [snapshot_sha256, source_path, content_sha256],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "source-" + hashlib.sha256(encoded).hexdigest()


def admit_snapshot_source(
    *,
    root: str | os.PathLike[str] | SourceRootBinding,
    snapshot: SourceSnapshot,
    path: str | os.PathLike[str],
    ledger: ContextLedger,
    source_order: int,
) -> SnapshotContextReceipt:
    """Retrieve verified bytes and admit their strict UTF-8 text atomically.

    The caller supplies the root, snapshot, path, ledger, and deterministic
    source order. No source bytes are included in the receipt or retained by
    this bridge after `ContextLedger.add_segment` completes.
    """
    if not isinstance(ledger, ContextLedger):
        return SnapshotContextReceipt(SnapshotContextStatus.CONTEXT_REJECTED, reason="invalid_context_ledger")

    result = retrieve_exact(root, snapshot, path)
    retrieval_outcomes = {
        RetrievalStatus.UNKNOWN_SNAPSHOT: SnapshotContextStatus.UNKNOWN_SNAPSHOT,
        RetrievalStatus.UNKNOWN_SOURCE: SnapshotContextStatus.UNKNOWN_SOURCE,
        RetrievalStatus.MISSING: SnapshotContextStatus.MISSING,
        RetrievalStatus.CHANGED: SnapshotContextStatus.STALE,
        RetrievalStatus.UNSAFE: SnapshotContextStatus.UNSAFE,
    }
    if result.status in retrieval_outcomes:
        return SnapshotContextReceipt(retrieval_outcomes[result.status], source_path=result.path)

    # retrieve_exact is the authority for byte identity. Defensively reject a
    # malformed success result before decoding or changing the ledger.
    data = result.data
    if result.status is not RetrievalStatus.OK or not isinstance(data, bytes):
        return SnapshotContextReceipt(SnapshotContextStatus.UNSAFE, source_path=result.path)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return SnapshotContextReceipt(SnapshotContextStatus.NON_TEXT, source_path=result.path)
    if not text:
        return SnapshotContextReceipt(SnapshotContextStatus.NON_TEXT, source_path=result.path, reason="empty_text")

    assert isinstance(snapshot, SourceSnapshot)
    assert result.path is not None
    content_sha256 = hashlib.sha256(data).hexdigest()
    segment_id = _segment_id(snapshot.snapshot_sha256, result.path, content_sha256)
    metadata = {
        "source_snapshot_sha256": snapshot.snapshot_sha256,
        "source_path": result.path,
        "source_content_sha256": content_sha256,
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
        return SnapshotContextReceipt(
            SnapshotContextStatus.CONTEXT_REJECTED,
            segment_id=segment_id,
            snapshot_sha256=snapshot.snapshot_sha256,
            source_path=result.path,
            content_sha256=content_sha256,
            reason=str(exc),
        )

    return SnapshotContextReceipt(
        SnapshotContextStatus.ADMITTED,
        segment_id=segment_id,
        snapshot_sha256=snapshot.snapshot_sha256,
        source_path=result.path,
        content_sha256=content_sha256,
    )


__all__ = ["SnapshotContextReceipt", "SnapshotContextStatus", "admit_snapshot_source"]
