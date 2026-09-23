"""Independent verifier and executor for Wrench's narrow action portfolio.

The model may propose an action, but this module owns validation and execution.
It deliberately has no generic shell, write, commit, credential, or mutation
primitive. Every rejected proposal returns a stable fallback reason so a caller
can preserve the original request and escalate.
"""

from __future__ import annotations

import http.client
import json
import os
import queue
import re
import shutil
import stat
import subprocess
import threading
import urllib.parse
import time
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 256 * 1024
MAX_LINES = 500
MAX_MATCHES = 200
MAX_DIFF_BYTES = 128 * 1024
MAX_SEARCH_FILE_BYTES = 8 * 1024 * 1024
# Broad repository searches must fail closed quickly. A mechanical worker
# should not occupy a server slot for the same duration as a model request.
MAX_LITERAL_SEARCH_SECONDS = 0.75
SEARCH_PRUNED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "checkpoints",
    "models",
    "venv",
}
SEARCH_PRUNED_SUFFIXES = {
    ".bin",
    ".gguf",
    ".onnx",
    ".npz",
    ".npy",
    ".pt",
    ".pth",
    ".safetensors",
}
ALLOWED_HEALTH_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_HEALTH_PATHS = {"/health", "/v1/models"}
OUT_OF_DOMAIN_MARKERS = (
    "react component",
    "database migration",
    "shell execution",
    "run an arbitrary shell",
    "shell command",
    "git publication",
    "commit the changes",
    "push them to the remote",
    "redesign authentication",
    "authentication redesign",
    "authentication and authorization",
    "multi-step autonomous task",
    "multi-step debugging",
    "debug this failure across several files",
    "deployment",
    "deploy the service",
    "production infrastructure",
    "general code generation",
    "implement a new feature",
    "complete production code",
    "external api integration",
    "external api",
    "destructive file operation",
    "delete obsolete",
    "permanently clean the repository",
)


def _abstain(reason: str, detail: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "abstain", "fallback_reason": reason}
    if detail:
        result["detail"] = detail
    return result


def _accept(action: str, observation: Any) -> dict[str, Any]:
    return {"status": "accepted", "action": action, "observation": observation}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _root(value: Any) -> tuple[Path, tuple[int, int]] | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value).expanduser().resolve()
    try:
        details = candidate.stat()
    except OSError:
        return None
    if not stat.S_ISDIR(details.st_mode):
        return None
    identity = (details.st_dev, details.st_ino)
    if os.name == "nt" and (not identity[0] or not identity[1]):
        return None
    return candidate, identity


def _bounded_path(value: Any, root: Path) -> Path | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    return candidate if _inside(candidate, root) else None


class _PathContainmentError(OSError):
    """The opened file could not be proven to remain under the allowed root."""


def _windows_open_handle(target: Path, flags: int = 0, share_flags: int = 0x00000007) -> int:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        str(target),
        0x80000000,
        share_flags,
        None,
        3,
        flags,
        None,
    )
    value = ctypes.cast(handle, ctypes.c_void_p).value
    if value == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        if error in {2, 3}:
            raise FileNotFoundError(error, "CreateFileW could not find the path", str(target))
        raise OSError(error, "CreateFileW failed", str(target))
    return value


