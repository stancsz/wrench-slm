"""Synthetic file-only checks for the development model-version state machine."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from wrench_harness import model_lifecycle as lifecycle


SCRATCH_ROOT = Path(
    r"C:\wrench-slm-data\tmp\W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924\impl"
)
RESET_SERIALIZATION_SCRATCH_ROOT = Path(
    r"C:\wrench-slm-data\tmp\W2-NS-E3-RESET-SERIALIZATION-20260924"
)
FACTORY = {
    "foundation": b"synthetic-foundation-v1",
    "core": b"synthetic-core-v1",
    "runtime": b"runtime-id-v1",
    "tokenizer": b"tokenizer-id-v1",
    "compatibility": b"compatibility-v1",
}


@pytest.fixture
def store_root():
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="case-", dir=SCRATCH_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _new_store(path: Path) -> lifecycle.ModelLifecycle:
    return lifecycle.ModelLifecycle.create(path, factory_version_id="factory", payloads=FACTORY)


def _candidate(store: lifecycle.ModelLifecycle, version_id: str = "personal-1", *,
               overrides: dict | None = None) -> None:
    payloads = dict(FACTORY)
    payloads["personal"] = b"synthetic-personal-v1"
    payloads.update(overrides or {})
    store.stage_candidate(version_id, parent_version_id=store.active_version_id,
                          payloads=payloads)


def test_request_pin_stays_on_starting_version_after_activation(store_root):
    store = _new_store(store_root)
    old_pin = store.pin("request-before-switch")
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    new_pin = store.pin("request-after-switch")

    assert old_pin.version_id == "factory"
    assert new_pin.version_id == "personal-1"
    assert store.read_payload(old_pin, "core") == FACTORY["core"]
    with pytest.raises(lifecycle.ModelLifecycleError, match="layer_unavailable"):
        store.read_payload(old_pin, "personal")
    assert store.read_payload(new_pin, "personal") == b"synthetic-personal-v1"
    assert store.training_eligible is False
    assert store.production_activation is False


def test_incomplete_corrupt_and_incompatible_candidates_never_admit(store_root):
    store = _new_store(store_root)
    incomplete = dict(FACTORY)
    incomplete.pop("tokenizer")
    with pytest.raises(lifecycle.ModelLifecycleError, match="payload_layers_incomplete"):
        store.stage_candidate("incomplete", parent_version_id="factory", payloads=incomplete)

    _candidate(store, "corrupt")
    (store.versions_dir / "corrupt" / "personal.bin").write_bytes(b"changed")
    with pytest.raises(lifecycle.ModelLifecycleError, match="payload_corrupt"):
        store.admit_candidate("corrupt")

    _candidate(store, "incompatible", overrides={"tokenizer": b"other-tokenizer"})
    with pytest.raises(lifecycle.ModelLifecycleError, match="candidate_compatibility_mismatch"):
        store.admit_candidate("incompatible")
    assert store.active_version_id == "factory"


def test_reopen_verifies_active_and_recovers_corrupt_active_to_prior(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    reopened = lifecycle.ModelLifecycle.open(store_root)
    assert reopened.active_version_id == "personal-1"
    assert reopened.previous_version_id == "factory"

    (store.versions_dir / "personal-1" / "personal.bin").write_bytes(b"tampered")
    recovered = lifecycle.ModelLifecycle.open(store_root)
    assert recovered.active_version_id == "factory"
    assert recovered.factory_version_id == "factory"
    assert recovered.pin("after-recovery").version_id == "factory"


def test_failed_active_pointer_replace_keeps_old_version_active(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    real_replace = lifecycle.os.replace

    def fail_main_state(source, destination):
        if Path(destination) == store.state_path:
            raise OSError("synthetic interrupted pointer replace")
        return real_replace(source, destination)

    with patch.object(lifecycle.os, "replace", side_effect=fail_main_state):
        with pytest.raises(OSError, match="synthetic interrupted"):
            store.activate_candidate("personal-1")
    assert store.active_version_id == "factory"
    assert lifecycle.ModelLifecycle.open(store_root).active_version_id == "factory"


def test_rollback_and_personal_reset_preserve_factory_layers(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")

    assert store.reset_personal("reset-1") == "reset-1"
    reset_pin = store.pin("after-reset")
    assert store.read_payload(reset_pin, "foundation") == FACTORY["foundation"]
    assert store.read_payload(reset_pin, "core") == FACTORY["core"]
    with pytest.raises(lifecycle.ModelLifecycleError, match="layer_unavailable"):
        store.read_payload(reset_pin, "personal")
    assert store.rollback() == "personal-1"
    assert store.read_payload(store.pin("after-rollback"), "personal") == b"synthetic-personal-v1"
    assert lifecycle.ModelLifecycle.open(store_root).active_version_id == "personal-1"


def test_uncommitted_candidate_remains_inactive_after_reopen(store_root):
    store = _new_store(store_root)
    _candidate(store)
    reopened = lifecycle.ModelLifecycle.open(store_root)
    assert reopened.active_version_id == "factory"
    with pytest.raises(lifecycle.ModelLifecycleError, match="candidate_not_admitted"):
        reopened.activate_candidate("personal-1")


def test_open_recovers_pointer_to_unadmitted_staged_candidate(store_root):
    store = _new_store(store_root)
    _candidate(store)
    manifest = store._load_manifest("personal-1")
    state = json.loads(store.state_path.read_text(encoding="ascii"))
    state["generation"] += 1
    state["active"] = "personal-1"
    state["active_manifest_sha256"] = lifecycle._digest(lifecycle._canonical(manifest))
    store.state_path.write_bytes(lifecycle._canonical(state))

    reopened = lifecycle.ModelLifecycle.open(store_root)

    assert reopened.active_version_id == "factory"
    assert reopened.read_payload(reopened.pin("after-recovery"), "core") == FACTORY["core"]


def test_open_recovers_active_candidate_when_admission_receipt_is_missing(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    (store.admissions_dir / "personal-1.json").unlink()

    reopened = lifecycle.ModelLifecycle.open(store_root)

    assert reopened.active_version_id == "factory"
    assert reopened.previous_version_id is None


def test_manifest_tampering_and_missing_prior_fail_closed(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    prior_manifest = store.versions_dir / "factory" / "manifest.json"
    manifest = json.loads(prior_manifest.read_text(encoding="ascii"))
    manifest["artifacts"]["core"]["artifact_id"] = "wrong:core"
    prior_manifest.write_text(json.dumps(manifest), encoding="ascii")
    active_payload = store.versions_dir / "personal-1" / "personal.bin"
    active_payload.write_bytes(b"tampered")
    with pytest.raises(lifecycle.ModelLifecycleError, match="active_and_previous_unavailable"):
        lifecycle.ModelLifecycle.open(store_root)


def test_invalid_main_restores_verified_backup_and_survives_next_interruption(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    expected_backup = store.backup_path.read_bytes()
    store.state_path.write_bytes(b"{truncated pointer")

    recovered = lifecycle.ModelLifecycle.open(store_root)
    assert recovered.active_version_id == "factory"
    assert recovered.state_path.read_bytes() == expected_backup
    assert recovered.backup_path.read_bytes() == expected_backup

    real_replace = lifecycle.os.replace

    def interrupt_state_replace(source, destination):
        if Path(destination) == recovered.state_path:
            raise OSError("synthetic crash before active pointer replace")
        return real_replace(source, destination)

    with patch.object(lifecycle.os, "replace", side_effect=interrupt_state_replace):
        with pytest.raises(OSError, match="synthetic crash"):
            recovered.activate_candidate("personal-1")
    reopened = lifecycle.ModelLifecycle.open(store_root)
    assert reopened.active_version_id == "factory"
    assert reopened.backup_path.read_bytes() == expected_backup


def test_oversized_main_restores_verified_backup(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    expected_backup = store.backup_path.read_bytes()
    store.state_path.write_bytes(b"x" * (lifecycle.MAX_MANIFEST_BYTES + 1))

    recovered = lifecycle.ModelLifecycle.open(store_root)

    assert recovered.active_version_id == "factory"
    assert recovered.backup_path.read_bytes() == expected_backup
    assert recovered.state_path.read_bytes() == expected_backup


def test_parseable_invalid_main_recovery_interruption_preserves_backup(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    expected_backup = store.backup_path.read_bytes()
    damaged = json.loads(store.state_path.read_text(encoding="ascii"))
    damaged["active"] = "missing-version"
    damaged["active_manifest_sha256"] = "0" * 64
    store.state_path.write_bytes(lifecycle._canonical(damaged))

    real_replace = lifecycle.os.replace

    def interrupt_state_replace(source, destination):
        if Path(destination) == store.state_path:
            raise OSError("synthetic crash before recovered pointer replace")
        return real_replace(source, destination)

    with patch.object(lifecycle.os, "replace", side_effect=interrupt_state_replace):
        with pytest.raises(OSError, match="synthetic crash"):
            lifecycle.ModelLifecycle.open(store_root)
    assert store.backup_path.read_bytes() == expected_backup

    reopened = lifecycle.ModelLifecycle.open(store_root)
    assert reopened.active_version_id == "factory"
    assert reopened.backup_path.read_bytes() == expected_backup


def test_stale_instance_write_rejected_and_pin_refreshes_disk_active(store_root):
    first = _new_store(store_root)
    stale = lifecycle.ModelLifecycle.open(store_root)
    old_pin = stale.pin("in-flight")
    _candidate(first)
    first.admit_candidate("personal-1")
    first.activate_candidate("personal-1")

    with pytest.raises(lifecycle.ModelLifecycleError, match="stale_instance"):
        stale.stage_candidate("stale-write", parent_version_id="factory", payloads={
            **FACTORY, "personal": b"never-written"
        })
    assert stale.read_payload(old_pin, "core") == FACTORY["core"]
    refreshed_pin = stale.pin("after-external-switch")
    assert refreshed_pin.version_id == "personal-1"
    assert stale.read_payload(refreshed_pin, "personal") == b"synthetic-personal-v1"

    reopened = lifecycle.ModelLifecycle.open(store_root)
    with pytest.raises(lifecycle.ModelLifecycleError, match="pin_not_issued_by_store"):
        reopened.read_payload(refreshed_pin, "personal")


def test_stale_reset_is_rejected_after_another_instance_activates(store_root):
    first = _new_store(store_root)
    stale = lifecycle.ModelLifecycle.open(store_root)
    _candidate(first)
    first.admit_candidate("personal-1")
    first.activate_candidate("personal-1")
    committed = json.loads(first.state_path.read_text(encoding="ascii"))

    with pytest.raises(lifecycle.ModelLifecycleError, match="stale_instance"):
        stale.reset_personal("stale-reset")

    assert json.loads(first.state_path.read_text(encoding="ascii")) == committed
    assert first.active_version_id == "personal-1"
    assert first.state_path.read_bytes() == lifecycle.ModelLifecycle.open(
        store_root).state_path.read_bytes()
    assert not (first.versions_dir / "stale-reset").exists()


@pytest.mark.parametrize("mutation", ["numeric_false_flags", "duplicate_key"])
@pytest.mark.parametrize("operation", ["activate", "open"])
def test_noncanonical_admission_receipt_cannot_activate_or_open(
        store_root, mutation, operation):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    if operation == "open":
        store.activate_candidate("personal-1")

    receipt_path = store.admissions_dir / "personal-1.json"
    receipt_bytes = receipt_path.read_bytes()
    if mutation == "numeric_false_flags":
        receipt = json.loads(receipt_bytes.decode("ascii"))
        receipt["training_eligible"] = 0
        receipt["production_activation"] = 0
        receipt_bytes = lifecycle._canonical(receipt)
    else:
        receipt_bytes = receipt_bytes.replace(
            b'"schema":"wrench.model-version-admission.v1"',
            b'"schema":"wrong","schema":"wrench.model-version-admission.v1"',
        )
    receipt_path.write_bytes(receipt_bytes)
    before = store.state_path.read_bytes()

    if operation == "activate":
        with pytest.raises(lifecycle.ModelLifecycleError,
                           match="candidate_not_admitted_for_active_parent"):
            store.activate_candidate("personal-1")
        assert store.state_path.read_bytes() == before
        assert store.active_version_id == "factory"
    else:
        recovered = lifecycle.ModelLifecycle.open(store_root)
        recovered_state = json.loads(recovered.state_path.read_text(encoding="ascii"))
        original_state = json.loads(before.decode("ascii"))
        assert recovered.active_version_id == "factory"
        assert recovered.previous_version_id is None
        assert recovered_state["generation"] == original_state["generation"] + 1
        assert recovered_state["active_manifest_sha256"] == original_state["previous_manifest_sha256"]
    assert receipt_path.read_bytes() == receipt_bytes


@pytest.mark.parametrize("when,corruption", [
    ("admit", "manifest"),
    ("activate", "manifest"),
    ("activate", "payload"),
])
def test_corrupt_active_parent_blocks_admission_or_activation_without_promotion(
        store_root, when, corruption):
    store = _new_store(store_root)
    _candidate(store)
    if when == "activate":
        store.admit_candidate("personal-1")

    parent_manifest_path = store.versions_dir / "factory" / "manifest.json"
    parent_payload_path = store.versions_dir / "factory" / "foundation.bin"
    if corruption == "manifest":
        parent_manifest = json.loads(parent_manifest_path.read_text(encoding="ascii"))
        parent_manifest["artifacts"]["runtime"]["sha256"] = "a" * 64
        parent_manifest["artifacts"]["runtime"]["artifact_id"] = "runtime:" + "a" * 64
        parent_manifest_path.write_bytes(lifecycle._canonical(parent_manifest))
    else:
        parent_payload_path.write_bytes(b"corrupted parent payload")
    before = store.state_path.read_bytes()

    operation = store.admit_candidate if when == "admit" else store.activate_candidate
    expected_error = "state_manifest_hash_mismatch" if corruption == "manifest" else "payload_corrupt"
    with pytest.raises(lifecycle.ModelLifecycleError, match=expected_error):
        operation("personal-1")

    assert store.state_path.read_bytes() == before
    assert json.loads(before.decode("ascii"))["generation"] == 0
    assert store.active_version_id == "factory"


def test_forged_pin_cannot_read_even_a_known_version(store_root):
    store = _new_store(store_root)
    genuine = store.pin("request-1")
    forged = lifecycle.VersionPin(
        genuine.version_id, genuine.manifest_sha256, genuine._manifest_json,
        "forged-request", b"not-a-store-proof"
    )
    with pytest.raises(lifecycle.ModelLifecycleError, match="pin_not_issued_by_store"):
        store.read_payload(forged, "core")


def test_os_lock_blocks_second_process_and_stale_generation_is_rejected(store_root):
    first = _new_store(store_root)
    second = lifecycle.ModelLifecycle.open(store_root)
    attempt_marker = store_root.parent / f"{store_root.name}-lock-attempt"
    acquired_marker = store_root.parent / f"{store_root.name}-lock-acquired"
    code = (
        "import sys; from pathlib import Path; "
        "from wrench_harness.model_lifecycle import ModelLifecycle; "
        "Path(sys.argv[2]).write_text('attempting'); "
        "ModelLifecycle.open(sys.argv[1]); Path(sys.argv[3]).write_text('locked')"
    )
    process = None
    try:
        with first._writer_lock():
            process = subprocess.Popen(
                [sys.executable, "-c", code, str(store_root),
                 str(attempt_marker), str(acquired_marker)],
                cwd=Path(__file__).resolve().parents[1],
                env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            deadline = time.monotonic() + 5
            while process.poll() is None and not attempt_marker.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            assert attempt_marker.exists(), "second process did not reach the lock attempt"
            time.sleep(0.25)
            assert not acquired_marker.exists(), "second process entered while first held the lock"
        assert process.wait(timeout=15) == 0
        assert acquired_marker.read_text(encoding="ascii") == "locked"
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        attempt_marker.unlink(missing_ok=True)
        acquired_marker.unlink(missing_ok=True)
    _candidate(first)
    first.admit_candidate("personal-1")
    first.activate_candidate("personal-1")
    with pytest.raises(lifecycle.ModelLifecycleError, match="stale_instance"):
        second.stage_candidate("stale", parent_version_id="factory", payloads={
            **FACTORY, "personal": b"stale"
        })


def test_reset_serializes_against_stale_process_activation():
    RESET_SERIALIZATION_SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    job_scratch = Path(tempfile.mkdtemp(
        prefix="case-", dir=RESET_SERIALIZATION_SCRATCH_ROOT
    ))
    store_root = job_scratch / "store"
    store_root.mkdir()
    store = _new_store(store_root)
    _candidate(store, "personal-1")
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    _candidate(store, "personal-2")
    store.admit_candidate("personal-2")

    resetter = lifecycle.ModelLifecycle.open(store_root)
    markers = job_scratch / "markers"
    markers.mkdir()
    ready = markers / "activation-ready"
    attempt = markers / "activation-attempt"
    acquired = markers / "activation-acquired"
    result = markers / "activation-result"
    start_activation = markers / "start-activation"
    reset_staged = threading.Event()
    finish_reset = threading.Event()
    reset_errors = []
    process = None
    reset_thread = None
    original_write_version = resetter._write_version

    def pause_after_reset_version(version_id, **kwargs):
        digest = original_write_version(version_id, **kwargs)
        if version_id == "reset-race":
            reset_staged.set()
            if not finish_reset.wait(timeout=10):
                raise AssertionError("test did not release the staged reset")
        return digest

    def run_reset():
        try:
            resetter.reset_personal("reset-race")
        except Exception as exc:  # surfaced in the test thread below
            reset_errors.append(exc)

    code = """
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from wrench_harness.model_lifecycle import ModelLifecycle, ModelLifecycleError

