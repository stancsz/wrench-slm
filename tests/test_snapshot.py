from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
import os

import pytest
import wrench_harness.snapshot as snapshot_module

from wrench_harness.snapshot import (
    MAX_SNAPSHOT_BYTES,
    MAX_SNAPSHOT_FILES,
    MAX_SOURCE_BYTES,
    MAX_SOURCE_PATH_CHARS,
    RetrievalStatus,
    SnapshotAdmissionError,
    SourceRecord,
    SourceSnapshot,
    _has_reparse_attribute,
    _posix_read_stable_source,
    _windows_read_stable_source,
    create_snapshot,
    retrieve_exact,
)


def test_exact_round_trip_and_snapshot_order_independent(tmp_path):
    (tmp_path / "b.txt").write_bytes(b"original b\x00")
    (tmp_path / "a.txt").write_bytes(b"original a")

    first = create_snapshot(tmp_path, ["b.txt", "./a.txt"])
    second = create_snapshot(tmp_path, ["a.txt", "b.txt"])

    assert first == second
    assert [source.path for source in first.sources] == ["a.txt", "b.txt"]
    result = retrieve_exact(tmp_path, first, "a.txt")
    assert result.status is RetrievalStatus.OK
    assert result.data == b"original a"


def test_snapshot_is_bound_to_its_normalized_configured_root(tmp_path):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    (first_root / "source.txt").write_bytes(b"same bytes")
    (second_root / "source.txt").write_bytes(b"same bytes")

    first = create_snapshot(first_root, ["source.txt"])
    second = create_snapshot(second_root, ["source.txt"])

    assert first.root_location_sha256 != second.root_location_sha256
    assert first.snapshot_sha256 != second.snapshot_sha256
    assert retrieve_exact(first_root, first, "source.txt").status is RetrievalStatus.OK
    cross_root = retrieve_exact(second_root, first, "source.txt")
    assert cross_root.status is RetrievalStatus.UNKNOWN_SNAPSHOT
    assert cross_root.data is None
    assert retrieve_exact(first_root / ".", first, "source.txt").status is RetrievalStatus.OK


def test_root_pathlike_is_converted_once_for_identity_and_read(tmp_path):
    root = tmp_path / "root"
    other = tmp_path / "other"
    root.mkdir()
    other.mkdir()
    (root / "source.txt").write_bytes(b"root content")
    (other / "source.txt").write_bytes(b"other content")

    class OneShotPath(os.PathLike):
        def __init__(self):
            self.calls = 0

        def __fspath__(self):
            self.calls += 1
            return str(root if self.calls == 1 else other)

    create_root = OneShotPath()
    snapshot = create_snapshot(create_root, ["source.txt"])
    assert create_root.calls == 1

    retrieve_root = OneShotPath()
    result = retrieve_exact(retrieve_root, snapshot, "source.txt")
    assert retrieve_root.calls == 1
    assert result.status is RetrievalStatus.OK
    assert result.data == b"root content"


def test_changed_missing_and_unknown_source_are_explicit_misses(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"before")
    snapshot = create_snapshot(tmp_path, ["source.txt"])

    (tmp_path / "source.txt").write_bytes(b"after!")
    changed = retrieve_exact(tmp_path, snapshot, "source.txt")
    assert changed.status is RetrievalStatus.CHANGED
    assert changed.data is None

    (tmp_path / "source.txt").unlink()
    missing = retrieve_exact(tmp_path, snapshot, "source.txt")
    assert missing.status is RetrievalStatus.MISSING
    assert missing.data is None

    unknown = retrieve_exact(tmp_path, snapshot, "other.txt")
    assert unknown.status is RetrievalStatus.UNKNOWN_SOURCE
    assert unknown.data is None

    missing_root = retrieve_exact(tmp_path / "missing-root", snapshot, "source.txt")
    assert missing_root.status is RetrievalStatus.UNKNOWN_SNAPSHOT
    assert missing_root.data is None


def test_unknown_or_tampered_snapshot_fails_closed(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"value")
    snapshot = create_snapshot(tmp_path, ["source.txt"])

    assert retrieve_exact(tmp_path, object(), "source.txt").status is RetrievalStatus.UNKNOWN_SNAPSHOT
    forged = replace(snapshot, snapshot_sha256="0" * 64)
    assert retrieve_exact(tmp_path, forged, "source.txt").status is RetrievalStatus.UNKNOWN_SNAPSHOT


