"""Bounded, synthetic-only model-version lifecycle mechanics.

This module stores opaque payload bytes and hash-bound references. It does not
load a runtime, train a candidate, or establish production readiness.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import shutil
import secrets
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Mapping


SCHEMA = "wrench.model-version.v1"
STATE_SCHEMA = "wrench.model-lifecycle-state.v1"
ADMISSION_SCHEMA = "wrench.model-version-admission.v1"
MAX_LAYER_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 256 * 1024
MAX_MANIFEST_BYTES = 32 * 1024
MAX_VERSIONS = 32
MAX_STORE_BYTES = 10_000_000
MAX_STORE_ENTRIES = 512
LAYERS = ("foundation", "core", "runtime", "tokenizer", "compatibility")
_VERSION_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REPARSE_POINT = 0x400


class ModelLifecycleError(ValueError):
    """A version reference, payload, transition, or state failed validation."""


@dataclass(frozen=True)
class VersionPin:
    """Immutable request snapshot. Pins are process-local and never load a model."""

    version_id: str
    manifest_sha256: str
    _manifest_json: bytes
    _request_id: str
    _proof: bytes

    @property
    def manifest(self) -> dict:
        return json.loads(self._manifest_json.decode("utf-8"))


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ModelLifecycleError("json_invalid") from exc


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _assert_no_reparse(path: Path) -> None:
    """Reject symlinks/junctions in every existing component before access."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ModelLifecycleError("path_component_unavailable") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & _REPARSE_POINT:
            raise ModelLifecycleError("reparse_path_forbidden")


