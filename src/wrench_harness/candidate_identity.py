"""Read-only verification of a local model snapshot against pinned metadata.

This module checks file identity only. It never imports a model runtime or
loads checkpoint contents into memory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any, Mapping


METADATA_SCHEMA = "wrench.model-candidate-metadata.v1"
RECEIPT_SCHEMA = "wrench.candidate-local-identity.v1"
MAX_METADATA_FILES = 64
MAX_METADATA_BYTES = 256 * 1024
MAX_METADATA_NODES = 2048
MAX_METADATA_STRING_CHARS = 16_384
MAX_CANDIDATE_BYTES = 4_000_000_000
MAX_PATH_CHARS = 512
MAX_TREE_ENTRIES = 256
HASH_BUFFER_BYTES = 64 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_BLOB_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_REVISION = re.compile(r"^[0-9a-f]{40}$")
_REPARSE_POINT = 0x400


class CandidateIdentityError(ValueError):
    """Pinned metadata or a local snapshot failed bounded identity checks."""


def _is_reparse(st: os.stat_result) -> bool:
    return bool(getattr(st, "st_file_attributes", 0) & _REPARSE_POINT)


def _validate_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_PATH_CHARS:
        raise CandidateIdentityError("metadata_path_invalid")
    if "\x00" in value or "\\" in value or value.startswith("/"):
        raise CandidateIdentityError("metadata_path_invalid")
    parts = value.split("/")
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        raise CandidateIdentityError("metadata_path_invalid")
    if any(part.endswith((".", " ")) for part in parts):
        raise CandidateIdentityError("metadata_path_invalid")
    return value


def _check_json_bounds(value: Any, *, depth: int = 0, state: list[int] | None = None) -> None:
    """Bound an already-parsed JSON tree before canonical serialization."""
    if state is None:
        state = [0, 0]  # node count, conservative encoded-size budget
    state[0] += 1
    if state[0] > MAX_METADATA_NODES or depth > 16:
        raise CandidateIdentityError("metadata_complexity_limit_exceeded")
    state[1] += 16
    if state[1] > MAX_METADATA_BYTES:
        raise CandidateIdentityError("metadata_size_limit_exceeded")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value.bit_length() > 64:
            raise CandidateIdentityError("metadata_number_limit_exceeded")
        state[1] += 24
        return
    if type(value) is float:
        if not (-1e308 < value < 1e308):
            raise CandidateIdentityError("metadata_number_limit_exceeded")
        state[1] += 32
        return
    if type(value) is str:
        if len(value) > MAX_METADATA_STRING_CHARS:
            raise CandidateIdentityError("metadata_string_limit_exceeded")
        state[1] += len(value) * 6
        if state[1] > MAX_METADATA_BYTES:
            raise CandidateIdentityError("metadata_size_limit_exceeded")
        return
    if type(value) is list:
        if len(value) > MAX_METADATA_NODES:
            raise CandidateIdentityError("metadata_complexity_limit_exceeded")
        for item in value:
            _check_json_bounds(item, depth=depth + 1, state=state)
        return
    if type(value) is dict:
        if len(value) > MAX_METADATA_NODES:
            raise CandidateIdentityError("metadata_complexity_limit_exceeded")
        for key, item in value.items():
            if type(key) is not str or len(key) > MAX_METADATA_STRING_CHARS:
                raise CandidateIdentityError("metadata_key_invalid")
            _check_json_bounds(key, depth=depth + 1, state=state)
            _check_json_bounds(item, depth=depth + 1, state=state)
        return
    raise CandidateIdentityError("metadata_value_type_invalid")


def _validate_metadata(metadata: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(metadata, Mapping) or metadata.get("schema") != METADATA_SCHEMA:
        raise CandidateIdentityError("metadata_schema_invalid")
    model_id = metadata.get("model_id")
    revision = metadata.get("revision")
    if (not isinstance(model_id, str) or not model_id.strip() or len(model_id) > 256
            or not isinstance(revision, str) or not _REVISION.fullmatch(revision)):
        raise CandidateIdentityError("metadata_pin_invalid")
    repository_bytes = metadata.get("repository_bytes")
    if (type(repository_bytes) is not int or not 1 <= repository_bytes <= MAX_CANDIDATE_BYTES):
        raise CandidateIdentityError("metadata_total_invalid")
    rows = metadata.get("files")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_METADATA_FILES:
        raise CandidateIdentityError("metadata_file_count_invalid")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for row in rows:
        if not isinstance(row, Mapping):
            raise CandidateIdentityError("metadata_file_row_invalid")
        relative = _validate_relative_path(row.get("path"))
        key = relative.casefold()
        if key in seen:
            raise CandidateIdentityError("metadata_duplicate_path")
        seen.add(key)
        size = row.get("size_bytes")
        if type(size) is not int or not 0 <= size <= MAX_CANDIDATE_BYTES:
            raise CandidateIdentityError("metadata_file_size_invalid")
        raw_sha256 = row.get("upstream_sha256")
        if raw_sha256 is not None and (
            not isinstance(raw_sha256, str) or not _SHA256.fullmatch(raw_sha256)
        ):
            raise CandidateIdentityError("metadata_sha256_invalid")
        git_blob_id = row.get("git_blob_id")
        if not isinstance(git_blob_id, str) or not _GIT_BLOB_SHA1.fullmatch(git_blob_id):
            raise CandidateIdentityError("metadata_git_blob_invalid")
        if raw_sha256 is None and git_blob_id is None:
            raise CandidateIdentityError("metadata_identity_missing")
        total += size
        if total > MAX_CANDIDATE_BYTES:
            raise CandidateIdentityError("metadata_total_limit_exceeded")
        normalized.append({
            "path": relative,
            "size_bytes": size,
            "upstream_sha256": raw_sha256,
            "git_blob_id": git_blob_id,
        })
    if total != repository_bytes:
        raise CandidateIdentityError("metadata_total_mismatch")
    return normalized


def _expected_tree(files: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    expected_files = {row["path"] for row in files}
    expected_dirs: set[str] = set()
    for relative in expected_files:
        parent = Path(relative).parent.as_posix()
        while parent not in {"", "."}:
            expected_dirs.add(parent)
            parent = Path(parent).parent.as_posix()
    return expected_files, expected_dirs


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    # Identity comparisons must fail closed on filesystems that do not expose
    # stable device and inode numbers.
    if not left.st_dev or not right.st_dev or not left.st_ino or not right.st_ino:
        return False
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _open_root_chain(absolute_root: Path, initial_root_st: os.stat_result) -> int:
    """Open each root component relative to a pinned parent without following links."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_fd = os.open(absolute_root.anchor, flags)
    except OSError as exc:
        raise CandidateIdentityError("snapshot_root_unavailable") from exc
    current = Path(absolute_root.anchor)
    try:
        for component in absolute_root.parts[1:]:
            current = current / component
            try:
                observed = current.lstat()
                if stat.S_ISLNK(observed.st_mode) or _is_reparse(observed):
                    raise CandidateIdentityError("snapshot_root_unsafe")
                child_fd = os.open(component, flags, dir_fd=root_fd)
            except CandidateIdentityError:
                raise
            except OSError as exc:
                raise CandidateIdentityError("snapshot_root_unavailable") from exc
            try:
                opened = os.fstat(child_fd)
            except OSError as exc:
                os.close(child_fd)
                raise CandidateIdentityError("snapshot_root_unavailable") from exc
            if not stat.S_ISDIR(opened.st_mode) or not _same_file_identity(observed, opened):
                os.close(child_fd)
                raise CandidateIdentityError("snapshot_root_changed")
            os.close(root_fd)
            root_fd = child_fd
        if not _same_file_identity(initial_root_st, os.fstat(root_fd)):
            raise CandidateIdentityError("snapshot_root_changed")
        return root_fd
    except Exception:
        os.close(root_fd)
        raise


