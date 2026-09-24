from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

import wrench_harness.artifact_store as store_module
from wrench_harness.artifact_store import (
    ArtifactHandle,
    ArtifactReadStatus,
    ArtifactStore,
    ArtifactStoreCorruption,
    ArtifactStoreLimitError,
)


def _put(store, snapshot, path, data, *, disposition="protected", expires_at_unix_seconds=None):
    return store.put(
        snapshot_sha256=hashlib.sha256(snapshot.encode()).hexdigest(),
        source_path=path,
        expected_content_sha256=hashlib.sha256(data).hexdigest(),
        data=data,
        disposition=disposition,
        expires_at_unix_seconds=expires_at_unix_seconds,
    )


def _write_manifest(path, payload):
    body = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    envelope = {"payload": payload, "sha256": hashlib.sha256(body).hexdigest()}
    encoded = json.dumps(
        envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path.write_bytes(encoded)


def _store_disk_state(store):
    return {
        "manifest": (store.root / "manifest.json").read_bytes(),
        "previous": (store.root / "manifest.prev.json").read_bytes() if (store.root / "manifest.prev.json").exists() else None,
        "objects": {item.name: item.read_bytes() for item in sorted(store.objects.iterdir())},
        "staging": {item.name: item.read_bytes() for item in sorted(store.staging.iterdir())},
    }


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


def test_put_requires_projected_write_and_five_gigabyte_volume_reserve(tmp_path):
    available = [10_000_000_000]
    next_values = []
    probe_calls = []

    def probe(path):
        probe_calls.append(path)
        if next_values:
            return next_values.pop(0)
        return available[0]

    store = ArtifactStore(tmp_path / "store", free_space_probe=probe)
    probe_calls.clear()
    data = b"headroom boundary"
    available[0] = store_module.MIN_FREE_SPACE_BYTES + len(data) - 1
    with pytest.raises(ArtifactStoreLimitError, match="physical_volume_headroom_insufficient"):
        _put(store, "snapshot", "a", data)

    assert probe_calls == [store.root]
    assert not list(store.objects.iterdir())
    assert not list(store.staging.iterdir())

    next_values.extend([store_module.MIN_FREE_SPACE_BYTES + len(data), 10_000_000_000, 10_000_000_000])
    handle = _put(store, "snapshot", "a", data)
    assert store.read(handle).data == data


def test_manifest_save_headroom_failure_leaves_old_manifest_and_read_path_usable(tmp_path):
    available = [10_000_000_000]
    probe_calls = []

    def probe(path):
        probe_calls.append(path)
        return available[0]

    store = ArtifactStore(tmp_path / "store", free_space_probe=probe)
    first = _put(store, "snapshot", "first", b"shared bytes")
    before_manifest = (store.root / "manifest.json").read_bytes()
    probe_calls.clear()

    # The second handle reuses the existing object, so the next guarded write
    # is a manifest staging write.
    available[0] = store_module.MIN_FREE_SPACE_BYTES
    with pytest.raises(ArtifactStoreLimitError, match="physical_volume_headroom_insufficient"):
        _put(store, "snapshot", "second", b"shared bytes")

    assert probe_calls == [store.root]
    assert (store.root / "manifest.json").read_bytes() == before_manifest
    assert store.read(first).data == b"shared bytes"
    assert not list(store.staging.iterdir())


@pytest.mark.parametrize("probe_result", [None, -1, True])
def test_invalid_or_unavailable_volume_headroom_fails_closed(tmp_path, probe_result):
    store = ArtifactStore(tmp_path / "store", free_space_probe=lambda _path: 10_000_000_000)
    store._free_space_probe = lambda _path: probe_result

    with pytest.raises(ArtifactStoreLimitError, match="physical_volume_headroom_insufficient"):
        _put(store, "snapshot", "a", b"payload")
    assert not list(store.objects.iterdir())


def test_volume_probe_error_fails_closed_before_write(tmp_path):
    store = ArtifactStore(tmp_path / "store", free_space_probe=lambda _path: 10_000_000_000)

    def unavailable(_path):
        raise OSError("fixture volume unavailable")

    store._free_space_probe = unavailable
    with pytest.raises(ArtifactStoreLimitError, match="physical_volume_headroom_unavailable"):
        _put(store, "snapshot", "a", b"payload")
    assert not list(store.objects.iterdir())


def test_read_only_read_does_not_probe_volume_headroom(tmp_path):
    probe_calls = []
    store = ArtifactStore(
        tmp_path / "store",
        free_space_probe=lambda path: probe_calls.append(path) or 10_000_000_000,
    )
    handle = _put(store, "snapshot", "a", b"payload")
    probe_calls.clear()

    assert store.read(handle).data == b"payload"
    assert probe_calls == []


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


def test_oversized_current_manifest_recovers_valid_previous_generation(tmp_path):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    first = _put(store, "snapshot", "a", b"first")
    _put(store, "snapshot", "b", b"second")
    (root / "manifest.json").write_bytes(
        b"x" * (store_module.MAX_MANIFEST_BYTES + 1)
    )

    recovered = ArtifactStore(root)

    assert recovered.recovery_status == "restored_previous_manifest"
    assert recovered.read(first).data == b"first"
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
    pinned = _put(store, "snapshot", "a", b"pinned", disposition="disposable", expires_at_unix_seconds=10)
    eligible = _put(store, "snapshot", "b", b"eligible", disposition="disposable", expires_at_unix_seconds=10)
    with store.request() as request:
        assert request.pin(pinned).data == b"pinned"
        evicted = store.evict(target_bytes=len(b"eligible"), now_unix_seconds=10)
        assert [handle.handle_id for handle in evicted.handles] == [eligible.handle_id]
        assert store.read(pinned).status is ArtifactReadStatus.OK
        assert store.read(eligible).status is ArtifactReadStatus.EVICTED

    second = store.evict(target_bytes=len(b"pinned"), now_unix_seconds=10)
    assert [handle.handle_id for handle in second.handles] == [pinned.handle_id]
    assert second.object_bytes_reclaimed == len(b"pinned")
    assert store.read(pinned).status is ArtifactReadStatus.EVICTED
    assert ArtifactStore(tmp_path / "store").read(pinned).status is ArtifactReadStatus.EVICTED


def test_request_pin_scope_duration_is_null_while_open_then_measured(tmp_path, monkeypatch):
    clock_values = iter((100, 137))
    monkeypatch.setattr(
        store_module, "time", SimpleNamespace(monotonic_ns=lambda: next(clock_values))
    )
    store = ArtifactStore(tmp_path / "store")
    request = store.request()

    assert request.pin_scope_duration_ns is None
    with request:
        assert request.pin_scope_duration_ns is None

    assert request.pin_scope_duration_ns == 37


def test_request_pin_scope_duration_is_recorded_on_exception_exit(tmp_path, monkeypatch):
    clock_values = iter((200, 245))
    monkeypatch.setattr(
        store_module, "time", SimpleNamespace(monotonic_ns=lambda: next(clock_values))
    )
    store = ArtifactStore(tmp_path / "store")
    request = store.request()

    with pytest.raises(RuntimeError, match="synthetic failure"):
        with request:
            request.pin(
                _put(
                    store,
                    "snapshot",
                    "exception.py",
                    b"pinned",
                    disposition="disposable",
                    expires_at_unix_seconds=10,
                )
            )
            raise RuntimeError("synthetic failure")

    assert request.pin_scope_duration_ns == 45
    evicted = store.evict(target_bytes=len(b"pinned"), now_unix_seconds=10)
    assert len(evicted.handles) == 1


def test_request_pin_scope_duration_is_unchanged_by_repeated_exit(tmp_path, monkeypatch):
    clock_values = iter((300, 360))
    monkeypatch.setattr(
        store_module, "time", SimpleNamespace(monotonic_ns=lambda: next(clock_values))
    )
    request = ArtifactStore(tmp_path / "store").request()
    request.__enter__()
    request.__exit__(None, None, None)
    duration = request.pin_scope_duration_ns
    request.__exit__(None, None, None)

    assert duration == 60
    assert request.pin_scope_duration_ns == duration


def test_separate_request_pin_scopes_have_independent_durations(tmp_path, monkeypatch):
    clock_values = iter((400, 405, 500, 512))
    monkeypatch.setattr(
        store_module, "time", SimpleNamespace(monotonic_ns=lambda: next(clock_values))
    )
    store = ArtifactStore(tmp_path / "store")

    with store.request() as first:
        assert first.pin_scope_duration_ns is None
    with store.request() as second:
        assert second.pin_scope_duration_ns is None

    assert first.pin_scope_duration_ns == 5
    assert second.pin_scope_duration_ns == 12


def test_eviction_is_deterministic_by_generation_then_handle_id(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    first = _put(store, "snapshot", "first", b"one", disposition="disposable", expires_at_unix_seconds=10)
    second = _put(store, "snapshot", "second", b"two", disposition="disposable", expires_at_unix_seconds=10)
    result = store.evict(target_bytes=1, now_unix_seconds=10)
    assert result.handles == (first,)
    assert store.read(second).status is ArtifactReadStatus.OK


@pytest.mark.parametrize("blocked_reference", ["protected", "unexpired"])
def test_shared_content_is_not_evicted_when_any_reference_is_ineligible(tmp_path, blocked_reference):
    store = ArtifactStore(tmp_path / "store")
    data = b"shared object"
    eligible = _put(store, "snapshot", "eligible.py", data, disposition="disposable", expires_at_unix_seconds=10)
    if blocked_reference == "protected":
        blocked = _put(store, "snapshot", "protected.py", data)
    else:
        blocked = _put(store, "snapshot", "unexpired.py", data, disposition="disposable", expires_at_unix_seconds=11)
    before = _store_disk_state(store)

    result = store.evict(target_bytes=len(data), now_unix_seconds=10)

    assert result.handles == ()
    assert result.object_bytes_reclaimed == 0
    assert _store_disk_state(store) == before
    assert store.read(eligible).data == data
    assert store.read(blocked).data == data


def test_unreachable_eviction_target_leaves_all_store_state_unchanged(tmp_path):
    store = ArtifactStore(tmp_path / "store")
    first = _put(store, "snapshot", "first.py", b"one", disposition="disposable", expires_at_unix_seconds=10)
    second = _put(store, "snapshot", "second.py", b"two", disposition="disposable", expires_at_unix_seconds=10)
    protected = _put(store, "snapshot", "protected.py", b"keep")
    before_disk = _store_disk_state(store)
    before_payload = json.loads(json.dumps(store._payload))

    result = store.evict(target_bytes=7, now_unix_seconds=10)

    assert result.handles == ()
    assert result.object_bytes_reclaimed == 0
    assert _store_disk_state(store) == before_disk
    assert store._payload == before_payload
    for handle in (first, second, protected):
        assert store.read(handle).status is ArtifactReadStatus.OK


def test_legacy_v1_records_migrate_as_protected_without_changing_handle_identity(tmp_path):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    legacy_handle = _put(store, "legacy-snapshot", "src/legacy.py", b"legacy bytes")
    legacy_payload = {
        "schema": "wrench.artifact-store.v1",
        "generation": store._payload["generation"],
        "entries": [
            {key: value for key, value in entry.items() if key not in {"disposition", "expires_at_unix_seconds"}}
            for entry in store._payload["entries"]
        ],
        "evicted": store._payload["evicted"],
    }
    _write_manifest(root / "manifest.json", legacy_payload)
    _write_manifest(root / "manifest.prev.json", legacy_payload)

    migrated = ArtifactStore(root)
    normalized = migrated._payload["entries"][0]
    before = _store_disk_state(migrated)
    attempted = migrated.evict(target_bytes=len(b"legacy bytes"), now_unix_seconds=10**9)

    assert normalized["disposition"] == "protected"
    assert normalized["expires_at_unix_seconds"] is None
    assert migrated.read(legacy_handle).data == b"legacy bytes"
    assert attempted.handles == ()
    assert _store_disk_state(migrated) == before
    with pytest.raises(ValueError, match="artifact_retention_conflict"):
        _put(migrated, "legacy-snapshot", "src/legacy.py", b"legacy bytes", disposition="disposable", expires_at_unix_seconds=10)

    new_handle = _put(migrated, "new-snapshot", "src/new.py", b"new bytes", disposition="disposable", expires_at_unix_seconds=10)
    current = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["payload"]
    assert current["schema"] == "wrench.artifact-store.v2"
    persisted_legacy = next(row for row in current["entries"] if row["handle_id"] == legacy_handle.handle_id)
    assert persisted_legacy["disposition"] == "protected"
    assert persisted_legacy["expires_at_unix_seconds"] is None
    assert persisted_legacy["handle_id"] == legacy_handle.handle_id
    assert ArtifactStore(root).read(legacy_handle).data == b"legacy bytes"
    assert migrated.read(new_handle).data == b"new bytes"


@pytest.mark.parametrize(
    "interruption",
    ["before_second_commit", "during_second_manifest_replace", "after_second_commit"],
)
def test_eviction_recovery_across_manifest_commit_interruption(tmp_path, monkeypatch, interruption):
    root = tmp_path / "store"
    store = ArtifactStore(root)
    handle = _put(store, "snapshot", "a.py", b"disposable", disposition="disposable", expires_at_unix_seconds=10)
    original_commit = store._commit
    original_atomic_write = store._atomic_write
    calls = 0
    writes = 0

    def interrupted_commit(payload):
        nonlocal calls
        calls += 1
        if calls == 2 and interruption == "before_second_commit":
            raise RuntimeError("simulated interruption before second manifest commit")
        original_commit(payload)
        if calls == 2 and interruption == "after_second_commit":
            raise RuntimeError("simulated interruption after second manifest commit")

    def interrupted_atomic_write(destination, data):
        nonlocal writes
        writes += 1
        if writes == 4 and interruption == "during_second_manifest_replace":
            raise RuntimeError("simulated interruption between manifest slot replacements")
        original_atomic_write(destination, data)

    if interruption == "during_second_manifest_replace":
        monkeypatch.setattr(store, "_atomic_write", interrupted_atomic_write)
    else:
        monkeypatch.setattr(store, "_commit", interrupted_commit)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        store.evict(target_bytes=len(b"disposable"), now_unix_seconds=10)

    reopened = ArtifactStore(root)
    assert reopened.read(handle).status is ArtifactReadStatus.EVICTED
    object_path = reopened.objects / f"{handle.content_sha256}.blob"
    assert object_path.exists()
    if interruption == "before_second_commit":
        # The prior manifest still references the object, so recovery may safely restore it.
        (root / "manifest.json").write_bytes(b"interrupted current manifest")
        restored = ArtifactStore(root)
        assert restored.recovery_status == "restored_previous_manifest"
        assert restored.read(handle).data == b"disposable"
    else:
        # Both slots record eviction before deletion, so corruption cannot resurrect this handle.
        (root / "manifest.json").write_bytes(b"interrupted current manifest")
        recovered = ArtifactStore(root)
        assert recovered.recovery_status == "restored_previous_manifest"
        assert recovered.read(handle).status is ArtifactReadStatus.EVICTED


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
