"""Bounded append-only persistence for validated execution-state patches.

Each committed transition is one hash-linked event file. A state is rebuilt
from the event sequence on load, so a process interruption after the event is
published does not lose the latest revision. A fully written staging event is
also verified and promoted during recovery. This is process-interruption
recovery, not a claim of power-loss durability.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from .execution_state import (
    EvidenceSource,
    ExecutionState,
    ExecutionStateError,
    StateFieldSpec,
    StatePatchResult,
    _canonical_json,
    _validate_evidence_manifest,
    stable_source_evidence_id,
    _validate_field_specs,
    apply_state_patch,
    new_execution_state,
)


EVENT_SCHEMA = "wrench.execution-state-event.v1"
GENESIS_SHA256 = "0" * 64
MAX_STORE_EVENTS = 4096
MAX_STORE_BYTES = 64 * 1024 * 1024
MAX_EVENT_BYTES = 256 * 1024
MAX_STAGING_FILES = 16
_FINAL_NAME_RE = re.compile(r"^revision-(\d{8})\.json$")
_TEMP_NAME_RE = re.compile(r"^revision-(\d{8})\.([0-9a-f]{32})\.tmp$")
_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.RLock] = {}


@dataclass(frozen=True)
class StateStoreLoadReceipt:
    state: ExecutionState
    event_count: int
    last_event_sha256: str
    recovered_staged_event: bool
    ignored_staging_files: tuple[str, ...]
    current_evidence_verified: bool = True


@dataclass(frozen=True)
class StateStoreCommitReceipt:
    result: StatePatchResult
    event_sha256: str
    event_count: int
    recovered_staged_event_before_commit: bool
    ignored_staging_files: tuple[str, ...]


class ExecutionStateStore:
    """Host-authorized directory containing one task's bounded state log.

    Callers must choose a root under an approved Wrench storage location and
    reserve the expected writes before use. The model never supplies paths.
    Every load requires the caller's current evidence manifest; state with a
    missing or changed evidence hash fails closed.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        session_id: str,
        task_spec_sha256: str,
        field_specs: Mapping[str, StateFieldSpec],
        max_events: int = MAX_STORE_EVENTS,
        max_bytes: int = MAX_STORE_BYTES,
    ) -> None:
        requested_root = Path(root)
        if ".." in requested_root.parts:
            raise ValueError("state_store_root_parent_traversal_invalid")
        self.root = requested_root.absolute()
        if not self.root.is_absolute():
            raise ValueError("state_store_root_must_be_absolute")
        self.events_dir = self.root / "events"
        self.lock_path = self.root / "state.lock"
        self.session_id = session_id
        self.task_spec_sha256 = task_spec_sha256
        self._initial_state = new_execution_state(session_id, task_spec_sha256)
        self.field_specs = _validate_field_specs(field_specs)
        self.field_schema_sha256 = _field_schema_sha256(self.field_specs)
        if (
            not isinstance(max_events, int)
            or isinstance(max_events, bool)
            or not 1 <= max_events <= MAX_STORE_EVENTS
        ):
            raise ValueError("state_store_event_limit_invalid")
        if (
            not isinstance(max_bytes, int)
            or isinstance(max_bytes, bool)
            or not 1 <= max_bytes <= MAX_STORE_BYTES
        ):
            raise ValueError("state_store_byte_limit_invalid")
        self.max_events = max_events
        self.max_bytes = max_bytes

    def load(self, *, evidence_hashes: Mapping[str, str]) -> StateStoreLoadReceipt:
        """Replay and validate the event log against current source evidence."""

        with self._locked():
            return self._load_locked(evidence_hashes=evidence_hashes)

    def load_for_revalidation(self) -> StateStoreLoadReceipt:
        """Replay the hash-linked event chain before reacquiring live sources.

        The returned facts are not current-evidence-validated. They must not be
        sent to a model or otherwise relied on until a caller reacquires every
        cited source and checks its exact path, namespace, and content hash.
        """

        with self._locked():
            return self._load_locked(evidence_hashes={}, verify_current_evidence=False)

    def commit(
        self,
        proposal: object,
        *,
        evidence_hashes: Mapping[str, str],
        evidence_sources: Mapping[str, EvidenceSource] | None = None,
    ) -> StateStoreCommitReceipt:
        """Validate, serialize, and atomically publish one state transition."""

        with self._locked():
            loaded = self._load_locked(evidence_hashes=evidence_hashes)
            result = apply_state_patch(
                loaded.state,
                proposal,
                field_specs=self.field_specs,
                evidence_hashes=evidence_hashes,
                evidence_sources=evidence_sources,
            )
            patch = json.loads(result.normalized_patch_json.decode("utf-8"))
            referenced_ids = {
                evidence_id
                for change in patch["changes"]
                for evidence_id in change["evidence_ids"]
            }
            referenced_ids.update(_state_evidence_hashes(result.state))
            event_evidence = {
                evidence_id: evidence_hashes[evidence_id]
                for evidence_id in sorted(referenced_ids)
            }
            record = {
                "schema": EVENT_SCHEMA,
                "session_id": self.session_id,
                "task_spec_sha256": self.task_spec_sha256,
                "field_schema_sha256": self.field_schema_sha256,
                "revision": result.state.revision,
                "previous_event_sha256": loaded.last_event_sha256,
                "patch": patch,
                "evidence_hashes": event_evidence,
                "state_sha256": result.state.sha256,
            }
            state_sources = _state_evidence_sources(result.state)
            if state_sources:
                record["evidence_sources"] = {
                    evidence_id: {
                        "source_namespace_sha256": source.source_namespace_sha256,
                        "source_path": source.source_path,
                    }
                    for evidence_id, source in sorted(state_sources.items())
                }
            event_sha256 = hashlib.sha256(_canonical_json(record)).hexdigest()
            encoded = _canonical_json({**record, "event_sha256": event_sha256}) + b"\n"
            if len(encoded) > MAX_EVENT_BYTES:
                raise ExecutionStateError("state_store_event_byte_limit_exceeded")

            finals, staging, total_bytes = self._scan_store_files()
            if len(finals) >= self.max_events:
                raise ExecutionStateError("state_store_event_limit_exceeded")
            if len(staging) >= MAX_STAGING_FILES:
                raise ExecutionStateError("state_store_staging_limit_exceeded")
            if total_bytes + len(encoded) > self.max_bytes:
                raise ExecutionStateError("state_store_byte_limit_exceeded")

            revision = result.state.revision
            final_path = self.events_dir / f"revision-{revision:08d}.json"
            if os.path.lexists(final_path):
                raise ExecutionStateError("state_store_revision_exists")
            temp_path = self.events_dir / f"revision-{revision:08d}.{uuid.uuid4().hex}.tmp"
            self._write_staging_file(temp_path, encoded)
            try:
                os.replace(temp_path, final_path)
            except OSError as exc:
                # Keep the complete staged record for deterministic recovery.
                raise ExecutionStateError("state_store_publish_failed") from exc
            return StateStoreCommitReceipt(
                result=result,
                event_sha256=event_sha256,
                event_count=revision,
                recovered_staged_event_before_commit=loaded.recovered_staged_event,
                ignored_staging_files=loaded.ignored_staging_files,
            )

    def _load_locked(
        self,
        *,
        evidence_hashes: Mapping[str, str],
        verify_current_evidence: bool = True,
    ) -> StateStoreLoadReceipt:
        live_evidence = _validate_evidence_manifest(evidence_hashes)
        finals, staging, _ = self._scan_store_files()
        if len(finals) > self.max_events:
            raise ExecutionStateError("state_store_event_limit_exceeded")

        state = self._initial_state
        known_evidence: dict[str, str] = {}
        last_event_sha256 = GENESIS_SHA256
        expected_revision = 1
        for revision in sorted(finals):
            if revision != expected_revision:
                raise ExecutionStateError("state_store_revision_gap")
            event = self._read_event(finals[revision])
            state, last_event_sha256, known_evidence = self._apply_event(
                state,
                event,
                known_evidence=known_evidence,
                previous_event_sha256=last_event_sha256,
                expected_revision=expected_revision,
            )
            expected_revision += 1

        candidates: list[tuple[Path, ExecutionState, str, dict[str, str]]] = []
        ignored: list[str] = []
        for path, revision in staging:
            if revision != expected_revision or revision in finals:
                ignored.append(path.name)
                continue
            try:
                event = self._read_event(path)
                next_state, next_sha, next_evidence = self._apply_event(
                    state,
                    event,
                    known_evidence=known_evidence,
                    previous_event_sha256=last_event_sha256,
                    expected_revision=expected_revision,
                )
            except (ExecutionStateError, OSError, UnicodeDecodeError, json.JSONDecodeError):
                ignored.append(path.name)
                continue
            candidates.append((path, next_state, next_sha, next_evidence))

        if len(candidates) > 1:
            raise ExecutionStateError("state_store_ambiguous_staged_events")
        recovered = False
        if candidates:
            if expected_revision > self.max_events:
                raise ExecutionStateError("state_store_event_limit_exceeded")
            path, state, last_event_sha256, known_evidence = candidates[0]
            final_path = self.events_dir / f"revision-{expected_revision:08d}.json"
            if os.path.lexists(final_path):
                raise ExecutionStateError("state_store_revision_exists")
            try:
                os.replace(path, final_path)
            except OSError as exc:
                raise ExecutionStateError("state_store_recovery_publish_failed") from exc
            expected_revision += 1
            recovered = True

        if verify_current_evidence:
            for field_fact in (state.facts or {}).values():
                for ref in field_fact.evidence:
                    if live_evidence.get(ref.evidence_id) != ref.sha256:
                        raise ExecutionStateError("state_store_evidence_unavailable")

        return StateStoreLoadReceipt(
            state=state,
            event_count=expected_revision - 1,
            last_event_sha256=last_event_sha256,
            recovered_staged_event=recovered,
            ignored_staging_files=tuple(sorted(ignored)),
            current_evidence_verified=verify_current_evidence,
        )

    def _apply_event(
        self,
        current: ExecutionState,
        event: dict[str, Any],
        *,
        known_evidence: Mapping[str, str],
        previous_event_sha256: str,
        expected_revision: int,
    ) -> tuple[ExecutionState, str, dict[str, str]]:
        expected_keys = {
            "schema",
            "session_id",
            "task_spec_sha256",
            "field_schema_sha256",
            "revision",
            "previous_event_sha256",
            "patch",
            "evidence_hashes",
            "state_sha256",
            "event_sha256",
        }
        if type(event) is not dict or set(event) not in (
            expected_keys,
            expected_keys | {"evidence_sources"},
        ):
            raise ExecutionStateError("state_store_event_shape_invalid")
        event_sha256 = event["event_sha256"]
        if not isinstance(event_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", event_sha256):
            raise ExecutionStateError("state_store_event_hash_invalid")
        unhashed = {key: value for key, value in event.items() if key != "event_sha256"}
        if hashlib.sha256(_canonical_json(unhashed)).hexdigest() != event_sha256:
            raise ExecutionStateError("state_store_event_hash_mismatch")
        if event["schema"] != EVENT_SCHEMA:
            raise ExecutionStateError("state_store_event_schema_mismatch")
        if event["session_id"] != self.session_id:
            raise ExecutionStateError("state_store_session_mismatch")
        if event["task_spec_sha256"] != self.task_spec_sha256:
            raise ExecutionStateError("state_store_task_spec_mismatch")
        if event["field_schema_sha256"] != self.field_schema_sha256:
            raise ExecutionStateError("state_store_field_schema_mismatch")
        if (
            not isinstance(event["revision"], int)
            or isinstance(event["revision"], bool)
            or event["revision"] != expected_revision
        ):
            raise ExecutionStateError("state_store_revision_mismatch")
        if event["previous_event_sha256"] != previous_event_sha256:
            raise ExecutionStateError("state_store_event_chain_mismatch")
        if not isinstance(event["state_sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", event["state_sha256"]
        ):
            raise ExecutionStateError("state_store_state_hash_invalid")

        event_evidence = _validate_evidence_manifest(event["evidence_hashes"])
        has_source_map = "evidence_sources" in event
        event_sources: dict[str, EvidenceSource] = {}
        if has_source_map:
            raw_sources = event["evidence_sources"]
            if not isinstance(raw_sources, dict) or len(raw_sources) > 10_000:
                raise ExecutionStateError("state_store_evidence_sources_invalid")
            for evidence_id, raw_source in raw_sources.items():
                if (
                    not isinstance(raw_source, dict)
                    or set(raw_source) != {"source_namespace_sha256", "source_path"}
                    or evidence_id not in event_evidence
                ):
                    raise ExecutionStateError("state_store_evidence_sources_invalid")
                try:
                    source = EvidenceSource(
                        source_namespace_sha256=raw_source["source_namespace_sha256"],
                        source_path=raw_source["source_path"],
                    )
                except (TypeError, ValueError) as exc:
                    raise ExecutionStateError("state_store_evidence_sources_invalid") from exc
                if stable_source_evidence_id(
                    source.source_namespace_sha256,
                    source.source_path,
                    event_evidence[evidence_id],
                ) != evidence_id:
                    raise ExecutionStateError("state_store_evidence_sources_invalid")
                event_sources[evidence_id] = source
        merged_evidence = dict(known_evidence)
        for evidence_id, digest in event_evidence.items():
            old_digest = merged_evidence.get(evidence_id)
            if old_digest is not None and old_digest != digest:
                raise ExecutionStateError("state_store_evidence_hash_changed")
            merged_evidence[evidence_id] = digest
        if len(merged_evidence) > 10_000:
            raise ExecutionStateError("state_store_evidence_limit_exceeded")

        try:
            patch_value = event["patch"]
            patch_changes = patch_value.get("changes") if isinstance(patch_value, dict) else None
            patch_evidence_ids = {
                evidence_id
                for change in (patch_changes if isinstance(patch_changes, list) else ())
                if isinstance(change, dict)
                and change.get("op") == "set"
                and isinstance(change.get("evidence_ids"), list)
                for evidence_id in change["evidence_ids"]
                if isinstance(evidence_id, str)
            }
            result = apply_state_patch(
                current,
                event["patch"],
                field_specs=self.field_specs,
                evidence_hashes=merged_evidence,
                evidence_sources={
                    evidence_id: source
                    for evidence_id, source in event_sources.items()
                    if evidence_id in patch_evidence_ids
                },
            )
        except ExecutionStateError as exc:
            raise ExecutionStateError("state_store_patch_invalid") from exc
        if result.normalized_patch_json != _canonical_json(event["patch"]):
            raise ExecutionStateError("state_store_patch_not_canonical")
        required_evidence_ids = {
            evidence_id
            for change in event["patch"]["changes"]
            for evidence_id in change["evidence_ids"]
        }
        required_evidence_ids.update(_state_evidence_hashes(result.state))
        if set(event_evidence) != required_evidence_ids:
            raise ExecutionStateError("state_store_event_evidence_set_mismatch")
        state_sources = _state_evidence_sources(result.state)
        if (state_sources != event_sources) or (bool(state_sources) != has_source_map):
            raise ExecutionStateError("state_store_event_evidence_sources_mismatch")
        if result.state.sha256 != event["state_sha256"]:
            raise ExecutionStateError("state_store_state_hash_mismatch")
        return result.state, event_sha256, merged_evidence

    def _read_event(self, path: Path) -> dict[str, Any]:
        _reject_reparse_point(path)
        try:
            file_stat = path.lstat()
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size > MAX_EVENT_BYTES:
                raise ExecutionStateError("state_store_event_file_invalid")
            raw = path.read_bytes()
            if len(raw) != file_stat.st_size:
                raise ExecutionStateError("state_store_event_read_incomplete")
            return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        except ExecutionStateError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ExecutionStateError("state_store_event_unreadable") from exc

    def _scan_store_files(self) -> tuple[dict[int, Path], list[tuple[Path, int]], int]:
        self._ensure_tree()
        allowed_root_names = {"state.lock", "events"}
        if any(child.name not in allowed_root_names for child in self.root.iterdir()):
            raise ExecutionStateError("state_store_unexpected_root_entry")
        finals: dict[int, Path] = {}
        staging: list[tuple[Path, int]] = []
        total_bytes = 0
        if os.path.lexists(self.lock_path):
            _reject_reparse_point(self.lock_path)
            lock_stat = self.lock_path.lstat()
            if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_size not in {0, 1}:
                raise ExecutionStateError("state_store_lock_file_invalid")
            total_bytes += lock_stat.st_size
        for child in self.events_dir.iterdir():
            _reject_reparse_point(child)
            child_stat = child.lstat()
            if not stat.S_ISREG(child_stat.st_mode):
                raise ExecutionStateError("state_store_unexpected_event_entry")
            if child_stat.st_size > MAX_EVENT_BYTES:
                raise ExecutionStateError("state_store_event_file_limit_exceeded")
            final_match = _FINAL_NAME_RE.fullmatch(child.name)
            if final_match:
                revision = int(final_match.group(1))
                if revision < 1 or revision in finals:
                    raise ExecutionStateError("state_store_event_filename_invalid")
                finals[revision] = child
            else:
                temp_match = _TEMP_NAME_RE.fullmatch(child.name)
                if not temp_match:
                    raise ExecutionStateError("state_store_event_filename_invalid")
                staging.append((child, int(temp_match.group(1))))
            total_bytes += child_stat.st_size
        if len(staging) > MAX_STAGING_FILES:
            raise ExecutionStateError("state_store_staging_limit_exceeded")
        if total_bytes > self.max_bytes:
            raise ExecutionStateError("state_store_byte_limit_exceeded")
        return finals, staging, total_bytes

    def _ensure_tree(self) -> None:
        _reject_existing_reparse_ancestors(self.root)
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            _reject_reparse_point(self.root)
            if not self.root.is_dir():
                raise ExecutionStateError("state_store_root_not_directory")
            self.events_dir.mkdir(exist_ok=True)
            _reject_reparse_point(self.events_dir)
            if not self.events_dir.is_dir():
                raise ExecutionStateError("state_store_events_not_directory")
        except ExecutionStateError:
            raise
        except OSError as exc:
            raise ExecutionStateError("state_store_directory_unavailable") from exc

    def _write_staging_file(self, path: Path, data: bytes) -> None:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o600)
            with os.fdopen(fd, "wb") as handle:
                written = handle.write(data)
                if written != len(data):
                    raise OSError("short state event write")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ExecutionStateError("state_store_staging_write_failed") from exc

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._ensure_tree()
        if os.path.lexists(self.lock_path):
            _reject_reparse_point(self.lock_path)
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self.lock_path, flags, 0o600)
        except OSError as exc:
            raise ExecutionStateError("state_store_lock_unavailable") from exc
        local_lock = _local_lock_for(self.root)
        try:
            lock_stat = os.fstat(fd)
            if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_size not in {0, 1}:
                raise ExecutionStateError("state_store_lock_file_invalid")
            if lock_stat.st_size == 0:
                os.write(fd, b"\0")
                os.fsync(fd)
            local_lock.acquire()
            try:
                _acquire_process_lock(fd)
                try:
                    yield
                finally:
                    _release_process_lock(fd)
            finally:
                local_lock.release()
        except OSError as exc:
            raise ExecutionStateError("state_store_lock_failed") from exc
        finally:
            os.close(fd)