def _stat_child_at(root_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=root_fd, follow_symlinks=False)


def _inventory_exact(root: Path, files: list[dict[str, Any]]) -> tuple[dict[str, tuple[str, os.stat_result]], Path, int]:
    expected_files, expected_dirs = _expected_tree(files)
    if expected_dirs:
        raise CandidateIdentityError("directory_manifest_requires_handle_relative_traversal")
    if (os.name == "nt" or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW")
            or os.scandir not in os.supports_fd or os.stat not in os.supports_dir_fd):
        raise CandidateIdentityError("handle_relative_no_follow_unavailable")
    try:
        absolute_root = Path(os.path.abspath(root))
        root_st = absolute_root.lstat()
    except OSError as exc:
        raise CandidateIdentityError("snapshot_root_unavailable") from exc
    if not stat.S_ISDIR(root_st.st_mode) or _is_reparse(root_st):
        raise CandidateIdentityError("snapshot_root_unsafe")
    root_real = absolute_root
    found: dict[str, tuple[str, os.stat_result]] = {}
    root_fd: int | None = None
    try:
        root_fd = _open_root_chain(absolute_root, root_st)
        opened_root_st = os.fstat(root_fd)
        if not stat.S_ISDIR(opened_root_st.st_mode) or not _same_file_identity(root_st, opened_root_st):
            raise CandidateIdentityError("snapshot_root_changed")
        opened_root_path = _opened_path(root_fd)
        if os.path.normcase(os.path.abspath(opened_root_path)) != os.path.normcase(str(root_real)):
            raise CandidateIdentityError("snapshot_path_changed")
        try:
            with os.scandir(root_fd) as iterator:
                entries_seen = 0
                for child in iterator:
                    entries_seen += 1
                    if entries_seen > MAX_TREE_ENTRIES:
                        raise CandidateIdentityError("snapshot_tree_limit_exceeded")
                    relative = child.name
                    if len(relative) > MAX_PATH_CHARS:
                        raise CandidateIdentityError("snapshot_path_limit_exceeded")
                    try:
                        child_st = _stat_child_at(root_fd, child.name)
                    except OSError as exc:
                        raise CandidateIdentityError("snapshot_entry_unreadable") from exc
                    if child.is_symlink() or stat.S_ISLNK(child_st.st_mode) or _is_reparse(child_st):
                        raise CandidateIdentityError("snapshot_link_forbidden")
                    if stat.S_ISDIR(child_st.st_mode):
                        raise CandidateIdentityError("snapshot_unexpected_entry")
                    if not stat.S_ISREG(child_st.st_mode):
                        raise CandidateIdentityError("snapshot_entry_type_invalid")
                    try:
                        entry_inode = child.inode()
                    except OSError as exc:
                        raise CandidateIdentityError("snapshot_entry_unreadable") from exc
                    if not entry_inode or entry_inode != child_st.st_ino:
                        raise CandidateIdentityError("snapshot_entry_changed")
                    if relative not in expected_files or relative in found:
                        raise CandidateIdentityError("snapshot_unexpected_entry")
                    found[relative] = (relative, child_st)
        except CandidateIdentityError:
            raise
        except OSError as exc:
            raise CandidateIdentityError("snapshot_directory_unreadable") from exc
        final_root_st = os.fstat(root_fd)
        if (not _same_file_identity(root_st, final_root_st)
                or os.path.normcase(os.path.abspath(_opened_path(root_fd))) != os.path.normcase(str(root_real))):
            raise CandidateIdentityError("snapshot_path_changed")
        if set(found) != expected_files:
            raise CandidateIdentityError("snapshot_file_set_mismatch")
        return found, root_real, root_fd
    except Exception:
        if root_fd is not None:
            os.close(root_fd)
        raise


