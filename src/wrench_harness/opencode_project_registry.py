"""Explicit, bounded Wrench-owned OpenCode project enrollment.

The registry is independent of repository configuration and hook payloads.
Only callers of :meth:`OpenCodeProjectRegistry.enroll_project` can add a
project. Resolution checks a returned OpenCode session against one enrolled
root and re-captures its filesystem identity before returning source policy.
This module does not prepare context, authorize dispatch, or prove tokenizer
parity.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .e0_context_pipeline import (
    MAX_AGGREGATE_SOURCE_BYTES,
    MAX_PATHS,
    MAX_SOURCE_BYTES,
)
from .opencode_session_root import (
    OpenCodeSessionRoot,
    OpenCodeSessionRootError,
    resolve_opencode_session_root,
)
from .snapshot import (
    MAX_SOURCE_PATH_CHARS,
    SnapshotAdmissionError,
    SourceRootBinding,
    _normalize_relative_path,
    _root_location_sha256,
    bind_source_root,
)


SCHEMA = "wrench.opencode-project-registry.v1"
POLICY_ID = "explicit-paths-v1"
MAX_PROJECTS = 32
MAX_REGISTRY_BYTES = 256 * 1024
MAX_PROJECT_ID_CHARS = 64
_PROJECT_ID_RE = re.compile(r"^prj_[a-z0-9][a-z0-9_-]{0,59}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ROOT_IDENTITY_RE = re.compile(
    r"^(?:posix:(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)|win:[0-9a-f]{16}:[0-9a-f]{32})$"
)
_DATA_DIRECTORY = "opencode"
_REGISTRY_FILENAME = "projects.json"
_STORE_DIRECTORY = "artifacts/opencode-projects"


class ProjectRegistryError(ValueError):
    """The explicit project registry or requested binding is invalid."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ExactTokenGateStatus(str, Enum):
    """Exact gate eligibility represented by this enrollment contract."""

    UNAVAILABLE = "exact_gate_unavailable"


@dataclass(frozen=True)
class EnrolledProject:
    """One enrolled root and its finite, bounded source policy."""

    project_id: str
    session_id: str = field(repr=False)
    binding: SourceRootBinding = field(repr=False)
    source_paths: tuple[str, ...] = field(repr=False)
    exclusions: tuple[str, ...] = field(repr=False)
    policy_id: str
    max_file_bytes: int
    max_total_bytes: int
    store_path: Path = field(repr=False)
    exact_token_gate: ExactTokenGateStatus = ExactTokenGateStatus.UNAVAILABLE


@dataclass(frozen=True)
class _Profile:
    project_id: str
    configured_root: str
    root_location_sha256: str
    root_identity: str
    source_paths: tuple[str, ...]
    exclusions: tuple[str, ...]
    policy_id: str
    max_file_bytes: int
    max_total_bytes: int


_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[str, threading.RLock] = {}


def _path_key(value: str | os.PathLike[str]) -> str:
    path = os.path.normpath(os.fspath(value))
    return os.path.normcase(path) if os.name == "nt" else path


def _within(path: str, prefix: str) -> bool:
    path_key = path.casefold() if os.name == "nt" else path
    prefix_key = prefix.casefold() if os.name == "nt" else prefix
    if prefix_key == ".":
        return True
    return path_key == prefix_key or path_key.startswith(prefix_key + "/")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectRegistryError("duplicate_json_field")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ProjectRegistryError("invalid_json_constant")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _profile_payload(profile: _Profile) -> dict[str, object]:
    return {
        "project_id": profile.project_id,
        "configured_root": profile.configured_root,
        "root_location_sha256": profile.root_location_sha256,
        "root_identity": profile.root_identity,
        "source_paths": list(profile.source_paths),
        "exclusions": list(profile.exclusions),
        "policy_id": profile.policy_id,
        "max_file_bytes": profile.max_file_bytes,
        "max_total_bytes": profile.max_total_bytes,
    }


def _validate_project_id(value: object) -> str:
    if (
        type(value) is not str
        or len(value) > MAX_PROJECT_ID_CHARS
        or _PROJECT_ID_RE.fullmatch(value) is None
    ):
        raise ProjectRegistryError("invalid_project_id")
    return value


