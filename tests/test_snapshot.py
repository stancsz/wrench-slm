from __future__ import annotations

from dataclasses import replace
from pathlib import Path
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
    SourceRootBinding,
    SourceRecord,
    SourceSnapshot,
    _has_reparse_attribute,
    _posix_read_stable_source,
    _windows_read_stable_source,
    bind_source_root,
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


def test_snapshot_rejects_byte_identical_replacement_at_same_root_path(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_bytes(b"same bytes")
    snapshot = create_snapshot(root, ["source.txt"])

    saved = tmp_path / "saved-project"
    replacement = tmp_path / "replacement-project"
    replacement.mkdir()
    (replacement / "source.txt").write_bytes(b"same bytes")
    root.rename(saved)
    replacement.rename(root)

    result = retrieve_exact(root, snapshot, "source.txt")
    assert result.status is RetrievalStatus.UNKNOWN_SNAPSHOT
    assert result.data is None


def test_create_snapshot_rejects_root_replacement_between_source_reads(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_bytes(b"same root")
    (root / "b.txt").write_bytes(b"same root")
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    (replacement / "a.txt").write_bytes(b"same root")
    (replacement / "b.txt").write_bytes(b"same root")
    saved = tmp_path / "saved-project"
    real_read = snapshot_module._read_stable_source

    def swap_between_reads(path, relative_path, expected_root_identity=None):
        if relative_path == "b.txt":
            root.rename(saved)
            replacement.rename(root)
        return real_read(path, relative_path, expected_root_identity)

    monkeypatch.setattr(snapshot_module, "_read_stable_source", swap_between_reads)
    with pytest.raises(SnapshotAdmissionError, match="snapshot_root_identity_mismatch"):
        create_snapshot(root, ["a.txt", "b.txt"])


def test_bound_root_rejects_replacement_during_caller_path_iteration(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_bytes(b"authorized root")
    binding = bind_source_root(root)
    assert type(binding) is SourceRootBinding

    replacement = tmp_path / "replacement"
    replacement.mkdir()
    (replacement / "source.txt").write_bytes(b"replacement root")
    saved = tmp_path / "saved-project"

    def replacing_paths():
        root.rename(saved)
        replacement.rename(root)
        yield "source.txt"

    with pytest.raises(SnapshotAdmissionError, match="snapshot_root_identity_mismatch"):
        create_snapshot(binding, replacing_paths())


def test_exact_retrieval_accepts_bound_root_and_rejects_same_path_replacement(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_bytes(b"same source")
    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, ["source.txt"])

    result = retrieve_exact(binding, snapshot, "source.txt")
    assert result.status is RetrievalStatus.OK
    assert result.data == b"same source"

    saved = tmp_path / "saved-project"
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    (replacement / "source.txt").write_bytes(b"same source")
    root.rename(saved)
    replacement.rename(root)

    replaced = retrieve_exact(binding, snapshot, "source.txt")
    assert replaced.status is RetrievalStatus.UNKNOWN_SNAPSHOT
    assert replaced.data is None


def test_plain_root_is_bound_before_caller_path_iteration(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "source.txt").write_bytes(b"original root")
    replacement = tmp_path / "replacement"
    replacement.mkdir()
    (replacement / "source.txt").write_bytes(b"replacement root")
    saved = tmp_path / "saved-project"

    def replacing_paths():
        root.rename(saved)
        replacement.rename(root)
        yield "source.txt"

    with pytest.raises(SnapshotAdmissionError, match="snapshot_root_identity_mismatch"):
        create_snapshot(root, replacing_paths())


def test_root_binding_rejects_replacement_during_directory_handle_capture(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX directory-handle race")
    root = tmp_path / "selected-root-race"
    replacement = tmp_path / "replacement-root-race"
    saved = tmp_path / "saved-root-race"
    root.mkdir()
    replacement.mkdir()
    real_open = snapshot_module._open_posix_relative
    swapped = False

    def replace_before_open(name, flags, parent_fd):
        nonlocal swapped
        if name == root.name and not swapped:
            swapped = True
            root.rename(saved)
            replacement.rename(root)
        return real_open(name, flags, parent_fd)

    monkeypatch.setattr(snapshot_module, "_open_posix_relative", replace_before_open)
    with pytest.raises(SnapshotAdmissionError, match="root_directory_binding_changed"):
        bind_source_root(root)
    assert swapped


def test_public_root_binding_requires_absolute_configured_path(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    binding = bind_source_root(root)
    relative = Path("relative-root")
    malformed = replace(
        binding,
        configured_root=relative,
        root_location_sha256=snapshot_module._root_location_sha256(relative),
    )

    with pytest.raises(SnapshotAdmissionError, match="invalid_root_binding"):
        create_snapshot(malformed, ["source.txt"])


def test_root_binding_maps_missing_posix_dir_fd_support_to_admission_error(tmp_path, monkeypatch):
    if os.name == "nt":
        pytest.skip("POSIX dir_fd capability check")
    root = tmp_path / "root"
    root.mkdir()
    monkeypatch.setattr(os, "supports_dir_fd", set())

    with pytest.raises(SnapshotAdmissionError, match="secure_dirfd_unavailable"):
        bind_source_root(root)


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
        replace(valid, schema="wrench.source-snapshot.v2"),
        replace(valid, root_location_sha256="0" * 64),
        replace(valid, root_identity=None),
        replace(valid, root_identity="invalid"),
        replace(valid, root_identity="win:0000000000000000:00000000000000000000000000000001"),
        replace(valid, sources=(SourceRecord("../escape", 1, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", True, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", MAX_SOURCE_BYTES + 1, valid_digest),)),
        replace(valid, sources=(SourceRecord("source.txt", 1, "not-a-digest"),)),
        SourceSnapshot(valid.schema, too_many, valid_digest, valid.root_location_sha256, valid.root_identity),
        SourceSnapshot(valid.schema, too_large, valid_digest, valid.root_location_sha256, valid.root_identity),
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
    data, info, identity = _windows_read_stable_source(tmp_path, "nested/source.txt")
    assert data == b"pinned exact bytes"
    assert info.st_size == len(data)
    assert identity.startswith("win:")


def test_windows_resolved_root_through_static_ancestor_symlink(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows native handle walk is platform-specific")
    target_parent = tmp_path / "target"
    root = target_parent / "project"
    root.mkdir(parents=True)
    (root / "source.txt").write_bytes(b"junction target bytes")
    alias_parent = tmp_path / "alias"
    try:
        alias_parent.symlink_to(target_parent, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is unavailable")

    configured_root = alias_parent / "project"
    snapshot = create_snapshot(configured_root, ["source.txt"])
    result = retrieve_exact(configured_root, snapshot, "source.txt")

    assert result.status is RetrievalStatus.OK
    assert result.data == b"junction target bytes"


def test_windows_root_ancestor_swap_before_handle_walk_fails_closed(tmp_path, monkeypatch):
    if os.name != "nt":
        pytest.skip("Windows native handle walk is platform-specific")
    parent = tmp_path / "original-parent"
    root = parent / "project"
    root.mkdir(parents=True)
    (root / "source.txt").write_bytes(b"same bytes")
    snapshot = create_snapshot(root, ["source.txt"])

    decoy_parent = tmp_path / "decoy-parent"
    decoy_root = decoy_parent / "project"
    decoy_root.mkdir(parents=True)
    (decoy_root / "source.txt").write_bytes(b"same bytes")
    saved_parent = tmp_path / "saved-parent"
    real_read = snapshot_module._windows_read_stable_source

    def swap_before_root_open(path, relative_path, expected_root_identity=None):
        assert path == root.resolve()
        parent.rename(saved_parent)
        try:
            parent.symlink_to(decoy_parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            saved_parent.rename(parent)
            pytest.skip("directory symlink creation is unavailable")
        try:
            return real_read(path, relative_path, expected_root_identity)
        finally:
            parent.unlink()
            saved_parent.rename(parent)

    monkeypatch.setattr(snapshot_module, "_windows_read_stable_source", swap_before_root_open)
    result = retrieve_exact(root, snapshot, "source.txt")

    assert result.status is RetrievalStatus.UNSAFE
    assert result.data is None


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
    data, info, identity = _posix_read_stable_source(tmp_path, "nested/source.txt")
    assert data == b"dirfd exact bytes"
    assert info.st_size == len(data)
    assert identity.startswith("posix:")
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