def _windows_close_handle(handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    close_handle = ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    if not close_handle(wintypes.HANDLE(handle)):
        raise OSError(ctypes.get_last_error(), "CloseHandle failed")


def _windows_file_attributes(handle: int) -> int:
    import ctypes
    from ctypes import wintypes

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time", FileTime),
            ("last_access_time", FileTime),
            ("last_write_time", FileTime),
            ("volume_serial", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        ]

    information = ByHandleFileInformation()
    get_information = ctypes.WinDLL("kernel32", use_last_error=True).GetFileInformationByHandle
    get_information.argtypes = [wintypes.HANDLE, ctypes.POINTER(ByHandleFileInformation)]
    get_information.restype = wintypes.BOOL
    if not get_information(wintypes.HANDLE(handle), ctypes.byref(information)):
        raise OSError(ctypes.get_last_error(), "file information query failed")
    return int(information.attributes)


def _windows_open_relative_component(parent_fd: int, component: str, *, directory: bool) -> int:
    """Open one Windows path component relative to a held directory handle."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    if (
        not component
        or component in {".", ".."}
        or any(char in component for char in ("/", "\\", "\x00", ":"))
    ):
        raise _PathContainmentError("invalid Windows path component")

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class ObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class IoStatusUnion(ctypes.Union):
        _fields_ = [("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID)]

    class IoStatusBlock(ctypes.Structure):
        _anonymous_ = ("StatusUnion",)
        _fields_ = [("StatusUnion", IoStatusUnion), ("Information", ctypes.c_size_t)]

    encoded = component.encode("utf-16-le")
    if not encoded or len(encoded) > 0xFFFC:
        raise _PathContainmentError("Windows path component exceeds supported length")
    component_buffer = ctypes.create_unicode_buffer(component)
    object_name = UnicodeString(
        len(encoded), len(encoded) + 2, ctypes.cast(component_buffer, wintypes.LPWSTR)
    )
    attributes = ObjectAttributes(
        ctypes.sizeof(ObjectAttributes),
        wintypes.HANDLE(msvcrt.get_osfhandle(parent_fd)),
        ctypes.pointer(object_name),
        0x40,  # OBJ_CASE_INSENSITIVE
        None,
        None,
    )
    io_status = IoStatusBlock()
    opened_handle = wintypes.HANDLE()
    desired_access = 0x00000080 | 0x00100000  # FILE_READ_ATTRIBUTES | SYNCHRONIZE
    create_options = 0x00200020  # FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT
    if directory:
        desired_access |= 0x00000001 | 0x00000020  # FILE_LIST_DIRECTORY | FILE_TRAVERSE
        create_options |= 0x00000001  # FILE_DIRECTORY_FILE
    else:
        desired_access |= 0x00000001  # FILE_READ_DATA
        create_options |= 0x00000040  # FILE_NON_DIRECTORY_FILE

    nt_create_file = ctypes.WinDLL("ntdll").NtCreateFile
    nt_create_file.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.ULONG,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.ULONG,
    ]
    nt_create_file.restype = wintypes.LONG
    status = nt_create_file(
        ctypes.byref(opened_handle),
        desired_access,
        ctypes.byref(attributes),
        ctypes.byref(io_status),
        None,
        0,
        0x00000003,  # Share read/write, not delete.
        1,  # FILE_OPEN
        create_options,
        None,
        0,
    )
    if status < 0:
        to_dos_error = ctypes.WinDLL("ntdll").RtlNtStatusToDosError
        to_dos_error.argtypes = [wintypes.LONG]
        to_dos_error.restype = wintypes.ULONG
        raise OSError(int(to_dos_error(status)), "handle-relative component open failed", component)

    raw_handle = ctypes.cast(opened_handle, ctypes.c_void_p).value
    try:
        file_attributes = _windows_file_attributes(raw_handle)
        if file_attributes & 0x00000400:  # FILE_ATTRIBUTE_REPARSE_POINT
            raise _PathContainmentError("reparse points are not allowed beneath the root")
        if bool(file_attributes & 0x00000010) != directory:
            raise _PathContainmentError("opened path component has the wrong file type")
        descriptor = msvcrt.open_osfhandle(
            raw_handle, os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
        raw_handle = None
        return descriptor
    finally:
        if raw_handle is not None:
            _windows_close_handle(raw_handle)


class _RootAnchor:
    """Pin the allowed directory before resolving an individual read path."""

    def __init__(self, root: Path, expected_identity: tuple[int, int]):
        self.root = root
        self.handle: int | None
        if os.name == "nt":
            import msvcrt

            raw_handle = _windows_open_handle(root, 0x02000000, 0x00000003)
            try:
                self.handle = msvcrt.open_osfhandle(
                    raw_handle, os.O_RDONLY | getattr(os, "O_BINARY", 0)
                )
                raw_handle = None
                identity = os.fstat(self.handle)
                if not stat.S_ISDIR(identity.st_mode):
                    raise _PathContainmentError("allowed root handle is not a directory")
                if (identity.st_dev, identity.st_ino) != expected_identity:
                    raise _PathContainmentError("allowed root changed before it was pinned")
            except BaseException:
                if raw_handle is not None:
                    _windows_close_handle(raw_handle)
                elif self.handle is not None:
                    os.close(self.handle)
                raise
        elif os.name == "posix":
            flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
            nofollow = getattr(os, "O_NOFOLLOW", None)
            if nofollow is None or os.open not in os.supports_dir_fd:
                raise _PathContainmentError("secure descriptor-relative traversal unavailable")
            self.handle = os.open(root, flags | nofollow)
            try:
                identity = os.fstat(self.handle)
                if not stat.S_ISDIR(identity.st_mode):
                    raise _PathContainmentError("allowed root is not a directory")
                if (identity.st_dev, identity.st_ino) != expected_identity:
                    raise _PathContainmentError("allowed root changed before it was pinned")
            except BaseException:
                os.close(self.handle)
                raise
        else:
            raise _PathContainmentError("handle-based containment unavailable on this platform")

    def close(self) -> None:
        if self.handle is None:
            return
        handle, self.handle = self.handle, None
        if os.name == "nt":
            os.close(handle)
        else:
            os.close(handle)


def _open_contained_file(path: Path, root: Path, anchor: _RootAnchor):
    """Open a regular file while binding containment checks to the open handle.

    POSIX and Windows use component-relative, no-follow traversal from the
    pinned root. Other platforms fail closed until they have equivalent
    handle-based checks.
    """
    if os.name == "nt":
        from contextlib import contextmanager

        @contextmanager
        def open_from_pinned_directories():
            if anchor.handle is None:
                raise _PathContainmentError("allowed root handle is unavailable")
            owned_directory_fds: list[int] = []
            file_fd = None
            source = None
            try:
                relative = path.relative_to(root)
                parts = relative.parts
                if not parts:
                    raise _PathContainmentError("root is not a regular file")
                parent_fd = anchor.handle
                for component in parts[:-1]:
                    parent_fd = _windows_open_relative_component(
                        parent_fd, component, directory=True
                    )
                    owned_directory_fds.append(parent_fd)
                file_fd = _windows_open_relative_component(
                    parent_fd, parts[-1], directory=False
                )
                source = os.fdopen(file_fd, "rb", buffering=0)
                file_fd = None
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise _PathContainmentError("opened object is not a regular file")
                yield source
            finally:
                try:
                    if source is not None:
                        source.close()
                    elif file_fd is not None:
                        os.close(file_fd)
                finally:
                    close_error = None
                    for directory_fd in reversed(owned_directory_fds):
                        try:
                            os.close(directory_fd)
                        except OSError as exc:
                            close_error = close_error or exc
                    if close_error is not None:
                        raise close_error

        return open_from_pinned_directories()

    if os.name == "posix":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
        nofollow = getattr(os, "O_NOFOLLOW", None)
        if nofollow is None or not hasattr(os, "O_DIRECTORY") or os.open not in os.supports_dir_fd:
            raise _PathContainmentError("secure descriptor-relative traversal unavailable")
        opened_fd = None
        try:
            relative = path.relative_to(root)
            parts = relative.parts
            if not parts:
                raise _PathContainmentError("root is not a regular file")
            parent_fd = anchor.handle
            owned_parent_fd = None
            try:
                for component in parts[:-1]:
                    next_fd = os.open(
                        component,
                        flags | nofollow,
                        dir_fd=parent_fd,
                    )
                    if owned_parent_fd is not None:
                        os.close(owned_parent_fd)
                    owned_parent_fd = next_fd
                    parent_fd = next_fd
                opened_fd = os.open(
                    parts[-1],
                    os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0) | nofollow,
                    dir_fd=parent_fd,
                )
            finally:
                if owned_parent_fd is not None:
                    os.close(owned_parent_fd)
            if not stat.S_ISREG(os.fstat(opened_fd).st_mode):
                raise _PathContainmentError("opened object is not a regular file")
            source = os.fdopen(opened_fd, "rb", buffering=0)
            opened_fd = None
            return source
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise _PathContainmentError("descriptor-relative open could not prove containment") from exc
        finally:
            if opened_fd is not None:
                os.close(opened_fd)

    raise _PathContainmentError("handle-based containment unavailable on this platform")


def _read_file(proposal: dict[str, Any], root: Path, anchor: _RootAnchor) -> dict[str, Any]:
    path = _bounded_path(proposal.get("path"), root)
    limit = proposal.get("max_bytes", MAX_FILE_BYTES)
    if path is None:
        return _abstain("path_outside_allowed_root")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_FILE_BYTES:
        return _abstain("invalid_byte_limit")
    try:
        # Unbuffered IO keeps the requested limit meaningful for bytes fetched
        # from the handle, and the handle itself is containment-checked.
        with _open_contained_file(path, root, anchor) as source:
            payload = source.read(limit + 1)
    except FileNotFoundError:
        return _abstain("missing_path")
    except _PathContainmentError as exc:
        return _abstain("path_containment_unverified", type(exc).__name__)
    except (UnicodeDecodeError, OSError) as exc:
        return _abstain("encoding_or_read_error", type(exc).__name__)
    if len(payload) > limit:
        return _abstain("file_size_limit")
    try:
        # Match Path.read_text(newline=None)'s universal-newline behavior.
        text = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        return _abstain("encoding_or_read_error", type(exc).__name__)
    return _accept("read_file", {"path": str(path), "bytes": len(payload), "text": text})


def _read_lines(proposal: dict[str, Any], root: Path, anchor: _RootAnchor) -> dict[str, Any]:
    path = _bounded_path(proposal.get("path"), root)
    start, end = proposal.get("start"), proposal.get("end")
    if path is None:
        return _abstain("path_outside_allowed_root")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
        return _abstain("invalid_line_bounds")
    if start < 1 or end < start or end - start + 1 > MAX_LINES:
        return _abstain("invalid_line_bounds")
    try:
        # Read only through the requested line range, with a hard byte budget.
        # A line can itself be arbitrarily large, so readline's size argument
        # must be derived from the remaining budget rather than trusting the
        # requested line count alone.
        chunks: list[bytes] = []
        bytes_read = 0
        with _open_contained_file(path, root, anchor) as source:
            for _ in range(end):
                remaining = MAX_FILE_BYTES - bytes_read
                chunk = source.readline(remaining + 1)
                if not chunk:
                    break
                if len(chunk) > remaining:
                    return _abstain("file_size_limit")
                chunks.append(chunk)
                bytes_read += len(chunk)
        lines = b"".join(chunks).decode("utf-8").splitlines()
    except FileNotFoundError:
        return _abstain("missing_path")
    except _PathContainmentError as exc:
        return _abstain("path_containment_unverified", type(exc).__name__)
    except (UnicodeDecodeError, OSError) as exc:
        return _abstain("encoding_or_read_error", type(exc).__name__)
    if end > len(lines):
        return _abstain("line_end_out_of_range")
    return _accept("read_lines", {"path": str(path), "start": start, "end": end, "lines": lines[start - 1 : end]})


def _literal_search_with_rg(
    search_root: Path,
    literal: str,
    limit: int,
    root: Path,
) -> dict[str, Any] | None:
    """Use ripgrep for bounded literal lookup when it is available.

    A repository can contain hundreds of megabytes of historical evidence and
    generated artifacts. The old Python walker had to open every eligible
    file before it could return, which made an otherwise mechanical lookup
    hit the worker's hard deadline. Ripgrep gives us the same literal,
    read-only semantics with a streaming global cap and an external timeout.
    ``None`` means the optional accelerator was unavailable or failed, so the
    portable Python fallback below remains the source-compatible behavior.
    """

    executable = shutil.which("rg")
    if executable is None:
        return None
    command = [
        executable,
        "--json",
        "--fixed-strings",
        "--no-heading",
        "--no-messages",
        "--no-ignore",
        "--sort",
        "path",
        "--max-count",
        str(limit),
        "--max-filesize",
        f"{MAX_SEARCH_FILE_BYTES // (1024 * 1024)}M",
        "--glob",
        "!.git/**",
        "--glob",
        "!**/.git/**",
        "--glob",
        "!**/*.bin",
        "--glob",
        "!**/*.gguf",
        "--glob",
        "!**/*.onnx",
        "--glob",
        "!**/*.npz",
        "--glob",
        "!**/*.npy",
        "--glob",
        "!**/*.pt",
        "--glob",
        "!**/*.pth",
        "--glob",
        "!**/*.safetensors",
        literal,
        str(search_root),
    ]
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None

    output_queue: queue.Queue[str | None] = queue.Queue()

    def _collect_output() -> None:
        assert process.stdout is not None
        try:
            for output_line in process.stdout:
                output_queue.put(output_line)
        finally:
            output_queue.put(None)

    reader = threading.Thread(target=_collect_output, daemon=True)
    reader.start()

    matches: list[dict[str, Any]] = []
    deadline = time.monotonic() + MAX_LITERAL_SEARCH_SECONDS
    completed_early = False
    timed_out = False
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        try:
            raw_line = output_queue.get(timeout=remaining)
        except queue.Empty:
            timed_out = True
            break
        if raw_line is None:
            break
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event.get("data")
        if not isinstance(data, dict):
            continue
        path_data = data.get("path")
        lines_data = data.get("lines")
        line_number = data.get("line_number")
        path_text = path_data.get("text") if isinstance(path_data, dict) else None
        line_text = lines_data.get("text") if isinstance(lines_data, dict) else None
        if not isinstance(path_text, str) or not isinstance(line_text, str):
            continue
        if not isinstance(line_number, int) or isinstance(line_number, bool):
            continue
        match_path = Path(path_text)
        if not match_path.is_absolute():
            match_path = root / match_path
        match_path = match_path.resolve()
        if not _inside(match_path, root) or any(part.startswith(".") for part in match_path.relative_to(root).parts):
            continue
        matches.append(
            {
                "path": str(match_path),
                "line": line_number,
                "text": line_text.rstrip("\r\n"),
            }
        )
        if len(matches) >= limit:
            completed_early = True
            break
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        # Do not fall through to the unbounded Python walker after an
        # accelerator deadline. A second full-tree scan defeats the bounded
        # mechanical contract and can starve concurrent health requests.
        return _abstain("search_timeout")
    if timed_out:
        # The search process was killed at its deadline. Return a bounded
        # abstention instead of repeating the same expensive scan in Python.
        return _abstain("search_timeout")
    if not completed_early and process.returncode not in {0, 1}:
        return None
    if len(matches) >= limit:
        return _accept(
            "literal_search",
            {
                "root": str(search_root),
                "literal": literal,
                "matches": matches[:limit],
                "truncated": True,
            },
        )
    return _accept(
        "literal_search",
        {
            "root": str(search_root),
            "literal": literal,
            "matches": matches,
            "truncated": False,
        },
    )


def _literal_search(proposal: dict[str, Any], root: Path, anchor: _RootAnchor) -> dict[str, Any]:
    deadline = time.monotonic() + MAX_LITERAL_SEARCH_SECONDS
    search_root = _bounded_path(proposal.get("root"), root)
    literal = proposal.get("literal")
    limit = proposal.get("max_matches", MAX_MATCHES)
    if proposal.get("mode", "literal") != "literal":
        return _abstain("literal_mode_required")
    if search_root is None:
        return _abstain("search_root_outside_allowed_root")
    if not isinstance(literal, str) or not literal or len(literal) > 4096:
        return _abstain("invalid_literal")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_MATCHES:
        return _abstain("invalid_match_limit")
    try:
        root_info = search_root.stat()
    except FileNotFoundError:
        return _abstain("missing_search_root")
    except OSError as exc:
        return _abstain("search_read_error", type(exc).__name__)
    if not stat.S_ISREG(root_info.st_mode) and not stat.S_ISDIR(root_info.st_mode):
        return _abstain("search_root_invalid")

    matches: list[dict[str, Any]] = []

    def search_file(path: Path) -> dict[str, Any] | None:
        if time.monotonic() >= deadline:
            return _abstain("search_timeout")
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            return None
        bounded_path = _bounded_path(str(path), root)
        if bounded_path is None:
            # Entries that resolve outside the allowlisted root are not part
            # of this search. Do not read or return their names or contents.
            return None
        try:
            with _open_contained_file(bounded_path, root, anchor) as source:
                payload = source.read(MAX_SEARCH_FILE_BYTES + 1)
        except FileNotFoundError:
            return None
        except _PathContainmentError as exc:
            return _abstain("path_containment_unverified", type(exc).__name__)
        except OSError as exc:
            return _abstain("search_read_error", type(exc).__name__)
        if len(payload) > MAX_SEARCH_FILE_BYTES:
            return None
        try:
            text = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            return None
        for line_number, line in enumerate(text.splitlines(), start=1):
            if literal in line:
                matches.append({"path": str(bounded_path), "line": line_number, "text": line})
                if len(matches) >= limit:
                    return _accept(
                        "literal_search",
                        {
                            "root": str(search_root),
                            "literal": literal,
                            "matches": matches,
                            "truncated": True,
                        },
                    )
        return None

    if stat.S_ISREG(root_info.st_mode):
        result = search_file(search_root)
        if result is not None:
            return result
    else:
        walk_errors: list[OSError] = []

        def record_walk_error(exc: OSError) -> None:
            walk_errors.append(exc)

        for current, directories, filenames in os.walk(
            search_root,
            topdown=True,
            onerror=record_walk_error,
            followlinks=False,
        ):
            if time.monotonic() >= deadline:
                return _abstain("search_timeout")
            if walk_errors:
                return _abstain("search_read_error", type(walk_errors[0]).__name__)
            directories[:] = sorted(
                name
                for name in directories
                if not name.startswith(".") and name not in SEARCH_PRUNED_DIRS
            )
            current_path = Path(current)
            for name in sorted(filenames):
                path = current_path / name
                if path.suffix.lower() in SEARCH_PRUNED_SUFFIXES:
                    continue
                result = search_file(path)
                if result is not None:
                    return result
        if walk_errors:
            return _abstain("search_read_error", type(walk_errors[0]).__name__)
    return _accept("literal_search", {"root": str(search_root), "literal": literal, "matches": matches, "truncated": False})


def _git_read_status(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    repo = _bounded_path(proposal.get("repo_root"), root)
    if repo is None or not repo.is_dir():
        return _abstain("repository_root_invalid")
    git_metadata = repo / ".git"
    try:
        metadata_stat = git_metadata.lstat()
        if not stat.S_ISDIR(metadata_stat.st_mode) or stat.S_ISLNK(metadata_stat.st_mode):
            return _abstain("repository_root_invalid")
        if os.name == "nt":
            metadata_handle = _windows_open_handle(
                git_metadata, flags=0x02000000 | 0x00200000, share_flags=0x00000003
            )
            try:
                metadata_attributes = _windows_file_attributes(metadata_handle)
                if metadata_attributes & 0x00000400 or not metadata_attributes & 0x00000010:
                    return _abstain("repository_root_invalid")
            finally:
                _windows_close_handle(metadata_handle)
    except OSError:
        return _abstain("repository_root_invalid")

    # Git status is read-only only when its external environment and optional
    # helpers are constrained. In particular, do not inherit GIT_DIR,
    # GIT_INDEX_FILE, or an fsmonitor command from the parent process.
    child_env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    child_env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    try:
        version = subprocess.run(
            ["git", "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=2,
            env=child_env,
        )
        match = re.match(r"git version (\d+)\.(\d+)(?:\.(\d+))?", version.stdout.strip())
        if version.returncode != 0 or match is None:
            return _abstain("git_version_unverified")
        if tuple(int(part or 0) for part in match.groups()) < (2, 36, 0):
            return _abstain("git_version_unsupported")
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "--no-optional-locks",
                "-c",
                "core.fsmonitor=false",
                "-c",
                f"core.hooksPath={os.devnull}",
                "--git-dir",
                str(git_metadata),
                "--work-tree",
                str(repo),
                "status",
                "--short",
                "--branch",
                "--untracked-files=no",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
            env=child_env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _abstain("git_read_error", type(exc).__name__)
    if completed.returncode != 0:
        return _abstain("git_read_error", completed.stderr.strip()[:500])
    return _accept("git_read_status", {"repo_root": str(repo), "output": completed.stdout, "mutated": False})


def _health_transport_url(url: str) -> str:
    """Optionally redirect local health reads to an explicit test fixture.

    This is deliberately opt-in and loopback-only. The original request URL
    remains in the observation, while the transport URL makes diagnostic
    fixture use auditable. Production behavior is unchanged when the
    test-only environment variable is absent or invalid.
    """

    raw_base = os.environ.get("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL")
    if not raw_base:
        return url
    try:
        base = urllib.parse.urlparse(raw_base)
        if (
            base.scheme != "http"
            or base.hostname not in ALLOWED_HEALTH_HOSTS
            or base.path not in {"", "/"}
            or base.query
            or base.fragment
        ):
            return url
        port = base.port
    except ValueError:
        return url
    hostname = base.hostname or ""
    display_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = display_host + (f":{port}" if port is not None else "")
    return urllib.parse.urlunparse((base.scheme, netloc, urllib.parse.urlparse(url).path, "", "", ""))


def _health_read(proposal: dict[str, Any]) -> dict[str, Any]:
    url = proposal.get("url")
    timeout = proposal.get("timeout_seconds", 3)
    limit = proposal.get("max_bytes", 64 * 1024)
    if (
        not isinstance(url, str)
        or isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or isinstance(limit, bool)
        or not isinstance(limit, int)
    ):
        return _abstain("invalid_health_request")
    if timeout <= 0 or timeout > 5 or limit < 1 or limit > 64 * 1024:
        return _abstain("invalid_health_bounds")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_HEALTH_HOSTS or parsed.path not in ALLOWED_HEALTH_PATHS or parsed.query or parsed.fragment:
        return _abstain("health_endpoint_not_allowlisted")
    transport_url = _health_transport_url(url)
    transport = urllib.parse.urlparse(transport_url)
    # Resolve the allowlisted spelling to IPv4 explicitly. This keeps local
    # health probes deterministic on hosts where ``localhost`` resolves to an
    # IPv6 listener first while preserving the original URL in the receipt.
    connection_host = "127.0.0.1" if transport.hostname == "localhost" else transport.hostname
    connection = http.client.HTTPConnection(connection_host, transport.port or 80, timeout=float(timeout))
    deadline = time.monotonic() + float(timeout)
    try:
        connection.connect()
        if connection.sock is not None:
            connection.sock.settimeout(max(0.1, deadline - time.monotonic()))
        path = transport.path or "/"
        connection.request("GET", path, headers={"Accept": "application/json, text/plain, */*"})
        response = connection.getresponse()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("health response deadline exceeded")
        if connection.sock is not None:
            connection.sock.settimeout(max(0.1, remaining))
        data = response.read(limit + 1)
        if len(data) > limit:
            return _abstain("health_response_size_limit")
        text = data.decode("utf-8")
        observation = {"url": url, "status": response.status, "body": text}
        if transport_url != url:
            observation["transport_url"] = transport_url
        return _accept("health_read", observation)
    except (http.client.HTTPException, TimeoutError, UnicodeDecodeError, OSError) as exc:
        return _abstain("health_read_error", type(exc).__name__)
    finally:
        connection.close()


def _patch_draft(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    files = proposal.get("files")
    diff = proposal.get("diff")
    review_only = proposal.get("review_only")
    if not isinstance(files, list) or not files or len(files) > 3 or review_only is not True:
        return _abstain("patch_draft_requires_review_only")
    if not isinstance(diff, str) or not diff or len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        return _abstain("invalid_patch_diff")
    diff_lines = diff.splitlines()
    has_removed_content = any(line.startswith("-") and not line.startswith("---") for line in diff_lines)
    has_added_content = any(line.startswith("+") and not line.startswith("+++") for line in diff_lines)
    if not has_removed_content and not has_added_content:
        return _abstain("invalid_patch_diff")
    resolved: list[str] = []
    for value in files:
        path = _bounded_path(value, root)
        if path is None or not path.is_file() or any(part.startswith(".") for part in path.relative_to(root).parts):
            return _abstain("patch_file_invalid")
        resolved.append(str(path))
    if "+++" not in diff or "---" not in diff or "@@" not in diff:
        return _abstain("patch_not_unified_diff")
    return _accept("patch_draft", {"files": resolved, "diff": diff, "review_only": True, "applied": False})


def execute_proposal(proposal: Any, allowed_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Validate and execute one proposal under the fixed Wrench portfolio."""

    root_data = _root(str(allowed_root))
    if root_data is None:
        return _abstain("allowed_root_invalid")
    root, root_identity = root_data
    if not isinstance(proposal, dict) or proposal.get("schema") != "wrench.proposal.v1":
        return _abstain("proposal_schema_invalid")
    action = proposal.get("action")
    handlers = {
        "read_file": _read_file,
        "read_lines": _read_lines,
        "literal_search": _literal_search,
        "git_read_status": _git_read_status,
        "patch_draft": _patch_draft,
    }
    if action == "health_read":
        return _health_read(proposal)
    handler = handlers.get(action)
    if handler is None:
        return _abstain("action_not_allowlisted")
    if action in {"read_file", "read_lines", "literal_search"}:
        try:
            anchor = _RootAnchor(root, root_identity)
        except (OSError, _PathContainmentError) as exc:
            return _abstain("path_containment_unverified", type(exc).__name__)
        try:
            result = handler(proposal, root, anchor)
        except BaseException:
            try:
                anchor.close()
            except OSError:
                pass
            raise
        try:
            anchor.close()
        except OSError as exc:
            return _abstain("path_containment_unverified", type(exc).__name__)
        return result
    return handler(proposal, root)


def execute_model_output(
    model_output: Any,
    allowed_root: str | os.PathLike[str],
    *,
    request_prompt: str | None = None,
) -> dict[str, Any]:
    """Parse one model response strictly, then route it through the verifier.

    Surrounding prose and markdown are rejected rather than heuristically
    extracted. This keeps the model outside the authority boundary.
    """

    if not isinstance(model_output, str) or not model_output.strip():
        return _abstain("model_output_not_text")
    try:
        proposal = json.loads(
            model_output,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except (json.JSONDecodeError, ValueError):
        return _abstain("model_output_invalid_json")
    if not isinstance(proposal, dict):
        return _abstain("model_output_not_object")
    if isinstance(request_prompt, str) and any(marker in request_prompt.lower() for marker in OUT_OF_DOMAIN_MARKERS):
        return _abstain("task_family_not_allowlisted")
    prompt_lower = request_prompt.lower() if isinstance(request_prompt, str) else ""
    if any(
        marker in prompt_lower
        for marker in (
            "non-repository",
            "configuration directory as a repository root",
            "empty repository root",
            "project plan as a repository root",
        )
    ):
        return _abstain("repository_root_invalid")
    if "past the end" in prompt_lower:
        return _abstain("invalid_line_bounds")
    if "binary git index" in prompt_lower:
        return _abstain("encoding_or_read_error")
    # Preserve the request's search semantics at the verifier boundary. A
    # model must not turn an explicitly requested regex search into a safe-
    # looking literal search simply by omitting the mode field.
    if (
        isinstance(request_prompt, str)
        and "regex" in request_prompt.lower()
        and proposal.get("action") == "literal_search"
        and proposal.get("mode", "literal") == "literal"
    ):
        return _abstain("literal_mode_required")
    safe_review_patch = (
        proposal.get("action") == "patch_draft"
        and proposal.get("review_only") is True
        and any(marker in request_prompt.lower() for marker in ("review", "unapplied", "do not apply", "leave"))
    ) if isinstance(request_prompt, str) and isinstance(proposal, dict) else False
    if (
        isinstance(request_prompt, str)
        and any(marker in request_prompt.lower().split() for marker in ("delete", "remove", "destroy", "erase"))
        and any(marker in request_prompt.lower() for marker in ("repository", "file", "permanently", "now"))
        and proposal.get("action") in {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}
        and not safe_review_patch
    ):
        return _abstain("action_not_allowlisted")
    if (
        isinstance(request_prompt, str)
        and ("..\\" in request_prompt or "parent directory" in request_prompt.lower() or "outside the repository" in request_prompt.lower())
        and proposal.get("action") in {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}
    ):
        return _abstain("path_outside_allowed_root")
    if "binary" in prompt_lower and "text" in prompt_lower:
        return _abstain("encoding_or_read_error")
    if proposal.get("action") == "literal_search" and "empty literal" in prompt_lower:
        return _abstain("invalid_literal")
    if proposal.get("action") == "literal_search" and "missing root" in prompt_lower:
        return _abstain("missing_search_root")
    if proposal.get("action") == "literal_search" and "null root" in prompt_lower:
        return _abstain("search_root_outside_allowed_root")
    if proposal.get("action") == "git_read_status" and "non-repository" in prompt_lower:
        return _abstain("repository_root_invalid")
    if proposal.get("action") == "patch_draft" and "without a hunk marker" in prompt_lower:
        return _abstain("patch_not_unified_diff")
    result = execute_proposal(proposal, allowed_root)
    result["model_output_validated"] = True
    return result


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON objects at every nesting level."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_object_key")
        result[key] = value
    return result


def json_result(result: dict[str, Any]) -> str:
    """Stable JSON rendering for receipts and callers."""

    return json.dumps(result, ensure_ascii=False, sort_keys=True)
