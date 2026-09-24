from __future__ import annotations

import hashlib

import pytest

import wrench_harness.artifact_store as store_module
from wrench_harness.artifact_store import (
    ArtifactHandle,
    ArtifactReadStatus,
    ArtifactStore,
    ArtifactStoreCorruption,
    ArtifactStoreLimitError,
)


def _put(store, snapshot, path, data):
    return store.put(
        snapshot_sha256=hashlib.sha256(snapshot.encode()).hexdigest(),
        source_path=path,
        expected_content_sha256=hashlib.sha256(data).hexdigest(),
        data=data,
    )


def test_content_addressed_round_trip_and_reopen(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    data = b"bounded exact artifact\x00"
    handle = _put(store, "snapshot-a", "src/example.py", data)

    assert handle.content_sha256 == hashlib.sha256(data).hexdigest()
    assert store.read(handle).status is ArtifactReadStatus.OK
    assert store.read(handle).data == data
    assert list(store.objects.iterdir())[0].name == f"{handle.content_sha256}.blob"

    reopened = ArtifactStore(tmp_path / "store")
    assert reopened.read(handle).data == data


def test_source_identity_and_expected_content_hash_are_bound(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    data = b"evidence"
    handle = _put(store, "snapshot-a", "src/a.py", data)
    other_snapshot = _put(store, "snapshot-b", "src/a.py", data)
    other_path = _put(store, "snapshot-a", "src/b.py", data)

    assert len(list(store.objects.iterdir())) == 1
    assert len({handle.handle_id, other_snapshot.handle_id, other_path.handle_id}) == 3
    with pytest.raises(ValueError, match="source_content_hash_mismatch"):
        store.put(
            snapshot_sha256=hashlib.sha256(b"snapshot-a").hexdigest(),
            source_path="src/a.py",
            expected_content_sha256="0" * 64,
            data=data,
        )


def test_malformed_public_handle_fails_as_missing(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    malformed = ArtifactHandle([], "source", "0" * 64, 1, "0" * 64)
    assert store.read(malformed).status is ArtifactReadStatus.MISSING


def test_hard_object_and_object_count_limits(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path / "size-store")
    monkeypatch.setattr(store_module, "MAX_OBJECT_BYTES", 8)
    with pytest.raises(ArtifactStoreLimitError, match="object_size_limit_exceeded"):
        _put(store, "snapshot", "a", b"123456789")

    count_store = ArtifactStore(tmp_path / "count-store")
    _put(count_store, "snapshot", "a", b"one")
    monkeypatch.setattr(store_module, "MAX_OBJECT_COUNT", 1)
    with pytest.raises(ArtifactStoreLimitError, match="object_count_limit_exceeded"):
        _put(count_store, "snapshot", "b", b"two")


def test_aggregate_limit_stops_growth_before_write(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path / "store")
    before = store._disk_usage()
    monkeypatch.setattr(store_module, "MAX_STORE_BYTES", before + 1)
    with pytest.raises(ArtifactStoreLimitError, match="aggregate_store_limit_exceeded"):
        _put(store, "snapshot", "a", b"payload")
    assert not list(store.objects.iterdir())


def test_manifest_recovery_restores_only_valid_previous_generation(tmp_path):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    first = _put(store, "snapshot", "a", b"first")
    _put(store, "snapshot", "b", b"second")
    (root / "manifest.json").write_bytes(b"partial manifest")

    recovered = ArtifactStore(root)
    assert recovered.recovery_status == "restored_previous_manifest"
    assert recovered.read(first).status is ArtifactReadStatus.OK
    assert recovered.read(recovered._entry_handle(recovered._payload["entries"][0])).status is ArtifactReadStatus.OK
    assert len(recovered._payload["entries"]) == 1


def test_no_valid_manifest_reports_corruption_without_deleting_data(tmp_path):
    root = tmp_path / "store"
    ArtifactStore(root)
    keep = root / "manifest.json"
    keep.write_bytes(b"corrupt")
    before = keep.read_bytes()
    with pytest.raises(ArtifactStoreCorruption, match="no valid current or previous manifest"):
        ArtifactStore(root)
    assert keep.read_bytes() == before


def test_unrecognized_user_entries_fail_closed_and_are_preserved(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    user_file = root / "notes.txt"
    user_file.write_bytes(b"keep me")

    with pytest.raises(ArtifactStoreCorruption, match="unrecognized root entry"):
        ArtifactStore(root)
    assert user_file.read_bytes() == b"keep me"


def test_request_pins_block_eviction_then_release_and_tombstone(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    pinned = _put(store, "snapshot", "a", b"pinned")
    eligible = _put(store, "snapshot", "b", b"eligible")
    with store.request() as request:
        assert request.pin(pinned).data == b"pinned"
        evicted = store.evict(target_bytes=len(b"eligible"))
        assert [handle.handle_id for handle in evicted.handles] == [eligible.handle_id]
        assert store.read(pinned).status is ArtifactReadStatus.OK
        assert store.read(eligible).status is ArtifactReadStatus.EVICTED

    second = store.evict(target_bytes=len(b"pinned"))
    assert [handle.handle_id for handle in second.handles] == [pinned.handle_id]
    assert second.object_bytes_reclaimed == len(b"pinned")
    assert store.read(pinned).status is ArtifactReadStatus.EVICTED
    assert ArtifactStore(tmp_path / "store").read(pinned).status is ArtifactReadStatus.EVICTED


def test_eviction_is_deterministic_by_generation_then_handle_id(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    first = _put(store, "snapshot", "first", b"one")
    second = _put(store, "snapshot", "second", b"two")
    result = store.evict(target_bytes=1)
    assert result.handles == (first,)
    assert store.read(second).status is ArtifactReadStatus.OK


def test_corrupt_object_is_an_explicit_read_miss(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    handle = _put(store, "snapshot", "a", b"original")
    (store.objects / f"{handle.content_sha256}.blob").write_bytes(b"tampered")
    assert store.read(handle).status is ArtifactReadStatus.CORRUPT


def test_interrupted_stage_is_retained_never_promoted_or_deleted(tmp_path):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    staged = store.staging / ("stage-" + "a" * 32 + ".tmp")
    staged.write_bytes(b"partial object")

    reopened = ArtifactStore(root)
    assert reopened.recovery_status.endswith("staging_retained")
    assert staged.read_bytes() == b"partial object"
    assert reopened.read(  # unknown identity remains a miss
        type("Unknown", (), {})()
    ).status is ArtifactReadStatus.MISSING


def test_atomic_manifest_write_rejects_ninth_existing_stage(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    for index in range(store_module.MAX_STAGING_FILES):
        (store.staging / f"stage-{index:032x}.tmp").write_bytes(b"x")
    before = (store.root / "manifest.json").read_bytes()

    with pytest.raises(ArtifactStoreLimitError, match="staging_file_count_limit_exceeded"):
        store._atomic_write(store.root / "manifest.json", before)
    assert len(list(store.staging.iterdir())) == store_module.MAX_STAGING_FILES
    assert (store.root / "manifest.json").read_bytes() == before


def test_object_put_rejects_ninth_existing_stage_before_write(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    for index in range(store_module.MAX_STAGING_FILES):
        (store.staging / f"stage-{index:032x}.tmp").write_bytes(b"x")

    with pytest.raises(ArtifactStoreLimitError, match="staging_file_count_limit_exceeded"):
        _put(store, "snapshot", "a", b"object")
    assert len(list(store.staging.iterdir())) == store_module.MAX_STAGING_FILES
    assert not list(store.objects.iterdir())


@pytest.mark.parametrize(
    "bad_manifest",
    [
        b"[" * 2000 + b"]" * 2000,
        (
            b'{"payload":{"schema":"wrench.artifact-store.v1","generation":0,'
            b'"entries":[],"evicted":[],"extra":"\\ud800"},"sha256":"'
            + b"0" * 64
            + b'"}'
        ),
    ],
    ids=["deep-json", "escaped-lone-surrogate"],
)
def test_unencodable_or_deep_current_manifest_recovers_valid_previous(tmp_path, bad_manifest):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    first = _put(store, "snapshot", "a", b"known good")
    _put(store, "snapshot", "b", b"new generation")
    (root / "manifest.json").write_bytes(bad_manifest)

    recovered = ArtifactStore(root)
    assert recovered.recovery_status == "restored_previous_manifest"
    assert recovered.read(first).status is ArtifactReadStatus.OK
    assert recovered.read(first).data == b"known good"


def test_stage_file_count_and_size_are_bounded(tmp_path):
    root = tmp_path / "store-count"
    store = ArtifactStore(root)
    for index in range(store_module.MAX_STAGING_FILES + 1):
        (store.staging / f"stage-{index:032x}.tmp").write_bytes(b"x")
    with pytest.raises(ArtifactStoreLimitError, match="staging_file_count_limit_exceeded"):
        ArtifactStore(root)

    size_root = tmp_path / "store-size"
    size_store = ArtifactStore(size_root)
    staged = size_store.staging / ("stage-" + "f" * 32 + ".tmp")
    staged.write_bytes(b"x" * (store_module.MAX_STAGING_FILE_BYTES + 1))
    with pytest.raises(ArtifactStoreLimitError, match="staging_file_size_limit_exceeded"):
        ArtifactStore(size_root)


def test_dangling_manifest_symlink_is_not_treated_as_missing(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    manifest_link = root / "manifest.json"
    try:
        manifest_link.symlink_to(root / "absent-target.json")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ArtifactStoreCorruption, match="unsafe store entry"):
        ArtifactStore(root)
    assert manifest_link.is_symlink()


def test_manifest_size_limit_is_hard(tmp_path, monkeypatch):
    store = ArtifactStore(tmp_path / "store")
    monkeypatch.setattr(store_module, "MAX_MANIFEST_BYTES", 16)
    with pytest.raises(ArtifactStoreLimitError, match="manifest_size_limit_exceeded"):
        _put(store, "snapshot", "a", b"bytes")
    assert not list(store.objects.iterdir())


def test_manifest_and_identity_paths_are_bounded_and_canonical(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    with pytest.raises(ValueError, match="parent_source_path_forbidden"):
        _put(store, "snapshot", "../outside", b"bytes")
    with pytest.raises(ValueError, match="alternate_data_stream_forbidden"):
        _put(store, "snapshot", "file.txt:secret", b"bytes")


def test_root_layout_rejects_symlinked_objects_directory(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    try:
        (root / "objects").symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ArtifactStoreCorruption, match="unsafe store directory"):
        ArtifactStore(root)


def test_root_chain_rejects_symlinked_ancestor_before_creating_target(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    ancestor_link = tmp_path / "ancestor-link"
    target_root = ancestor_link / "new-store"
    try:
        ancestor_link.symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")

    with pytest.raises(ArtifactStoreCorruption, match="root chain contains an unsafe component"):
        ArtifactStore(target_root)
    assert not (external / "new-store").exists()
    assert not target_root.exists()