root, ready, start, attempt, acquired, result = map(Path, sys.argv[1:])
store = ModelLifecycle.open(root)
original_lock = store._writer_lock

@contextmanager
def observed_lock():
    attempt.write_text("attempting")
    with original_lock():
        acquired.write_text("acquired")
        yield

store._writer_lock = observed_lock
ready.write_text("ready")
deadline = time.monotonic() + 10
while not start.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
try:
    store.activate_candidate("personal-2")
    outcome = "activated"
except ModelLifecycleError as exc:
    outcome = str(exc)
result.write_text(outcome)
"""
    try:
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(store_root), str(ready),
             str(start_activation), str(attempt), str(acquired), str(result)],
            cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 5
        while process.poll() is None and not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), "competing process did not open its generation snapshot"

        resetter._write_version = pause_after_reset_version
        reset_thread = threading.Thread(target=run_reset, daemon=True)
        reset_thread.start()
        assert reset_staged.wait(timeout=5), "reset did not reach the serialized staging point"

        start_activation.write_text("go")
        deadline = time.monotonic() + 5
        while process.poll() is None and not attempt.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert attempt.exists(), "competing process did not attempt activation"
        time.sleep(0.2)
        assert not acquired.exists(), "activation acquired the writer lock during reset"
        assert not result.exists(), "activation completed before the reset committed"

        finish_reset.set()
        reset_thread.join(timeout=10)
        assert not reset_thread.is_alive(), "reset did not finish after releasing the barrier"
        assert process.wait(timeout=10) == 0
        assert not reset_errors, reset_errors
        assert result.read_text(encoding="ascii") == "stale_instance"

        reopened = lifecycle.ModelLifecycle.open(store_root)
        assert reopened.active_version_id == "reset-race"
        assert reopened.previous_version_id == "personal-1"
        state = json.loads((store_root / "state.json").read_text(encoding="ascii"))
        assert state["generation"] == 2
        assert state["factory"] == "factory"
        factory_manifest = json.loads(
            (store_root / "versions" / "factory" / "manifest.json").read_text(encoding="ascii")
        )
        assert state["factory_manifest_sha256"] == lifecycle._digest(
            lifecycle._canonical(factory_manifest)
        )
        active_manifest = json.loads(
            (store_root / "versions" / "reset-race" / "manifest.json").read_text(encoding="ascii")
        )
        previous_manifest = json.loads(
            (store_root / "versions" / "personal-1" / "manifest.json").read_text(encoding="ascii")
        )
        assert state["active_manifest_sha256"] == lifecycle._digest(
            lifecycle._canonical(active_manifest)
        )
        assert state["previous_manifest_sha256"] == lifecycle._digest(
            lifecycle._canonical(previous_manifest)
        )
    finally:
        finish_reset.set()
        start_activation.touch(exist_ok=True)
        if reset_thread is not None:
            reset_thread.join(timeout=10)
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        shutil.rmtree(job_scratch, ignore_errors=True)


def test_rejected_admission_receipt_cannot_activate(store_root):
    store = _new_store(store_root)
    _candidate(store)
    store.admit_candidate("personal-1")
    receipt_path = store.admissions_dir / "personal-1.json"
    receipt_path.write_bytes(b"{corrupt receipt")
    with pytest.raises(lifecycle.ModelLifecycleError, match="admission_record_corrupt"):
        store.activate_candidate("personal-1")
    assert store.active_version_id == "factory"


def test_store_byte_and_entry_limits_reject_projected_growth(store_root, monkeypatch):
    store = _new_store(store_root)
    current_bytes, current_entries = store._check_inventory()
    monkeypatch.setattr(lifecycle, "MAX_STORE_BYTES", current_bytes)
    with pytest.raises(lifecycle.ModelLifecycleError, match="store_size_limit_exceeded"):
        store.stage_candidate("over-byte-limit", parent_version_id="factory", payloads={
            **FACTORY, "personal": b"synthetic-personal"
        })
    assert not (store.versions_dir / "over-byte-limit").exists()

    monkeypatch.setattr(lifecycle, "MAX_STORE_BYTES", 10_000_000)
    monkeypatch.setattr(lifecycle, "MAX_STORE_ENTRIES", current_entries)
    with pytest.raises(lifecycle.ModelLifecycleError, match="store_entry_limit_exceeded"):
        store.stage_candidate("over-entry-limit", parent_version_id="factory", payloads={
            **FACTORY, "personal": b"synthetic-personal"
        })
    assert not (store.versions_dir / "over-entry-limit").exists()


def test_inventory_rejects_orphan_and_oversized_entries_without_removal(store_root):
    store = _new_store(store_root)
    orphan = store.root / "orphan.bin"
    orphan.write_bytes(b"synthetic orphan")
    with pytest.raises(lifecycle.ModelLifecycleError, match="store_entry_unexpected"):
        lifecycle.ModelLifecycle.open(store_root)
    assert orphan.read_bytes() == b"synthetic orphan"
    orphan.unlink()

    oversized = store.backup_path
    oversized.write_bytes(b"x" * (lifecycle.MAX_MANIFEST_BYTES + 1))
    with pytest.raises(lifecycle.ModelLifecycleError, match="store_entry_size_limit_exceeded"):
        lifecycle.ModelLifecycle.open(store_root)
    assert oversized.stat().st_size == lifecycle.MAX_MANIFEST_BYTES + 1


def test_reparse_components_are_rejected_when_host_allows_symlinks(store_root):
    outside_dir = store_root / "outside-dir"
    outside_dir.mkdir()
    outside_file = store_root / "outside.bin"
    outside_file.write_bytes(b"synthetic external target")

    def link(path: Path, target: Path, *, directory: bool = False):
        try:
            os.symlink(target, path, target_is_directory=directory)
        except OSError as exc:
            pytest.skip(f"Host does not permit os.symlink for {path.name}: {exc}")

    def moved_link(path: Path, target: Path, *, directory: bool = False):
        saved = store_root / f"saved-{path.parent.name}-{path.name}"
        path.rename(saved)
        link(path, target, directory=directory)

    store = _new_store(store_root / "store")
    link(store_root / "root-link", store.root, directory=True)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store_root / "root-link")

    moved_link(store.versions_dir, outside_dir, directory=True)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "admissions-store")
    moved_link(store.admissions_dir, outside_dir, directory=True)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "version-store")
    moved_link(store.versions_dir / "factory", outside_dir, directory=True)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "file-store")
    moved_link(store.versions_dir / "factory" / "core.bin", outside_file)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "state-store")
    moved_link(store.state_path, outside_file)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "backup-store")
    _candidate(store)
    store.admit_candidate("personal-1")
    store.activate_candidate("personal-1")
    moved_link(store.backup_path, outside_file)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)

    store = _new_store(store_root / "lock-store")
    moved_link(store.lock_path, outside_file)
    with pytest.raises(lifecycle.ModelLifecycleError, match="reparse_path_forbidden"):
        lifecycle.ModelLifecycle.open(store.root)
