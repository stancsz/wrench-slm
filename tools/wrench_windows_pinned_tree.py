"""Read-only Windows tree snapshots for the bounded Wrench gateway jobs.

Each directory and file is opened with reparse-point inspection enabled.
Model snapshots use read-only sharing. Scratch snapshots allow active writes,
retain no-delete directory handles for the tree instance lifetime, and keep
file handles only for one size sample. Retained handles prevent already pinned
names from being renamed or redirected while a caller hashes, loads, or
accounts for the captured tree. This is not an OS quota for later scratch
growth.
"""

from __future__ import annotations

import ctypes
import hashlib
import msvcrt
import os
import stat
from pathlib import Path
from typing import Any


class FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


class ByHandleFileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", ctypes.c_uint32),
        ("creation_time", FileTime),
        ("last_access_time", FileTime),
        ("last_write_time", FileTime),
        ("volume_serial_number", ctypes.c_uint32),
        ("file_size_high", ctypes.c_uint32),
        ("file_size_low", ctypes.c_uint32),
        ("number_of_links", ctypes.c_uint32),
        ("file_index_high", ctypes.c_uint32),
        ("file_index_low", ctypes.c_uint32),
    ]


class PinnedTree:
    """Pin and hash a directory tree below one approved Windows root."""

    SHARE_READ = 0x00000001
    SHARE_READ_WRITE = 0x00000001 | 0x00000002
    OPEN_EXISTING = 3
    FILE_READ_ATTRIBUTES = 0x00000080
    GENERIC_READ = 0x80000000
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    INVALID_HANDLE = ctypes.c_void_p(-1).value

    def __init__(self, approved_root: Path, *, allow_writes: bool = False) -> None:
        if os.name != "nt":
            raise RuntimeError("pinned Wrench trees require the reviewed Windows host")
        self.approved_root = Path(os.path.abspath(approved_root))
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateFileW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ]
        self._kernel32.CreateFileW.restype = ctypes.c_void_p
        self._kernel32.GetFileInformationByHandle.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ByHandleFileInformation),
        ]
        self._kernel32.GetFileInformationByHandle.restype = ctypes.c_int
        self._kernel32.GetFinalPathNameByHandleW.argtypes = [
            ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
        ]
        self._kernel32.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
        self._kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        self._kernel32.CloseHandle.restype = ctypes.c_int
        self._directory_handles: dict[str, Any] = {}
        self._directory_paths: dict[str, Path] = {}
        self.files: dict[str, dict[str, Any]] = {}
        self._closed = False
        self._allow_writes = allow_writes
        self._share_mode = self.SHARE_READ_WRITE if allow_writes else self.SHARE_READ
        self._scan_root: Path | None = None

    @staticmethod
    def _key(path: Path) -> str:
        return os.path.normcase(os.path.normpath(str(path)))

    @classmethod
    def _same_path(cls, left: Path, right: Path) -> bool:
        return cls._key(left) == cls._key(right)

    def _final_path(self, handle: Any) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        length = self._kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if length == 0 or length >= len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)

    def _info(self, handle: Any) -> ByHandleFileInformation:
        info = ByHandleFileInformation()
        if not self._kernel32.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        return info

    def _open_directory(self, path: Path) -> None:
        expected = Path(os.path.abspath(path))
        key = self._key(expected)
        if key in self._directory_handles:
            return
        handle = self._kernel32.CreateFileW(
            str(expected), self.FILE_READ_ATTRIBUTES, self._share_mode, None,
            self.OPEN_EXISTING,
            self.FILE_FLAG_BACKUP_SEMANTICS | self.FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if not handle or handle == self.INVALID_HANDLE:
            raise ctypes.WinError(ctypes.get_last_error())
        stream = None
        try:
            info = self._info(handle)
            if (info.attributes & self.FILE_ATTRIBUTE_REPARSE_POINT
                    or not info.attributes & self.FILE_ATTRIBUTE_DIRECTORY
                    or not self._same_path(self._final_path(handle), expected)):
                raise RuntimeError(f"directory is redirected, linked, or unstable: {expected}")
            self._directory_handles[key] = handle
            self._directory_paths[key] = expected
        except BaseException:
            self._kernel32.CloseHandle(handle)
            raise

    def _pin_chain(self, directory: Path) -> None:
        expected_root = self.approved_root
        candidate = Path(os.path.abspath(directory))
        if not candidate.is_relative_to(expected_root):
            raise RuntimeError(f"tree path escapes approved Wrench root: {directory}")
        self._open_directory(expected_root)
        relative = candidate.relative_to(expected_root)
        current = expected_root
        for part in relative.parts:
            current = current / part
            self._open_directory(current)

    def _open_file(self, path: Path, relative: str, *, hash_file: bool) -> dict[str, Any]:
        expected = Path(os.path.abspath(path))
        self._pin_chain(expected.parent)
        handle = self._kernel32.CreateFileW(
            str(expected), self.GENERIC_READ, self._share_mode, None,
            self.OPEN_EXISTING, self.FILE_FLAG_OPEN_REPARSE_POINT, None,
        )
        if not handle or handle == self.INVALID_HANDLE:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            info = self._info(handle)
            final_path = self._final_path(handle)
            if (info.attributes & (self.FILE_ATTRIBUTE_REPARSE_POINT | self.FILE_ATTRIBUTE_DIRECTORY)
                    or info.number_of_links != 1
                    or not final_path.is_relative_to(self.approved_root)
                    or not self._same_path(final_path, expected)):
                raise RuntimeError(f"file is linked, redirected, or unstable: {expected}")
            size = (int(info.file_size_high) << 32) | int(info.file_size_low)
            fd = msvcrt.open_osfhandle(int(handle), os.O_RDONLY | os.O_BINARY)
            handle = None
            try:
                stream = os.fdopen(fd, "rb")
            except BaseException:
                os.close(fd)
                raise
            before = os.fstat(stream.fileno())
            if (not stat.S_ISREG(before.st_mode) or before.st_size != size
                    or getattr(before, "st_nlink", 1) != 1):
                stream.close()
                raise RuntimeError(f"file metadata differs from its pinned handle: {expected}")
            digest = hashlib.sha256()
            git_blob = hashlib.sha1(f"blob {size}\0".encode("ascii"))
            if hash_file:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                    digest.update(block)
                    git_blob.update(block)
                stream.seek(0)
            identity = (
                int(info.volume_serial_number), int(info.file_index_high), int(info.file_index_low),
            )
            return {
                "path": expected, "stream": stream, "size_bytes": size,
                "sha256": digest.hexdigest() if hash_file else None,
                "git_blob_id": git_blob.hexdigest() if hash_file else None,
                "identity": identity,
            }
        except BaseException:
            if stream is not None:
                stream.close()
            raise
        finally:
            if handle and handle != self.INVALID_HANDLE:
                self._kernel32.CloseHandle(handle)

    def scan(self, root: Path, *, hash_files: bool = True) -> dict[str, dict[str, Any]]:
        """Pin directories for this instance and return one file-size snapshot."""
        if self._closed:
            raise RuntimeError("a closed pinned tree cannot be scanned")
        if hash_files == self._allow_writes:
            raise RuntimeError("tree write mode and hashing mode do not match")
        if self.files:
            raise RuntimeError("release the prior file snapshot before rescanning")
        resolved_root = Path(os.path.abspath(root))
        if self._scan_root is None:
            self._scan_root = resolved_root
        elif not self._same_path(self._scan_root, resolved_root):
            raise RuntimeError("a pinned tree instance cannot change its scan root")
        self._pin_chain(resolved_root)
        pending = [resolved_root]
        while pending:
            directory = pending.pop()
            if key := self._key(directory):
                if key not in self._directory_handles:
                    raise RuntimeError(f"scratch directory was not pinned: {directory}")
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    metadata = entry.stat(follow_symlinks=False)
                    reparse = bool(getattr(metadata, "st_file_attributes", 0)
                                   & self.FILE_ATTRIBUTE_REPARSE_POINT)
                    if reparse or stat.S_ISLNK(metadata.st_mode):
                        raise RuntimeError(f"tree contains a reparse point: {path}")
                    if stat.S_ISDIR(metadata.st_mode):
                        self._pin_chain(path)
                        pending.append(path)
                        continue
                    if not stat.S_ISREG(metadata.st_mode):
                        raise RuntimeError(f"tree contains an unsupported filesystem entry: {path}")
                    relative = path.relative_to(resolved_root).as_posix()
                    record = self._open_file(path, relative, hash_file=hash_files)
                    if record["size_bytes"] != metadata.st_size:
                        record["stream"].close()
                        raise RuntimeError(f"tree file changed while being pinned: {path}")
                    if metadata.st_ino and metadata.st_ino != (
                            (record["identity"][1] << 32) | record["identity"][2]):
                        record["stream"].close()
                        raise RuntimeError(f"tree file identity changed while being pinned: {path}")
                    if relative in self.files:
                        record["stream"].close()
                        raise RuntimeError(f"tree contains a duplicate relative path: {relative}")
                    self.files[relative] = record
        for relative, record in self.files.items():
            if os.fstat(record["stream"].fileno()).st_size != record["size_bytes"]:
                raise RuntimeError(f"tree file size changed during the bounded scan: {relative}")
        return self.files

    def release_files(self) -> None:
        """Close one snapshot's files while retaining directory pins."""
        for record in self.files.values():
            record["stream"].close()
        self.files.clear()

    def verify_unchanged(self) -> None:
        for relative, record in self.files.items():
            if record["sha256"] is None:
                raise RuntimeError(f"pinned tree file has no initial digest: {relative}")
            stream = record["stream"]
            before = os.fstat(stream.fileno())
            if before.st_size != record["size_bytes"] or getattr(before, "st_nlink", 1) != 1:
                raise RuntimeError(f"pinned tree file metadata changed: {relative}")
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            stream.seek(0)
            if digest != record["sha256"]:
                raise RuntimeError(f"pinned tree file content changed after verification: {relative}")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.release_files()
        for handle in reversed(list(self._directory_handles.values())):
            self._kernel32.CloseHandle(handle)
        self._directory_handles.clear()
        self._directory_paths.clear()