def test_malformed_public_snapshot_handles_return_unknown_snapshot(tmp_path):
    (tmp_path / "source.txt").write_bytes(b"value")
    valid = create_snapshot(tmp_path, ["source.txt"])
    valid_digest = "0" * 64
    too_many = tuple(
        SourceRecord(f"{index:03}.txt", 0, valid_digest)
        for index in range(MAX_SNAPSHOT_FILES + 1)
    )
    too_large = tuple(
        SourceRecord(f"{index:02}.bin", MAX_SOURCE_BYTES, valid_digest)
        for index in range(MAX_SNAPSHOT_BYTES // MAX_SOURCE_BYTES + 1)
    )
    malformed = [
        replace(valid, sources=[]),
        replace(valid, schema="wrench.source-snapshot.v1"),
        replace(valid, root_location_sha256="0" * 64),
        replace(valid, sources=(SourceRecord("../escape", 1, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", True, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", MAX_SOURCE_BYTES + 1, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", 1, "not-a-digest"),)),
        SourceSnapshot(valid.schema, too_many, valid_digest, valid.root_location_sha256),
        SourceSnapshot(valid.schema, too_large, valid_digest, valid.root_location_sha256),
    ]
    for snapshot in malformed:
        result = retrieve_exact(tmp_path, snapshot, "source.txt")
        assert result.status is RetrievalStatus.UNKNOWN_SNAPSHOT
        assert result.data is None


def test_windows_case_aliases_are_rejected_on_windows(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows path aliases are platform-specific")
    (tmp_path / "Name.txt").write_bytes(b"one")
    with pytest.raises(SnapshotAdmissionError, match="duplicate_source_path"):
        create_snapshot(tmp_path, ["Name.txt", "name.txt"])


def test_reparse_attribute_detection_is_deterministic_without_symlink():
    assert _has_reparse_attribute(SimpleNamespace(st_file_attributes=0x400))
    assert not _has_reparse_attribute(SimpleNamespace(st_file_attributes=0))
    assert not _has_reparse_attribute(SimpleNamespace())


def test_windows_parent_relative_handle_walk_reads_exact_bytes(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows native handle walk is platform-specific")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "source.txt").write_bytes(b"pinned exact bytes")
    data, info = _windows_read_stable_source(tmp_path, "nested/source.txt")
    assert data == b"pinned exact bytes"
    assert info.st_size == len(data)


def test_posix_nested_dirfd_walk_and_symlink_rejection(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX dirfd walk is platform-specific")
    nested = tmp_path / "nested"
    nested.mkdir()
    source = nested / "source.txt"
    source.write_bytes(b"dirfd exact bytes")

    real_open = snapshot_module._open_posix_relative
    dirfd_calls = []

    def tracking_open(path, flags, parent_fd):
        dirfd_calls.append((path, flags, parent_fd))
        return real_open(path, flags, parent_fd)

    monkeypatch.setattr(snapshot_module, "_open_posix_relative", tracking_open)
    data, info = _posix_read_stable_source(tmp_path, "nested/source.txt")
    assert data == b"dirfd exact bytes"
    assert info.st_size == len(data)
    assert len(dirfd_calls) >= 2
    assert dirfd_calls[-1][0] == "source.txt"
    assert all(flags & os.O_NOFOLLOW for _, flags, _ in dirfd_calls)
    assert dirfd_calls[-1][1] & os.O_NONBLOCK

    alias = tmp_path / "alias"
    try:
        alias.symlink_to(nested, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is unavailable")
    with pytest.raises(SnapshotAdmissionError, match="reparse_point_forbidden"):
        _posix_read_stable_source(tmp_path, "alias/source.txt")


def test_posix_root_ancestor_swap_after_resolution_is_rejected(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX root walk is platform-specific")
    parent = tmp_path / "parent"
    root = parent / "root"
    root.mkdir(parents=True)
    (root / "source.txt").write_bytes(b"admitted bytes")
    snapshot = create_snapshot(root, ["source.txt"])

    decoy_parent = tmp_path / "decoy-parent"
    decoy_root = decoy_parent / "root"
    decoy_root.mkdir(parents=True)
    (decoy_root / "source.txt").write_bytes(b"untrusted replacement")
    lexical_root = root.absolute()
    assert lexical_root.resolve() == root.resolve()

    open_chain = snapshot_module._open_posix_directory_chain

    def swap_after_root_resolution(path, flags):
        assert path == lexical_root
        parent.rename(tmp_path / "saved-parent")
        parent.symlink_to(decoy_parent, target_is_directory=True)
        return open_chain(path, flags)

    monkeypatch.setattr(snapshot_module, "_open_posix_directory_chain", swap_after_root_resolution)
    result = retrieve_exact(lexical_root, snapshot, "source.txt")
    assert result.status is RetrievalStatus.UNSAFE
    assert result.data is None


def test_posix_final_symlink_replacement_is_not_followed(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX dirfd walk is platform-specific")
    source = tmp_path / "source.txt"
    source.write_bytes(b"original")
    snapshot = create_snapshot(tmp_path, ["source.txt"])
    replacement = tmp_path / "replacement.txt"
    replacement.write_bytes(b"substitute")
    real_open = snapshot_module._open_posix_relative

    def replace_before_open(path, flags, parent_fd):
        if path == "source.txt":
            os.unlink(path, dir_fd=parent_fd)
            os.symlink(replacement, path, dir_fd=parent_fd)
        return real_open(path, flags, parent_fd)

    monkeypatch.setattr(snapshot_module, "_open_posix_relative", replace_before_open)
    result = retrieve_exact(tmp_path, snapshot, "source.txt")
    assert result.status is RetrievalStatus.UNSAFE
    assert result.data is None


def test_path_length_is_bounded_before_normalization(tmp_path):
    with pytest.raises(SnapshotAdmissionError, match="source_path_length_limit_exceeded"):
        create_snapshot(tmp_path, ["a" * (MAX_SOURCE_PATH_CHARS + 1)])


@pytest.mark.parametrize(
    ("paths", "error"),
    [
        (["../outside.txt"], "parent_path_forbidden"),
        (["/absolute.txt"], "absolute_path_forbidden"),
        (["C:\\absolute.txt"], "absolute_path_forbidden"),
        (["stream:name.txt"], "alternate_data_stream_forbidden"),
        (["trailing. "], "ambiguous_windows_component"),
        (["a/./b", "a\\b"], "duplicate_source_path"),
        (["."], "empty_relative_path"),
    ],
)
def test_unsafe_and_duplicate_paths_are_rejected(tmp_path, paths, error):
    with pytest.raises(SnapshotAdmissionError, match=error):
        create_snapshot(tmp_path, paths)


def test_non_regular_and_oversized_files_are_rejected(tmp_path):
    (tmp_path / "directory").mkdir()
    with pytest.raises(SnapshotAdmissionError, match="non_regular_source"):
        create_snapshot(tmp_path, ["directory"])

    (tmp_path / "large.bin").write_bytes(b"x" * (MAX_SOURCE_BYTES + 1))
    with pytest.raises(SnapshotAdmissionError, match="source_size_limit_exceeded"):
        create_snapshot(tmp_path, ["large.bin"])


def test_file_count_and_aggregate_limits_are_rejected(tmp_path):
    many = tmp_path / "many"
    many.mkdir()
    for index in range(MAX_SNAPSHOT_FILES + 1):
        (many / f"{index:03}.txt").write_bytes(b"x")
    with pytest.raises(SnapshotAdmissionError, match="source_count_limit_exceeded"):
        create_snapshot(many, (f"{index:03}.txt" for index in range(MAX_SNAPSHOT_FILES + 1)))

    total = tmp_path / "total"
    total.mkdir()
    # Every individual file is within its cap; their selected total is not.
    count = MAX_SNAPSHOT_BYTES // MAX_SOURCE_BYTES + 1
    paths = []
    for index in range(count):
        name = f"{index:02}.bin"
        (total / name).write_bytes(b"x" * MAX_SOURCE_BYTES)
        paths.append(name)
    with pytest.raises(SnapshotAdmissionError, match="snapshot_size_limit_exceeded"):
        create_snapshot(total, paths)


def test_symlink_is_rejected_for_snapshot_and_read(tmp_path):
    target = tmp_path / "target.txt"
    target.write_bytes(b"contents")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(SnapshotAdmissionError, match="reparse_point_forbidden"):
        create_snapshot(tmp_path, ["link.txt"])

    (tmp_path / "safe.txt").write_bytes(b"safe")
    snapshot = create_snapshot(tmp_path, ["safe.txt"])
    (tmp_path / "safe.txt").unlink()
    link.rename(tmp_path / "safe.txt")
    result = retrieve_exact(tmp_path, snapshot, "safe.txt")
    assert result.status is RetrievalStatus.UNSAFE
    assert result.data is None


def test_invalid_and_unbounded_path_container_is_rejected(tmp_path):
    with pytest.raises(SnapshotAdmissionError, match="paths_must_be_finite_iterable"):
        create_snapshot(tmp_path, "source.txt")
