from __future__ import annotations

import hashlib

import pytest

from wrench_harness.artifact_store import (
    ArtifactRead,
    ArtifactReadStatus,
    ArtifactStore,
    ArtifactStoreLimitError,
)
from wrench_harness.context import ContextLedger
from wrench_harness.snapshot import create_snapshot
from wrench_harness.snapshot_artifact_context import (
    SnapshotArtifactContextStatus,
    admit_snapshot_artifact_source,
)


def _store(tmp_path, name="store"):
    return ArtifactStore(tmp_path / name)


def _snapshot(root, path="source.txt"):
    return create_snapshot(root, [path])


def _admit(root, snapshot, path, store, ledger, source_order=1):
    return admit_snapshot_artifact_source(
        source_root=root,
        snapshot=snapshot,
        path=path,
        store=store,
        ledger=ledger,
        source_order=source_order,
    )


def test_exact_snapshot_artifact_roundtrip_admits_bound_text(tmp_path):
    data = b"verified artifact context"
    (tmp_path / "source.txt").write_bytes(data)
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.ADMITTED
    assert receipt.content_sha256 == hashlib.sha256(data).hexdigest()
    assert receipt.artifact_handle_id is not None
    assert not hasattr(receipt, "data")
    segment = ledger._segments[receipt.segment_id]
    assert segment.text == data.decode()
    assert segment.metadata == {
        "source_snapshot_sha256": snapshot.snapshot_sha256,
        "source_path": "source.txt",
        "source_content_sha256": hashlib.sha256(data).hexdigest(),
        "artifact_handle_id": receipt.artifact_handle_id,
    }
    assert store._pins == {}
    assert store.read(store._entry_handle(store._entry_map()[receipt.artifact_handle_id])).data == data


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("unknown_snapshot", SnapshotArtifactContextStatus.UNKNOWN_SNAPSHOT),
        ("unknown_source", SnapshotArtifactContextStatus.UNKNOWN_SOURCE),
        ("missing", SnapshotArtifactContextStatus.MISSING),
        ("stale", SnapshotArtifactContextStatus.STALE),
        ("unsafe", SnapshotArtifactContextStatus.UNSAFE),
    ],
)
def test_retrieval_failures_do_not_write_store_or_ledger(tmp_path, case, expected):
    source = tmp_path / "source.txt"
    source.write_bytes(b"original source")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)
    supplied_snapshot = snapshot
    path = "source.txt"
    if case == "unknown_snapshot":
        supplied_snapshot = object()
    elif case == "unknown_source":
        path = "other.txt"
    elif case == "missing":
        source.unlink()
    elif case == "stale":
        source.write_bytes(b"changed source")
    elif case == "unsafe":
        path = "../source.txt"

    receipt = _admit(tmp_path, supplied_snapshot, path, store, ledger)

    assert receipt.status is expected
    assert ledger.segment_count == 0
    assert store._objects_on_disk == {}
    assert store._payload["entries"] == []


def test_deterministic_artifact_and_segment_identity_across_stores(tmp_path):
    data = b"repeatable identity"
    source = tmp_path / "source.txt"
    source.write_bytes(data)
    snapshot = _snapshot(tmp_path)
    receipts = []
    for name in ("store-one", "store-two"):
        receipts.append(
            _admit(
                tmp_path,
                snapshot,
                "source.txt",
                _store(tmp_path, name),
                ContextLedger(max_logical_tokens=100),
            )
        )

    assert receipts[0].status is SnapshotArtifactContextStatus.ADMITTED
    assert receipts[1].status is SnapshotArtifactContextStatus.ADMITTED
    assert receipts[0].artifact_handle_id == receipts[1].artifact_handle_id
    assert receipts[0].segment_id == receipts[1].segment_id


def test_corrupt_artifact_roundtrip_is_explicit_and_ledger_stays_empty(tmp_path, monkeypatch):
    (tmp_path / "source.txt").write_bytes(b"verified bytes")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)
    monkeypatch.setattr(store, "read", lambda handle: ArtifactRead(ArtifactReadStatus.CORRUPT))

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.ARTIFACT_CORRUPT
    assert ledger.segment_count == 0
    assert len(store._payload["entries"]) == 1


def test_bounded_store_write_failure_is_explicit_and_ledger_stays_empty(tmp_path, monkeypatch):
    (tmp_path / "source.txt").write_bytes(b"verified bytes")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)
    monkeypatch.setattr(
        store,
        "put",
        lambda **kwargs: (_ for _ in ()).throw(ArtifactStoreLimitError("object_count_limit_exceeded")),
    )

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.STORE_ERROR
    assert receipt.reason == "object_count_limit_exceeded"
    assert ledger.segment_count == 0


def test_roundtrip_identity_mismatch_is_explicit_and_ledger_stays_empty(tmp_path, monkeypatch):
    (tmp_path / "source.txt").write_bytes(b"verified bytes")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)
    monkeypatch.setattr(
        store,
        "read",
        lambda handle: ArtifactRead(ArtifactReadStatus.OK, data=b"different bytes"),
    )

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.ROUNDTRIP_MISMATCH
    assert ledger.segment_count == 0
    assert len(store._payload["entries"]) == 1


def test_context_rejection_keeps_verified_artifact_but_not_ledger_segment(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"two words")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=1)

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.CONTEXT_REJECTED
    assert receipt.reason == "logical_context_limit_exceeded"
    assert receipt.artifact_handle_id is not None
    assert ledger.segment_count == 0
    assert len(store._payload["entries"]) == 1
    assert len(store._objects_on_disk) == 1


def test_non_utf8_bytes_are_stored_but_not_admitted(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"\xff\xfe")
    snapshot = _snapshot(tmp_path)
    store = _store(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)

    receipt = _admit(tmp_path, snapshot, "source.txt", store, ledger)

    assert receipt.status is SnapshotArtifactContextStatus.NON_TEXT
    assert ledger.segment_count == 0
    assert len(store._payload["entries"]) == 1