def _normalize_path_list(value: object, *, field: str, allow_empty: bool) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ProjectRegistryError(f"{field}_invalid")
    if (not allow_empty and not 1 <= len(value) <= MAX_PATHS) or (
        allow_empty and len(value) > MAX_PATHS
    ):
        raise ProjectRegistryError(f"{field}_limit_exceeded")
    normalized: list[str] = []
    try:
        for path in value:
            if type(path) is not str:
                raise ProjectRegistryError(f"{field}_invalid")
            normalized.append(_normalize_relative_path(path))
    except (SnapshotAdmissionError, TypeError, OSError, ValueError) as exc:
        if isinstance(exc, ProjectRegistryError):
            raise
        raise ProjectRegistryError(f"{field}_invalid") from exc
    duplicate_keys = [path.casefold() if os.name == "nt" else path for path in normalized]
    if len(set(duplicate_keys)) != len(normalized):
        raise ProjectRegistryError(f"{field}_duplicate")
    return tuple(sorted(normalized, key=lambda item: item.casefold() if os.name == "nt" else item))


def _new_profile(
    project_id: object,
    binding: SourceRootBinding,
    source_paths: object,
    *,
    policy_id: object,
    exclusions: object,
    max_file_bytes: object,
    max_total_bytes: object,
) -> _Profile:
    project_id = _validate_project_id(project_id)
    if type(binding) is not SourceRootBinding:
        raise ProjectRegistryError("root_binding_invalid")
    paths = _normalize_path_list(source_paths, field="source_paths", allow_empty=False)
    excluded = _normalize_path_list(exclusions, field="exclusions", allow_empty=True)
    if type(policy_id) is not str or policy_id != POLICY_ID:
        raise ProjectRegistryError("policy_id_unsupported")
    if (
        type(max_file_bytes) is not int
        or not 1 <= max_file_bytes <= MAX_SOURCE_BYTES
        or type(max_total_bytes) is not int
        or not 1 <= max_total_bytes <= MAX_AGGREGATE_SOURCE_BYTES
        or max_file_bytes > max_total_bytes
    ):
        raise ProjectRegistryError("byte_cap_invalid")
    if any(_within(path, excluded_path) for path in paths for excluded_path in excluded):
        raise ProjectRegistryError("source_path_excluded")
    if len(os.fspath(binding.configured_root)) > 32_767:
        raise ProjectRegistryError("configured_root_too_long")
    if (
        not _SHA256_RE.fullmatch(binding.root_location_sha256)
        or not _ROOT_IDENTITY_RE.fullmatch(binding.root_identity)
    ):
        raise ProjectRegistryError("root_binding_invalid")
    return _Profile(
        project_id=project_id,
        configured_root=os.fspath(binding.configured_root),
        root_location_sha256=binding.root_location_sha256,
        root_identity=binding.root_identity,
        source_paths=paths,
        exclusions=excluded,
        policy_id=policy_id,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )


def _parse_profile(value: object) -> _Profile:
    expected = {
        "project_id", "configured_root", "root_location_sha256", "root_identity",
        "source_paths", "exclusions", "policy_id", "max_file_bytes", "max_total_bytes",
    }
    if type(value) is not dict or set(value) != expected:
        raise ProjectRegistryError("profile_fields_invalid")
    project_id = _validate_project_id(value["project_id"])
    configured_root = value["configured_root"]
    if (
        type(configured_root) is not str
        or not configured_root
        or len(configured_root) > 32_767
        or not Path(configured_root).is_absolute()
        or "\x00" in configured_root
    ):
        raise ProjectRegistryError("configured_root_invalid")
    location_hash = value["root_location_sha256"]
    root_identity = value["root_identity"]
    if type(location_hash) is not str or _SHA256_RE.fullmatch(location_hash) is None:
        raise ProjectRegistryError("root_location_hash_invalid")
    if type(root_identity) is not str or _ROOT_IDENTITY_RE.fullmatch(root_identity) is None:
        raise ProjectRegistryError("root_identity_invalid")
    try:
        normalized_root = Path(configured_root).absolute()
        if _root_location_sha256(normalized_root) != location_hash:
            raise ProjectRegistryError("root_location_hash_mismatch")
    except ProjectRegistryError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise ProjectRegistryError("configured_root_invalid") from exc
    binding = SourceRootBinding(normalized_root, location_hash, root_identity)
    return _new_profile(
        project_id,
        binding,
        value["source_paths"],
        policy_id=value["policy_id"],
        exclusions=value["exclusions"],
        max_file_bytes=value["max_file_bytes"],
        max_total_bytes=value["max_total_bytes"],
    )


class OpenCodeProjectRegistry:
    """Strict on-disk registry below an explicitly configured Wrench data root.

    Registry writes are atomic and synchronized across instances in this
    process. The owning Wrench service must serialize access across processes.
    This registry never imports or reads repository-local configuration.
    """

    def __init__(self, data_root: str | os.PathLike[str]) -> None:
        try:
            self.data_root = Path(data_root).absolute()
            self._data_binding = bind_source_root(self.data_root)
        except (SnapshotAdmissionError, OSError, TypeError, ValueError) as exc:
            raise ProjectRegistryError("data_root_unusable") from exc
        self.registry_path = self.data_root / _DATA_DIRECTORY / _REGISTRY_FILENAME
        self._assert_under_data_root(self.registry_path)
        key = _path_key(self.data_root)
        with _LOCKS_GUARD:
            self._lock = _LOCKS.setdefault(key, threading.RLock())

    def enroll_project(
        self,
        project_id: str,
        source_root: str | os.PathLike[str],
        source_paths: Iterable[str],
        *,
        policy_id: str = POLICY_ID,
        exclusions: Iterable[str] = (),
        max_file_bytes: int = MAX_SOURCE_BYTES,
        max_total_bytes: int = MAX_AGGREGATE_SOURCE_BYTES,
    ) -> EnrolledProject:
        """Explicitly enroll one local root and finite source path set.

        Call this only from a Wrench enrollment action. Repository files,
        OpenCode hook payloads, and implicit cwd discovery are not enrollment
        authorities.
        """
        self._assert_data_root()
        try:
            binding = bind_source_root(source_root)
        except (SnapshotAdmissionError, OSError, TypeError, ValueError) as exc:
            raise ProjectRegistryError("source_root_unusable") from exc
        profile = _new_profile(
            project_id,
            binding,
            tuple(source_paths) if not isinstance(source_paths, (str, bytes)) else source_paths,
            policy_id=policy_id,
            exclusions=tuple(exclusions) if not isinstance(exclusions, (str, bytes)) else exclusions,
            max_file_bytes=max_file_bytes,
            max_total_bytes=max_total_bytes,
        )
        with self._lock:
            profiles = self._read_profiles()
            if len(profiles) >= MAX_PROJECTS:
                raise ProjectRegistryError("project_limit_exceeded")
            if any(item.project_id == profile.project_id for item in profiles):
                raise ProjectRegistryError("project_id_already_enrolled")
            if any(_path_key(item.configured_root) == _path_key(profile.configured_root) for item in profiles):
                raise ProjectRegistryError("root_already_enrolled")
            self._write_profiles((*profiles, profile))
        return self._as_enrolled(profile, "", binding)

    def list_projects(self) -> tuple[EnrolledProject, ...]:
        """Return enrolled metadata without reading source files."""
        self._assert_data_root()
        with self._lock:
            profiles = self._read_profiles()
        return tuple(self._as_enrolled(item, "", self._binding_from_profile(item)) for item in profiles)

    def resolve_session(self, event_session_id: str, session_record: Any) -> EnrolledProject:
        """Resolve one enrolled project for a matching current session/root."""
        self._assert_data_root()
        try:
            session_root = resolve_opencode_session_root(event_session_id, session_record)
        except OpenCodeSessionRootError as exc:
            raise ProjectRegistryError(exc.code) from exc
        with self._lock:
            profiles = self._read_profiles()
        root_key = _path_key(session_root.binding.configured_root)
        path_matches = [item for item in profiles if _path_key(item.configured_root) == root_key]
        if len(path_matches) != 1:
            raise ProjectRegistryError("enrolled_root_match_not_unique")
        profile = path_matches[0]
        if (
            session_root.binding.root_location_sha256 != profile.root_location_sha256
            or session_root.binding.root_identity != profile.root_identity
        ):
            raise ProjectRegistryError("enrolled_root_replaced")
        return self._as_enrolled(profile, session_root.session_id, session_root.binding)

    def _as_enrolled(
        self,
        profile: _Profile,
        session_id: str,
        binding: SourceRootBinding,
    ) -> EnrolledProject:
        store_path = self.data_root / _STORE_DIRECTORY / profile.project_id
        self._check_data_path(store_path, allow_missing_tail=True, final_kind="directory")
        return EnrolledProject(
            project_id=profile.project_id,
            session_id=session_id,
            binding=binding,
            source_paths=profile.source_paths,
            exclusions=profile.exclusions,
            policy_id=profile.policy_id,
            max_file_bytes=profile.max_file_bytes,
            max_total_bytes=profile.max_total_bytes,
            store_path=store_path,
        )

    def _binding_from_profile(self, profile: _Profile) -> SourceRootBinding:
        try:
            binding = bind_source_root(profile.configured_root)
        except (SnapshotAdmissionError, OSError, TypeError, ValueError) as exc:
            raise ProjectRegistryError("enrolled_root_unusable") from exc
        if (
            binding.root_location_sha256 != profile.root_location_sha256
            or binding.root_identity != profile.root_identity
        ):
            raise ProjectRegistryError("enrolled_root_replaced")
        return binding

    def _assert_under_data_root(self, path: Path) -> None:
        try:
            if not path.absolute().is_relative_to(self.data_root):
                raise ProjectRegistryError("registry_path_outside_data_root")
        except (OSError, ValueError) as exc:
            raise ProjectRegistryError("registry_path_invalid") from exc

    def _assert_data_root(self) -> None:
        try:
            current = bind_source_root(self.data_root)
        except (SnapshotAdmissionError, OSError, TypeError, ValueError) as exc:
            raise ProjectRegistryError("data_root_unusable") from exc
        if (
            current.root_location_sha256 != self._data_binding.root_location_sha256
            or current.root_identity != self._data_binding.root_identity
        ):
            raise ProjectRegistryError("data_root_replaced")

    def _check_data_path(
        self,
        path: Path,
        *,
        allow_missing_tail: bool,
        final_kind: str,
    ) -> bool:
        """Check existing descendants without following links or reparse points.

        Rechecking around path operations narrows races. Path-based lstat/open/
        replace is not a filesystem transaction and cannot eliminate them.
        """
        if final_kind not in ("file", "directory"):
            raise ProjectRegistryError("registry_path_invalid")
        self._assert_under_data_root(path)
        self._assert_data_root()
        root = self.data_root
        _reject_reparse_or_wrong_type(root, want_directory=True)
        try:
            relative = path.absolute().relative_to(root)
        except (OSError, ValueError) as exc:
            raise ProjectRegistryError("registry_path_outside_data_root") from exc
        parts = relative.parts
        if not parts:
            if final_kind != "directory":
                raise ProjectRegistryError("registry_path_wrong_type")
            return True
        current = root
        for index, component in enumerate(parts):
            current = current / component
            is_final = index == len(parts) - 1
            try:
                info = current.lstat()
            except FileNotFoundError:
                if allow_missing_tail:
                    return False
                raise ProjectRegistryError("registry_path_unavailable")
            except OSError as exc:
                raise ProjectRegistryError("registry_path_unavailable") from exc
            expected_directory = not is_final or final_kind == "directory"
            if (
                stat.S_ISLNK(info.st_mode)
                or bool(getattr(info, "st_file_attributes", 0) & 0x400)
                or (expected_directory and not stat.S_ISDIR(info.st_mode))
                or (is_final and final_kind == "file" and not stat.S_ISREG(info.st_mode))
            ):
                raise ProjectRegistryError("registry_path_unsafe")
        self._assert_data_root()
        return True

    def _ensure_registry_directory(self) -> None:
        directory = self.data_root / _DATA_DIRECTORY
        if self._check_data_path(
            directory, allow_missing_tail=True, final_kind="directory"
        ):
            return
        try:
            directory.mkdir(exist_ok=True)
        except OSError as exc:
            raise ProjectRegistryError("registry_directory_unavailable") from exc
        self._check_data_path(directory, allow_missing_tail=False, final_kind="directory")

    def _read_profiles(self) -> tuple[_Profile, ...]:
        path = self.registry_path
        if not self._check_data_path(path, allow_missing_tail=True, final_kind="file"):
            return ()
        try:
            info = path.lstat()
            if info.st_size > MAX_REGISTRY_BYTES:
                raise ProjectRegistryError("registry_size_limit_exceeded")
            with path.open("rb") as stream:
                opened_info = os.fstat(stream.fileno())
                if _stat_signature(info) != _stat_signature(opened_info):
                    raise ProjectRegistryError("registry_changed_during_read")
                raw = stream.read(MAX_REGISTRY_BYTES + 1)
                after_read = os.fstat(stream.fileno())
            if len(raw) > MAX_REGISTRY_BYTES:
                raise ProjectRegistryError("registry_size_limit_exceeded")
            self._check_data_path(path, allow_missing_tail=False, final_kind="file")
            after_path = path.lstat()
            if (
                _stat_signature(info) != _stat_signature(after_read)
                or _stat_signature(info) != _stat_signature(after_path)
            ):
                raise ProjectRegistryError("registry_changed_during_read")
            document = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_unique_pairs,
                parse_constant=_reject_constant,
            )
        except ProjectRegistryError:
            raise
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ProjectRegistryError("registry_invalid") from exc
        if type(document) is not dict or set(document) != {"schema", "projects"}:
            raise ProjectRegistryError("registry_fields_invalid")
        if document["schema"] != SCHEMA:
            raise ProjectRegistryError("registry_schema_unsupported")
        rows = document["projects"]
        if type(rows) is not list or len(rows) > MAX_PROJECTS:
            raise ProjectRegistryError("project_limit_exceeded")
        profiles = tuple(_parse_profile(row) for row in rows)
        ids = [profile.project_id for profile in profiles]
        roots = [_path_key(profile.configured_root) for profile in profiles]
        if len(set(ids)) != len(ids):
            raise ProjectRegistryError("duplicate_project_id")
        if len(set(roots)) != len(roots):
            raise ProjectRegistryError("duplicate_enrolled_root")
        if rows != [_profile_payload(item) for item in profiles]:
            raise ProjectRegistryError("registry_not_canonical")
        return profiles

    def _write_profiles(self, profiles: Iterable[_Profile]) -> None:
        ordered = tuple(sorted(profiles, key=lambda item: item.project_id))
        payload = _canonical_json({
            "schema": SCHEMA,
            "projects": [_profile_payload(profile) for profile in ordered],
        })
        if len(payload) > MAX_REGISTRY_BYTES:
            raise ProjectRegistryError("registry_size_limit_exceeded")
        self._ensure_registry_directory()
        parent = self.registry_path.parent
        self._check_data_path(parent, allow_missing_tail=False, final_kind="directory")
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".projects-", suffix=".tmp", dir=parent,
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self._check_data_path(temporary_path, allow_missing_tail=False, final_kind="file")
            self._check_data_path(
                self.registry_path, allow_missing_tail=True, final_kind="file"
            )
            os.replace(temporary_path, self.registry_path)
            temporary_path = None
            self._check_data_path(
                self.registry_path, allow_missing_tail=False, final_kind="file"
            )
        except ProjectRegistryError:
            raise
        except OSError as exc:
            raise ProjectRegistryError("registry_write_failed") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass


def _reject_reparse_or_wrong_type(path: Path, *, want_directory: bool) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ProjectRegistryError("registry_path_unavailable") from exc
    if (
        stat.S_ISLNK(info.st_mode)
        or bool(getattr(info, "st_file_attributes", 0) & 0x400)
        or (want_directory and not stat.S_ISDIR(info.st_mode))
        or (not want_directory and not stat.S_ISREG(info.st_mode))
    ):
        raise ProjectRegistryError("registry_path_unsafe")


def _stat_signature(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        getattr(info, "st_mtime_ns", int(info.st_mtime * 1_000_000_000)),
        getattr(info, "st_ctime_ns", int(info.st_ctime * 1_000_000_000)),
        getattr(info, "st_file_attributes", 0),
    )


__all__ = [
    "ExactTokenGateStatus",
    "EnrolledProject",
    "MAX_PROJECTS",
    "MAX_REGISTRY_BYTES",
    "OpenCodeProjectRegistry",
    "POLICY_ID",
    "ProjectRegistryError",
    "SCHEMA",
]
