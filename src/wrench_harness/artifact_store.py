"""Small, bounded, single-process content-addressed artifact store.

The caller must provide a dedicated root. This module never discovers a
default path and never removes entries it does not recognize.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import shutil
import stat
import threading
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable


MAX_OBJECT_BYTES = 256 * 1024
MAX_OBJECT_COUNT = 64
MAX_MANIFEST_BYTES = 256 * 1024
MAX_MANIFEST_ENTRIES = 128
MAX_EVICTED_TOMBSTONES = 512
MAX_STORE_BYTES = 8 * 1024 * 1024
MAX_STAGING_FILES = 8
MAX_STAGING_FILE_BYTES = MAX_MANIFEST_BYTES
MAX_SOURCE_PATH_CHARS = 1024
MIN_FREE_SPACE_BYTES = 5_000_000_000
_SCHEMA = "wrench.artifact-store.v2"
_LEGACY_SCHEMA = "wrench.artifact-store.v1"
_MAX_UNIX_SECONDS = 253402300799
_HEX = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_NAME = re.compile(r"^[0-9a-f]{64}\.blob$")
_STAGE_NAME = re.compile(r"^stage-[0-9a-f]{32}\.tmp$")


class ArtifactStoreError(RuntimeError):
    """Base class for fail-closed store errors."""


class ArtifactStoreCorruption(ArtifactStoreError):
    """The store cannot prove a complete known-good view."""


class ArtifactStoreLimitError(ArtifactStoreError):
    """A hard object, manifest, or aggregate storage limit was reached."""


class ArtifactRequestError(ArtifactStoreError):
    """An artifact request scope is inactive, mismatched, or already closed."""


class ArtifactIdentityError(ValueError):
    """The caller supplied invalid or inconsistent source identity data."""


class ArtifactReadStatus(str, Enum):
    OK = "ok"
    MISSING = "missing"
    EVICTED = "evicted"
    CORRUPT = "corrupt"


@dataclass(frozen=True)
class ArtifactHandle:
    snapshot_sha256: str
    source_path: str
    content_sha256: str
    size_bytes: int
    handle_id: str


@dataclass(frozen=True)
class ArtifactRead:
    status: ArtifactReadStatus
    data: bytes | None = None


@dataclass(frozen=True)
class EvictionResult:
    handles: tuple[ArtifactHandle, ...]
    object_bytes_reclaimed: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _normalize_source_path(path: str) -> str:
    if not isinstance(path, str) or not path or len(path) > MAX_SOURCE_PATH_CHARS or "\x00" in path:
        raise ArtifactIdentityError("invalid_source_path")
    path = path.replace("\\", "/")
    if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
        raise ArtifactIdentityError("absolute_source_path_forbidden")
    components = path.split("/")
    if any(part == ".." for part in components):
        raise ArtifactIdentityError("parent_source_path_forbidden")
    if any(":" in part for part in components):
        raise ArtifactIdentityError("alternate_data_stream_forbidden")
    if any(part not in ("", ".") and part.endswith((".", " ")) for part in components):
        raise ArtifactIdentityError("ambiguous_source_path")
    normalized = "/".join(part for part in components if part not in ("", "."))
    if not normalized:
        raise ArtifactIdentityError("empty_source_path")
    try:
        normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ArtifactIdentityError("source_path_encoding_invalid") from exc
    return normalized


def _make_handle_id(snapshot_sha256: str, source_path: str, content_sha256: str) -> str:
    return _sha256(_canonical_json([snapshot_sha256, source_path, content_sha256]))


def _is_reparse(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _regular_file(path: Path) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ArtifactStoreCorruption(f"store file unavailable: {path.name}") from exc
    if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISREG(info.st_mode):
        raise ArtifactStoreCorruption(f"unsafe store entry: {path.name}")
    return info


def _prepare_store_root(root: str | os.PathLike[str]) -> Path:
    """Validate/create every root component without following links."""
    try:
        raw_root = os.fspath(root)
    except TypeError as exc:
        raise ValueError("an explicit dedicated store root is required") from exc
    if not isinstance(raw_root, str) or not raw_root:
        raise ValueError("an explicit dedicated store root is required")

    target = Path(os.path.abspath(raw_root))
    anchor = Path(target.anchor)
    if not target.anchor:
        raise ArtifactStoreCorruption("store root has no filesystem anchor")

    current = anchor
    try:
        anchor_info = current.lstat()
    except OSError as exc:
        raise ArtifactStoreCorruption("cannot inspect store root anchor") from exc
    if stat.S_ISLNK(anchor_info.st_mode) or _is_reparse(anchor_info) or not stat.S_ISDIR(anchor_info.st_mode):
        raise ArtifactStoreCorruption("store root anchor is unsafe")

    for component in target.parts[1:]:
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                # Recheck a concurrent creator without following its entry.
                pass
            except OSError as exc:
                raise ArtifactStoreCorruption("cannot create validated store root") from exc
            try:
                info = current.lstat()
            except OSError as exc:
                raise ArtifactStoreCorruption("cannot inspect store root component") from exc
        except OSError as exc:
            raise ArtifactStoreCorruption("cannot inspect store root component") from exc

        if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
            raise ArtifactStoreCorruption("store root chain contains an unsafe component")
    return target


def _bounded_children(directory: Path, limit: int, label: str) -> list[Path]:
    try:
        with os.scandir(directory) as iterator:
            names = [entry.name for entry in itertools.islice(iterator, limit + 1)]
    except OSError as exc:
        raise ArtifactStoreCorruption(f"cannot enumerate {label}") from exc
    if len(names) > limit:
        raise ArtifactStoreLimitError(f"{label}_count_limit_exceeded")
    return [directory / name for name in names]


class ArtifactStore:
    """Explicit-root artifact store with atomic manifests and local request pins.

    Use one instance per root. Concurrency protection is process-local only.
    Do not open the same root from multiple instances/processes or allow
    external writers while a store is active.
    """

    def __init__(
        self,
        root: str | os.PathLike[str],
        *,
        free_space_probe: Callable[[Path], int] | None = None,
    ):
        self.root = _prepare_store_root(root)
        if free_space_probe is not None and not callable(free_space_probe):
            raise TypeError("free_space_probe must be callable")
        self._free_space_probe = (
            free_space_probe
            if free_space_probe is not None
            else lambda path: shutil.disk_usage(path).free
        )
        self.objects = self.root / "objects"
        self.staging = self.root / "staging"
        self._lock = threading.RLock()
        self._pins: dict[str, int] = {}
        self._active_handles: dict[str, ArtifactHandle] = {}
        self.recovery_status = "clean"
        for directory in (self.objects, self.staging):
            try:
                directory.mkdir(exist_ok=True)
            except OSError as exc:
                raise ArtifactStoreCorruption("cannot create store directories") from exc
            info = directory.lstat()
            if stat.S_ISLNK(info.st_mode) or _is_reparse(info) or not stat.S_ISDIR(info.st_mode):
                raise ArtifactStoreCorruption(f"unsafe store directory: {directory.name}")
        self._validate_layout()
        self._objects_on_disk = self._scan_objects()
        self._load_recover()
        self._assert_store_size()

    def _validate_layout(self) -> None:
        allowed = {"objects", "staging", "manifest.json", "manifest.prev.json"}
        for item in _bounded_children(self.root, len(allowed), "root_entry"):
            if item.name not in allowed:
                raise ArtifactStoreCorruption(f"unrecognized root entry: {item.name}")
        for item in self._staging_files():
            info = item.lstat()
            if (
                not _STAGE_NAME.fullmatch(item.name)
                or stat.S_ISLNK(info.st_mode)
                or _is_reparse(info)
                or not stat.S_ISREG(info.st_mode)
            ):
                raise ArtifactStoreCorruption(f"unrecognized staging entry: {item.name}")
            if info.st_size > MAX_STAGING_FILE_BYTES:
                raise ArtifactStoreLimitError("staging_file_size_limit_exceeded")

    def _staging_files(self) -> list[Path]:
        return _bounded_children(self.staging, MAX_STAGING_FILES, "staging_file")

    def _ensure_stage_slot(self) -> None:
        staged = self._staging_files()
        if len(staged) >= MAX_STAGING_FILES:
            raise ArtifactStoreLimitError("staging_file_count_limit_exceeded")
        for path in staged:
            info = _regular_file(path)
            if not _STAGE_NAME.fullmatch(path.name):
                raise ArtifactStoreCorruption(f"unrecognized staging entry: {path.name}")
            if info.st_size > MAX_STAGING_FILE_BYTES:
                raise ArtifactStoreLimitError("staging_file_size_limit_exceeded")

    def _scan_objects(self) -> dict[str, int]:
        objects: dict[str, int] = {}
        for item in _bounded_children(self.objects, MAX_OBJECT_COUNT, "object"):
            info = _regular_file(item)
            match = _OBJECT_NAME.fullmatch(item.name)
            if not match:
                raise ArtifactStoreCorruption(f"unrecognized object entry: {item.name}")
            digest = item.name[:-5]
            if digest in objects:
                raise ArtifactStoreCorruption("duplicate object digest")
            data = self._read_bounded(item, MAX_OBJECT_BYTES)
            if len(data) != info.st_size or _sha256(data) != digest:
                raise ArtifactStoreCorruption(f"object hash mismatch: {item.name}")
            objects[digest] = len(data)
        return objects

    @staticmethod
    def _read_bounded(path: Path, limit: int) -> bytes:
        info = _regular_file(path)
        if info.st_size > limit:
            raise ArtifactStoreCorruption(f"store file exceeds limit: {path.name}")
        try:
            with path.open("rb") as stream:
                data = stream.read(limit + 1)
                after = os.fstat(stream.fileno())
        except OSError as exc:
            raise ArtifactStoreCorruption(f"store read failed: {path.name}") from exc
        if len(data) > limit or len(data) != info.st_size or len(data) != after.st_size:
            raise ArtifactStoreCorruption(f"store file changed during read: {path.name}")
        return data

    def _disk_usage(self) -> int:
        total = 0
        for name in ("manifest.json", "manifest.prev.json"):
            path = self.root / name
            if os.path.lexists(path):
                total += _regular_file(path).st_size
        for directory in (self.objects, self.staging):
            if directory == self.objects:
                children = _bounded_children(directory, MAX_OBJECT_COUNT, "object")
            else:
                children = self._staging_files()
            for path in children:
                size = _regular_file(path).st_size
                if directory == self.staging and size > MAX_STAGING_FILE_BYTES:
                    raise ArtifactStoreLimitError("staging_file_size_limit_exceeded")
                total += size
        return total

    def _assert_store_size(self, additional: int = 0) -> None:
        if self._disk_usage() + additional > MAX_STORE_BYTES:
            raise ArtifactStoreLimitError("aggregate_store_limit_exceeded")

    def _require_volume_headroom(self, projected_write_bytes: int) -> None:
        """Require the documented physical free-space reserve before a bounded write."""
        if (
            not isinstance(projected_write_bytes, int)
            or isinstance(projected_write_bytes, bool)
            or projected_write_bytes < 0
        ):
            raise ValueError("projected_write_bytes must be a nonnegative integer")
        try:
            free_bytes = self._free_space_probe(self.root)
        except Exception as exc:
            raise ArtifactStoreLimitError("physical_volume_headroom_unavailable") from exc
        if (
            not isinstance(free_bytes, int)
            or isinstance(free_bytes, bool)
            or free_bytes < projected_write_bytes + MIN_FREE_SPACE_BYTES
        ):
            raise ArtifactStoreLimitError("physical_volume_headroom_insufficient")

    def _encode_manifest(self, payload: dict[str, object]) -> bytes:
        body = _canonical_json(payload)
        encoded = _canonical_json({"payload": payload, "sha256": _sha256(body)})
        if len(encoded) > MAX_MANIFEST_BYTES:
            raise ArtifactStoreLimitError("manifest_size_limit_exceeded")
        return encoded

    def _decode_manifest(self, raw: bytes) -> dict[str, object]:
        if len(raw) > MAX_MANIFEST_BYTES:
            raise ArtifactStoreCorruption("manifest_size_limit_exceeded")

        def no_duplicate_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result

        try:
            envelope = json.loads(raw, object_pairs_hook=no_duplicate_keys)
        except (ValueError, UnicodeDecodeError, RecursionError) as exc:
            raise ArtifactStoreCorruption("manifest_json_invalid") from exc
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "sha256"}:
            raise ArtifactStoreCorruption("manifest_envelope_invalid")
        payload = envelope["payload"]
        try:
            checksum = _sha256(_canonical_json(payload))
        except (UnicodeEncodeError, RecursionError, TypeError, ValueError) as exc:
            raise ArtifactStoreCorruption("manifest_checksum_invalid") from exc
        if not isinstance(payload, dict) or envelope["sha256"] != checksum:
            raise ArtifactStoreCorruption("manifest_checksum_invalid")
        legacy = payload.get("schema") == _LEGACY_SCHEMA
        expected_payload_keys = {"schema", "generation", "entries", "evicted"}
        if not legacy:
            expected_payload_keys.add("retention_schema")
        if (
            set(payload) != expected_payload_keys
            or not isinstance(payload["schema"], str)
            or payload["schema"] not in {_SCHEMA, _LEGACY_SCHEMA}
        ):
            raise ArtifactStoreCorruption("manifest_schema_invalid")
        if not legacy and (
            not isinstance(payload["retention_schema"], int)
            or isinstance(payload["retention_schema"], bool)
            or payload["retention_schema"] != 1
        ):
            raise ArtifactStoreCorruption("manifest_retention_schema_invalid")
        generation = payload["generation"]
        entries = payload["entries"]
        evicted = payload["evicted"]
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            raise ArtifactStoreCorruption("manifest_generation_invalid")
        if not isinstance(entries, list) or len(entries) > MAX_MANIFEST_ENTRIES:
            raise ArtifactStoreCorruption("manifest_entry_limit_exceeded")
        if not isinstance(evicted, list) or len(evicted) > MAX_EVICTED_TOMBSTONES:
            raise ArtifactStoreCorruption("manifest_tombstone_limit_exceeded")
        ids: list[str] = []
        normalized_entries: list[dict[str, object]] = []
        legacy_entry_keys = {
            "handle_id", "snapshot_sha256", "source_path", "content_sha256", "size_bytes", "added_generation"
        }
        current_entry_keys = legacy_entry_keys | {"disposition", "expires_at_unix_seconds"}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != (legacy_entry_keys if legacy else current_entry_keys):
                raise ArtifactStoreCorruption("manifest_entry_invalid")
            snapshot = entry["snapshot_sha256"]
            digest = entry["content_sha256"]
            path = entry["source_path"]
            size = entry["size_bytes"]
            handle_id = entry["handle_id"]
            added = entry["added_generation"]
            if not isinstance(snapshot, str) or not _HEX.fullmatch(snapshot):
                raise ArtifactStoreCorruption("manifest_snapshot_identity_invalid")
            if not isinstance(digest, str) or not _HEX.fullmatch(digest):
                raise ArtifactStoreCorruption("manifest_content_identity_invalid")
            if not isinstance(path, str) or _normalize_source_path(path) != path:
                raise ArtifactStoreCorruption("manifest_source_path_invalid")
            if not isinstance(size, int) or isinstance(size, bool) or not 0 <= size <= MAX_OBJECT_BYTES:
                raise ArtifactStoreCorruption("manifest_object_size_invalid")
            try:
                expected_handle_id = _make_handle_id(snapshot, path, digest)
            except (UnicodeEncodeError, RecursionError, TypeError, ValueError) as exc:
                raise ArtifactStoreCorruption("manifest_handle_invalid") from exc
            if not isinstance(handle_id, str) or handle_id != expected_handle_id:
                raise ArtifactStoreCorruption("manifest_handle_invalid")
            if not isinstance(added, int) or isinstance(added, bool) or not 0 <= added <= generation:
                raise ArtifactStoreCorruption("manifest_entry_generation_invalid")
            ids.append(handle_id)
            normalized = dict(entry)
            if legacy:
                normalized["disposition"] = "protected"
                normalized["expires_at_unix_seconds"] = None
            else:
                disposition = entry["disposition"]
                expiry = entry["expires_at_unix_seconds"]
                if not isinstance(disposition, str) or disposition not in {"protected", "disposable"}:
                    raise ArtifactStoreCorruption("manifest_disposition_invalid")
                if expiry is not None and (
                    not isinstance(expiry, int)
                    or isinstance(expiry, bool)
                    or not 0 <= expiry <= _MAX_UNIX_SECONDS
                ):
                    raise ArtifactStoreCorruption("manifest_expiry_invalid")
                if (disposition == "protected") != (expiry is None):
                    raise ArtifactStoreCorruption("manifest_retention_pair_invalid")
            normalized_entries.append(normalized)
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise ArtifactStoreCorruption("manifest_entry_order_invalid")
        if any(not isinstance(value, str) or not _HEX.fullmatch(value) for value in evicted):
            raise ArtifactStoreCorruption("manifest_tombstone_invalid")
        if len(evicted) != len(set(evicted)):
            raise ArtifactStoreCorruption("manifest_tombstone_duplicate")
        return {
            "schema": _SCHEMA,
            "retention_schema": 1,
            "generation": generation,
            "entries": normalized_entries,
            "evicted": list(evicted),
        }

    def _validate_references(self, payload: dict[str, object]) -> None:
        for entry in payload["entries"]:
            digest = entry["content_sha256"]
            size = entry["size_bytes"]
            if self._objects_on_disk.get(digest) != size:
                raise ArtifactStoreCorruption(f"manifest object missing or mismatched: {digest}")

    def _manifest_raw(self, name: str) -> bytes | None:
        path = self.root / name
        if not os.path.lexists(path):
            return None
        info = _regular_file(path)
        if info.st_size > MAX_MANIFEST_BYTES:
            raise ArtifactStoreCorruption("manifest_size_limit_exceeded")
        return self._read_bounded(path, MAX_MANIFEST_BYTES)

    def _load_recover(self) -> None:
        current_raw = self._manifest_raw("manifest.json")
        previous_raw = self._manifest_raw("manifest.prev.json")
        current = previous = None
        current_error = previous_error = None
        if current_raw is not None:
            try:
                current = self._decode_manifest(current_raw)
                self._validate_references(current)
            except (ArtifactStoreError, ArtifactIdentityError) as exc:
                current_error = exc
        if previous_raw is not None:
            try:
                previous = self._decode_manifest(previous_raw)
                self._validate_references(previous)
            except (ArtifactStoreError, ArtifactIdentityError) as exc:
                previous_error = exc
        if current is not None:
            if previous_raw is not None and previous is None:
                raise ArtifactStoreCorruption("previous manifest is corrupt") from previous_error
            self._payload = current
        elif previous is not None:
            self._payload = previous
            self._atomic_write(self.root / "manifest.json", previous_raw)
            self.recovery_status = "restored_previous_manifest"
        elif current_raw is None and previous_raw is None and not self._objects_on_disk and not self._staging_files():
            self._payload = {
                "schema": _SCHEMA, "retention_schema": 1,
                "generation": 0, "entries": [], "evicted": [],
            }
            self._atomic_write(self.root / "manifest.json", self._encode_manifest(self._payload))
            self.recovery_status = "initialized_empty_store"
        else:
            raise ArtifactStoreCorruption("no valid current or previous manifest") from (current_error or previous_error)
        if self._staging_files():
            self.recovery_status = f"{self.recovery_status}:staging_retained"

    def _atomic_write(self, destination: Path, data: bytes) -> None:
        if len(data) > MAX_MANIFEST_BYTES:
            raise ArtifactStoreLimitError("manifest_size_limit_exceeded")
        self._assert_store_size(len(data))
        # Atomic replacement first stages a complete extra copy while the old
        # destination may still exist, so reserve the full staged byte count.
        self._require_volume_headroom(len(data))
        temporary = self.staging / f"stage-{uuid.uuid4().hex}.tmp"
        self._ensure_stage_slot()
        created = False
        try:
            with temporary.open("xb") as stream:
                created = True
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            created = False
        finally:
            if created and temporary.exists():
                temporary.unlink()

    def _commit(self, payload: dict[str, object]) -> None:
        raw = self._encode_manifest(payload)
        current = self._manifest_raw("manifest.json")
        if current is not None:
            self._atomic_write(self.root / "manifest.prev.json", current)
        self._atomic_write(self.root / "manifest.json", raw)
        self._payload = payload

    def _entry_map(self) -> dict[str, dict[str, object]]:
        return {item["handle_id"]: item for item in self._payload["entries"]}

    @staticmethod
    def _entry_handle(entry: dict[str, object]) -> ArtifactHandle:
        return ArtifactHandle(
            entry["snapshot_sha256"], entry["source_path"], entry["content_sha256"],
            entry["size_bytes"], entry["handle_id"],
        )

    def put(
        self,
        *,
        snapshot_sha256: str,
        source_path: str,
        expected_content_sha256: str,
        data: bytes,
        disposition: str = "protected",
        expires_at_unix_seconds: int | None = None,
    ) -> ArtifactHandle:
        """Store verified bytes with protected-by-default retention.

        Disposable records require an explicit UTC Unix expiry. Re-putting an
        existing identity can promote it to protected, but cannot silently
        replace or shorten its retention metadata.
        """
        if not isinstance(snapshot_sha256, str) or not _HEX.fullmatch(snapshot_sha256):
            raise ArtifactIdentityError("invalid_snapshot_sha256")
        path = _normalize_source_path(source_path)
        if not isinstance(expected_content_sha256, str) or not _HEX.fullmatch(expected_content_sha256):
            raise ArtifactIdentityError("invalid_expected_content_sha256")
        if not isinstance(data, bytes):
            raise ArtifactIdentityError("artifact_data_must_be_bytes")
        if len(data) > MAX_OBJECT_BYTES:
            raise ArtifactStoreLimitError("object_size_limit_exceeded")
        if not isinstance(disposition, str) or disposition not in {"protected", "disposable"}:
            raise ArtifactIdentityError("invalid_artifact_disposition")
        if expires_at_unix_seconds is not None and (
            not isinstance(expires_at_unix_seconds, int)
            or isinstance(expires_at_unix_seconds, bool)
            or not 0 <= expires_at_unix_seconds <= _MAX_UNIX_SECONDS
        ):
            raise ArtifactIdentityError("invalid_artifact_expiry")
        if (disposition == "protected") != (expires_at_unix_seconds is None):
            raise ArtifactIdentityError("artifact_retention_pair_invalid")
        actual_digest = _sha256(data)
        if actual_digest != expected_content_sha256:
            raise ArtifactIdentityError("source_content_hash_mismatch")
        handle_id = _make_handle_id(snapshot_sha256, path, actual_digest)
        with self._lock:
            current = self._entry_map()
            existing = current.get(handle_id)
            if existing is not None:
                result = self.read(self._entry_handle(existing))
                if result.status is not ArtifactReadStatus.OK or result.data != data:
                    raise ArtifactStoreCorruption("existing handle failed exact verification")
                if existing["disposition"] == "disposable" and disposition == "protected":
                    promoted = dict(existing)
                    promoted["disposition"] = "protected"
                    promoted["expires_at_unix_seconds"] = None
                    candidate = dict(self._payload)
                    candidate["generation"] = self._payload["generation"] + 1
                    candidate["entries"] = sorted(
                        [promoted if row["handle_id"] == handle_id else row for row in current.values()],
                        key=lambda row: row["handle_id"],
                    )
                    self._commit(candidate)
                    # Do not report a completed promotion while the rollback
                    # manifest could still restore the old disposable class.
                    compacted = dict(candidate)
                    compacted["generation"] = candidate["generation"] + 1
                    self._commit(compacted)
                    return self._entry_handle(promoted)
                if (
                    existing["disposition"] != disposition
                    or existing["expires_at_unix_seconds"] != expires_at_unix_seconds
                ):
                    raise ArtifactIdentityError("artifact_retention_conflict")
                return self._entry_handle(existing)
            if len(current) >= MAX_MANIFEST_ENTRIES:
                raise ArtifactStoreLimitError("manifest_entry_limit_exceeded")
            if actual_digest not in self._objects_on_disk and len(self._objects_on_disk) >= MAX_OBJECT_COUNT:
                raise ArtifactStoreLimitError("object_count_limit_exceeded")
            generation = self._payload["generation"] + 1
            entry = {
                "handle_id": handle_id,
                "snapshot_sha256": snapshot_sha256,
                "source_path": path,
                "content_sha256": actual_digest,
                "size_bytes": len(data),
                "added_generation": generation,
                "disposition": disposition,
                "expires_at_unix_seconds": expires_at_unix_seconds,
            }
            candidate = dict(self._payload)
            candidate["generation"] = generation
            candidate["entries"] = sorted([*current.values(), entry], key=lambda row: row["handle_id"])
            candidate["evicted"] = [item for item in candidate["evicted"] if item != handle_id]
            raw = self._encode_manifest(candidate)
            has_object = actual_digest in self._objects_on_disk
            self._assert_store_size((0 if has_object else len(data)) + max(len(raw), len(self._manifest_raw("manifest.json") or b"")))
            if not has_object:
                staged = self.staging / f"stage-{uuid.uuid4().hex}.tmp"
                self._ensure_stage_slot()
                self._require_volume_headroom(len(data))
                try:
                    with staged.open("xb") as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                    if _sha256(self._read_bounded(staged, MAX_OBJECT_BYTES)) != actual_digest:
                        raise ArtifactStoreCorruption("staged object verification failed")
                    os.replace(staged, self.objects / f"{actual_digest}.blob")
                finally:
                    if staged.exists():
                        staged.unlink()
                self._objects_on_disk[actual_digest] = len(data)
            self._commit(candidate)
            return self._entry_handle(entry)

    def read(self, handle: ArtifactHandle) -> ArtifactRead:
        with self._lock:
            if not isinstance(handle, ArtifactHandle):
                return ArtifactRead(ArtifactReadStatus.MISSING)
            if (
                not isinstance(handle.snapshot_sha256, str)
                or not _HEX.fullmatch(handle.snapshot_sha256)
                or not isinstance(handle.content_sha256, str)
                or not _HEX.fullmatch(handle.content_sha256)
                or not isinstance(handle.source_path, str)
                or not isinstance(handle.size_bytes, int)
                or isinstance(handle.size_bytes, bool)
                or not 0 <= handle.size_bytes <= MAX_OBJECT_BYTES
                or not isinstance(handle.handle_id, str)
                or not _HEX.fullmatch(handle.handle_id)
            ):
                return ArtifactRead(ArtifactReadStatus.MISSING)
            try:
                if _normalize_source_path(handle.source_path) != handle.source_path:
                    return ArtifactRead(ArtifactReadStatus.MISSING)
                expected_handle_id = _make_handle_id(
                    handle.snapshot_sha256, handle.source_path, handle.content_sha256
                )
            except (ArtifactIdentityError, TypeError, ValueError):
                return ArtifactRead(ArtifactReadStatus.MISSING)
            if handle.handle_id != expected_handle_id:
                return ArtifactRead(ArtifactReadStatus.MISSING)
            entries = self._entry_map()
            entry = entries.get(handle.handle_id)
            if entry is None:
                status = ArtifactReadStatus.EVICTED if handle.handle_id in self._payload["evicted"] else ArtifactReadStatus.MISSING
                return ArtifactRead(status)
            if self._entry_handle(entry) != handle:
                return ArtifactRead(ArtifactReadStatus.MISSING)
            object_path = self.objects / f"{entry['content_sha256']}.blob"
            try:
                data = self._read_bounded(object_path, MAX_OBJECT_BYTES)
            except ArtifactStoreCorruption:
                return ArtifactRead(ArtifactReadStatus.CORRUPT)
            if len(data) != entry["size_bytes"] or _sha256(data) != entry["content_sha256"]:
                return ArtifactRead(ArtifactReadStatus.CORRUPT)
            return ArtifactRead(ArtifactReadStatus.OK, data)

    def request(self) -> "ArtifactRequest":
        return ArtifactRequest(self)

    def evict(self, *, target_bytes: int, now_unix_seconds: int) -> EvictionResult:
        """Remove only expired, unpinned disposable blobs meeting the target.

        A blob is eligible only when every manifest handle referencing it is
        itself eligible. If eligible blobs cannot satisfy the requested byte
        target, the store is left unchanged.
        """
        if not isinstance(target_bytes, int) or isinstance(target_bytes, bool) or target_bytes < 1:
            raise ValueError("target_bytes must be positive")
        if (
            not isinstance(now_unix_seconds, int)
            or isinstance(now_unix_seconds, bool)
            or not 0 <= now_unix_seconds <= _MAX_UNIX_SECONDS
        ):
            raise ValueError("now_unix_seconds must be a valid UTC epoch second")
        with self._lock:
            entries = self._entry_map()
            references: dict[str, list[dict[str, object]]] = {}
            for entry in entries.values():
                references.setdefault(entry["content_sha256"], []).append(entry)
            eligible_groups: list[tuple[str, list[dict[str, object]]]] = []
            for digest, rows in references.items():
                if digest not in self._objects_on_disk:
                    continue
                if not all(
                    entry["disposition"] == "disposable"
                    and entry["expires_at_unix_seconds"] <= now_unix_seconds
                    and self._pins.get(entry["handle_id"], 0) == 0
                    for entry in rows
                ):
                    continue
                eligible_groups.append((digest, rows))
            eligible_groups.sort(
                key=lambda group: (
                    min(entry["expires_at_unix_seconds"] for entry in group[1]),
                    min(entry["added_generation"] for entry in group[1]),
                    min(entry["handle_id"] for entry in group[1]),
                    group[0],
                )
            )
            removed: list[dict[str, object]] = []
            remaining = dict(entries)
            reclaimed_hashes: set[str] = set()
            reclaimed = 0
            for digest, group in eligible_groups:
                removed.extend(sorted(group, key=lambda entry: entry["handle_id"]))
                for entry in group:
                    remaining.pop(entry["handle_id"])
                reclaimed_hashes.add(digest)
                reclaimed += self._objects_on_disk[digest]
                if reclaimed >= target_bytes:
                    break
            if not removed or reclaimed < target_bytes:
                return EvictionResult((), 0)
            tombstones = list(self._payload["evicted"])
            tombstones.extend(row["handle_id"] for row in removed)
            tombstones = tombstones[-MAX_EVICTED_TOMBSTONES:]
            candidate = dict(self._payload)
            candidate["generation"] = self._payload["generation"] + 1
            candidate["entries"] = sorted(remaining.values(), key=lambda row: row["handle_id"])
            candidate["evicted"] = tombstones
            self._commit(candidate)
            # The first commit retains the old manifest. A second verified
            # generation makes the new manifest the rollback point before any
            # object deletion, so a crash cannot restore references we removed.
            compacted = dict(candidate)
            compacted["generation"] = candidate["generation"] + 1
            self._commit(compacted)
            still_referenced = {row["content_sha256"] for row in self._payload["entries"]}
            deleted_hashes = reclaimed_hashes.difference(still_referenced)
            deleted_bytes = 0
            for digest in sorted(deleted_hashes):
                object_path = self.objects / f"{digest}.blob"
                if object_path.exists():
                    _regular_file(object_path)
                    object_path.unlink()
                    deleted_bytes += self._objects_on_disk[digest]
                    self._objects_on_disk.pop(digest, None)
            handles = tuple(self._entry_handle(entry) for entry in removed)
            return EvictionResult(handles, deleted_bytes)


class ArtifactRequest:
    """One-shot, request-scoped process-local pins released on context exit."""

    def __init__(self, store: ArtifactStore):
        self._store = store
        self._pinned: set[str] = set()
        self._entered = False
        self._closed = False

    def __enter__(self) -> "ArtifactRequest":
        with self._store._lock:
            if self._entered or self._closed:
                raise ArtifactRequestError("request scope cannot be entered more than once")
            self._entered = True
        return self

    def is_active_for(self, store: ArtifactStore) -> bool:
        """Return whether this open scope belongs to ``store``."""
        if type(store) is not ArtifactStore:
            return False
        with self._store._lock:
            return self._store is store and self._entered and not self._closed

    def pin(self, handle: ArtifactHandle) -> ArtifactRead:
        with self._store._lock:
            if not self._entered or self._closed:
                raise ArtifactRequestError("request scope is not active")
            result = self._store.read(handle)
            if result.status is ArtifactReadStatus.OK and handle.handle_id not in self._pinned:
                self._store._pins[handle.handle_id] = self._store._pins.get(handle.handle_id, 0) + 1
                self._pinned.add(handle.handle_id)
            return result

    def read(self, handle: ArtifactHandle) -> ArtifactRead:
        with self._store._lock:
            if not self._entered or self._closed:
                raise ArtifactRequestError("request scope is not active")
            return self._store.read(handle)

    def __exit__(self, exc_type, exc, traceback) -> None:
        with self._store._lock:
            if not self._entered or self._closed:
                return None
            self._entered = False
            self._closed = True
            for handle_id in tuple(self._pinned):
                count = self._store._pins.get(handle_id, 0) - 1
                if count > 0:
                    self._store._pins[handle_id] = count
                else:
                    self._store._pins.pop(handle_id, None)
            self._pinned.clear()


__all__ = [
    "ArtifactHandle",
    "ArtifactIdentityError",
    "ArtifactRead",
    "ArtifactReadStatus",
    "ArtifactRequest",
    "ArtifactRequestError",
    "ArtifactStore",
    "ArtifactStoreCorruption",
    "ArtifactStoreError",
    "ArtifactStoreLimitError",
    "EvictionResult",
    "MAX_EVICTED_TOMBSTONES",
    "MAX_MANIFEST_BYTES",
    "MAX_MANIFEST_ENTRIES",
    "MAX_OBJECT_BYTES",
    "MAX_OBJECT_COUNT",
    "MAX_STORE_BYTES",
]