def _opened_path(fd: int) -> Path:
    """Resolve the path attached to the open file handle where supported."""
    proc_fd = Path(f"/proc/self/fd/{fd}")
    if proc_fd.exists():
        return Path(os.path.realpath(proc_fd))
    raise CandidateIdentityError("snapshot_handle_path_unavailable")


def _hash_file(root_fd: int, relative: str, root: Path, expected_stat: os.stat_result,
               expected_size: int) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    git_blob = hashlib.sha1()
    git_blob.update(f"blob {expected_size}\0".encode("ascii"))
    read_bytes = 0
    try:
        file_fd = os.open(relative, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
        with os.fdopen(file_fd, "rb", buffering=0) as stream:
            opened = os.fstat(stream.fileno())
            if (not stat.S_ISREG(opened.st_mode) or opened.st_size != expected_size
                    or not _same_file_identity(expected_stat, opened)):
                raise CandidateIdentityError("snapshot_file_size_mismatch")
            actual_path = _opened_path(stream.fileno())
            if os.path.normcase(os.path.abspath(actual_path)) != os.path.normcase(os.path.abspath(root / relative)):
                raise CandidateIdentityError("snapshot_path_changed")
            while True:
                block = stream.read(HASH_BUFFER_BYTES)
                if not block:
                    break
                read_bytes += len(block)
                if read_bytes > expected_size:
                    raise CandidateIdentityError("snapshot_file_size_mismatch")
                sha256.update(block)
                git_blob.update(block)
            after = os.fstat(stream.fileno())
    except CandidateIdentityError:
        raise
    except OSError as exc:
        raise CandidateIdentityError("snapshot_file_unreadable") from exc
    if (read_bytes != expected_size or after.st_size != expected_size
            or expected_stat.st_mtime_ns != after.st_mtime_ns
            or expected_stat.st_ctime_ns != after.st_ctime_ns
            or not _same_file_identity(expected_stat, after)):
        raise CandidateIdentityError("snapshot_file_changed")
    try:
        path_after = _stat_child_at(root_fd, relative)
    except OSError as exc:
        raise CandidateIdentityError("snapshot_path_changed") from exc
    if (not stat.S_ISREG(path_after.st_mode) or _is_reparse(path_after)
            or path_after.st_size != expected_size
            or path_after.st_mtime_ns != expected_stat.st_mtime_ns
            or path_after.st_ctime_ns != expected_stat.st_ctime_ns
            or not _same_file_identity(expected_stat, path_after)):
        raise CandidateIdentityError("snapshot_path_changed")
    return sha256.hexdigest(), git_blob.hexdigest()


def verify_candidate_identity(metadata: Mapping[str, Any], snapshot_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Verify a bounded local file tree against pinned candidate metadata.

    Files with an upstream SHA-256 are checked against that raw-file digest.
    Other files are checked using their Git blob SHA-1, which includes Git's
    ``blob <length>\0`` header. Reads are streamed and never retained.
    """
    if type(metadata) is not dict:
        raise CandidateIdentityError("metadata_value_type_invalid")
    _check_json_bounds(metadata)
    try:
        canonical_metadata = json.dumps(
            metadata, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CandidateIdentityError("metadata_encoding_invalid") from exc
    if len(canonical_metadata) > MAX_METADATA_BYTES:
        raise CandidateIdentityError("metadata_size_limit_exceeded")
    files = _validate_metadata(metadata)
    root = Path(snapshot_root)
    local_files, root_real, root_fd = _inventory_exact(root, files)
    verified: list[dict[str, Any]] = []
    try:
        for row in sorted(files, key=lambda value: value["path"]):
            relative, enumerated_stat = local_files[row["path"]]
            actual_sha256, actual_git_blob = _hash_file(
                root_fd, relative, root_real, enumerated_stat, row["size_bytes"]
            )
            if row["upstream_sha256"] is not None:
                identity_kind = "upstream_sha256"
                expected_identity = row["upstream_sha256"]
                actual_identity = actual_sha256
            else:
                identity_kind = "git_blob_id"
                expected_identity = row["git_blob_id"]
                actual_identity = actual_git_blob
            if actual_identity != expected_identity:
                raise CandidateIdentityError("snapshot_identity_mismatch")
            verified.append({
                "path": row["path"],
                "size_bytes": row["size_bytes"],
                "identity_kind": identity_kind,
                "identity": actual_identity,
            })
        final_root_stat = os.fstat(root_fd)
        if (not stat.S_ISDIR(final_root_stat.st_mode)
                or os.path.normcase(os.path.abspath(_opened_path(root_fd))) != os.path.normcase(str(root_real))):
            raise CandidateIdentityError("snapshot_path_changed")
    finally:
        os.close(root_fd)
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "status": "VERIFIED_LOCAL_FILES",
        "model_id": metadata["model_id"],
        "revision": metadata["revision"],
        "file_count": len(verified),
        "total_bytes": sum(item["size_bytes"] for item in verified),
        "verification_scope": "local_file_identity_only_no_model_load",
        "files": verified,
    }
    receipt["receipt_sha256"] = hashlib.sha256(json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    receipt_bytes = json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(receipt_bytes) > MAX_METADATA_BYTES:
        raise CandidateIdentityError("receipt_size_limit_exceeded")
    return receipt


__all__ = ["CandidateIdentityError", "verify_candidate_identity"]
