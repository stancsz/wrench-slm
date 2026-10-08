"""Score the frozen gateway screen only after its LoRA run is complete.

This local-only runner has two one-shot modes. ``preflight`` reads one
development example and selects a safe inference device/dtype. ``score-heldout``
first verifies the completed training receipt, adapter, base snapshot, protocol,
dataset hashes, and a live storage reservation, then opens the sealed split.
Predictions are flushed and hashed before any oracle labels are joined.
"""

from __future__ import annotations

import argparse
import _thread
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import stat
import sys
import threading
import time
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVED_ROOT = Path(r"C:\wrench-slm-data")
DATA_ROOT = APPROVED_ROOT / "datasets/wrench-gateway-model-research/lora-screen-01"
MODEL_DIR = APPROVED_ROOT / "weights/Qwen3.5-0.8B"
MODEL_CANDIDATE = REPO_ROOT / "docs/archive/2026-10-08-clean-slate/model-candidate.json"
MODEL_INVENTORY = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-01-model-inventory.json"
TRAIN_LOG_DIR = APPROVED_ROOT / "logs/wrench-gateway-model-research/lora-screen-02-fit-03-attention-only"
TRAIN_MANIFEST = TRAIN_LOG_DIR / "run-manifest.json"
TRAIN_PROTOCOL = REPO_ROOT / "docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md"
EVAL_PROTOCOL = REPO_ROOT / "docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md"
GENERATOR_SOURCE = REPO_ROOT / "tools/generate_gateway_lora_screen_01.py"
EVALUATOR_SOURCE = Path(__file__).resolve()
TRAIN_SOURCE_SNAPSHOT = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-02/fit-03-attention-only/train_gateway_lora_screen_02_gpu.py"
ADAPTER_DIR = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-02/fit-03-attention-only/adapter"
EVAL_ARTIFACTS = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-02-eval"
EVAL_LOGS = APPROVED_ROOT / "logs/wrench-gateway-model-research/lora-screen-02-eval"
GLOBAL_HELDOUT_MARKER = EVAL_ARTIFACTS / "heldout-access.started.json"
GLOBAL_HELDOUT_LOCK = EVAL_ARTIFACTS / "heldout-scoring.lock"
ADDON_DIR = APPROVED_ROOT / "envs/wrench-gateway-lora-screen-01-addons"
MODEL_ID = "Qwen/Qwen3.5-0.8B"
MODEL_REVISION = "2fc06364715b967f1860aea9cf38778875588b17"
TRAIN_JOB_ID = "WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN"
PREFLIGHT_JOB_PREFIX = "WRENCH-GATEWAY-SCREEN-02-EVAL-PREFLIGHT-20260927-"
HELDOUT_JOB_PREFIX = "WRENCH-GATEWAY-SCREEN-02-HELDOUT-20260927-"
PREFLIGHT_MIN_RESERVATION_BYTES = 500_000_000
HELDOUT_MIN_RESERVATION_BYTES = 1_000_000_000
TRAIN_MAX_SCRATCH_BYTES = 512 * 1024 * 1024
PREFLIGHT_MAX_SCRATCH_BYTES = 256 * 1024 * 1024
HELDOUT_MAX_SCRATCH_BYTES = 512 * 1024 * 1024
EXPECTED_STEPS = 96
EXPECTED_ADAPTER_PROFILE = "softmax-attention-only"
EXPECTED_TARGET_COUNT = 24
EXPECTED_TRAINABLE_PARAMETER_COUNT = 540_672
EXPECTED_TRAINER_SOURCE_SHA256 = "62319402f24721532eeece095a298ffbd47da7852cde2b397589ffb48b3c13cc"
EXPECTED_TARGET_MODULES = tuple(
    f"model.language_model.layers.{layer}.self_attn.{projection}_proj"
    for layer in (3, 7, 11, 15, 19, 23)
    for projection in ("q", "k", "v", "o")
)
MAX_NEW_TOKENS = 96
MAX_SPLIT_READ_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
MAX_JOB_OUTPUT_BYTES = 128 * 1024 * 1024
MAX_GENERATION_SECONDS = 300
RAM_FLOOR = 0.10
VRAM_FLOOR = 0.10
EXPECTED_GPU_UUID = "GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021"
EXPECTED_GPU_NAME = "NVIDIA GeForce RTX 5060 Ti"
MODEL_INVENTORY_SHA256 = "64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519"
MODEL_CANDIDATE_SHA256 = "6cefdbbd0203d8e78eb1dee655e82c65efcfa425b57a80cb335242645f47f0a9"
DATA_MANIFEST_SHA256 = "11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed"
TRAIN_DATA_SHA256 = "22f45c8b51ef680f9d05e8c42243ebb34e9f596b22d76577c64e371d272a39d2"
DEV_DATA_SHA256 = "ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7"
PINNED_TREE_SOURCE = Path(__file__).resolve().with_name("wrench_windows_pinned_tree.py")
PINNED_TREE_SOURCE_SHA256 = "E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499"
REQUIRED_FIELDS = {"route", "operation", "selected_evidence_ids", "retrieve_more", "reason_code"}
ROUTES = {"LOCAL_MECHANICAL", "LOCAL_COMPACTION", "FRONTIER", "ABSTAIN"}
OPERATIONS = {"EXACT_RETRIEVE", "COMPACT", "NOOP"}
REASONS = {
    "EXACT_CURRENT_MATCH", "ENOUGH_CURRENT_EVIDENCE", "REFRESH_STALE_EVIDENCE",
    "EXACT_EVIDENCE_MISSING", "PRESERVE_HOT_RETRIEVE_COLD", "BOUNDED_EXACT_OPERATION",
    "OPEN_ENDED_ENGINEERING", "REQUIREMENTS_OR_EVIDENCE_MISSING",
}
AUTHORITY_KEYS = {"tool", "command", "shell", "permissions", "execute", "modify_file", "write_file"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


_ACTIVE_RESERVATION: dict[str, Any] | None = None
_ACTIVE_ARTIFACT_DIR: Path | None = None
_ACTIVE_LOG_DIR: Path | None = None
_ACTIVE_SCRATCH_ROOT: Path | None = None
_ACTIVE_SCRATCH_LIMIT = 0
_ACTIVE_PINNED_TREES: list[Any] = []
_ACTIVE_SCRATCH_TREE: Any | None = None
_ACTIVE_SCRATCH_SCAN_LOCK = threading.Lock()
_ACTIVE_OUTPUT_BUDGET_LOCK = threading.Lock()
_PINNED_TREE_API: Any | None = None


def load_pinned_tree_module() -> Any:
    global _PINNED_TREE_API
    if _PINNED_TREE_API is not None:
        return _PINNED_TREE_API
    source_bytes = PINNED_TREE_SOURCE.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest().upper() != PINNED_TREE_SOURCE_SHA256:
        raise RuntimeError("Windows pinned-tree helper source hash mismatch")
    module = types.ModuleType("wrench_screen_02_pinned_tree")
    exec(compile(source_bytes, str(PINNED_TREE_SOURCE), "exec"), module.__dict__)
    _PINNED_TREE_API = module
    return _PINNED_TREE_API


def verify_pinned_input_trees() -> None:
    for tree in _ACTIVE_PINNED_TREES:
        tree.verify_unchanged()


def require_approved_path(path: Path) -> None:
    approved_root = APPROVED_ROOT.resolve(strict=True)
    resolved = path.resolve(strict=False)
    if resolved == approved_root or not resolved.is_relative_to(approved_root):
        raise RuntimeError(f"evaluation output path escaped approved Wrench storage: {path}")


def require_live_reservation() -> None:
    if _ACTIVE_RESERVATION is None:
        raise RuntimeError("no admitted storage reservation is active")
    path = _ACTIVE_RESERVATION["path"]
    if not path.is_file() or sha256_file(path) != _ACTIVE_RESERVATION["sha256"]:
        raise RuntimeError("active storage reservation disappeared or changed")
    record = load_json(path)
    if (record.get("schema") != "wrench.storage-reservation.v1"
            or record.get("job_id") != _ACTIVE_RESERVATION["job_id"]
            or record.get("reserve_bytes") != _ACTIVE_RESERVATION["minimum_record_bytes"]
            or record["reserve_bytes"] < _ACTIVE_RESERVATION["minimum_bytes"]):
        raise RuntimeError("active storage reservation identity or size changed")
    if shutil.disk_usage(APPROVED_ROOT).free < record["reserve_bytes"]:
        raise RuntimeError("destination volume free space fell below the active reservation")


def resolve_approved_child_file(path: Path, parent: Path, *,
                                allow_missing: bool = False) -> Path | None:
    approved_root = APPROVED_ROOT.resolve(strict=True)
    resolved_parent = parent.resolve(strict=True)
    if not resolved_parent.is_relative_to(approved_root):
        raise RuntimeError("file parent resolves outside approved Wrench storage")
    if path.parent.resolve(strict=True) != resolved_parent or path.is_symlink():
        raise RuntimeError("approved child file has a linked or redirected path")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        if allow_missing:
            return None
        raise RuntimeError("required approved child file does not exist")
    if (resolved != resolved_parent / path.name or not resolved.is_file()):
        raise RuntimeError("approved child file resolves outside its expected parent")
    return resolved


def path_is_reparse_point(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return False
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if (path.is_symlink()
            or bool(getattr(metadata, "st_file_attributes", 0) & reparse_attribute)):
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def require_plain_approved_parent(parent: Path, approved_root: Path) -> None:
    lexical_parent = Path(os.path.abspath(parent))
    if not lexical_parent.is_relative_to(approved_root):
        raise RuntimeError("approved child parent is not lexically under Wrench storage")
    current = lexical_parent
    while current != approved_root:
        if path_is_reparse_point(current):
            raise RuntimeError("approved child parent contains a linked directory")
        current = current.parent


def require_output_budget(extra_bytes: int = 0, *, lock_handle: Any | None = None,
                          check_scratch: bool = True) -> None:
    if check_scratch:
        require_scratch_budget()
    if extra_bytes < 0:
        raise ValueError("output budget increment must be non-negative")
    total = 0
    roots = [root for root in (_ACTIVE_ARTIFACT_DIR, _ACTIVE_LOG_DIR) if root is not None]
    approved_root = APPROVED_ROOT.resolve(strict=True)
    for root in roots:
        if root.is_symlink():
            raise RuntimeError("evaluation output root must not be a linked directory")
        if not root.exists():
            continue
        resolved_root = root.resolve(strict=True)
        if not resolved_root.is_relative_to(approved_root):
            raise RuntimeError("evaluation output root escaped approved storage")
        for path in resolved_root.rglob("*"):
            resolved_path = path.resolve(strict=True)
            if path.is_symlink() or not resolved_path.is_relative_to(resolved_root):
                raise RuntimeError("evaluation output contains a linked or redirected path")
            if resolved_path.is_file():
                total += resolved_path.stat().st_size
    opened_marker = open_confined_windows_child_file(
        GLOBAL_HELDOUT_MARKER, access=0x80000000, disposition=3,
        fd_flags=os.O_RDONLY, stream_mode="rb", allow_missing=True,
    )
    if opened_marker is not None:
        marker_stream, _ = opened_marker
        try:
            total += os.fstat(marker_stream.fileno()).st_size
        finally:
            marker_stream.close()
    if lock_handle is None and _ACTIVE_HELDOUT_LOCK is not None:
        lock_handle = _ACTIVE_HELDOUT_LOCK.handle
    if lock_handle is not None:
        total += os.fstat(lock_handle.fileno()).st_size
    else:
        opened_lock = open_confined_windows_child_file(
            GLOBAL_HELDOUT_LOCK, access=0x80000000, disposition=3,
            fd_flags=os.O_RDONLY, stream_mode="rb", allow_missing=True,
        )
        if opened_lock is not None:
            lock_stream, _ = opened_lock
            try:
                total += os.fstat(lock_stream.fileno()).st_size
            finally:
                lock_stream.close()
    if total + extra_bytes > MAX_JOB_OUTPUT_BYTES:
        raise RuntimeError("aggregate evaluation artifact and log cap would be exceeded")


def scratch_tree_bytes() -> int:
    global _ACTIVE_SCRATCH_TREE
    with _ACTIVE_SCRATCH_SCAN_LOCK:
        if _ACTIVE_SCRATCH_ROOT is None:
            return 0
        if not _ACTIVE_SCRATCH_ROOT.exists():
            if _ACTIVE_SCRATCH_TREE is not None:
                raise RuntimeError("pinned evaluation scratch root disappeared")
            return 0
        if _ACTIVE_SCRATCH_TREE is None:
            _ACTIVE_SCRATCH_TREE = load_pinned_tree_module().PinnedTree(
                APPROVED_ROOT, allow_writes=True,
            )
        tree = _ACTIVE_SCRATCH_TREE
        try:
            records = tree.scan(_ACTIVE_SCRATCH_ROOT, hash_files=False)
            return sum(record["size_bytes"] for record in records.values())
        finally:
            tree.release_files()


def require_scratch_budget() -> int:
    monitor = _ACTIVE_MONITOR
    if monitor is not None and monitor.is_alive():
        if monitor.last_scratch_bytes is None:
            raise RuntimeError("resource monitor has not sampled runtime scratch yet")
        scratch_bytes = monitor.last_scratch_bytes
    else:
        scratch_bytes = scratch_tree_bytes()
        if monitor is not None:
            monitor.final_scratch_bytes = scratch_bytes
    if scratch_bytes > _ACTIVE_SCRATCH_LIMIT:
        raise RuntimeError("evaluation runtime scratch byte cap would be exceeded")
    return scratch_bytes


def initialize_scratch() -> None:
    if _ACTIVE_SCRATCH_ROOT is None:
        raise RuntimeError("evaluation scratch root was not admitted")
    require_live_reservation()
    require_approved_path(_ACTIVE_SCRATCH_ROOT)
    if _ACTIVE_SCRATCH_ROOT.exists():
        raise RuntimeError("refusing to reuse or overwrite this job's runtime scratch")
    _ACTIVE_SCRATCH_ROOT.mkdir(parents=True, exist_ok=False)
    require_approved_path(_ACTIVE_SCRATCH_ROOT)
    require_approved_path(Path(os.environ["TEMP"]))
    Path(os.environ["TEMP"]).mkdir(parents=True, exist_ok=False)
    require_approved_path(Path(os.environ["TEMP"]))
    require_scratch_budget()


def write_json(path: Path, value: Any) -> None:
    require_live_reservation()
    payload = canonical_bytes(value)
    if len(payload) > MAX_OUTPUT_BYTES:
        raise RuntimeError(f"receipt too large: {path.name}")
    with _ACTIVE_OUTPUT_BUDGET_LOCK:
        require_output_budget(len(payload))
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                            capture_output=True, text=True, timeout=5, check=True)
    return result.stdout.strip()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def verify_fit03_candidate_identity(run: dict[str, Any], source_snapshot_sha256: str) -> None:
    """Require the reviewed trainer bytes and exact attention-only target list."""
    if (source_snapshot_sha256 != EXPECTED_TRAINER_SOURCE_SHA256
            or run.get("runner_sha256") != EXPECTED_TRAINER_SOURCE_SHA256):
        raise RuntimeError("fit-03 trainer source differs from the reviewed runner")
    if (run.get("adapter_profile") != EXPECTED_ADAPTER_PROFILE
            or run.get("matched_target_count") != EXPECTED_TARGET_COUNT
            or run.get("matched_target_modules") != list(EXPECTED_TARGET_MODULES)
            or run.get("trainable_parameter_count") != EXPECTED_TRAINABLE_PARAMETER_COUNT
            or run.get("fit_mode") is not True
            or run.get("preflight_only") is not False
            or run.get("expected_fit_optimizer_steps") != EXPECTED_STEPS
            or run.get("optimizer_steps") != EXPECTED_STEPS):
        raise RuntimeError("training receipt is not the reviewed attention-only fit-03 candidate")


class ResourceMonitor(threading.Thread):
    """Sample host reserves and interrupt the job immediately on a breach."""

    def __init__(self, output: Path) -> None:
        super().__init__(name="wrench-gateway-screen-resource-monitor", daemon=True)
        self.output = output
        self.stop_event = threading.Event()
        self.breach_reason: str | None = None
        self.samples: list[dict[str, Any]] = []
        self.max_scratch_bytes = 0
        self.last_scratch_bytes: int | None = None
        self.final_scratch_bytes: int | None = None

    @staticmethod
    def ram() -> tuple[int, int]:
        import psutil

        memory = psutil.virtual_memory()
        return int(memory.available), int(memory.total)

    @staticmethod
    def gpu() -> dict[str, Any]:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,uuid,pci.bus_id,name,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        rows = [line.split(",", maxsplit=5) for line in result.stdout.strip().splitlines() if line.strip()]
        if len(rows) != 1 or len(rows[0]) != 6:
            raise RuntimeError("evaluation requires exactly one visible NVIDIA GPU")
        index, uuid, pci_bus_id, name, total_mib, free_mib = [part.strip() for part in rows[0]]
        if index != "0" or uuid != EXPECTED_GPU_UUID or name != EXPECTED_GPU_NAME:
            raise RuntimeError("monitored GPU differs from the pinned screen-02 device")
        return {"index": int(index), "uuid": uuid, "pci_bus_id": pci_bus_id, "name": name,
                "total_mib": int(total_mib), "free_mib": int(free_mib)}

    def sample(self) -> None:
        require_live_reservation()
        scratch_bytes = scratch_tree_bytes()
        self.last_scratch_bytes = scratch_bytes
        self.max_scratch_bytes = max(self.max_scratch_bytes, scratch_bytes)
        if scratch_bytes > _ACTIVE_SCRATCH_LIMIT:
            self.breach_reason = "RUNTIME_SCRATCH_BYTE_CAP"
            self.stop_event.set()
            return
        ram_free, ram_total = self.ram()
        gpu = self.gpu()
        row = {
            "time_utc": utc_now(),
            "ram_free_bytes": ram_free,
            "ram_total_bytes": ram_total,
            "ram_free_fraction": ram_free / ram_total,
            "gpu_index": gpu["index"],
            "gpu_uuid": gpu["uuid"],
            "gpu_pci_bus_id": gpu["pci_bus_id"],
            "gpu_name": gpu["name"],
            "gpu_free_mib": gpu["free_mib"],
            "gpu_total_mib": gpu["total_mib"],
            "gpu_free_fraction": gpu["free_mib"] / gpu["total_mib"],
            "runtime_scratch_bytes": scratch_bytes,
        }
        line = canonical_bytes(row)
        if self.output.stat().st_size + len(line) > MAX_OUTPUT_BYTES:
            self.breach_reason = "RESOURCE_LOG_BYTE_CAP"
            self.stop_event.set()
            return
        with _ACTIVE_OUTPUT_BUDGET_LOCK:
            require_output_budget(len(line), check_scratch=False)
            with self.output.open("ab") as stream:
                stream.write(line)
                stream.flush()
        self.samples.append(row)
        if row["ram_free_fraction"] < RAM_FLOOR:
            self.breach_reason = "RAM_FREE_BELOW_10_PERCENT"
        elif row["gpu_free_fraction"] < VRAM_FLOOR:
            self.breach_reason = "VRAM_FREE_BELOW_10_PERCENT"
        if self.breach_reason:
            self.stop_event.set()

    def run(self) -> None:
        try:
            while not self.stop_event.is_set():
                self.sample()
                if self.breach_reason:
                    _thread.interrupt_main()
                    return
                self.stop_event.wait(1.0)
        except BaseException as exc:
            self.breach_reason = f"RESOURCE_MONITOR_ERROR:{type(exc).__name__}"
            _thread.interrupt_main()

    def summary(self) -> dict[str, Any]:
        if not self.samples:
            return {"sample_count": 0, "breach_reason": self.breach_reason,
                    "runtime_scratch_limit_bytes": _ACTIVE_SCRATCH_LIMIT,
                    "runtime_scratch_bytes_at_finalize": self.final_scratch_bytes,
                    "runtime_scratch_peak_bytes": max(
                        self.max_scratch_bytes, self.final_scratch_bytes or 0,
                    )}
        return {
            "sample_count": len(self.samples),
            "minimum_ram_free_bytes": min(row["ram_free_bytes"] for row in self.samples),
            "minimum_ram_free_fraction": min(row["ram_free_fraction"] for row in self.samples),
            "minimum_gpu_free_mib": min(row["gpu_free_mib"] for row in self.samples),
            "minimum_gpu_free_fraction": min(row["gpu_free_fraction"] for row in self.samples),
            "breach_reason": self.breach_reason,
            "runtime_scratch_limit_bytes": _ACTIVE_SCRATCH_LIMIT,
            "runtime_scratch_bytes_at_finalize": self.final_scratch_bytes,
            "runtime_scratch_peak_bytes": max(
                self.max_scratch_bytes,
                self.final_scratch_bytes or 0,
                max(row.get("runtime_scratch_bytes", 0) for row in self.samples),
            ),
        }


_ACTIVE_MONITOR: ResourceMonitor | None = None
_ACTIVE_ARTIFACT_DIR: Path | None = None
_ACTIVE_HELDOUT_LOCK: Any | None = None
_ACTIVE_GLOBAL_HELDOUT_MARKER: Any | None = None


def open_confined_windows_child_file(
    path: Path, *, access: int = 0xC0000000, disposition: int = 4,
    fd_flags: int = os.O_RDWR, stream_mode: str = "r+b",
    allow_missing: bool = False, share_mode: int = 0x00000003,
) -> tuple[Any, tuple[int, int, int]] | None:
    """Open one approved child without following reparse points; verify its live handle."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    if os.name != "nt":
        raise RuntimeError("confined evaluator files require the pinned Windows host")
    approved_root = APPROVED_ROOT.resolve(strict=True)
    if path_is_reparse_point(APPROVED_ROOT):
        raise RuntimeError("approved Wrench storage root must not be a reparse point")
    require_plain_approved_parent(path.parent, approved_root)
    if not path.parent.exists():
        if allow_missing:
            return None
        raise RuntimeError("approved child parent does not exist")
    parent = path.parent.resolve(strict=True)
    if not parent.is_relative_to(approved_root):
        raise RuntimeError("held-out lock parent resolves outside approved storage")
    if path.parent.resolve(strict=True) != parent:
        raise RuntimeError("held-out lock parent changed during resolution")
    expected_path = parent / path.name

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time", FileTime),
            ("last_access_time", FileTime),
            ("last_write_time", FileTime),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(ByHandleFileInformation),
    ]
    kernel32.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel32.GetFinalPathNameByHandleW.argtypes = [
        wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD,
    ]
    kernel32.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    invalid_handle = ctypes.c_void_p(-1).value
    share_read_write = 0x00000001 | 0x00000002
    open_reparse_point = 0x00200000
    file_attribute_reparse_point = 0x00000400
    file_attribute_directory = 0x00000010

    def handle_final_path(handle: Any) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        length = kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if length == 0 or length >= len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        name = buffer.value
        if name.startswith("\\\\?\\UNC\\"):
            name = "\\\\" + name[8:]
        elif name.startswith("\\\\?\\"):
            name = name[4:]
        return Path(name)

    def same_path(left: Path, right: Path) -> bool:
        return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(os.path.normpath(str(right)))

    parent_handle = kernel32.CreateFileW(
        str(parent), 0x00000080, share_read_write, None, 3,
        0x02000000 | open_reparse_point, None,
    )
    if not parent_handle or parent_handle == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    file_handle: Any | None = None
    try:
        parent_info = ByHandleFileInformation()
        if not kernel32.GetFileInformationByHandle(parent_handle, ctypes.byref(parent_info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if (parent_info.attributes & file_attribute_reparse_point
                or not parent_info.attributes & file_attribute_directory
                or not same_path(handle_final_path(parent_handle), parent)):
            raise RuntimeError("held-out lock directory handle is redirected or not a directory")

        file_handle = kernel32.CreateFileW(
            str(expected_path), access, share_mode, None, disposition,
            0x00000080 | open_reparse_point, None,
        )
        if not file_handle or file_handle == invalid_handle:
            error = ctypes.WinError(ctypes.get_last_error())
            if allow_missing and getattr(error, "winerror", None) in {2, 3}:
                return None
            raise error
        file_info = ByHandleFileInformation()
        if not kernel32.GetFileInformationByHandle(file_handle, ctypes.byref(file_info)):
            raise ctypes.WinError(ctypes.get_last_error())
        final_path = handle_final_path(file_handle)
        if (file_info.attributes & (file_attribute_reparse_point | file_attribute_directory)
                or file_info.number_of_links != 1
                or not final_path.is_relative_to(approved_root)
                or not same_path(final_path, expected_path)):
            raise RuntimeError("opened approved child handle is linked or outside its expected path")
        identity = (
            int(file_info.volume_serial_number),
            int(file_info.file_index_high),
            int(file_info.file_index_low),
        )
        fd = msvcrt.open_osfhandle(int(file_handle), fd_flags | os.O_BINARY)
        file_handle = None
        try:
            return os.fdopen(fd, stream_mode), identity
        except BaseException:
            os.close(fd)
            raise
    finally:
        if file_handle and file_handle != invalid_handle:
            kernel32.CloseHandle(file_handle)
        kernel32.CloseHandle(parent_handle)


def sha256_approved_child(path: Path, parent: Path, *,
                          allow_missing: bool = False) -> str | None:
    if Path(os.path.abspath(path.parent)) != Path(os.path.abspath(parent)):
        raise RuntimeError("approved child path does not have its expected parent")
    opened = open_confined_windows_child_file(
        path, access=0x80000000, disposition=3,
        fd_flags=os.O_RDONLY, stream_mode="rb", allow_missing=allow_missing,
    )
    if opened is None:
        return None
    stream, _ = opened
    with stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_approved_child_bytes(path: Path, parent: Path, *,
                              max_bytes: int) -> tuple[bytes, str]:
    if max_bytes <= 0:
        raise ValueError("approved child read limit must be positive")
    if Path(os.path.abspath(path.parent)) != Path(os.path.abspath(parent)):
        raise RuntimeError("approved child path does not have its expected parent")
    opened = open_confined_windows_child_file(
        path, access=0x80000000, disposition=3,
        fd_flags=os.O_RDONLY, stream_mode="rb", share_mode=0x00000001,
    )
    if opened is None:
        raise RuntimeError("required approved child file does not exist")
    stream, _ = opened
    with stream:
        before = os.fstat(stream.fileno())
        if before.st_size > max_bytes:
            raise RuntimeError("approved child file exceeds its bounded read limit")
        payload = stream.read(max_bytes + 1)
        after = os.fstat(stream.fileno())
        if (len(payload) != before.st_size or len(payload) > max_bytes
                or after.st_size != before.st_size):
            raise RuntimeError("approved child file changed or was truncated while reading")
    return payload, hashlib.sha256(payload).hexdigest()


def required_sha256_approved_child(path: Path, parent: Path) -> str:
    digest = sha256_approved_child(path, parent)
    if digest is None:
        raise RuntimeError("required approved child file disappeared")
    return digest


class HeldoutRunLock:
    """Cross-process Windows lock that prevents concurrent held-out scoring."""

    def __init__(self, path: Path, job_id: str) -> None:
        self.path = path
        self.job_id = job_id
        self.handle: Any | None = None
        self.file_identity: tuple[int, int, int] | None = None

    def acquire(self) -> None:
        import msvcrt

        require_live_reservation()
        opened = open_confined_windows_child_file(self.path)
        if opened is None:
            raise RuntimeError("held-out lock could not be opened")
        handle, identity = opened
        try:
            with _ACTIVE_OUTPUT_BUDGET_LOCK:
                require_output_budget(1024, lock_handle=handle)
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError("another held-out scoring process owns the global lock") from exc
        except BaseException:
            handle.close()
            raise
        self.handle = handle
        self.file_identity = identity
        try:
            metadata = canonical_bytes({
                "job_id": self.job_id,
                "pid": os.getpid(),
                "locked_at_utc": utc_now(),
            })
            with _ACTIVE_OUTPUT_BUDGET_LOCK:
                require_output_budget(len(metadata), lock_handle=handle)
                handle.seek(0)
                handle.truncate(0)
                handle.write(metadata)
                handle.flush()
        except BaseException:
            self.release()
            raise

    def release(self) -> None:
        if self.handle is None:
            return
        import msvcrt

        try:
            self.handle.seek(0)
            try:
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                # Closing the handle still releases the process-owned range lock.
                pass
        finally:
            self.handle.close()
            self.handle = None


def release_heldout_lock() -> None:
    global _ACTIVE_HELDOUT_LOCK
    if _ACTIVE_HELDOUT_LOCK is not None:
        _ACTIVE_HELDOUT_LOCK.release()
        _ACTIVE_HELDOUT_LOCK = None


def release_global_heldout_marker() -> None:
    global _ACTIVE_GLOBAL_HELDOUT_MARKER
    if _ACTIVE_GLOBAL_HELDOUT_MARKER is not None:
        _ACTIVE_GLOBAL_HELDOUT_MARKER.close()
        _ACTIVE_GLOBAL_HELDOUT_MARKER = None


def require_storage_reservation(job_id: str, mode: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", job_id):
        raise RuntimeError("invalid storage reservation job ID")
    expected_prefix = PREFLIGHT_JOB_PREFIX if mode == "preflight" else HELDOUT_JOB_PREFIX
    minimum_bytes = PREFLIGHT_MIN_RESERVATION_BYTES if mode == "preflight" else HELDOUT_MIN_RESERVATION_BYTES
    if not re.fullmatch(re.escape(expected_prefix) + r"[0-9]{2}", job_id):
        raise RuntimeError(f"{mode} storage reservation job ID must use {expected_prefix}NN")
    path = APPROVED_ROOT / ".budget/reservations" / f"{job_id}.json"
    require_approved_path(path)
    if not path.is_file():
        raise RuntimeError(f"storage reservation missing: {job_id}")
    record = load_json(path)
    if record.get("schema") != "wrench.storage-reservation.v1" or record.get("job_id") != job_id:
        raise RuntimeError("storage reservation identity/schema mismatch")
    if (not isinstance(record.get("reserve_bytes"), int)
            or isinstance(record.get("reserve_bytes"), bool)
            or record["reserve_bytes"] < minimum_bytes
            or Path(record.get("storage_root", "")).resolve() != APPROVED_ROOT.resolve()):
        raise RuntimeError("storage reservation is undersized or bound to another root")
    if shutil.disk_usage(APPROVED_ROOT).free < record["reserve_bytes"]:
        raise RuntimeError("destination volume free space is below the active reservation")
    return {"job_id": job_id, "path": path, "record": record,
            "sha256": sha256_file(path), "minimum_bytes": minimum_bytes,
            "minimum_record_bytes": record["reserve_bytes"]}


def resolve_manifest_path(root: Path, relative_value: Any) -> Path:
    if not isinstance(relative_value, str) or not relative_value:
        raise RuntimeError("dataset manifest path must be a non-empty relative string")
    windows_path = PureWindowsPath(relative_value)
    candidate = Path(relative_value)
    if (candidate.is_absolute() or windows_path.is_absolute() or windows_path.drive
            or ".." in candidate.parts or ".." in windows_path.parts):
        raise RuntimeError(f"dataset path must stay relative to its approved root: {relative_value}")
    approved = APPROVED_ROOT.resolve(strict=True)
    resolved_root = root.resolve(strict=True)
    if not resolved_root.is_relative_to(approved):
        raise RuntimeError("dataset root resolves outside approved Wrench storage")
    resolved = (resolved_root / candidate).resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise RuntimeError(f"dataset path escaped the approved root: {relative_value}")
    return resolved


def verify_resource_log(payload: bytes, expected: dict[str, Any], *,
                        scratch_limit_bytes: int,
                        expected_sha256: str | None = None) -> None:
    if scratch_limit_bytes not in {PREFLIGHT_MAX_SCRATCH_BYTES, HELDOUT_MAX_SCRATCH_BYTES}:
        raise RuntimeError("resource log validation received an unrecognized scratch limit")
    if len(payload) > MAX_OUTPUT_BYTES:
        raise RuntimeError("resource log exceeds its bounded validation size")
    if expected_sha256 is not None and hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise RuntimeError("resource log bytes do not match their pinned hash")
    rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    if not rows:
        raise RuntimeError("preflight resource log is empty")
    final_scratch_bytes = expected.get("runtime_scratch_bytes_at_finalize")
    if (type(final_scratch_bytes) is not int
            or final_scratch_bytes < 0 or final_scratch_bytes > scratch_limit_bytes):
        raise RuntimeError("resource summary lacks a bounded final scratch measurement")
    if any(row.get("gpu_uuid") != EXPECTED_GPU_UUID
           or row.get("gpu_index") != 0
           or row.get("gpu_name") != EXPECTED_GPU_NAME
           or row.get("ram_free_fraction", 0) < RAM_FLOOR
           or row.get("gpu_free_fraction", 0) < VRAM_FLOOR
           or not isinstance(row.get("runtime_scratch_bytes"), int)
           or row["runtime_scratch_bytes"] > scratch_limit_bytes
           for row in rows):
        raise RuntimeError("resource log has a GPU, resource-floor, or scratch-cap breach")
    actual = {
        "sample_count": len(rows),
        "minimum_ram_free_bytes": min(row["ram_free_bytes"] for row in rows),
        "minimum_ram_free_fraction": min(row["ram_free_fraction"] for row in rows),
        "minimum_gpu_free_mib": min(row["gpu_free_mib"] for row in rows),
        "minimum_gpu_free_fraction": min(row["gpu_free_fraction"] for row in rows),
        "breach_reason": None,
        "runtime_scratch_limit_bytes": scratch_limit_bytes,
        "runtime_scratch_bytes_at_finalize": final_scratch_bytes,
        "runtime_scratch_peak_bytes": max(
            final_scratch_bytes, max(row["runtime_scratch_bytes"] for row in rows),
        ),
    }
    for key, value in actual.items():
        if expected.get(key) != value:
            raise RuntimeError(f"preflight resource summary mismatch: {key}")
    if actual["minimum_ram_free_fraction"] < RAM_FLOOR or actual["minimum_gpu_free_fraction"] < VRAM_FLOOR:
        raise RuntimeError("preflight resource log records a breached 10% reserve")


def verify_training_and_inputs() -> tuple[
        dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, bytes]]:
    for path in (DATA_ROOT, MODEL_DIR, MODEL_INVENTORY, TRAIN_MANIFEST,
                 TRAIN_SOURCE_SNAPSHOT, ADAPTER_DIR, ADDON_DIR):
        require_approved_path(path)
    reservation_path = APPROVED_ROOT / ".budget/reservations" / f"{TRAIN_JOB_ID}.json"
    require_approved_path(reservation_path)
    if reservation_path.exists():
        raise RuntimeError("training reservation must be released after the run stops and outputs are accounted")
    training_manifest_bytes, training_manifest_sha256 = read_approved_child_bytes(
        TRAIN_MANIFEST, TRAIN_LOG_DIR, max_bytes=MAX_OUTPUT_BYTES,
    )
    run = json.loads(training_manifest_bytes.decode("utf-8"))
    if not isinstance(run, dict):
        raise RuntimeError("training manifest must be a JSON object")
    if run.get("schema") != "wrench.gateway_lora_screen_02.run.v1" or run.get("job_id") != TRAIN_JOB_ID:
        raise RuntimeError("training manifest identity mismatch")
    if run.get("status") != "COMPLETED":
        raise RuntimeError("held-out access requires the completed fit-03 training run")
    if any(not re.fullmatch(r"[0-9a-f]{64}", str(run.get(field, "")))
           for field in ("fit_preflight_manifest_sha256", "fit_preflight_resource_log_sha256")):
        raise RuntimeError("training receipt does not bind the successful fit preflight evidence")
    if run.get("heldout_opened_by_runner") is not False:
        raise RuntimeError("training receipt reports held-out access")
    if (run.get("runtime_scratch_limit_bytes") != TRAIN_MAX_SCRATCH_BYTES
            or run.get("runtime_scratch_bytes_at_finalize", TRAIN_MAX_SCRATCH_BYTES + 1)
            > TRAIN_MAX_SCRATCH_BYTES
            or run.get("runtime_scratch_peak_bytes", TRAIN_MAX_SCRATCH_BYTES + 1)
            > TRAIN_MAX_SCRATCH_BYTES):
        raise RuntimeError("training receipt does not prove bounded runtime scratch use")
    if run.get("model_id") != MODEL_ID or run.get("model_revision") != MODEL_REVISION:
        raise RuntimeError("base model identity mismatch")
    if sha256_file(TRAIN_PROTOCOL) != run.get("protocol_sha256"):
        raise RuntimeError("frozen training protocol hash mismatch")
    verify_fit03_candidate_identity(run, sha256_file(TRAIN_SOURCE_SNAPSHOT))
    if run.get("pinned_tree_source_sha256") != PINNED_TREE_SOURCE_SHA256:
        raise RuntimeError("pinned-tree helper hash differs from the training receipt")
    training_resource_log = TRAIN_LOG_DIR / "resources.jsonl"
    if not isinstance(run.get("resource_log_finalized_at_utc"), str):
        raise RuntimeError("training resource log lacks a finalization timestamp")
    training_log_bytes, training_log_sha256 = read_approved_child_bytes(
        training_resource_log, TRAIN_LOG_DIR, max_bytes=MAX_OUTPUT_BYTES,
    )
    if training_log_sha256 != run.get("resource_log_sha256"):
        raise RuntimeError("final training resource-log hash mismatch")
    training_samples = [
        json.loads(line) for line in training_log_bytes.decode("utf-8").splitlines() if line
    ]
    if (not training_samples
            or any(sample.get("gpu_uuid") != EXPECTED_GPU_UUID
                   or sample.get("gpu_index") != 0
                   or sample.get("gpu_name") != EXPECTED_GPU_NAME
                   or sample.get("ram_free_fraction", 0) < RAM_FLOOR
                   or sample.get("gpu_free_fraction", 0) < VRAM_FLOOR
                   or not isinstance(sample.get("runtime_scratch_bytes"), int)
                   or sample["runtime_scratch_bytes"] > TRAIN_MAX_SCRATCH_BYTES
                   for sample in training_samples)):
        raise RuntimeError("training resource log is empty, misidentifies the GPU, or breaches a reserve floor")

    inventory_bytes, inventory_sha256 = read_approved_child_bytes(
        MODEL_INVENTORY, MODEL_INVENTORY.parent, max_bytes=MAX_OUTPUT_BYTES,
    )
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    if (inventory.get("status") != "VERIFIED_LOCAL_SNAPSHOT"
            or inventory.get("model_id") != MODEL_ID
            or inventory.get("revision") != MODEL_REVISION
            or inventory_sha256 != MODEL_INVENTORY_SHA256
            or inventory_sha256 != run.get("model_inventory_sha256")):
        raise RuntimeError("frozen model inventory mismatch")
    candidate_bytes = MODEL_CANDIDATE.read_bytes()
    candidate_sha256 = hashlib.sha256(candidate_bytes).hexdigest()
    candidate = json.loads(candidate_bytes.decode("utf-8"))
    candidate_items = candidate.get("files", [])
    inventory_items = inventory.get("files", [])
    expected = {item["path"]: item for item in candidate_items}
    inventory_by_path = {item["path"]: item for item in inventory_items}
    if (candidate.get("model_id") != MODEL_ID or candidate.get("revision") != MODEL_REVISION
            or candidate.get("status") != "UPSTREAM_METADATA_ONLY_NO_WEIGHTS_DOWNLOADED"
            or candidate_sha256 != MODEL_CANDIDATE_SHA256
            or not expected or len(expected) != len(candidate_items)
            or len(inventory_by_path) != len(inventory_items)
            or set(expected) != set(inventory_by_path)):
        raise RuntimeError("pinned model candidate manifest mismatch")
    model_tree = load_pinned_tree_module().PinnedTree(APPROVED_ROOT)
    try:
        actual = model_tree.scan(MODEL_DIR)
        if set(actual) != set(expected):
            raise RuntimeError("pinned local model file set changed")
        verified_files = []
        for relative in sorted(expected):
            record, spec = actual[relative], expected[relative]
            local_spec = inventory_by_path[relative]
            if (record["size_bytes"] != spec.get("size_bytes")
                    or record["size_bytes"] != local_spec.get("size_bytes")
                    or record["git_blob_id"] != spec.get("git_blob_id")
                    or (spec.get("upstream_sha256") is not None
                        and record["sha256"].casefold()
                        != str(spec.get("upstream_sha256", "")).casefold())
                    or record["sha256"].casefold()
                    != str(local_spec.get("sha256", "")).casefold()):
                raise RuntimeError(f"pinned model file identity changed: {relative}")
            verified_files.append({
                "path": relative, "size_bytes": record["size_bytes"],
                "sha256": record["sha256"].casefold(),
            })
        if verified_files != [
            {"path": item["path"], "size_bytes": item["size_bytes"], "sha256": str(item["sha256"]).casefold()}
            for item in inventory.get("files", [])
        ]:
            raise RuntimeError("current model files differ from the run's hash-bound inventory")
        _ACTIVE_PINNED_TREES.append(model_tree)
    except BaseException:
        model_tree.close()
        raise

    adapter_expected = {item["path"]: item for item in run.get("adapter_files", [])}
    adapter_tree = load_pinned_tree_module().PinnedTree(APPROVED_ROOT)
    try:
        adapter_actual = adapter_tree.scan(ADAPTER_DIR)
        if not adapter_expected or set(adapter_actual) != set(adapter_expected):
            raise RuntimeError("adapter file set does not match completed run receipt")
        adapter_bytes = 0
        for relative, record in adapter_actual.items():
            spec = adapter_expected[relative]
            if (record["size_bytes"] != spec.get("size_bytes")
                    or record["sha256"].casefold() != str(spec.get("sha256", "")).casefold()):
                raise RuntimeError(f"adapter file hash mismatch: {relative}")
            adapter_bytes += record["size_bytes"]
        _ACTIVE_PINNED_TREES.append(adapter_tree)
    except BaseException:
        adapter_tree.close()
        raise
    if adapter_bytes != run.get("adapter_total_bytes") or adapter_bytes > 100 * 1024 * 1024:
        raise RuntimeError("adapter aggregate size does not match receipt or cap")

    data_manifest_path = resolve_manifest_path(DATA_ROOT, "manifest.json")
    data_manifest_bytes, data_manifest_sha256 = read_approved_child_bytes(
        data_manifest_path, data_manifest_path.parent, max_bytes=MAX_OUTPUT_BYTES,
    )
    data = json.loads(data_manifest_bytes.decode("utf-8"))
    if (not data.get("synthetic_only")
            or data_manifest_sha256 != DATA_MANIFEST_SHA256
            or data_manifest_sha256 != run.get("dataset_manifest_sha256")
            or data.get("files", {}).get("heldout", {}).get("count") != 128
            or str(data["files"]["heldout"].get("sha256", "")).casefold()
            != str(run.get("heldout_sha256", "")).casefold()):
        raise RuntimeError("sealed dataset manifest identity mismatch")
    if sha256_file(GENERATOR_SOURCE) != data.get("generator_sha256"):
        raise RuntimeError("synthetic corpus generator source hash mismatch")
    split_hashes = {"train": TRAIN_DATA_SHA256, "dev": DEV_DATA_SHA256}
    split_payloads: dict[str, bytes] = {}
    for split, field in (("train", "train_sha256"), ("dev", "dev_sha256")):
        spec = data["files"][split]
        path = resolve_manifest_path(DATA_ROOT, spec["path"])
        payload = read_verified_split_bytes(path, split, spec)
        if (str(spec.get("sha256", "")).casefold() != split_hashes[split]
                or str(run.get(field, "")).casefold() != split_hashes[split]):
            raise RuntimeError(f"training dataset identity mismatch: {split}")
        split_payloads[split] = payload
    return run, inventory, data, training_manifest_sha256, split_payloads


def read_verified_split_bytes(path: Path, expected_name: str,
                              spec: dict[str, Any]) -> bytes:
    """Read one pinned split once through a confined handle and return its bytes."""
    expected_size = spec.get("size_bytes")
    expected_sha256 = str(spec.get("sha256", "")).casefold()
    if (not isinstance(expected_size, int) or isinstance(expected_size, bool)
            or expected_size <= 0 or expected_size > MAX_SPLIT_READ_BYTES
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)):
        raise RuntimeError(f"{expected_name} split has an invalid bounded identity")
    payload, actual_sha256 = read_approved_child_bytes(
        path, path.parent, max_bytes=MAX_SPLIT_READ_BYTES,
    )
    if len(payload) != expected_size or actual_sha256.casefold() != expected_sha256:
        raise RuntimeError(f"{expected_name} split size/hash mismatch")
    return payload


def read_prompt_split(payload: bytes, expected_name: str,
                      spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Project only IDs plus system/user messages from already verified bytes."""
    prompts: list[dict[str, Any]] = []
    for line_no, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        if row.get("schema") != "wrench.gateway_lora_screen_01.synthetic.v1" or row.get("split") != expected_name:
            raise RuntimeError(f"split/schema mismatch at row {line_no}")
        messages = row.get("messages")
        if (not isinstance(messages, list) or len(messages) != 3
                or [item.get("role") for item in messages] != ["system", "user", "assistant"]):
            raise RuntimeError(f"message-shape mismatch at row {line_no}")
        prompts.append({"example_id": row["example_id"], "messages": [
            {"role": item["role"], "content": item["content"]} for item in messages[:2]
        ]})
    if len(prompts) != spec["count"]:
        raise RuntimeError(f"unexpected {expected_name} row count")
    return prompts


def read_references(payload: bytes, expected_name: str,
                    spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Read labels from the exact split bytes after predictions have been sealed."""
    references = []
    for line_no, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        if row.get("schema") != "wrench.gateway_lora_screen_01.synthetic.v1" or row.get("split") != expected_name:
            raise RuntimeError(f"split/schema mismatch at label row {line_no}")
        references.append({"example_id": row["example_id"], "family": row["family"], "gold": row["gold"]})
    if len(references) != spec["count"]:
        raise RuntimeError(f"unexpected {expected_name} reference count")
    return references


def extract_records(user_text: str) -> list[dict[str, Any]]:
    marker = "Records: "
    index = user_text.rfind(marker)
    if index < 0:
        return []
    try:
        value = json.loads(user_text[index + len(marker):])
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) and all(isinstance(item, dict) for item in value) else []


def requested_symbol(user_text: str) -> str | None:
    patterns = (
        r"\bsymbol\s+([A-Za-z][A-Za-z0-9_]*)",
        r"\bevidence is\s+([A-Za-z][A-Za-z0-9_]*)",
        r"\bFor\s+([A-Za-z][A-Za-z0-9_]*)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, user_text)
        if match:
            return match.group(1)
    return None


def decision(route: str, operation: str, ids: list[str], retrieve: bool, reason: str) -> dict[str, Any]:
    return {"route": route, "operation": operation, "selected_evidence_ids": ids,
            "retrieve_more": retrieve, "reason_code": reason}


def deterministic_policy(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Transparent finite policy; its only inputs are system/user prompt bytes."""
    user = messages[-1]["content"]
    records = extract_records(user)
    ids = [str(item.get("id")) for item in records if isinstance(item.get("id"), str)]
    hot = [item["id"] for item in records if item.get("temperature") == "hot" and item.get("recoverable") is True]
    if "Budget:" in user and any("temperature" in item for item in records):
        return decision("LOCAL_COMPACTION", "COMPACT", sorted(hot), False, "PRESERVE_HOT_RETRIEVE_COLD")

    symbol = requested_symbol(user)
    matches = [item for item in records if symbol and item.get("symbol") == symbol]
    if "exact definition" in user.lower() or "source id that proves" in user.lower() or "exact requested symbol" in user.lower():
        current = next((item for item in matches if item.get("state") == "current"), None)
        if current:
            return decision("LOCAL_MECHANICAL", "EXACT_RETRIEVE", [current["id"]], False, "EXACT_CURRENT_MATCH")
        return decision("ABSTAIN", "NOOP", [], True, "EXACT_EVIDENCE_MISSING")

    if "retrieve more or stop" in user.lower() or "request another read" in user.lower() or "choose enough" in user.lower():
        current = next((item for item in matches if item.get("state") == "current"), None)
        if current:
            return decision("LOCAL_MECHANICAL", "NOOP", [current["id"]], False, "ENOUGH_CURRENT_EVIDENCE")
        available = next((item for item in matches if item.get("state") == "available"), None)
        if available:
            return decision("LOCAL_MECHANICAL", "EXACT_RETRIEVE", [available["id"]], True, "REFRESH_STALE_EVIDENCE")
        return decision("ABSTAIN", "NOOP", [], True, "EXACT_EVIDENCE_MISSING")

    if "Diagnose why" in user or "multi-file semantic fix" in user:
        selected = [item["id"] for item in records if item.get("kind") in {"current_source", "failure_log"}]
        return decision("FRONTIER", "NOOP", selected, False, "OPEN_ENDED_ENGINEERING")
    if "No task details" in user or "no current failure evidence" in user:
        return decision("ABSTAIN", "NOOP", [], True, "REQUIREMENTS_OR_EVIDENCE_MISSING")
    if "line count" in user:
        item = next((item for item in records if item.get("kind") == "source_range"), None)
    elif "exact lines" in user:
        item = next((item for item in records if item.get("kind") == "current_source"), None)
    else:
        item = None
    if item:
        return decision("LOCAL_MECHANICAL", "EXACT_RETRIEVE", [item["id"]], False, "BOUNDED_EXACT_OPERATION")
    return decision("ABSTAIN", "NOOP", [], True, "REQUIREMENTS_OR_EVIDENCE_MISSING")


def parse_output(raw: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"valid": False, "parse_error": "INVALID_JSON", "parsed": None, "visible_ids": []}
    records = extract_records(messages[-1]["content"])
    visible_ids = [item["id"] for item in records if isinstance(item.get("id"), str)]
    if not isinstance(parsed, dict):
        return {"valid": False, "parse_error": "NOT_OBJECT", "parsed": None, "visible_ids": visible_ids}
    errors = []
    if set(parsed) != REQUIRED_FIELDS:
        errors.append("FIELD_SET")
    if not isinstance(parsed.get("route"), str) or parsed.get("route") not in ROUTES:
        errors.append("ROUTE_ENUM")
    if not isinstance(parsed.get("operation"), str) or parsed.get("operation") not in OPERATIONS:
        errors.append("OPERATION_ENUM")
    if not isinstance(parsed.get("reason_code"), str) or parsed.get("reason_code") not in REASONS:
        errors.append("REASON_ENUM")
    if not isinstance(parsed.get("retrieve_more"), bool):
        errors.append("RETRIEVE_TYPE")
    selected = parsed.get("selected_evidence_ids")
    if not isinstance(selected, list) or any(not isinstance(item, str) for item in selected):
        errors.append("SOURCE_LIST_TYPE")
        source_list_is_valid = False
    else:
        source_list_is_valid = True
    duplicate_source = source_list_is_valid and len(selected) != len(set(selected))
    if duplicate_source:
        errors.append("DUPLICATE_SOURCE")
    invalid_source = not source_list_is_valid or any(item not in visible_ids for item in selected)
    if invalid_source:
        errors.append("INVALID_SOURCE")
    extra_authority = {str(key).casefold() for key in parsed if str(key).casefold() in AUTHORITY_KEYS}
    return {"valid": not errors, "parse_error": ";".join(errors) if errors else None,
            "parsed": parsed, "visible_ids": visible_ids,
            "invalid_source": invalid_source, "duplicate_source": bool(duplicate_source),
            "authority_violation": bool(extra_authority)}


def prepare_runtime(addons: Path) -> tuple[Any, Any, Any]:
    if addons.is_dir():
        sys.path.insert(0, str(addons))
    require_scratch_budget()
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    import torch
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    torch.set_num_threads(4)
    return torch, PeftModel, (AutoModelForImageTextToText, AutoTokenizer)


def load_base(torch: Any, auto_classes: Any, device: str, dtype_name: str) -> tuple[Any, Any]:
    model_class, tokenizer_class = auto_classes
    require_approved_path(MODEL_DIR)
    if device == "cuda":
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("pinned single CUDA device is unavailable or ambiguous")
        torch.cuda.set_device(0)
        gpu = ResourceMonitor.gpu()
        if torch.cuda.get_device_name(0) != EXPECTED_GPU_NAME or gpu["uuid"] != EXPECTED_GPU_UUID:
            raise RuntimeError("PyTorch model device differs from the pinned monitored GPU")
    dtype = getattr(torch, dtype_name)
    tokenizer = tokenizer_class.from_pretrained(MODEL_DIR, local_files_only=True, trust_remote_code=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = model_class.from_pretrained(
        MODEL_DIR, local_files_only=True, trust_remote_code=False, dtype=dtype,
        low_cpu_mem_usage=True,
    )
    model.to(device)
    model.eval()
    return model, tokenizer


def generate_one(torch: Any, model: Any, tokenizer: Any, messages: list[dict[str, str]], device: str) -> tuple[str, int, int, float, bool]:
    prompt_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    encoded = tokenizer(prompt_text, add_special_tokens=False, return_tensors="pt")
    prompt_tokens = int(encoded["input_ids"].shape[-1])
    encoded = {key: value.to(device) for key, value in encoded.items() if key in {"input_ids", "attention_mask"}}
    started = time.perf_counter()
    with torch.inference_mode():
        result = model.generate(
            **encoded, do_sample=False, num_beams=1, max_new_tokens=MAX_NEW_TOKENS,
            max_time=MAX_GENERATION_SECONDS, use_cache=True, pad_token_id=tokenizer.pad_token_id,
        )
    elapsed = time.perf_counter() - started
    completion_ids = result[0, prompt_tokens:]
    raw = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
    return raw, prompt_tokens, int(completion_ids.numel()), elapsed, elapsed >= MAX_GENERATION_SECONDS


def output_dirs_for(mode: str, job_id: str) -> tuple[Path, Path]:
    artifacts = EVAL_ARTIFACTS / f"{mode}-{job_id}"
    logs = EVAL_LOGS / f"{mode}-{job_id}"
    if (APPROVED_ROOT.resolve() not in artifacts.resolve().parents
            or APPROVED_ROOT.resolve() not in logs.resolve().parents):
        raise RuntimeError("evaluation output escaped approved data root")
    if artifacts.exists() or logs.exists():
        raise RuntimeError(f"refusing to overwrite evaluation output: {artifacts} or {logs}")
    return artifacts, logs


def create_global_heldout_marker(job_id: str, run: dict[str, Any], data: dict[str, Any],
                                 training_manifest_sha256: str) -> None:
    global _ACTIVE_GLOBAL_HELDOUT_MARKER
    if _ACTIVE_GLOBAL_HELDOUT_MARKER is not None:
        raise RuntimeError("this process already owns the global held-out marker")
    payload = canonical_bytes({
        "schema": "wrench.gateway_lora_screen_02.heldout_global_access.v1",
        "status": "ACCESS_STARTED_ONCE", "job_id": job_id, "pid": os.getpid(),
        "model_id": run.get("model_id"), "model_revision": run.get("model_revision"),
        "training_protocol_sha256": run.get("protocol_sha256"),
        "repo_head": git_head(), "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_manifest_sha256": training_manifest_sha256,
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(DATA_ROOT / "manifest.json"),
        "heldout_sha256": data["files"]["heldout"]["sha256"], "time_utc": utc_now(),
    })
    require_live_reservation()
    with _ACTIVE_OUTPUT_BUDGET_LOCK:
        require_output_budget(len(payload))
        opened = open_confined_windows_child_file(
            GLOBAL_HELDOUT_MARKER, access=0xC0000000, disposition=1,
            fd_flags=os.O_RDWR, stream_mode="r+b", share_mode=0x00000001,
        )
        if opened is None:
            raise RuntimeError("global held-out marker could not be created")
        stream, _ = opened
        _ACTIVE_GLOBAL_HELDOUT_MARKER = stream
        try:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            release_global_heldout_marker()
            raise


def run_preflight(args: argparse.Namespace, job: dict[str, Any]) -> int:
    global _ACTIVE_ARTIFACT_DIR, _ACTIVE_LOG_DIR, _ACTIVE_MONITOR
    out, log_out = output_dirs_for("preflight", args.storage_reservation_job_id)
    require_live_reservation()
    out.mkdir(parents=True, exist_ok=False)
    _ACTIVE_ARTIFACT_DIR = out.resolve()
    log_out.mkdir(parents=True, exist_ok=False)
    _ACTIVE_LOG_DIR = log_out.resolve()
    resource_path = log_out / "resources.jsonl"
    require_live_reservation()
    require_output_budget(1)
    resource_path.write_bytes(b"")
    monitor = ResourceMonitor(resource_path)
    _ACTIVE_MONITOR = monitor
    monitor.sample()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    initialize_scratch()
    monitor.start()

    run, inventory, data, training_manifest_sha256, split_payloads = verify_training_and_inputs()
    dev_spec = data["files"]["dev"]
    dev_inputs = read_prompt_split(split_payloads["dev"], "dev", dev_spec)
    messages = dev_inputs[0]["messages"]
    torch, PeftModel, classes = prepare_runtime(ADDON_DIR)
    attempts = []
    choices = []
    preferred = args.device
    if preferred == "auto":
        preferred = "cuda" if torch.cuda.is_available() else "cpu"
    candidates = [preferred]
    if preferred == "cuda":
        candidates.append("cpu")
    for device in candidates:
        dtype = ("bfloat16" if torch.cuda.is_bf16_supported() else "float16") if device == "cuda" else "float32"
        model = tokenizer = adapter_model = None
        try:
            if device == "cuda" and not torch.cuda.is_available():
                raise RuntimeError("CUDA unavailable")
            model, tokenizer = load_base(torch, classes, device, dtype)
            base_raw, prompt_tokens, completion_tokens, elapsed, base_timeout = generate_one(torch, model, tokenizer, messages, device)
            base_check = parse_output(base_raw, messages)
            if base_timeout:
                attempts.append({"device": device, "dtype": dtype, "status": "FAILED",
                                 "stage": "BASE_GENERATION", "error_type": "GENERATION_TIMEOUT",
                                 "base_raw_output": base_raw, "base_valid": base_check["valid"],
                                 "base_prompt_tokens": prompt_tokens, "base_completion_tokens": completion_tokens,
                                 "base_seconds": elapsed, "base_timed_out": True})
                del adapter_model, model, tokenizer
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                if monitor.breach_reason:
                    attempts[-1]["resource_breach_reason"] = monitor.breach_reason
                    raise KeyboardInterrupt(monitor.breach_reason)
                continue
            adapter_model = PeftModel.from_pretrained(model, ADAPTER_DIR, local_files_only=True, is_trainable=False)
            adapter_model.eval()
            verify_pinned_input_trees()
            lora_raw, lora_prompt_tokens, lora_completion_tokens, lora_elapsed, lora_timeout = generate_one(torch, adapter_model, tokenizer, messages, device)
            lora_check = parse_output(lora_raw, messages)
            if lora_timeout:
                attempts.append({"device": device, "dtype": dtype, "status": "FAILED",
                                 "stage": "LORA_GENERATION", "error_type": "GENERATION_TIMEOUT",
                                 "base_raw_output": base_raw, "base_valid": base_check["valid"],
                                 "lora_raw_output": lora_raw, "lora_valid": lora_check["valid"],
                                 "base_prompt_tokens": prompt_tokens, "base_completion_tokens": completion_tokens,
                                 "base_seconds": elapsed, "base_timed_out": False,
                                 "lora_prompt_tokens": lora_prompt_tokens,
                                 "lora_completion_tokens": lora_completion_tokens,
                                 "lora_seconds": lora_elapsed, "lora_timed_out": True})
                del adapter_model, model, tokenizer
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                if monitor.breach_reason:
                    attempts[-1]["resource_breach_reason"] = monitor.breach_reason
                    raise KeyboardInterrupt(monitor.breach_reason)
                continue
            attempts.append({"device": device, "dtype": dtype, "status": "PREFLIGHT_COMPLETED",
                             "base_raw_output": base_raw, "lora_raw_output": lora_raw,
                             "base_valid": base_check["valid"], "lora_valid": lora_check["valid"],
                             "base_prompt_tokens": prompt_tokens, "base_completion_tokens": completion_tokens,
                             "base_seconds": elapsed, "base_timed_out": base_timeout,
                             "lora_prompt_tokens": lora_prompt_tokens,
                             "lora_completion_tokens": lora_completion_tokens, "lora_seconds": lora_elapsed,
                             "lora_timed_out": lora_timeout})
            choices.append((device, dtype))
            del adapter_model
            del model
            break
        except KeyboardInterrupt:
            raise
        except BaseException as exc:
            attempts.append({"device": device, "dtype": dtype, "status": "FAILED",
                             "error_type": type(exc).__name__, "error": str(exc)[:500]})
            del adapter_model, model, tokenizer
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            if monitor.breach_reason:
                raise RuntimeError(monitor.breach_reason) from exc
    monitor.stop_event.set()
    monitor.join(timeout=5)
    if monitor.is_alive() or monitor.breach_reason:
        raise RuntimeError("resource monitor did not stop cleanly")
    require_scratch_budget()
    resource_log_bytes, resource_log_sha256 = read_approved_child_bytes(
        resource_path, log_out, max_bytes=MAX_OUTPUT_BYTES,
    )
    verify_resource_log(
        resource_log_bytes, monitor.summary(),
        scratch_limit_bytes=PREFLIGHT_MAX_SCRATCH_BYTES,
        expected_sha256=resource_log_sha256,
    )
    if not choices:
        receipt = {"schema": "wrench.gateway_lora_screen_02.preflight.v1", "status": "FAILED",
                   "job_id": args.storage_reservation_job_id, "training_manifest_sha256": training_manifest_sha256,
                   "attempts": attempts, "resource_summary": monitor.summary(), "resource_log_sha256": resource_log_sha256}
        write_json(out / "preflight.json", receipt)
        return 2
    selected_device, selected_dtype = choices[0]
    receipt = {
        "schema": "wrench.gateway_lora_screen_02.preflight.v1", "status": "COMPLETED",
        "job_id": args.storage_reservation_job_id, "created_at_utc": utc_now(),
        "repo_head": git_head(),
        "training_manifest_sha256": training_manifest_sha256,
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_protocol_sha256": run["protocol_sha256"],
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(resolve_manifest_path(DATA_ROOT, "manifest.json")),
        "model_inventory_sha256": sha256_file(MODEL_INVENTORY),
        "adapter_files": run["adapter_files"], "device": selected_device, "dtype": selected_dtype,
        "max_new_tokens": MAX_NEW_TOKENS, "decoding": {"do_sample": False, "num_beams": 1},
        "attempts": attempts, "resource_summary": monitor.summary(),
        "resource_log": str(resource_path), "resource_log_sha256": resource_log_sha256,
    }
    require_live_reservation()
    write_json(out / "preflight.json", receipt)
    return 0


def wilson(successes: int, total: int) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": total, "rate": None, "ci95": None}
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return {"successes": successes, "total": total, "rate": p,
            "ci95": [max(0.0, center - margin), min(1.0, center + margin)]}


def records_and_budget(user_text: str) -> tuple[list[dict[str, Any]], int | None]:
    records = extract_records(user_text)
    match = re.search(r"\bBudget:\s*(\d+)\s*tokens\b", user_text)
    return records, int(match.group(1)) if match else None


def bootstrap_ratio(numerators: list[int], denominators: list[int]) -> dict[str, Any]:
    if not numerators or len(numerators) != len(denominators) or sum(denominators) == 0:
        return {"numerator": sum(numerators), "denominator": sum(denominators),
                "rate": None, "case_bootstrap_ci95": None}
    estimate = sum(numerators) / sum(denominators)
    rng = random.Random(20260927)
    draws = []
    for _ in range(10000):
        indices = [rng.randrange(len(numerators)) for _ in numerators]
        denominator = sum(denominators[index] for index in indices)
        draws.append(sum(numerators[index] for index in indices) / denominator if denominator else 0.0)
    draws.sort()
    return {
        "numerator": sum(numerators), "denominator": sum(denominators), "rate": estimate,
        "case_bootstrap_ci95": [draws[int(0.025 * (len(draws) - 1))],
                                 draws[int(0.975 * (len(draws) - 1))]],
        "bootstrap_resamples": len(draws), "seed": 20260927,
    }


def score_context_policy(rows: list[dict[str, Any]], predictions: dict[str, dict[str, Any]], tokenizer: Any) -> dict[str, Any]:
    context_rows = [row for row in rows if row["family"] == "compaction_policy"]
    omission_numerators: list[int] = []
    omission_denominators: list[int] = []
    critical_numerators: list[int] = []
    critical_denominators: list[int] = []
    full_record_tokens: list[int] = []
    projected_saved_tokens: list[int] = []
    safe_saved_tokens: list[int] = []
    preserved_cases = 0
    hot_preserving_compactions = 0
    applied_compactions = 0
    refetch = {
        "all_accepted_compactions": {"attempts": 0, "successes": 0},
        "hot_preserving_compactions": {"attempts": 0, "successes": 0},
        "hot_dropping_compactions": {"attempts": 0, "successes": 0},
    }

    for row in context_rows:
        prediction = predictions[row["example_id"]]
        records, _ = records_and_budget(row["messages"][1]["content"])
        record_by_id = {item["id"]: item for item in records if isinstance(item.get("id"), str)}
        validation = prediction.get("validation", {})
        output = validation.get("parsed")
        completed_valid = (validation.get("valid", False) and not prediction.get("timed_out")
                           and not prediction.get("error"))
        selected_value = output.get("selected_evidence_ids") if isinstance(output, dict) else None
        selected_ids = set(selected_value) if completed_valid and isinstance(selected_value, list) else set()
        hot_ids = {item["id"] for item in records
                   if isinstance(item.get("id"), str) and item.get("temperature") == "hot"}
        is_compaction = (completed_valid and isinstance(output, dict)
                         and output.get("route") == "LOCAL_COMPACTION"
                         and output.get("operation") == "COMPACT"
                         and output.get("retrieve_more") is False
                         and selected_ids <= record_by_id.keys())
        selected_hot = selected_ids & hot_ids if is_compaction else set()
        critical_numerators.append(len(selected_hot))
        critical_denominators.append(len(hot_ids))
        hot_preserved = hot_ids <= selected_ids and is_compaction
        preserved_cases += int(not is_compaction or hot_preserved)
        hot_preserving_compactions += int(is_compaction and hot_preserved)
        omitted = [item for item in records
                   if isinstance(item.get("id"), str) and item["id"] not in selected_ids]
        omission_numerators.append(len(omitted) if is_compaction else 0)
        omission_denominators.append(len(records))

        full_tokens = len(tokenizer.encode(
            json.dumps(records, ensure_ascii=False, sort_keys=True), add_special_tokens=False,
        ))
        kept_records = [item for item in records
                        if isinstance(item.get("id"), str) and item["id"] in selected_ids]
        kept_tokens = len(tokenizer.encode(
            json.dumps(kept_records, ensure_ascii=False, sort_keys=True), add_special_tokens=False,
        ))
        saved = max(0, full_tokens - kept_tokens) if is_compaction else 0
        full_record_tokens.append(full_tokens)
        projected_saved_tokens.append(saved)
        safe_saved_tokens.append(saved if is_compaction and hot_preserved else 0)

        if is_compaction:
            applied_compactions += 1
        if is_compaction:
            compaction_stratum = (
                "hot_preserving_compactions" if hot_preserved else "hot_dropping_compactions"
            )
            for item in omitted:
                if item.get("temperature") != "cold":
                    continue
                refetch["all_accepted_compactions"]["attempts"] += 1
                refetch[compaction_stratum]["attempts"] += 1
                source_id = item.get("id")
                resolved = record_by_id.get(source_id)
                if (item.get("recoverable") is True and resolved is not None
                        and canonical_bytes(resolved) == canonical_bytes(item)):
                    refetch["all_accepted_compactions"]["successes"] += 1
                    refetch[compaction_stratum]["successes"] += 1

    full_total = sum(full_record_tokens)
    return {
        "scope": "synthetic compaction-policy cases only; not actual runtime retrieval or frontier usage",
        "n_cases": len(context_rows),
        "accepted_compaction_actions": applied_compactions,
        "omission_rate": bootstrap_ratio(omission_numerators, omission_denominators),
        "critical_evidence_recall": bootstrap_ratio(critical_numerators, critical_denominators),
        "hot_context_preservation": wilson(preserved_cases, len(context_rows)),
        "hot_preserving_compaction_rate": wilson(hot_preserving_compactions, applied_compactions),
        "unqualified_context_shrink_projection": bootstrap_ratio(projected_saved_tokens, full_record_tokens),
        "credited_hot_preserving_context_token_reduction": bootstrap_ratio(safe_saved_tokens, full_record_tokens),
        "hot_dropping_compaction_actions": applied_compactions - hot_preserving_compactions,
        "full_context_record_tokens": full_total,
        "unqualified_projected_record_tokens_saved": sum(projected_saved_tokens),
        "credited_safe_record_tokens_saved": sum(safe_saved_tokens),
        "simulated_refetch": {
            "attempted_omitted_cold_ids": refetch["all_accepted_compactions"]["attempts"],
            "resolved_to_exact_snapshot_record": refetch["all_accepted_compactions"]["successes"],
            "unresolved": (refetch["all_accepted_compactions"]["attempts"]
                           - refetch["all_accepted_compactions"]["successes"]),
            "by_compaction_safety": {
                name: {
                    "attempted_omitted_cold_ids": counts["attempts"],
                    "resolved_to_exact_snapshot_record": counts["successes"],
                    "unresolved": counts["attempts"] - counts["successes"],
                }
                for name, counts in refetch.items()
                if name != "all_accepted_compactions"
            },
        },
    }


def score_arm(rows: list[dict[str, Any]], predictions: dict[str, dict[str, Any]], tokenizer: Any) -> dict[str, Any]:
    n = len(rows)
    exact = valid = route_correct = invalid_source = duplicate_source = source_exact = authority = truncated = 0
    timeouts = 0
    over_budget = budget_cases = 0
    route_counts = {name: 0 for name in [*sorted(ROUTES), "INVALID", "TIMEOUT", "ERROR"]}
    family_bins: dict[str, list[int]] = {}
    failures = []
    local_input_tokens = local_output_tokens = 0
    for row in rows:
        case = row["example_id"]
        record = predictions[case]
        local_input_tokens += record.get("prompt_tokens", 0)
        local_output_tokens += record.get("completion_tokens", 0)
        truncated += int(record.get("completion_tokens") == MAX_NEW_TOKENS)
        parsed = record.get("validation", {})
        value = parsed.get("parsed")
        gold = row["gold"]
        timed_out = bool(record.get("timed_out", False))
        errored = bool(record.get("error"))
        timeouts += int(timed_out)
        completed_valid = parsed.get("valid", False) and not timed_out and not errored
        valid += int(completed_valid)
        exact += int(completed_valid and value == gold)
        route = value.get("route") if isinstance(value, dict) else None
        route_category = "TIMEOUT" if timed_out else "ERROR" if errored else route if isinstance(route, str) and route in ROUTES else "INVALID"
        route_counts[route_category] += 1
        route_correct += int(completed_valid and route == gold.get("route"))
        visible = parsed.get("visible_ids", [])
        selected = value.get("selected_evidence_ids", []) if isinstance(value, dict) else []
        if not isinstance(selected, list) or any(not isinstance(item, str) for item in selected):
            selected = []
        invalid_source += int(parsed.get("invalid_source", any(item not in visible for item in selected)))
        duplicate_source += int(parsed.get("duplicate_source", False))
        source_exact += int(completed_valid and selected == gold.get("selected_evidence_ids"))
        authority += int(parsed.get("authority_violation", False))
        records, budget = records_and_budget(row["messages"][1]["content"])
        if budget is not None:
            budget_cases += 1
            record_by_id = {item.get("id"): item for item in records}
            chosen = [record_by_id[item] for item in selected if item in record_by_id]
            tokens = sum(len(tokenizer.encode(json.dumps(item, ensure_ascii=False, sort_keys=True), add_special_tokens=False)) for item in chosen)
            over_budget += int(tokens > budget)
        bin_ = family_bins.setdefault(row["family"], [0, 0])
        bin_[0] += int(completed_valid and value == gold)
        bin_[1] += 1
        if record.get("error"):
            failures.append({"example_id": case, "error": record["error"]})
        elif timed_out:
            failures.append({"example_id": case, "error": "GENERATION_TIMEOUT"})
        elif not parsed.get("valid", False):
            failures.append({"example_id": case, "error": parsed.get("parse_error") or "INVALID_OUTPUT"})
        elif not (completed_valid and value == gold):
            failures.append({"example_id": case, "error": "DECISION_MISMATCH",
                             "expected": gold, "predicted": value})
    return {
        "n": n,
        "exact_decision_accuracy": wilson(exact, n),
        "strict_valid_output_rate": wilson(valid, n),
        "route_accuracy": wilson(route_correct, n),
        "route_counts": route_counts,
        "invalid_source_rate": wilson(invalid_source, n),
        "duplicate_source_rate": wilson(duplicate_source, n),
        "exact_selected_source_rate": wilson(source_exact, n),
        "authority_violation_rate": wilson(authority, n),
        "over_budget_rate": wilson(over_budget, budget_cases),
        "over_budget_applicable_n": budget_cases,
        "generation_limit_hit_rate": wilson(truncated, n),
        "timeout_rate": wilson(timeouts, n),
        "by_family": {key: wilson(value[0], value[1]) for key, value in sorted(family_bins.items())},
        "local_prompt_tokens": local_input_tokens,
        "local_completion_tokens": local_output_tokens,
        "local_total_tokens": local_input_tokens + local_output_tokens,
        "context_policy": score_context_policy(rows, predictions, tokenizer),
        "failures": failures,
    }


def paired_bootstrap(rows: list[dict[str, Any]], base: dict[str, dict[str, Any]], lora: dict[str, dict[str, Any]]) -> dict[str, Any]:
    diffs = []
    for row in rows:
        case = row["example_id"]
        gold = row["gold"]
        base_valid = base[case].get("validation", {}).get("valid", False) and not base[case].get("timed_out") and not base[case].get("error")
        lora_valid = lora[case].get("validation", {}).get("valid", False) and not lora[case].get("timed_out") and not lora[case].get("error")
        b = base[case].get("validation", {}).get("parsed")
        l = lora[case].get("validation", {}).get("parsed")
        diffs.append(int(lora_valid and l == gold) - int(base_valid and b == gold))
    rng = random.Random(20260927)
    draws = []
    for _ in range(10000):
        draws.append(sum(diffs[rng.randrange(len(diffs))] for _ in diffs) / len(diffs))
    draws.sort()
    return {"mean_paired_accuracy_difference": sum(diffs) / len(diffs),
            "bootstrap_ci95": [draws[int(0.025 * (len(draws) - 1))], draws[int(0.975 * (len(draws) - 1))]],
            "bootstrap_resamples": len(draws), "seed": 20260927}


def run_score(args: argparse.Namespace, job: dict[str, Any]) -> int:
    global _ACTIVE_ARTIFACT_DIR, _ACTIVE_LOG_DIR, _ACTIVE_HELDOUT_LOCK, _ACTIVE_MONITOR
    if _ACTIVE_HELDOUT_LOCK is not None:
        raise RuntimeError("this process already owns a held-out scoring lock")
    out, log_out = output_dirs_for("heldout", args.storage_reservation_job_id)
    require_live_reservation()
    out.mkdir(parents=True, exist_ok=False)
    _ACTIVE_ARTIFACT_DIR = out.resolve()
    log_out.mkdir(parents=True, exist_ok=False)
    _ACTIVE_LOG_DIR = log_out.resolve()
    resource_path = log_out / "resources.jsonl"
    require_live_reservation()
    require_output_budget(1)
    resource_path.write_bytes(b"")
    monitor = ResourceMonitor(resource_path)
    _ACTIVE_MONITOR = monitor
    monitor.sample()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    initialize_scratch()
    monitor.start()
    started = time.perf_counter()

    if sha256_approved_child(
        GLOBAL_HELDOUT_MARKER, EVAL_ARTIFACTS, allow_missing=True,
    ) is not None:
        raise RuntimeError("the global sealed held-out split already has an access claim")
    heldout_lock = HeldoutRunLock(GLOBAL_HELDOUT_LOCK, args.storage_reservation_job_id)
    heldout_lock.acquire()
    _ACTIVE_HELDOUT_LOCK = heldout_lock
    if sha256_approved_child(
        GLOBAL_HELDOUT_MARKER, EVAL_ARTIFACTS, allow_missing=True,
    ) is not None:
        raise RuntimeError("the global sealed held-out split already has an access claim")

    run, inventory, data, training_manifest_sha256, split_payloads = verify_training_and_inputs()
    preflight_path = Path(os.path.abspath(args.preflight_receipt))
    eval_artifacts_root = EVAL_ARTIFACTS.resolve(strict=True)
    if not preflight_path.is_relative_to(eval_artifacts_root):
        raise RuntimeError("preflight receipt must be under the approved evaluation artifact root")
    preflight_bytes, preflight_receipt_sha256 = read_approved_child_bytes(
        preflight_path, preflight_path.parent, max_bytes=MAX_OUTPUT_BYTES,
    )
    preflight = json.loads(preflight_bytes.decode("utf-8"))
    if not isinstance(preflight, dict):
        raise RuntimeError("preflight receipt must be a JSON object")
    preflight_job_id = preflight.get("job_id")
    if not isinstance(preflight_job_id, str) or not re.fullmatch(
            re.escape(PREFLIGHT_JOB_PREFIX) + r"[0-9]{2}", preflight_job_id):
        raise RuntimeError("preflight receipt has an invalid job ID")
    expected_preflight_receipt = EVAL_ARTIFACTS / f"preflight-{preflight_job_id}" / "preflight.json"
    if Path(os.path.abspath(preflight_path)) != Path(os.path.abspath(expected_preflight_receipt)):
        raise RuntimeError("preflight receipt path differs from its bound job ID")
    if (preflight.get("schema") != "wrench.gateway_lora_screen_02.preflight.v1"
            or preflight.get("status") != "COMPLETED"
            or not isinstance(preflight.get("job_id"), str)
            or not re.fullmatch(re.escape(PREFLIGHT_JOB_PREFIX) + r"[0-9]{2}", preflight.get("job_id", ""))
            or preflight.get("repo_head") != git_head()
            or preflight.get("training_manifest_sha256") != training_manifest_sha256
            or preflight.get("evaluator_sha256") != sha256_file(EVALUATOR_SOURCE)
            or preflight.get("training_protocol_sha256") != run.get("protocol_sha256")
            or preflight.get("eval_protocol_sha256") != sha256_file(EVAL_PROTOCOL)
            or preflight.get("dataset_manifest_sha256") != sha256_file(resolve_manifest_path(DATA_ROOT, "manifest.json"))
            or preflight.get("model_inventory_sha256") != sha256_file(MODEL_INVENTORY)
            or preflight.get("adapter_files") != run.get("adapter_files")
            or preflight.get("device") not in {"cpu", "cuda"}
            or preflight.get("dtype") not in {"float32", "bfloat16", "float16"}
            or preflight.get("max_new_tokens") != MAX_NEW_TOKENS
            or preflight.get("resource_summary", {}).get("runtime_scratch_limit_bytes")
            != PREFLIGHT_MAX_SCRATCH_BYTES
            or preflight.get("resource_summary", {}).get("runtime_scratch_peak_bytes",
                                                            PREFLIGHT_MAX_SCRATCH_BYTES + 1)
            > PREFLIGHT_MAX_SCRATCH_BYTES
            or preflight.get("decoding") != {"do_sample": False, "num_beams": 1}):
        raise RuntimeError("device/dtype preflight receipt identity mismatch")
    preflight_log = EVAL_LOGS / f"preflight-{preflight['job_id']}" / "resources.jsonl"
    declared_preflight_log = Path(preflight.get("resource_log", ""))
    if Path(os.path.abspath(declared_preflight_log)) != Path(os.path.abspath(preflight_log)):
        raise RuntimeError("preflight resource log path differs from its bound job ID")
    preflight_log_bytes, preflight_log_sha256 = read_approved_child_bytes(
        preflight_log, preflight_log.parent, max_bytes=MAX_OUTPUT_BYTES,
    )
    if preflight_log_sha256 != preflight.get("resource_log_sha256"):
        raise RuntimeError("preflight resource log hash does not match its receipt")
    resource_summary = preflight.get("resource_summary", {})
    verify_resource_log(
        preflight_log_bytes, resource_summary,
        scratch_limit_bytes=PREFLIGHT_MAX_SCRATCH_BYTES,
        expected_sha256=preflight_log_sha256,
    )
    if (resource_summary.get("minimum_ram_free_fraction", 0) < RAM_FLOOR
            or resource_summary.get("minimum_gpu_free_fraction", 0) < VRAM_FLOOR
            or resource_summary.get("runtime_scratch_limit_bytes") != PREFLIGHT_MAX_SCRATCH_BYTES
            or resource_summary.get("runtime_scratch_peak_bytes", PREFLIGHT_MAX_SCRATCH_BYTES + 1)
            > PREFLIGHT_MAX_SCRATCH_BYTES
            or resource_summary.get("breach_reason") is not None):
        raise RuntimeError("preflight did not maintain the 10% system resource reserves")

    if EVAL_ARTIFACTS.exists():
        prior_attempts = [path for path in EVAL_ARTIFACTS.glob("heldout-*")
                          if (path / "heldout-access.started.json").is_file()]
        if prior_attempts:
            raise RuntimeError("the sealed held-out split already has a recorded scoring attempt")
    heldout_spec = data["files"]["heldout"]
    heldout_path = resolve_manifest_path(DATA_ROOT, heldout_spec["path"])

    # Load both model arms under monitoring before consuming the held-out file.
    torch, PeftModel, classes = prepare_runtime(ADDON_DIR)
    device, dtype = preflight["device"], preflight["dtype"]
    model, tokenizer = load_base(torch, classes, device, dtype)
    template_hash = hashlib.sha256(str(tokenizer.chat_template).encode("utf-8")).hexdigest()
    if template_hash != run.get("chat_template_sha256"):
        raise RuntimeError("chat template hash differs from training receipt")
    adapted = PeftModel.from_pretrained(model, ADAPTER_DIR, local_files_only=True, is_trainable=False)
    adapted.eval()
    verify_pinned_input_trees()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)

    require_live_reservation()
    create_global_heldout_marker(
        args.storage_reservation_job_id, run, data, training_manifest_sha256,
    )
    write_json(out / "heldout-access.started.json", {
        "schema": "wrench.gateway_lora_screen_02.heldout_access.v1",
        "status": "ACCESS_STARTED_ONCE", "job_id": args.storage_reservation_job_id,
        "repo_head": git_head(),
        "training_manifest_sha256": training_manifest_sha256,
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "global_marker_sha256": required_sha256_approved_child(
            GLOBAL_HELDOUT_MARKER, EVAL_ARTIFACTS,
        ),
        "preflight_receipt_sha256": preflight_receipt_sha256,
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL), "time_utc": utc_now(),
    })

    # This is the first operation in the scorer that opens sealed examples.
    heldout_bytes = read_verified_split_bytes(heldout_path, "heldout", heldout_spec)
    inputs = read_prompt_split(heldout_bytes, "heldout", heldout_spec)
    expected_ids = [item["example_id"] for item in inputs]
    if len(set(expected_ids)) != len(expected_ids):
        raise RuntimeError("duplicate evaluation example IDs")

    predictions: dict[str, dict[str, dict[str, Any]]] = {"deterministic": {}, "base": {}, "lora": {}}
    for item in inputs:
        if monitor.breach_reason:
            raise RuntimeError(monitor.breach_reason)
        raw_obj = deterministic_policy(item["messages"])
        raw = json.dumps(raw_obj, ensure_ascii=False, sort_keys=True)
        parsed = parse_output(raw, item["messages"])
        prompt_text = tokenizer.apply_chat_template(item["messages"], tokenize=False, add_generation_prompt=True)
        prompt_tokens = len(tokenizer(prompt_text, add_special_tokens=False)["input_ids"])
        completion_tokens = len(tokenizer.encode(raw, add_special_tokens=False))
        predictions["deterministic"][item["example_id"]] = {
            "raw_output": raw, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
            "elapsed_seconds": 0.0, "timed_out": False, "validation": parsed,
        }

    deterministic_path = out / "deterministic-predictions.jsonl"
    require_live_reservation()
    require_output_budget(1)
    with deterministic_path.open("xb") as stream:
        for item in inputs:
            value = predictions["deterministic"][item["example_id"]]
            value["example_id"] = item["example_id"]
            value["input_sha256"] = hashlib.sha256(canonical_bytes(item["messages"])).hexdigest()
            line = canonical_bytes(value)
            if deterministic_path.stat().st_size + len(line) > MAX_OUTPUT_BYTES:
                raise RuntimeError("prediction file byte cap exceeded: deterministic-predictions.jsonl")
            require_live_reservation()
            with _ACTIVE_OUTPUT_BUDGET_LOCK:
                require_output_budget(len(line))
                stream.write(line)
                stream.flush()

    def run_arm(arm: str, active_model: Any) -> None:
        path = out / f"{arm}-predictions.jsonl"
        require_live_reservation()
        require_output_budget(1)
        with path.open("xb") as stream:
            for item in inputs:
                if monitor.breach_reason:
                    raise RuntimeError(monitor.breach_reason)
                started_one = time.perf_counter()
                try:
                    raw, prompt_tokens, completion_tokens, elapsed, timed_out = generate_one(
                        torch, active_model, tokenizer, item["messages"], device,
                    )
                    error = None
                except Exception as exc:
                    raw, prompt_tokens, completion_tokens = "", 0, 0
                    elapsed, timed_out, error = time.perf_counter() - started_one, False, f"{type(exc).__name__}:{str(exc)[:500]}"
                parsed = parse_output(raw, item["messages"])
                value = {
                    "example_id": item["example_id"],
                    "input_sha256": hashlib.sha256(canonical_bytes(item["messages"])).hexdigest(),
                    "raw_output": raw, "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens, "elapsed_seconds": elapsed,
                    "timed_out": timed_out, "error": error, "validation": parsed,
                }
                line = canonical_bytes(value)
                if path.stat().st_size + len(line) > MAX_OUTPUT_BYTES:
                    raise RuntimeError(f"prediction file byte cap exceeded: {path.name}")
                require_live_reservation()
                with _ACTIVE_OUTPUT_BUDGET_LOCK:
                    require_output_budget(len(line))
                    stream.write(line)
                    stream.flush()
                predictions[arm][item["example_id"]] = value
                if monitor.breach_reason:
                    raise RuntimeError(monitor.breach_reason)

    # PEFT installs adapter layers into the supplied base model in-place. Keep
    # one model resident, but explicitly disable those layers for the base arm.
    with adapted.disable_adapter():
        run_arm("base", adapted)
    run_arm("lora", adapted)
    del adapted
    del model

    # Seal every prediction file before joining any family/gold reference.
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    prediction_hashes = {path.name: sha256_file(path) for path in sorted(out.glob("*-predictions.jsonl"))}
    # Re-open labels only after all arms are written and their hashes are sealed.
    reference_rows = read_references(heldout_bytes, "heldout", heldout_spec)
    references = {row["example_id"]: {"family": row["family"], "gold": row["gold"]} for row in reference_rows}
    summary = {}
    scored_rows = []
    for item in inputs:
        reference = references[item["example_id"]]
        scored_rows.append({"example_id": item["example_id"], "family": reference["family"],
                            "gold": reference["gold"], "messages": item["messages"]})
    for arm in ("deterministic", "base", "lora"):
        summary[arm] = score_arm(scored_rows, predictions[arm], tokenizer)
        summary[arm]["token_count_basis"] = (
            "tokenizer-equivalent counts only; deterministic arm runs no language model"
            if arm == "deterministic" else "measured model prompt and generated tokens"
        )
    paired = paired_bootstrap(scored_rows, predictions["base"], predictions["lora"])
    monitor.stop_event.set()
    monitor.join(timeout=5)
    if monitor.is_alive() or monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason or "resource monitor did not stop cleanly")
    require_scratch_budget()
    resource_log_bytes, resource_log_sha256 = read_approved_child_bytes(
        resource_path, log_out, max_bytes=MAX_OUTPUT_BYTES,
    )
    verify_resource_log(
        resource_log_bytes, monitor.summary(),
        scratch_limit_bytes=HELDOUT_MAX_SCRATCH_BYTES,
        expected_sha256=resource_log_sha256,
    )
    result = {
        "schema": "wrench.gateway_lora_screen_02.heldout_result.v1",
        "status": "COMPLETED_DIAGNOSTIC_ONLY", "job_id": args.storage_reservation_job_id,
        "created_at_utc": utc_now(), "repo_head": git_head(), "training_job_id": TRAIN_JOB_ID,
        "training_manifest_sha256": training_manifest_sha256,
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_resource_log_sha256": run["resource_log_sha256"],
        "training_protocol_sha256": run["protocol_sha256"],
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(resolve_manifest_path(DATA_ROOT, "manifest.json")),
        "heldout_sha256": heldout_spec["sha256"], "model_inventory_sha256": sha256_file(MODEL_INVENTORY),
        "heldout_access_marker_sha256": sha256_file(out / "heldout-access.started.json"),
        "global_heldout_access_marker_sha256": required_sha256_approved_child(
            GLOBAL_HELDOUT_MARKER, EVAL_ARTIFACTS,
        ),
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION,
        "adapter_files": run["adapter_files"], "chat_template_sha256": template_hash,
        "device": device, "dtype": dtype, "runtime": {
            "python": sys.version, "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "peft": __import__("peft").__version__,
        },
        "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS},
        "n": len(expected_ids), "arms": summary, "paired_base_vs_lora": paired,
        "prediction_files": prediction_hashes, "resource_log": str(resource_path),
        "resource_log_sha256": resource_log_sha256, "resource_summary": monitor.summary(),
        "limitations": [
            "synthetic policy diagnostic only; not representative engineering workload",
            "deterministic-arm token counts are tokenizer-equivalent and are not model usage",
            "predicted route share is not real local task completion or frontier call usage",
            "does not establish 95/5/95, token savings, dollar savings, or all-day engineering",
            "the corpus has a frozen 104/8/16 local/frontier/abstain label mix",
        ],
        "elapsed_seconds": time.perf_counter() - started,
    }
    require_live_reservation()
    write_json(out / "result.json", result)
    release_global_heldout_marker()
    release_heldout_lock()
    return 0


def write_failure_receipt(args: argparse.Namespace, exc: BaseException) -> None:
    global _ACTIVE_ARTIFACT_DIR
    monitor = _ACTIVE_MONITOR
    if monitor is not None:
        monitor.stop_event.set()
        if monitor.ident is not None:
            monitor.join(timeout=5)
    out = EVAL_ARTIFACTS / f"{args.mode}-{args.storage_reservation_job_id}"
    root = EVAL_ARTIFACTS.resolve()
    resolved_out = out.resolve()
    if (root not in resolved_out.parents or not resolved_out.is_dir()
            or _ACTIVE_ARTIFACT_DIR is None or resolved_out != _ACTIVE_ARTIFACT_DIR):
        return
    failure_path = resolved_out / "failure.json"
    if failure_path.exists():
        return
    marker = resolved_out / "heldout-access.started.json"
    resource_path = EVAL_LOGS / f"{args.mode}-{args.storage_reservation_job_id}" / "resources.jsonl"
    resource = None
    try:
        resource_bytes, resource_sha256 = read_approved_child_bytes(
            resource_path, resource_path.parent, max_bytes=MAX_OUTPUT_BYTES,
        )
        resource = {"path": str(resource_path), "size_bytes": len(resource_bytes),
                    "sha256": resource_sha256,
                    "monitor_stopped": monitor is None or not monitor.is_alive()}
    except (OSError, RuntimeError, ValueError) as resource_error:
        resource = {"path": str(resource_path),
                    "read_error": f"{type(resource_error).__name__}:{str(resource_error)[:300]}",
                    "monitor_stopped": monitor is None or not monitor.is_alive()}
    local_marker_sha256 = sha256_approved_child(
        marker, resolved_out, allow_missing=True,
    )
    global_marker_sha256 = sha256_approved_child(
        GLOBAL_HELDOUT_MARKER, EVAL_ARTIFACTS, allow_missing=True,
    )
    write_json(failure_path, {
        "schema": "wrench.gateway_lora_screen_02.failure.v1",
        "status": "FAILED",
        "mode": args.mode,
        "job_id": args.storage_reservation_job_id,
        "time_utc": utc_now(),
        "repo_head": git_head(),
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "heldout_access_started": local_marker_sha256 is not None,
        "heldout_access_marker_sha256": local_marker_sha256,
        "global_heldout_access_claimed": global_marker_sha256 is not None,
        "global_heldout_access_marker_sha256": global_marker_sha256,
        "resource_log": resource,
        "resource_breach_reason": monitor.breach_reason if monitor is not None else None,
        "error_type": type(exc).__name__,
        "error": str(exc)[:1000],
    })


def main() -> int:
    global _ACTIVE_RESERVATION, _ACTIVE_SCRATCH_ROOT, _ACTIVE_SCRATCH_LIMIT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "score-heldout"), required=True)
    parser.add_argument("--storage-reservation-job-id", required=True)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--preflight-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "score-heldout" and args.preflight_receipt is None:
        parser.error("--preflight-receipt is required for score-heldout")
    job = require_storage_reservation(args.storage_reservation_job_id, args.mode)
    for path in (DATA_ROOT, MODEL_DIR, MODEL_INVENTORY, TRAIN_MANIFEST,
                 TRAIN_SOURCE_SNAPSHOT, ADAPTER_DIR, ADDON_DIR,
                 TRAIN_LOG_DIR, EVAL_ARTIFACTS, EVAL_LOGS):
        try:
            require_approved_path(path)
        except RuntimeError as exc:
            raise SystemExit(f"required Wrench path escaped approved storage: {exc}") from exc
    _ACTIVE_RESERVATION = job
    _ACTIVE_SCRATCH_ROOT = APPROVED_ROOT / "cache/gateway-screen-02" / args.storage_reservation_job_id
    _ACTIVE_SCRATCH_LIMIT = (
        PREFLIGHT_MAX_SCRATCH_BYTES if args.mode == "preflight" else HELDOUT_MAX_SCRATCH_BYTES
    )
    require_approved_path(_ACTIVE_SCRATCH_ROOT)
    if _ACTIVE_SCRATCH_ROOT.exists():
        raise SystemExit("this evaluation job ID already has a scratch directory")
    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices not in (None, "", EXPECTED_GPU_UUID):
        raise SystemExit("CUDA_VISIBLE_DEVICES conflicts with the pinned screen-02 GPU UUID")
    os.environ["CUDA_VISIBLE_DEVICES"] = EXPECTED_GPU_UUID
    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    # Output directories are created only after identities and reservations pass.
    if not all(path.is_dir() for path in (APPROVED_ROOT, DATA_ROOT, MODEL_DIR)):
        raise SystemExit("an approved root or required local input is missing")
    os.environ["HF_HOME"] = str(_ACTIVE_SCRATCH_ROOT / "huggingface")
    os.environ["HF_HUB_CACHE"] = str(_ACTIVE_SCRATCH_ROOT / "huggingface/hub")
    os.environ["HF_ASSETS_CACHE"] = str(_ACTIVE_SCRATCH_ROOT / "huggingface/assets")
    os.environ["HF_DATASETS_CACHE"] = str(_ACTIVE_SCRATCH_ROOT / "huggingface/datasets")
    os.environ["TRANSFORMERS_CACHE"] = str(_ACTIVE_SCRATCH_ROOT / "huggingface/transformers")
    os.environ["TORCH_HOME"] = str(_ACTIVE_SCRATCH_ROOT / "torch")
    os.environ["XDG_CACHE_HOME"] = str(_ACTIVE_SCRATCH_ROOT / "xdg")
    os.environ["TEMP"] = str(_ACTIVE_SCRATCH_ROOT / "tmp")
    os.environ["TMP"] = os.environ["TEMP"]
    os.environ["TMPDIR"] = os.environ["TEMP"]
    os.environ["TORCH_EXTENSIONS_DIR"] = str(_ACTIVE_SCRATCH_ROOT / "torch-extensions")
    os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(_ACTIVE_SCRATCH_ROOT / "torch-inductor")
    os.environ["TRITON_CACHE_DIR"] = str(_ACTIVE_SCRATCH_ROOT / "triton")
    os.environ["CUDA_CACHE_PATH"] = str(_ACTIVE_SCRATCH_ROOT / "cuda")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    try:
        if args.mode == "preflight":
            return run_preflight(args, job)
        return run_score(args, job)
    except BaseException as exc:
        try:
            write_failure_receipt(args, exc)
        except BaseException as receipt_error:
            sys.stderr.write(f"Could not write failure receipt: {type(receipt_error).__name__}: {str(receipt_error)[:500]}\n")
        finally:
            release_global_heldout_marker()
            release_heldout_lock()
        raise
    finally:
        monitor = _ACTIVE_MONITOR
        if monitor is not None:
            monitor.stop_event.set()
            if monitor.ident is not None:
                monitor.join(timeout=30)
        while _ACTIVE_PINNED_TREES:
            _ACTIVE_PINNED_TREES.pop().close()
        if (_ACTIVE_SCRATCH_TREE is not None
                and (monitor is None or not monitor.is_alive())):
            _ACTIVE_SCRATCH_TREE.close()


if __name__ == "__main__":
    raise SystemExit(main())
