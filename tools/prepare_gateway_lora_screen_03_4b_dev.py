"""Project the frozen synthetic dev source into isolated prompt/oracle files.

This offline preparation utility never loads a model or tokenizer. It is the
only package step that parses the combined labeled development JSONL. The
inference scorer consumes prompt-only JSONL and opens oracle-only JSONL only
after both model arms' prediction files have been sealed.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\wrench-slm-data")
SOURCE = ROOT / "datasets/wrench-gateway-model-research/lora-screen-01/dev.jsonl"
OUTPUT = ROOT / "artifacts/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-projections-iter169"
RESERVATIONS = ROOT / ".budget/reservations"
EXPECTED_SOURCE_SHA256 = "ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7"
EXPECTED_COUNT = 64
EXPECTED_SCHEMA = "wrench.gateway_lora_screen_01.synthetic.v1"
EXPECTED_FAMILIES = {"evidence_select", "retrieve_stop", "compaction_policy", "route"}
JOB_ID = "WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929"
MIN_RESERVATION = 5_000_000
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_PROMPT_BYTES = 2 * 1024 * 1024
MAX_ORACLE_BYTES = 512 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 3 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & flag) or bool(getattr(path, "is_junction", lambda: False)())


def assert_confined(path: Path, *, allow_missing: bool = False) -> Path:
    """Reject reparse points at every extant component and require ROOT ancestry."""
    root = Path(os.path.abspath(ROOT))
    target = Path(os.path.abspath(path))
    if target != root and not target.is_relative_to(root):
        raise RuntimeError(f"path escapes approved root: {target}")
    if is_reparse(root) or not root.is_dir() or Path(root.resolve(strict=True)) != root:
        raise RuntimeError("approved root is missing, redirected, or a reparse point")
    current = root
    relative = target.relative_to(root)
    for part in relative.parts:
        current = current / part
        if is_reparse(current):
            raise RuntimeError(f"path contains a symlink/junction/reparse point: {current}")
        if current.exists():
            resolved = Path(current.resolve(strict=True))
            if not resolved.is_relative_to(root) or resolved != current:
                raise RuntimeError(f"path component resolves outside its lexical location: {current}")
        elif not allow_missing:
            raise RuntimeError(f"required path component does not exist: {current}")
    return target


def guarded_mkdir(path: Path) -> None:
    target = assert_confined(path, allow_missing=True)
    root = Path(os.path.abspath(ROOT))
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        assert_confined(current, allow_missing=True)
        if not current.exists():
            current.mkdir()
        assert_confined(current)
        if not current.is_dir():
            raise RuntimeError(f"expected a directory: {current}")


def confined_read(path: Path, limit: int) -> bytes:
    if os.name != "nt":
        raise RuntimeError("the pinned Windows safe-read path is required")
    target = assert_confined(path)
    parent = assert_confined(target.parent)
    if not parent.is_dir():
        raise RuntimeError("input parent is not a directory")
    from ctypes import wintypes
    import msvcrt

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]
    class FileInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("creation", FileTime), ("access", FileTime), ("write", FileTime),
                    ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD), ("size_low", wintypes.DWORD),
                    ("links", wintypes.DWORD), ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(FileInfo)]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    kernel.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    invalid = ctypes.c_void_p(-1).value

    def final_path(handle: Any) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        count = kernel.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if count == 0 or count >= len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)

    parent_handle = kernel.CreateFileW(str(parent), 0x80, 1, None, 3, 0x02000000 | 0x00200000, None)
    if not parent_handle or parent_handle == invalid:
        raise ctypes.WinError(ctypes.get_last_error())
    file_handle = None
    try:
        parent_info = FileInfo()
        if not kernel.GetFileInformationByHandle(parent_handle, ctypes.byref(parent_info)) or parent_info.attributes & 0x400 or not parent_info.attributes & 0x10 or final_path(parent_handle) != parent:
            raise RuntimeError("input parent handle is redirected or not a directory")
        file_handle = kernel.CreateFileW(str(target), 0x80000000, 1, None, 3, 0x80 | 0x00200000, None)
        if not file_handle or file_handle == invalid:
            raise ctypes.WinError(ctypes.get_last_error())
        info = FileInfo()
        if not kernel.GetFileInformationByHandle(file_handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.attributes & (0x400 | 0x10) or info.links != 1 or final_path(file_handle) != target:
            raise RuntimeError("input is redirected, linked, or not a regular file")
        fd = msvcrt.open_osfhandle(int(file_handle), os.O_RDONLY | os.O_BINARY)
        file_handle = None
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if before.st_size > limit:
                raise RuntimeError("input exceeds its byte cap")
            payload = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            if len(payload) != before.st_size or after.st_size != before.st_size or len(payload) > limit or getattr(after, "st_nlink", 1) != 1:
                raise RuntimeError("input changed during bounded read")
            return payload
    finally:
        if file_handle and file_handle != invalid:
            kernel.CloseHandle(file_handle)
        kernel.CloseHandle(parent_handle)


def active_reservation() -> tuple[Path, dict[str, Any], str]:
    path = RESERVATIONS / f"{JOB_ID}.json"
    raw = confined_read(path, MAX_MANIFEST_BYTES)
    record = json.loads(raw.decode("utf-8"))
    if (record.get("schema") != "wrench.storage-reservation.v1" or record.get("job_id") != JOB_ID
            or record.get("storage_root") != str(ROOT) or type(record.get("reserve_bytes")) is not int
            or record["reserve_bytes"] < MIN_RESERVATION):
        raise RuntimeError("ITER169 storage reservation identity or minimum is invalid")
    if shutil.disk_usage(ROOT).free < record["reserve_bytes"] + 5 * 1024**3:
        raise RuntimeError("C: lacks reservation plus 5 GiB operating headroom")
    return path, record, sha256_bytes(raw)


def write_new(path: Path, payload: bytes, cap: int, reservation_path: Path, reservation_sha: str) -> None:
    if len(payload) > cap:
        raise RuntimeError(f"output exceeds its per-file byte cap: {path.name}")
    assert_confined(path.parent)
    assert_confined(path, allow_missing=True)
    current_reservation = confined_read(assert_confined(reservation_path), MAX_MANIFEST_BYTES)
    if sha256_bytes(current_reservation) != reservation_sha:
        raise RuntimeError("storage reservation changed before a write")
    with path.open("xb") as stream:
        assert_confined(path)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
        if os.fstat(stream.fileno()).st_size != len(payload):
            raise RuntimeError("output size differs from the flushed byte count")
    assert_confined(path)
    if path.stat().st_size != len(payload):
        raise RuntimeError("output changed after write")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-reservation-job-id", required=True)
    args = parser.parse_args()
    if args.storage_reservation_job_id != JOB_ID:
        raise RuntimeError("this one-shot projection package requires its exact ITER169 reservation")
    if os.name != "nt":
        raise RuntimeError("this projection job is pinned to the assigned Windows host")
    reservation_path, reservation_record, reservation_sha = active_reservation()
    assert_confined(SOURCE)
    assert_confined(OUTPUT, allow_missing=True)
    if OUTPUT.exists():
        raise RuntimeError("projection output already exists; this job ID cannot be reused")
    source = confined_read(SOURCE, MAX_SOURCE_BYTES)
    source_sha = sha256_bytes(source)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("combined development source hash mismatch")

    prompt_lines: list[bytes] = []
    oracle_lines: list[bytes] = []
    seen: set[str] = set()
    for line_number, line in enumerate(source.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        messages = row.get("messages")
        if (row.get("schema") != EXPECTED_SCHEMA or row.get("split") != "dev"
                or row.get("family") not in EXPECTED_FAMILIES or not isinstance(row.get("example_id"), str)
                or row["example_id"] in seen or not isinstance(messages, list) or len(messages) != 3
                or [item.get("role") for item in messages] != ["system", "user", "assistant"]
                or any(not isinstance(item.get("content"), str) for item in messages)
                or not isinstance(row.get("gold"), dict)):
            raise RuntimeError(f"combined dev source contract failed at line {line_number}")
        seen.add(row["example_id"])
        prompt_lines.append(canonical({"example_id": row["example_id"], "messages": messages[:2]}))
        oracle_lines.append(canonical({"example_id": row["example_id"], "family": row["family"], "gold": row["gold"]}))
    if len(seen) != EXPECTED_COUNT:
        raise RuntimeError("combined dev source must contain exactly 64 unique rows")
    prompt_payload, oracle_payload = b"".join(prompt_lines), b"".join(oracle_lines)
    if len(prompt_payload) > MAX_PROMPT_BYTES or len(oracle_payload) > MAX_ORACLE_BYTES or len(prompt_payload) + len(oracle_payload) > MAX_OUTPUT_BYTES:
        raise RuntimeError("projected files exceed their predeclared size caps")

    # Check every destination and scratch/log-equivalent path before the first
    # directory or file write. This package uses no scratch directory.
    for path in (OUTPUT, OUTPUT / "prompt-only.jsonl", OUTPUT / "oracle-only.jsonl",
                 OUTPUT / "prompt-manifest.json", OUTPUT / "oracle-manifest.json"):
        assert_confined(path, allow_missing=True)
    guarded_mkdir(OUTPUT)
    helper_sha = sha256_file(Path(__file__).resolve())
    common = {"schema": "wrench.gateway_lora_screen_03_4b.dev-projection.v1", "status": "PREPARED_OFFLINE",
              "job_id": JOB_ID, "created_at_utc": utc_now(), "source_sha256": source_sha,
              "source_rows": EXPECTED_COUNT, "projection_helper_sha256": helper_sha,
              "reservation_job_id": JOB_ID, "reservation_sha256": reservation_sha,
              "reservation_bytes": reservation_record["reserve_bytes"], "storage_root": str(ROOT)}
    prompt_manifest = {**common, "projection": "prompt_only", "payload_path": "prompt-only.jsonl",
                       "payload_sha256": sha256_bytes(prompt_payload), "payload_size_bytes": len(prompt_payload),
                       "row_count": len(prompt_lines), "fields": ["example_id", "messages[system,user]"]}
    oracle_manifest = {**common, "projection": "oracle_only", "payload_path": "oracle-only.jsonl",
                       "payload_sha256": sha256_bytes(oracle_payload), "payload_size_bytes": len(oracle_payload),
                       "row_count": len(oracle_lines), "fields": ["example_id", "family", "gold"]}
    writes = [(OUTPUT / "prompt-only.jsonl", prompt_payload, MAX_PROMPT_BYTES),
              (OUTPUT / "oracle-only.jsonl", oracle_payload, MAX_ORACLE_BYTES),
              (OUTPUT / "prompt-manifest.json", canonical(prompt_manifest), MAX_MANIFEST_BYTES),
              (OUTPUT / "oracle-manifest.json", canonical(oracle_manifest), MAX_MANIFEST_BYTES)]
    if sum(len(payload) for _, payload, _ in writes) > MAX_OUTPUT_BYTES:
        raise RuntimeError("aggregate projection package exceeds its cap")
    for path, payload, cap in writes:
        write_new(path, payload, cap, reservation_path, reservation_sha)
    print(json.dumps({"status": "PREPARED_OFFLINE", "job_id": JOB_ID,
                      "prompt_manifest_sha256": sha256_file(OUTPUT / "prompt-manifest.json"),
                      "oracle_manifest_sha256": sha256_file(OUTPUT / "oracle-manifest.json"),
                      "prompt_sha256": sha256_file(OUTPUT / "prompt-only.jsonl"),
                      "oracle_sha256": sha256_file(OUTPUT / "oracle-only.jsonl"),
                      "output_bytes": sum(path.stat().st_size for path, _, _ in writes)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
