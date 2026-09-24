from __future__ import annotations

import hashlib

import pytest

from wrench_harness.context import ContextLedger
from wrench_harness.snapshot import create_snapshot
from wrench_harness.snapshot_context import (
    SnapshotContextStatus,
    admit_snapshot_source,
)


def _snapshot(root, path="source.txt"):
    return create_snapshot(root, [path])


def _admit(root, snapshot, path, ledger, source_order=1):
    return admit_snapshot_source(
        root=root,
        snapshot=snapshot,
        path=path,
        ledger=ledger,
        source_order=source_order,
    )


def test_exact_text_is_admitted_with_snapshot_identity_and_deterministic_id(tmp_path):
    source = tmp_path / "source.txt"
    source.write_bytes("hello verified world".encode("utf-8"))
    snapshot = _snapshot(tmp_path)
    first_ledger = ContextLedger(max_logical_tokens=100)
    second_ledger = ContextLedger(max_logical_tokens=100)

    first = _admit(tmp_path, snapshot, "source.txt", first_ledger)
    second = _admit(tmp_path, snapshot, "source.txt", second_ledger)

    assert first.status is SnapshotContextStatus.ADMITTED
    assert first.segment_id == second.segment_id
    assert first.content_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert not hasattr(first, "data")
    segment = first_ledger._segments[first.segment_id]
    assert segment.text == "hello verified world"
    assert segment.kind == "source_snapshot"
    assert segment.retention == "reference"
    assert segment.metadata == {
        "source_snapshot_sha256": snapshot.snapshot_sha256,
        "source_path": "source.txt",
        "source_content_sha256": first.content_sha256,
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("changed", SnapshotContextStatus.STALE),
        ("missing", SnapshotContextStatus.MISSING),
    ],
)
def test_stale_or_missing_source_does_not_mutate_ledger(tmp_path, mutation, expected):
    source = tmp_path / "source.txt"
    source.write_bytes(b"original text")
    snapshot = _snapshot(tmp_path)
    if mutation == "changed":
        source.write_bytes(b"changed text")
    else:
        source.unlink()

    ledger = ContextLedger(max_logical_tokens=100)
    result = _admit(tmp_path, snapshot, "source.txt", ledger)
    assert result.status is expected
    assert ledger.segment_count == 0


def test_unknown_snapshot_source_and_unsafe_path_are_explicit_and_atomic(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"valid text")
    snapshot = _snapshot(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)

    unknown_snapshot = _admit(tmp_path, object(), "source.txt", ledger)
    unknown_source = _admit(tmp_path, snapshot, "other.txt", ledger)
    unsafe = _admit(tmp_path, snapshot, "../source.txt", ledger)

    assert unknown_snapshot.status is SnapshotContextStatus.UNKNOWN_SNAPSHOT
    assert unknown_source.status is SnapshotContextStatus.UNKNOWN_SOURCE
    assert unsafe.status is SnapshotContextStatus.UNSAFE
    assert ledger.segment_count == 0


@pytest.mark.parametrize("content", [b"\xff\xfe", b""])
def test_invalid_utf8_or_empty_text_is_rejected_without_ledger_mutation(tmp_path, content):
    (tmp_path / "source.txt").write_bytes(content)
    snapshot = _snapshot(tmp_path)
    ledger = ContextLedger(max_logical_tokens=100)

    result = _admit(tmp_path, snapshot, "source.txt", ledger)

    assert result.status is SnapshotContextStatus.NON_TEXT
    assert ledger.segment_count == 0


def test_context_admission_rejection_preserves_ledger(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"two words")
    snapshot = _snapshot(tmp_path)
    ledger = ContextLedger(max_logical_tokens=1)

    result = _admit(tmp_path, snapshot, "source.txt", ledger)

    assert result.status is SnapshotContextStatus.CONTEXT_REJECTED
    assert result.reason == "logical_context_limit_exceeded"
    assert ledger.segment_count == 0
    assert ledger.logical_token_count == 0