def _serialized_writer(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self._writer_lock():
            self._assert_fresh_state()
            self._check_inventory()
            result = method(self, *args, **kwargs)
            self._check_inventory()
            return result
    return guarded


def _version_id(value: object) -> str:
    if type(value) is not str or not _VERSION_ID.fullmatch(value):
        raise ModelLifecycleError("version_id_invalid")
    return value


def _read_regular(path: Path, max_bytes: int) -> bytes:
    try:
        _assert_no_reparse(path)
        if not path.is_file():
            raise ModelLifecycleError("reference_not_regular_file")
        size = path.stat().st_size
        if size > max_bytes:
            raise ModelLifecycleError("reference_size_limit_exceeded")
        data = path.read_bytes()
    except OSError as exc:
        raise ModelLifecycleError("reference_unavailable") from exc
    if len(data) != size:
        raise ModelLifecycleError("reference_read_incomplete")
    return data


class ModelLifecycle:
    """Small local state machine for immutable development version snapshots."""

    training_eligible = False
    production_activation = False

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(os.path.abspath(os.path.expanduser(os.fspath(root))))
        _assert_no_reparse(self.root)
        self.versions_dir = self.root / "versions"
        self.admissions_dir = self.root / "admissions"
        self.state_path = self.root / "state.json"
        self.backup_path = self.root / "state.previous.json"
        self.lock_path = self.root / ".lifecycle.lock"
        self._state: dict | None = None
        self._pin_secret = secrets.token_bytes(32)

    @classmethod
    def create(cls, root: str | os.PathLike[str], *, factory_version_id: str,
               payloads: Mapping[str, bytes]) -> "ModelLifecycle":
        """Create an empty store with one verified synthetic factory version."""
        instance = cls(root)
        factory_id = _version_id(factory_version_id)
        if factory_id != "factory":
            raise ModelLifecycleError("factory_version_id_must_be_factory")
        with instance._writer_lock():
            entries = list(instance.root.iterdir())
            _assert_no_reparse(instance.versions_dir)
            _assert_no_reparse(instance.admissions_dir)
            if any(path.name != instance.lock_path.name for path in entries):
                raise ModelLifecycleError("store_not_empty")
            instance._ensure_directory(instance.versions_dir)
            instance._ensure_directory(instance.admissions_dir)
            instance._check_inventory()
            instance._write_version("factory", kind="factory", parent=None,
                                    payloads=payloads, require_personal=False)
            manifest = instance._load_manifest("factory")
            factory_hash = _digest(_canonical(manifest))
            state = {"schema": STATE_SCHEMA, "generation": 0, "factory": "factory",
                     "factory_manifest_sha256": factory_hash,
                     "active": "factory", "previous": None,
                     "previous_manifest_sha256": None,
                     "active_manifest_sha256": factory_hash}
            instance._atomic_write(instance.state_path, _canonical(state))
            instance._state = state
            instance._check_inventory()
        return instance

    @classmethod
    def open(cls, root: str | os.PathLike[str]) -> "ModelLifecycle":
        """Open and verify state; recover to a verified previous version or fail."""
        instance = cls(root)
        with instance._writer_lock():
            # A damaged main pointer may be oversized but still within the
            # store ceiling. Permit it only during recovery so a verified
            # backup can replace it; ordinary operations reject it.
            instance._check_inventory(allow_oversized_main=True)
            instance._state = instance._load_current_state_locked()
            instance._check_inventory()
        return instance

    def _load_current_state_locked(self) -> dict:
        main = self._read_state(self.state_path)
        restored_from_backup = main is None
        if restored_from_backup:
            main = self._read_state(self.backup_path)
        if main is None:
            raise ModelLifecycleError("state_unavailable")
        try:
            self._verify_state_version(main, main["factory"],
                                       main["factory_manifest_sha256"], require_active=False)
            self._verify_state_version(main, main["active"], main["active_manifest_sha256"])
        except ModelLifecycleError:
            backup = self._read_state(self.backup_path)
            choices = [(main.get("previous"), main.get("previous_manifest_sha256"))]
            if backup and backup.get("active") != main.get("active"):
                choices.append((backup.get("active"), backup.get("active_manifest_sha256")))
            choices.append((main.get("factory"), main.get("factory_manifest_sha256")))
            recovered = None
            for version_id, version_hash in choices:
                if version_id is None or version_hash is None or version_id == main.get("active"):
                    continue
                try:
                    self._verify_state_version(main, version_id, version_hash, require_active=False)
                    recovered = (version_id, version_hash)
                    break
                except ModelLifecycleError:
                    continue
            if recovered is None:
                raise ModelLifecycleError("active_and_previous_unavailable")
            version_id, version_hash = recovered
            main = dict(main)
            main["generation"] += 1
            main["active"] = version_id
            main["active_manifest_sha256"] = version_hash
            main["previous"] = main["factory"] if version_id != main["factory"] else None
            main["previous_manifest_sha256"] = (
                main["factory_manifest_sha256"] if main["previous"] is not None else None)
            # The current pointer is invalid even when it parsed. Never copy
            # it over the good backup before the replacement pointer commits.
            restored_from_backup = True
        if main.get("previous") is not None:
            try:
                self._verify_state_version(main, main["previous"],
                                           main["previous_manifest_sha256"], require_active=False)
            except ModelLifecycleError:
                main = dict(main)
                main["generation"] += 1
                main["previous"] = main["factory"] if main["active"] != main["factory"] else None
                main["previous_manifest_sha256"] = (
                    main["factory_manifest_sha256"] if main["previous"] is not None else None)
                if not restored_from_backup:
                    self._write_state(main)
        if restored_from_backup:
            # Restore the verified pointer directly; never back up corrupt main bytes.
            self._remove_oversized_main_for_recovery()
            self._atomic_write(self.state_path, _canonical(main))
        return main

    def _remove_oversized_main_for_recovery(self) -> None:
        """Drop only an over-limit main pointer after backup validation.

        The verified backup remains intact if the following atomic write is
        interrupted, so the next open can recover from it again.
        """
        try:
            _assert_no_reparse(self.state_path)
            info = self.state_path.lstat()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ModelLifecycleError("state_unavailable") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ModelLifecycleError("state_entry_invalid")
        if info.st_size > MAX_MANIFEST_BYTES:
            try:
                self.state_path.unlink()
            except OSError as exc:
                raise ModelLifecycleError("state_unavailable") from exc

    @property
    def active_version_id(self) -> str:
        return self._require_state()["active"]

    @property
    def previous_version_id(self) -> str | None:
        return self._require_state()["previous"]

    @property
    def factory_version_id(self) -> str:
        return self._require_state()["factory"]

    def pin(self, request_id: str) -> VersionPin:
        """Return an immutable snapshot tied to the active version at call time."""
        if type(request_id) is not str or not 1 <= len(request_id) <= 128:
            raise ModelLifecycleError("request_id_invalid")
        with self._writer_lock():
            self._check_inventory()
            pin = self._pin_current_locked(request_id)
            self._check_inventory()
            return pin

    def read_payload(self, pin: VersionPin, layer: str) -> bytes:
        """Read only bytes verified against the pinned immutable manifest."""
        if (not isinstance(pin, VersionPin) or layer not in (*LAYERS, "personal")
                or type(pin._request_id) is not str or type(pin._proof) is not bytes
                or type(pin.manifest_sha256) is not str
                or not _SHA256.fullmatch(pin.manifest_sha256)):
            raise ModelLifecycleError("pin_or_layer_invalid")
        expected_proof = self._pin_proof(pin.version_id, pin.manifest_sha256, pin._request_id)
        if not hmac.compare_digest(pin._proof, expected_proof):
            raise ModelLifecycleError("pin_not_issued_by_store")
        manifest = pin.manifest
        if manifest.get("version_id") != pin.version_id or _digest(_canonical(manifest)) != pin.manifest_sha256:
            raise ModelLifecycleError("pin_manifest_invalid")
        self._verify_version_exists(pin.version_id, pin.manifest_sha256)
        ref = manifest["artifacts"].get(layer)
        if ref is None:
            raise ModelLifecycleError("layer_unavailable")
        path = self._version_dir(pin.version_id) / f"{layer}.bin"
        data = _read_regular(path, MAX_LAYER_BYTES)
        if len(data) != ref["size_bytes"] or _digest(data) != ref["sha256"]:
            raise ModelLifecycleError("payload_corrupt")
        return data

    @_serialized_writer
    def stage_candidate(self, version_id: str, *, parent_version_id: str,
                        payloads: Mapping[str, bytes]) -> str:
        """Store a complete, immutable candidate snapshot without activating it."""
        parent = _version_id(parent_version_id)
        state = self._require_state()
        if parent != state["active"]:
            raise ModelLifecycleError("candidate_parent_not_active")
        self._verify_state_version(state, parent, state["active_manifest_sha256"])
        return self._write_version(_version_id(version_id), kind="candidate", parent=parent,
                                   payloads=payloads, require_personal=True)

    @_serialized_writer
    def admit_candidate(self, version_id: str) -> str:
        """Validate references and compatibility, then persist a bounded receipt."""
        candidate_id = _version_id(version_id)
        state = self._require_state()
        active = self._verify_state_version(
            state, state["active"], state["active_manifest_sha256"])
        candidate = self._load_manifest(candidate_id)
        self._verify_manifest_payloads(candidate_id, candidate)
        if candidate.get("kind") != "candidate" or candidate.get("parent_version_id") != state["active"]:
            raise ModelLifecycleError("candidate_parent_or_kind_invalid")
        for layer in (*LAYERS,):
            if candidate["artifacts"][layer] != active["artifacts"][layer]:
                raise ModelLifecycleError("candidate_compatibility_mismatch")
        receipt = {"schema": ADMISSION_SCHEMA, "version_id": candidate_id,
                   "manifest_sha256": _digest(_canonical(candidate)),
                   "parent_version_id": state["active"],
                   "status": "development_admitted",
                   "training_eligible": False, "production_activation": False}
        path = self.admissions_dir / f"{candidate_id}.json"
        if path.exists():
            if _read_regular(path, MAX_MANIFEST_BYTES) != _canonical(receipt):
                raise ModelLifecycleError("admission_record_conflict")
        else:
            self._atomic_write(path, _canonical(receipt))
        return receipt["manifest_sha256"]

    @_serialized_writer
    def activate_candidate(self, version_id: str) -> None:
        """Atomically select a previously admitted candidate for later requests."""
        candidate_id = _version_id(version_id)
        state = self._require_state()
        active = self._verify_state_version(
            state, state["active"], state["active_manifest_sha256"])
        candidate = self._load_manifest(candidate_id)
        candidate_hash = _digest(_canonical(candidate))
        self._verify_manifest_payloads(candidate_id, candidate)
        receipt_path = self.admissions_dir / f"{candidate_id}.json"
        if not receipt_path.exists():
            raise ModelLifecycleError("candidate_not_admitted")
        receipt_bytes = _read_regular(receipt_path, MAX_MANIFEST_BYTES)
        try:
            receipt = json.loads(receipt_bytes.decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ModelLifecycleError("admission_record_corrupt") from exc
        expected_receipt = {"schema": ADMISSION_SCHEMA, "version_id": candidate_id,
                            "manifest_sha256": candidate_hash,
                            "parent_version_id": state["active"],
                            "status": "development_admitted",
                            "training_eligible": False, "production_activation": False}
        if (receipt_bytes != _canonical(expected_receipt)
                or candidate.get("kind") != "candidate"
                or candidate.get("parent_version_id") != state["active"]):
            raise ModelLifecycleError("candidate_not_admitted_for_active_parent")
        self._verify_compatibility(candidate, active)
        self._promote(candidate_id, candidate_hash)

    @_serialized_writer
    def rollback(self) -> str:
        """Switch to the retained prior version after revalidating all references."""
        state = self._require_state()
        prior = state.get("previous")
        if prior is None:
            raise ModelLifecycleError("previous_version_unavailable")
        digest = state["previous_manifest_sha256"]
        self._verify_state_version(state, prior, digest, require_active=False)
        self._promote(prior, digest)
        return prior

    @_serialized_writer
    def reset_personal(self, version_id: str) -> str:
        """Create and activate a base/core-preserving version without personal bytes."""
        state = self._require_state()
        active_id = state["active"]
        active = self._load_manifest(active_id)
        source_pin = self._pin_current_locked("reset")
        if source_pin.version_id != active_id:
            raise ModelLifecycleError("active_changed_during_reset")
        payloads = {layer: self.read_payload(source_pin, layer) for layer in LAYERS}
        if self._require_state()["active"] != active_id:
            raise ModelLifecycleError("active_changed_during_reset")
        self._write_version(_version_id(version_id), kind="reset", parent=active_id,
                            payloads=payloads, require_personal=False)
        reset = self._load_manifest(_version_id(version_id))
        for layer in LAYERS:
            if reset["artifacts"][layer] != active["artifacts"][layer]:
                raise ModelLifecycleError("reset_preservation_failed")
        reset_hash = _digest(_canonical(reset))
        self._promote(_version_id(version_id), reset_hash)
        return _version_id(version_id)

    def _verify_compatibility(self, candidate: dict, parent: dict) -> None:
        for layer in LAYERS:
            if candidate["artifacts"].get(layer) != parent["artifacts"].get(layer):
                raise ModelLifecycleError("candidate_compatibility_mismatch")

    def _promote(self, version_id: str, manifest_sha256: str) -> None:
        state = self._require_state()
        self._verify_state_version(state, version_id, manifest_sha256, require_active=False)
        updated = {"schema": STATE_SCHEMA, "generation": state["generation"] + 1,
                   "factory": state["factory"],
                   "factory_manifest_sha256": state["factory_manifest_sha256"],
                   "active": version_id, "previous": state["active"],
                   "previous_manifest_sha256": state["active_manifest_sha256"],
                   "active_manifest_sha256": manifest_sha256}
        self._write_state(updated)
        self._state = updated

    def _write_version(self, version_id: str, *, kind: str, parent: str | None,
                       payloads: Mapping[str, bytes], require_personal: bool) -> str:
        version_id = _version_id(version_id)
        if not isinstance(payloads, Mapping):
            raise ModelLifecycleError("payloads_invalid")
        allowed = set(LAYERS) | {"personal"}
        keys = set(payloads)
        if keys - allowed or not set(LAYERS).issubset(keys):
            raise ModelLifecycleError("payload_layers_incomplete")
        if require_personal and "personal" not in keys:
            raise ModelLifecycleError("personal_layer_required")
        if kind in {"factory", "reset"} and "personal" in keys:
            raise ModelLifecycleError("personal_layer_forbidden")
        total = 0
        normalized: dict[str, bytes] = {}
        refs: dict[str, dict] = {}
        for layer in (*LAYERS, "personal"):
            if layer not in payloads:
                continue
            data = payloads[layer]
            if type(data) is not bytes or len(data) > MAX_LAYER_BYTES:
                raise ModelLifecycleError("payload_type_or_size_invalid")
            total += len(data)
            if total > MAX_TOTAL_BYTES:
                raise ModelLifecycleError("payload_total_limit_exceeded")
            normalized[layer] = data
            content_hash = _digest(data)
            refs[layer] = {"layer": layer, "artifact_id": f"{layer}:{content_hash}",
                           "sha256": content_hash, "size_bytes": len(data)}
        self._check_version_capacity(version_id)
        version_dir = self._version_dir(version_id)
        if version_dir.exists():
            raise ModelLifecycleError("version_immutable_exists")
        manifest = {"schema": SCHEMA, "version_id": version_id, "kind": kind,
                    "parent_version_id": parent, "artifacts": refs,
                    "training_eligible": False, "production_activation": False}
        raw = _canonical(manifest)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ModelLifecycleError("manifest_size_limit_exceeded")
        self._ensure_directory(self.versions_dir)
        self._check_inventory(add_bytes=total + len(raw),
                              add_entries=len(normalized) + 2)
        staging = Path(tempfile.mkdtemp(prefix=f".{version_id}.", dir=self.versions_dir))
        try:
            for layer, data in normalized.items():
                self._write_file(staging / f"{layer}.bin", data)
            self._write_file(staging / "manifest.json", raw)
            _assert_no_reparse(staging)
            _assert_no_reparse(version_dir)
            if version_dir.exists():
                raise ModelLifecycleError("version_immutable_exists")
            os.replace(staging, version_dir)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        return _digest(raw)

    def _check_version_capacity(self, version_id: str) -> None:
        _version_id(version_id)
        if self.versions_dir.exists():
            count = sum(1 for item in self.versions_dir.iterdir() if item.is_dir())
            if count >= MAX_VERSIONS:
                raise ModelLifecycleError("version_count_limit_exceeded")

    def _version_dir(self, version_id: str) -> Path:
        return self.versions_dir / _version_id(version_id)

    def _load_manifest(self, version_id: str) -> dict:
        raw = _read_regular(self._version_dir(version_id) / "manifest.json", MAX_MANIFEST_BYTES)
        try:
            manifest = json.loads(raw.decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ModelLifecycleError("manifest_corrupt") from exc
        if (type(manifest) is not dict or manifest.get("schema") != SCHEMA
                or manifest.get("version_id") != version_id
                or manifest.get("kind") not in {"factory", "candidate", "reset"}
                or type(manifest.get("training_eligible")) is not bool
                or manifest["training_eligible"] is not False
                or manifest.get("production_activation") is not False):
            raise ModelLifecycleError("manifest_incompatible")
        kind = manifest["kind"]
        parent = manifest.get("parent_version_id")
        if ((kind == "factory" and parent is not None)
                or (kind in {"candidate", "reset"}
                    and (type(parent) is not str or not _VERSION_ID.fullmatch(parent)))):
            raise ModelLifecycleError("manifest_parent_invalid")
        refs = manifest.get("artifacts")
        if type(refs) is not dict or not set(LAYERS).issubset(refs) or set(refs) - (set(LAYERS) | {"personal"}):
            raise ModelLifecycleError("manifest_layers_incomplete")
        if manifest.get("kind") == "candidate" and "personal" not in refs:
            raise ModelLifecycleError("candidate_personal_missing")
        if manifest.get("kind") in {"factory", "reset"} and "personal" in refs:
            raise ModelLifecycleError("manifest_personal_forbidden")
        return manifest

    def _verify_manifest_payloads(self, version_id: str, manifest: dict) -> None:
        total = 0
        for layer, ref in manifest["artifacts"].items():
            if (type(ref) is not dict or ref.get("layer") != layer
                    or type(ref.get("artifact_id")) is not str
                    or type(ref.get("size_bytes")) is not int
                    or not 0 <= ref["size_bytes"] <= MAX_LAYER_BYTES
                    or type(ref.get("sha256")) is not str
                    or not _SHA256.fullmatch(ref["sha256"])):
                raise ModelLifecycleError("artifact_reference_invalid")
            if ref["artifact_id"] != f"{layer}:{ref['sha256']}":
                raise ModelLifecycleError("artifact_reference_invalid")
            data = _read_regular(self._version_dir(version_id) / f"{layer}.bin", MAX_LAYER_BYTES)
            if len(data) != ref["size_bytes"] or _digest(data) != ref["sha256"]:
                raise ModelLifecycleError("payload_corrupt")
            total += len(data)
        if total > MAX_TOTAL_BYTES:
            raise ModelLifecycleError("payload_total_limit_exceeded")
        for path in self._version_dir(version_id).iterdir():
            if path.name not in {"manifest.json", *(f"{key}.bin" for key in manifest["artifacts"])}:
                raise ModelLifecycleError("version_unexpected_file")

    def _verify_state_version(self, state: dict, version_id: str, expected_hash: str,
                              *, require_active: bool = True) -> dict:
        if type(expected_hash) is not str or not _SHA256.fullmatch(expected_hash):
            raise ModelLifecycleError("state_manifest_hash_invalid")
        manifest = self._load_manifest(version_id)
        if _digest(_canonical(manifest)) != expected_hash:
            raise ModelLifecycleError("state_manifest_hash_mismatch")
        self._verify_manifest_payloads(version_id, manifest)
        if manifest.get("kind") == "candidate":
            self._verify_admission_receipt(version_id, manifest)
        if version_id == state.get("factory") and manifest.get("kind") != "factory":
            raise ModelLifecycleError("factory_reference_invalid")
        if require_active and version_id != state.get("active"):
            raise ModelLifecycleError("state_active_reference_invalid")
        return manifest

    def _verify_version_exists(self, version_id: str, manifest_sha256: str) -> dict:
        manifest = self._load_manifest(version_id)
        if _digest(_canonical(manifest)) != manifest_sha256:
            raise ModelLifecycleError("state_manifest_hash_mismatch")
        self._verify_manifest_payloads(version_id, manifest)
        return manifest

    def _pin_proof(self, version_id: str, manifest_sha256: str, request_id: str) -> bytes:
        body = _canonical([version_id, manifest_sha256, request_id])
        return hmac.new(self._pin_secret, body, hashlib.sha256).digest()

    def _pin_current_locked(self, request_id: str) -> VersionPin:
        self._state = self._load_current_state_locked()
        state = self._require_state()
        manifest = self._verify_state_version(state, state["active"],
                                              state["active_manifest_sha256"])
        raw = _canonical(manifest)
        digest = _digest(raw)
        return VersionPin(state["active"], digest, raw, request_id,
                          self._pin_proof(state["active"], digest, request_id))

    def _read_state(self, path: Path) -> dict | None:
        try:
            raw = _read_regular(path, MAX_MANIFEST_BYTES)
            state = json.loads(raw.decode("ascii"))
        except (ModelLifecycleError, ValueError, UnicodeError):
            return None
        if (type(state) is not dict or state.get("schema") != STATE_SCHEMA
                or type(state.get("generation")) is not int or state["generation"] < 0):
            return None
        try:
            _version_id(state.get("factory"))
            _version_id(state.get("active"))
            if state.get("previous") is not None:
                _version_id(state["previous"])
        except ModelLifecycleError:
            return None
        for key in ("active_manifest_sha256", "factory_manifest_sha256"):
            if not isinstance(state.get(key), str) or not _SHA256.fullmatch(state[key]):
                return None
        if state.get("previous") is None:
            if state.get("previous_manifest_sha256") is not None:
                return None
        elif (not isinstance(state.get("previous_manifest_sha256"), str)
              or not _SHA256.fullmatch(state["previous_manifest_sha256"])):
            return None
        return state

    def _require_state(self) -> dict:
        if self._state is None:
            raise ModelLifecycleError("store_not_open")
        return self._state

    def _assert_fresh_state(self) -> None:
        disk = self._read_state(self.state_path)
        if disk is None or disk != self._require_state():
            raise ModelLifecycleError("stale_instance")

    @contextmanager
    def _writer_lock(self):
        self._ensure_directory(self.root)
        _assert_no_reparse(self.lock_path)
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = None
        try:
            fd = os.open(self.lock_path, flags, 0o600)
            _assert_no_reparse(self.lock_path)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 1:
                raise ModelLifecycleError("lock_file_invalid")
            if info.st_size == 0:
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, b"\0")
                os.fsync(fd)
            if os.name == "nt":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
        except Exception as exc:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if isinstance(exc, ModelLifecycleError):
                raise
            if isinstance(exc, OSError):
                raise ModelLifecycleError("writer_lock_unavailable") from exc
            raise
        try:
            _assert_no_reparse(self.lock_path)
            yield
        finally:
            try:
                if os.name == "nt":
                    import msvcrt
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _ensure_directory(self, path: Path) -> None:
        _assert_no_reparse(path)
        if not path.exists() and path != self.root and self.root.exists():
            self._check_inventory(add_entries=1)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ModelLifecycleError("directory_unavailable") from exc
        _assert_no_reparse(path)
        if not path.is_dir():
            raise ModelLifecycleError("directory_invalid")

    def _check_inventory(self, *, add_bytes: int = 0, add_entries: int = 0,
                         allow_oversized_main: bool = False) -> tuple[int, int]:
        _assert_no_reparse(self.root)
        if not self.root.is_dir():
            raise ModelLifecycleError("store_root_unavailable")
        allowed_root = {"versions", "admissions", "state.json", "state.previous.json", ".lifecycle.lock"}
        entries = 0
        total_bytes = 0

        def account(path: Path, category: str) -> None:
            nonlocal entries, total_bytes
            _assert_no_reparse(path)
            info = path.lstat()
            entries += 1
            if entries + add_entries > MAX_STORE_ENTRIES:
                raise ModelLifecycleError("store_entry_limit_exceeded")
            if stat.S_ISDIR(info.st_mode):
                return
            if not stat.S_ISREG(info.st_mode):
                raise ModelLifecycleError("store_entry_type_invalid")
            if category == "lock":
                maximum = 1
            elif category == "recoverable_state":
                maximum = MAX_STORE_BYTES
            elif category in {"state", "admission", "manifest"}:
                maximum = MAX_MANIFEST_BYTES
            elif category == "payload":
                maximum = MAX_LAYER_BYTES
            else:
                raise ModelLifecycleError("store_entry_unexpected")
            if info.st_size > maximum:
                raise ModelLifecycleError("store_entry_size_limit_exceeded")
            total_bytes += info.st_size
            if total_bytes + add_bytes > MAX_STORE_BYTES:
                raise ModelLifecycleError("store_size_limit_exceeded")

        for child in self.root.iterdir():
            _assert_no_reparse(child)
            if child.name not in allowed_root:
                raise ModelLifecycleError("store_entry_unexpected")
            if child.name in {"versions", "admissions"}:
                if not child.is_dir():
                    raise ModelLifecycleError("store_directory_invalid")
                account(child, "directory")
                if child.name == "versions":
                    versions = list(child.iterdir())
                    if len(versions) > MAX_VERSIONS:
                        raise ModelLifecycleError("version_count_limit_exceeded")
                    for version in versions:
                        _assert_no_reparse(version)
                        _version_id(version.name)
                        if not version.is_dir():
                            raise ModelLifecycleError("version_directory_invalid")
                        account(version, "directory")
                        filenames = set()
                        version_bytes = 0
                        for item in version.iterdir():
                            _assert_no_reparse(item)
                            if item.name == "manifest.json":
                                category = "manifest"
                            elif item.name in {f"{layer}.bin" for layer in (*LAYERS, "personal")}:
                                category = "payload"
                            else:
                                raise ModelLifecycleError("version_unexpected_file")
                            if not item.is_file():
                                raise ModelLifecycleError("version_entry_type_invalid")
                            filenames.add(item.name)
                            account(item, category)
                            if category == "payload":
                                version_bytes += item.stat().st_size
                        if version_bytes > MAX_TOTAL_BYTES:
                            raise ModelLifecycleError("version_payload_total_limit_exceeded")
                        if "manifest.json" not in filenames:
                            raise ModelLifecycleError("version_manifest_missing")
                else:
                    receipts = list(child.iterdir())
                    if len(receipts) > MAX_VERSIONS:
                        raise ModelLifecycleError("admission_count_limit_exceeded")
                    for receipt_path in receipts:
                        if (not receipt_path.name.endswith(".json") or not receipt_path.is_file()):
                            raise ModelLifecycleError("admission_entry_invalid")
                        _version_id(receipt_path.stem)
                        account(receipt_path, "admission")
            else:
                if not child.is_file():
                    raise ModelLifecycleError("state_entry_invalid")
                if child.name == "state.json" and allow_oversized_main:
                    account(child, "recoverable_state")
                else:
                    account(child, "lock" if child.name == ".lifecycle.lock" else "state")
        if entries + add_entries > MAX_STORE_ENTRIES:
            raise ModelLifecycleError("store_entry_limit_exceeded")
        if total_bytes + add_bytes > MAX_STORE_BYTES:
            raise ModelLifecycleError("store_size_limit_exceeded")
        self._validate_admission_entries()
        return total_bytes, entries

    def _validate_admission_entries(self) -> None:
        """Reject orphan receipt files while deferring receipt checks to use."""
        if not self.admissions_dir.exists():
            return
        for path in self.admissions_dir.iterdir():
            candidate_id = _version_id(path.stem)
            try:
                manifest = self._load_manifest(candidate_id)
            except ModelLifecycleError as exc:
                raise ModelLifecycleError("admission_record_orphaned") from exc
            if manifest.get("kind") != "candidate":
                raise ModelLifecycleError("admission_record_mismatch")

    def _verify_admission_receipt(self, candidate_id: str, manifest: dict) -> None:
        """Require a persisted, exact admission receipt before candidate use."""
        path = self.admissions_dir / f"{_version_id(candidate_id)}.json"
        try:
            raw = _read_regular(path, MAX_MANIFEST_BYTES)
        except ModelLifecycleError as exc:
            raise ModelLifecycleError("candidate_not_admitted") from exc
        expected = {"schema": ADMISSION_SCHEMA, "version_id": candidate_id,
                    "manifest_sha256": _digest(_canonical(manifest)),
                    "parent_version_id": manifest.get("parent_version_id"),
                    "status": "development_admitted", "training_eligible": False,
                    "production_activation": False}
        if raw != _canonical(expected):
            raise ModelLifecycleError("candidate_not_admitted")

    def _write_state(self, state: dict) -> None:
        if self.state_path.exists():
            current = _read_regular(self.state_path, MAX_MANIFEST_BYTES)
            # The backup is a recoverable snapshot of the last committed pointer.
            self._atomic_write(self.backup_path, current)
        self._atomic_write(self.state_path, _canonical(state))

    @staticmethod
    def _write_file(path: Path, data: bytes) -> None:
        _assert_no_reparse(path)
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

    def _atomic_write(self, path: Path, data: bytes) -> None:
        _assert_no_reparse(path)
        self._ensure_directory(path.parent)
        self._check_inventory(add_bytes=len(data), add_entries=1)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            _assert_no_reparse(path)
            _assert_no_reparse(Path(temporary))
            os.replace(temporary, path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise
