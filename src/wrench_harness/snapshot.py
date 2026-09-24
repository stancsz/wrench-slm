"""Bounded, caller-selected source snapshots with verified exact reads.

This module keeps only a small in-memory manifest. It never walks directories
or retains source bytes after a call completes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


MAX_SNAPSHOT_FILES = 256
MAX_SOURCE_BYTES = 256 * 1024
MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024
MAX_SOURCE_PATH_CHARS = 1_024
_SCHEMA = "wrench.source-snapshot.v1"
_REPARSE_POINT = 0x400
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SnapshotAdmissionError(ValueError):
    """The caller-selected source set cannot be admitted safely."""


class RetrievalStatus(str, Enum):
    OK = "ok"
    UNKNOWN_SNAPSHOT = "unknown_snapshot"
    UNKNOWN_SOURCE = "unknown_source"
    MISSING = "missing"
    CHANGED = "changed"
    UNSAFE = "unsafe"


@dataclass(frozen=True)
class SourceRecord:
    path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class SourceSnapshot:
    schema: str
    sources: tuple[SourceRecord, ...]
    snapshot_sha256: str


@dataclass(frozen=True)
class RetrievalResult:
    status: RetrievalStatus
    path: str | None = None
    data: bytes | None = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _has_reparse_attribute(stat_result: os.stat_result) -> bool:
    return bool(getattr(stat_result, "st_file_attributes", 0) & _REPARSE_POINT)


def _path_duplicate_key(path: str) -> str:
    return path.casefold() if os.name == "nt" else path


def _normalize_relative_path(value: str | os.PathLike[str]) -> str:
    raw = os.fspath(value)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise SnapshotAdmissionError("invalid_relative_path")
    if len(raw) > MAX_SOURCE_PATH_CHARS:
        raise SnapshotAdmissionError("source_path_length_limit_exceeded")
    raw = raw.replace("\\", "/")
    if raw.startswith("/") or (len(raw) >= 2 and raw[1] == ":"):
        raise SnapshotAdmissionError("absolute_path_forbidden")
    parts = raw.split("/")
    if any(part == ".." for part in parts):
        raise SnapshotAdmissionError("parent_path_forbidden")
    if any(":" in part for part in parts):
        raise SnapshotAdmissionError("alternate_data_stream_forbidden")
    if any(part not in ("", ".") and part.endswith((".", " ")) for part in parts):
        raise SnapshotAdmissionError("ambiguous_windows_component")
    normalized = "/".join(part for part in parts if part not in ("", "."))
    if not normalized:
        raise SnapshotAdmissionError("empty_relative_path")
    return normalized


def _safe_file(root: Path, relative_path: str) -> Path:
    """Resolve one path while rejecting links and reparse points."""
    current = root
    for component in relative_path.split("/"):
        current = current / component
        try:
            component_stat = current.lstat()
            mode = component_stat.st_mode
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise SnapshotAdmissionError("unsafe_source_path") from exc
        if stat.S_ISLNK(mode) or _has_reparse_attribute(component_stat):
            raise SnapshotAdmissionError("reparse_point_forbidden")
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root)
        current_stat = current.stat()
        mode = current_stat.st_mode
    except FileNotFoundError:
        raise
    except (OSError, ValueError) as exc:
        raise SnapshotAdmissionError("path_escape_or_resolution_failure") from exc
    if _has_reparse_attribute(current_stat):
        raise SnapshotAdmissionError("reparse_point_forbidden")
    if not stat.S_ISREG(mode):
        raise SnapshotAdmissionError("non_regular_source")
    return current


def _canonical_snapshot_payload(sources: tuple[SourceRecord, ...]) -> bytes:
    rows = [
        {"path": item.path, "size_bytes": item.size_bytes, "sha256": item.sha256}
        for item in sources
    ]
    return json.dumps(
        {"schema": _SCHEMA, "sources": rows},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_snapshot(snapshot: object) -> bool:
    """Validate untrusted public manifest fields before canonical serialization."""
    if not isinstance(snapshot, SourceSnapshot) or snapshot.schema != _SCHEMA:
        return False
    if not isinstance(snapshot.snapshot_sha256, str) or not _SHA256_RE.fullmatch(snapshot.snapshot_sha256):
        return False
    sources = snapshot.sources
    if not isinstance(sources, tuple) or not 1 <= len(sources) <= MAX_SNAPSHOT_FILES:
        return False
    paths: list[str] = []
    total = 0
    for item in sources:
        if not isinstance(item, SourceRecord) or not isinstance(item.path, str):
            return False
        try:
            canonical_path = _normalize_relative_path(item.path)
        except (SnapshotAdmissionError, TypeError, ValueError, OSError):
            return False
        if canonical_path != item.path:
            return False
        if (
            not isinstance(item.size_bytes, int)
            or isinstance(item.size_bytes, bool)
            or not 0 <= item.size_bytes <= MAX_SOURCE_BYTES
        ):
            return False
        if not isinstance(item.sha256, str) or not _SHA256_RE.fullmatch(item.sha256):
            return False
        paths.append(item.path)
        total += item.size_bytes
        if total > MAX_SNAPSHOT_BYTES:
            return False
    duplicate_keys = [_path_duplicate_key(path) for path in paths]
    if len(set(duplicate_keys)) != len(paths) or paths != sorted(paths):
        return False
    try:
        return _sha256(_canonical_snapshot_payload(sources)) == snapshot.snapshot_sha256
    except (TypeError, ValueError, OverflowError):
        return False


def _metadata(stat_result: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_size,
        getattr(stat_result, "st_mtime_ns", int(stat_result.st_mtime * 1_000_000_000)),
        getattr(stat_result, "st_ctime_ns", int(stat_result.st_ctime * 1_000_000_000)),
        getattr(stat_result, "st_file_attributes", 0),
    )


def _open_posix_relative(name: str, flags: int, parent_fd: int) -> int:
    return os.open(name, flags, dir_fd=parent_fd)


def _open_posix_directory_chain(path: Path, flags: int) -> tuple[list[int], list[tuple[str, int, int]]]:
    """Open an absolute directory path from `/`, refusing symlink components."""
    if not path.is_absolute() or path.anchor != "/":
        raise SnapshotAdmissionError("invalid_posix_root")
    opened: list[int] = []
    bindings: list[tuple[str, int, int]] = []
    try:
        anchor_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0))
        opened.append(anchor_fd)
        for component in path.parts[1:]:
            parent_fd = opened[-1]
            try:
                named = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            except (TypeError, NotImplementedError) as exc:
                raise SnapshotAdmissionError("secure_dirfd_unavailable") from exc
            if stat.S_ISLNK(named.st_mode) or _has_reparse_attribute(named):
                raise SnapshotAdmissionError("reparse_point_forbidden")
            if not stat.S_ISDIR(named.st_mode):
                raise SnapshotAdmissionError("root_must_be_real_directory")
            child_fd = _open_posix_relative(component, flags, parent_fd)
            opened.append(child_fd)
            bindings.append((component, len(opened) - 2, len(opened) - 1))
            child_info = os.fstat(child_fd)
            if _has_reparse_attribute(child_info) or not stat.S_ISDIR(child_info.st_mode):
                raise SnapshotAdmissionError("root_must_be_real_directory")
        return opened, bindings
    except BaseException:
        for descriptor in reversed(opened):
            os.close(descriptor)
        raise


def _read_stable_source(root: Path, relative_path: str) -> tuple[bytes, os.stat_result]:
    if os.name == "nt":
        # Early classification only. The actual read and containment are done
        # again through the pinned native-handle walk below.
        _safe_file(root, relative_path)
        return _windows_read_stable_source(root, relative_path)
    return _posix_read_stable_source(root, relative_path)


def _posix_read_stable_source(root: Path, relative_path: str) -> tuple[bytes, os.stat_result]:
    """Bounded read using only pinned, parent-relative POSIX directory handles."""
    required_flags = ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")
    if (
        os.open not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
        or os.stat not in os.supports_follow_symlinks
    ):
        raise SnapshotAdmissionError("secure_dirfd_unavailable")
    if any(not hasattr(os, flag) for flag in required_flags):
        raise SnapshotAdmissionError("secure_open_flags_unavailable")
    cloexec = getattr(os, "O_CLOEXEC", 0)
    nofollow = os.O_NOFOLLOW
    directory_flag = os.O_DIRECTORY
    nonblock = os.O_NONBLOCK
    opened_directories: list[int] = []
    directory_bindings: list[tuple[str, int, int]] = []
    final_fd: int | None = None

    def checked_stat(name: str, parent_fd: int) -> os.stat_result:
        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except (TypeError, NotImplementedError) as exc:
            raise SnapshotAdmissionError("secure_dirfd_unavailable") from exc
        if stat.S_ISLNK(info.st_mode) or _has_reparse_attribute(info):
            raise SnapshotAdmissionError("reparse_point_forbidden")
        return info

    def verify_binding(name: str, parent_fd: int, handle_fd: int) -> None:
        named = checked_stat(name, parent_fd)
        opened = os.fstat(handle_fd)
        if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
            raise SnapshotAdmissionError("source_changed_during_read")

    try:
        try:
            root_chain, root_bindings = _open_posix_directory_chain(
                root, os.O_RDONLY | directory_flag | nofollow | cloexec
            )
        except (TypeError, NotImplementedError) as exc:
            raise SnapshotAdmissionError("secure_dirfd_unavailable") from exc
        opened_directories.extend(root_chain)
        directory_bindings.extend(root_bindings)
        root_fd = opened_directories[-1]
        root_info = os.fstat(root_fd)
        if _has_reparse_attribute(root_info) or not stat.S_ISDIR(root_info.st_mode):
            raise SnapshotAdmissionError("root_must_be_real_directory")

        components = relative_path.split("/")
        for component in components[:-1]:
            parent_fd = opened_directories[-1]
            component_info = checked_stat(component, parent_fd)
            if not stat.S_ISDIR(component_info.st_mode):
                raise SnapshotAdmissionError("non_directory_source_component")
            try:
                child_fd = _open_posix_relative(
                    component,
                    os.O_RDONLY | directory_flag | nofollow | cloexec,
                    parent_fd,
                )
            except (TypeError, NotImplementedError) as exc:
                raise SnapshotAdmissionError("secure_dirfd_unavailable") from exc
            opened_directories.append(child_fd)
            child_info = os.fstat(child_fd)
            if _has_reparse_attribute(child_info) or not stat.S_ISDIR(child_info.st_mode):
                raise SnapshotAdmissionError("reparse_point_forbidden")
            directory_bindings.append((component, len(opened_directories) - 2, len(opened_directories) - 1))

        parent_fd = opened_directories[-1]
        file_name = components[-1]
        named_before = checked_stat(file_name, parent_fd)
        if not stat.S_ISREG(named_before.st_mode):
            raise SnapshotAdmissionError("non_regular_source")
        try:
            final_fd = _open_posix_relative(
                file_name,
                os.O_RDONLY | nofollow | nonblock | cloexec,
                parent_fd,
            )
        except (TypeError, NotImplementedError) as exc:
            raise SnapshotAdmissionError("secure_dirfd_unavailable") from exc
        before = os.fstat(final_fd)
        if _has_reparse_attribute(before):
            raise SnapshotAdmissionError("reparse_point_forbidden")
        if not stat.S_ISREG(before.st_mode):
            raise SnapshotAdmissionError("non_regular_source")
        if before.st_size > MAX_SOURCE_BYTES:
            raise SnapshotAdmissionError("source_size_limit_exceeded")

        chunks: list[bytes] = []
        total = 0
        while total <= MAX_SOURCE_BYTES:
            chunk = os.read(final_fd, min(64 * 1024, MAX_SOURCE_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        data = b"".join(chunks)
        after = os.fstat(final_fd)
        if _metadata(before) != _metadata(after) or len(data) > MAX_SOURCE_BYTES or len(data) != after.st_size:
            raise SnapshotAdmissionError("source_changed_during_read")
        verify_binding(file_name, parent_fd, final_fd)
        for component, parent_index, handle_index in reversed(directory_bindings):
            verify_binding(component, opened_directories[parent_index], opened_directories[handle_index])
        return data, after
    finally:
        if final_fd is not None:
            os.close(final_fd)
        for directory_fd in reversed(opened_directories):
            os.close(directory_fd)


def _windows_read_stable_source(root: Path, relative_path: str) -> tuple[bytes, os.stat_result]:
    """Read through a Win32 root handle and NtCreateFile parent-relative walk.

    Each directory handle denies write/delete sharing and remains open until the
    file read finishes. Child opens use that directory handle as RootDirectory,
    so names are never re-resolved from the original textual root path.
    """
    import ctypes
    import msvcrt

    from ctypes import wintypes

    GENERIC_READ = 0x80000000
    FILE_READ_ATTRIBUTES = 0x0080
    SYNCHRONIZE = 0x00100000
    FILE_SHARE_READ = 0x00000001
    OPEN_EXISTING = 3
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_REPARSE_POINT = _REPARSE_POINT
    FILE_OPEN = 1
    FILE_DIRECTORY_FILE = 0x00000001
    FILE_NON_DIRECTORY_FILE = 0x00000040
    FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    FILE_OPEN_REPARSE_POINT = 0x00200000
    FileAttributeTagInfo = 9

    class UNICODE_STRING(ctypes.Structure):
        _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT), ("Buffer", wintypes.LPWSTR)]

    class OBJECT_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UNICODE_STRING)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class IO_STATUS_BLOCK(ctypes.Structure):
        _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t)]

    class FILE_ATTRIBUTE_TAG_INFO(ctypes.Structure):
        _fields_ = [("FileAttributes", wintypes.DWORD), ("ReparseTag", wintypes.DWORD)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    get_info = kernel32.GetFileInformationByHandleEx
    get_info.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    get_info.restype = wintypes.BOOL
    nt_create_file = ntdll.NtCreateFile
    nt_create_file.argtypes = [
        ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, ctypes.POINTER(OBJECT_ATTRIBUTES),
        ctypes.POINTER(IO_STATUS_BLOCK), ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG,
        wintypes.ULONG, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG,
    ]
    nt_create_file.restype = ctypes.c_long
    ntstatus_to_error = ntdll.RtlNtStatusToDosError
    ntstatus_to_error.argtypes = [ctypes.c_long]
    ntstatus_to_error.restype = wintypes.ULONG

    invalid_handle = ctypes.c_void_p(-1).value
    root_handle = create_file(
        str(root), FILE_READ_ATTRIBUTES | SYNCHRONIZE, FILE_SHARE_READ, None,
        OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None,
    )
    if root_handle == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    directory_handles: list[int] = [root_handle]
    file_object = None

    def attributes(handle: int) -> int:
        info = FILE_ATTRIBUTE_TAG_INFO()
        if not get_info(handle, FileAttributeTagInfo, ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT:
            raise SnapshotAdmissionError("reparse_point_forbidden")
        return info.FileAttributes

    def open_relative(parent: int, component: str, *, directory: bool) -> int:
        name_buffer = ctypes.create_unicode_buffer(component)
        name = UNICODE_STRING(
            len(component.encode("utf-16-le")),
            len(component.encode("utf-16-le")) + ctypes.sizeof(wintypes.WCHAR),
            ctypes.cast(name_buffer, wintypes.LPWSTR),
        )
        object_attributes = OBJECT_ATTRIBUTES(
            ctypes.sizeof(OBJECT_ATTRIBUTES), parent, ctypes.pointer(name), 0x40, None, None
        )
        io_status = IO_STATUS_BLOCK()
        handle = wintypes.HANDLE()
        options = FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT
        desired = FILE_READ_ATTRIBUTES | SYNCHRONIZE
        if directory:
            options |= FILE_DIRECTORY_FILE
        else:
            options |= FILE_NON_DIRECTORY_FILE
            desired |= GENERIC_READ
        status = nt_create_file(
            ctypes.byref(handle), desired, ctypes.byref(object_attributes), ctypes.byref(io_status),
            None, 0, FILE_SHARE_READ, FILE_OPEN, options, None, 0,
        )
        if status < 0:
            raise ctypes.WinError(ntstatus_to_error(status))
        value = handle.value
        try:
            attributes(value)
            return value
        except BaseException:
            close_handle(value)
            raise

    try:
        root_attributes = attributes(root_handle)
        if not (root_attributes & FILE_ATTRIBUTE_DIRECTORY):
            raise SnapshotAdmissionError("root_must_be_real_directory")
        components = relative_path.split("/")
        for component in components[:-1]:
            child = open_relative(directory_handles[-1], component, directory=True)
            directory_handles.append(child)
        final_handle = open_relative(directory_handles[-1], components[-1], directory=False)
        try:
            descriptor = msvcrt.open_osfhandle(final_handle, os.O_RDONLY | getattr(os, "O_BINARY", 0))
        except BaseException:
            close_handle(final_handle)
            raise
        file_object = os.fdopen(descriptor, "rb")
        before = os.fstat(file_object.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise SnapshotAdmissionError("non_regular_source")
        if before.st_size > MAX_SOURCE_BYTES:
            raise SnapshotAdmissionError("source_size_limit_exceeded")
        data = file_object.read(MAX_SOURCE_BYTES + 1)
        after = os.fstat(file_object.fileno())
        if _metadata(before) != _metadata(after):
            raise SnapshotAdmissionError("source_changed_during_read")
        if len(data) > MAX_SOURCE_BYTES or len(data) != after.st_size:
            raise SnapshotAdmissionError("source_changed_during_read")
        return data, after
    finally:
        if file_object is not None:
            file_object.close()
        for handle in reversed(directory_handles):
            close_handle(handle)


def create_snapshot(root: str | os.PathLike[str], paths: Iterable[str | os.PathLike[str]]) -> SourceSnapshot:
    """Hash an explicit finite path list under ``root`` without directory scans."""
    try:
        root_path = Path(root).absolute()
    except (OSError, TypeError, ValueError) as exc:
        raise SnapshotAdmissionError("invalid_root") from exc
    if os.name == "nt":
        try:
            root_stat = root_path.lstat()
            root_mode = root_stat.st_mode
        except OSError as exc:
            raise SnapshotAdmissionError("invalid_root") from exc
        if stat.S_ISLNK(root_mode) or _has_reparse_attribute(root_stat) or not stat.S_ISDIR(root_mode):
            raise SnapshotAdmissionError("root_must_be_real_directory")
        try:
            root_path = root_path.resolve(strict=True)
        except OSError as exc:
            raise SnapshotAdmissionError("invalid_root") from exc

    if isinstance(paths, (str, bytes, os.PathLike)):
        raise SnapshotAdmissionError("paths_must_be_finite_iterable")
    try:
        # Pull one beyond the cap so infinite or excessive iterables fail early.
        normalized = tuple(_normalize_relative_path(p) for _, p in zip(range(MAX_SNAPSHOT_FILES + 1), paths))
    except (TypeError, OSError) as exc:
        raise SnapshotAdmissionError("invalid_paths_iterable") from exc
    if not normalized:
        raise SnapshotAdmissionError("empty_source_set")
    if len(normalized) > MAX_SNAPSHOT_FILES:
        raise SnapshotAdmissionError("source_count_limit_exceeded")
    duplicate_keys = [_path_duplicate_key(path) for path in normalized]
    if len(set(duplicate_keys)) != len(normalized):
        raise SnapshotAdmissionError("duplicate_source_path")

    records: list[SourceRecord] = []
    total_bytes = 0
    for relative_path in sorted(normalized):
        try:
            data, file_stat = _read_stable_source(root_path, relative_path)
        except FileNotFoundError as exc:
            raise SnapshotAdmissionError("source_missing") from exc
        except OSError as exc:
            raise SnapshotAdmissionError("source_read_failed") from exc
        total_bytes += len(data)
        if total_bytes > MAX_SNAPSHOT_BYTES:
            raise SnapshotAdmissionError("snapshot_size_limit_exceeded")
        records.append(SourceRecord(relative_path, len(data), _sha256(data)))

    sources = tuple(records)
    return SourceSnapshot(_SCHEMA, sources, _sha256(_canonical_snapshot_payload(sources)))


def retrieve_exact(
    root: str | os.PathLike[str], snapshot: SourceSnapshot, path: str | os.PathLike[str]
) -> RetrievalResult:
    """Return exact current bytes only when path, size, and SHA-256 still match."""
    if not _validate_snapshot(snapshot):
        return RetrievalResult(RetrievalStatus.UNKNOWN_SNAPSHOT)
    try:
        normalized = _normalize_relative_path(path)
    except (SnapshotAdmissionError, TypeError, ValueError, OSError):
        return RetrievalResult(RetrievalStatus.UNSAFE)
    record = next((item for item in snapshot.sources if item.path == normalized), None)
    if record is None:
        return RetrievalResult(RetrievalStatus.UNKNOWN_SOURCE, normalized)
    try:
        root_path = Path(root).absolute()
        if os.name == "nt":
            root_stat = root_path.lstat()
            root_mode = root_stat.st_mode
            if stat.S_ISLNK(root_mode) or _has_reparse_attribute(root_stat) or not stat.S_ISDIR(root_mode):
                return RetrievalResult(RetrievalStatus.UNSAFE, normalized)
            root_path = root_path.resolve(strict=True)
        data, _ = _read_stable_source(root_path, normalized)
    except FileNotFoundError:
        return RetrievalResult(RetrievalStatus.MISSING, normalized)
    except (OSError, SnapshotAdmissionError, TypeError, ValueError):
        return RetrievalResult(RetrievalStatus.UNSAFE, normalized)
    if len(data) != record.size_bytes or len(data) > MAX_SOURCE_BYTES or _sha256(data) != record.sha256:
        return RetrievalResult(RetrievalStatus.CHANGED, normalized)
    return RetrievalResult(RetrievalStatus.OK, normalized, data)


__all__ = [
    "MAX_SNAPSHOT_BYTES",
    "MAX_SNAPSHOT_FILES",
    "MAX_SOURCE_BYTES",
    "MAX_SOURCE_PATH_CHARS",
    "RetrievalResult",
    "RetrievalStatus",
    "SnapshotAdmissionError",
    "SourceRecord",
    "SourceSnapshot",
    "create_snapshot",
    "retrieve_exact",
]