def _field_schema_sha256(field_specs: Mapping[str, StateFieldSpec]) -> str:
    payload = {
        field: {
            "value_type": spec.value_type,
            "required": spec.required,
            "max_chars": spec.max_chars,
            "max_items": spec.max_items,
        }
        for field, spec in sorted(field_specs.items())
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _state_evidence_hashes(state: ExecutionState) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for fact in (state.facts or {}).values():
        for ref in fact.evidence:
            previous = evidence.get(ref.evidence_id)
            if previous is not None and previous != ref.sha256:
                raise ExecutionStateError("state_evidence_hash_conflict")
            evidence[ref.evidence_id] = ref.sha256
    return evidence


def _state_evidence_sources(state: ExecutionState) -> dict[str, EvidenceSource]:
    sources: dict[str, EvidenceSource] = {}
    for fact in (state.facts or {}).values():
        for ref in fact.evidence:
            if ref.source is None:
                continue
            previous = sources.get(ref.evidence_id)
            if previous is not None and previous != ref.source:
                raise ExecutionStateError("state_evidence_source_conflict")
            sources[ref.evidence_id] = ref.source
    return sources


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_reparse_point(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode):
        raise ExecutionStateError("state_store_reparse_point_rejected")
    attrs = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if attrs & reparse_flag:
        raise ExecutionStateError("state_store_reparse_point_rejected")
    is_junction = getattr(os.path, "isjunction", None)
    if callable(is_junction) and is_junction(path):
        raise ExecutionStateError("state_store_reparse_point_rejected")


def _reject_existing_reparse_ancestors(path: Path) -> None:
    anchor = Path(path.anchor)
    current = anchor
    for part in path.parts[1:]:
        current = current / part
        if os.path.lexists(current):
            _reject_reparse_point(current)


def _local_lock_for(path: Path) -> threading.RLock:
    key = os.path.normcase(str(path))
    with _LOCKS_GUARD:
        lock = _LOCAL_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCAL_LOCKS[key] = lock
        return lock


def _acquire_process_lock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_EX)


def _release_process_lock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)
