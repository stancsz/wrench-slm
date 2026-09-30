"""Run the separately pinned offline Qwen3.5-2B BF16 Wrench LoRA screen.

Only text q/k/v/o projections in the six config-pinned full-attention layers
are adapted. The runner reads synthetic train/dev only, never heldout, requires
an exact successful one-step preflight for fit, and leaves the candidate
adapter inactive. It grants no shell, tool, credential, or mutation authority.
"""

from __future__ import annotations

import argparse
import _thread
import ctypes
import hashlib
import json
import os
import random
import shutil
import stat
import subprocess
import sys
import threading
import time
import types
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


DATA_ROOT = Path(r"C:\wrench-slm-data\datasets\wrench-gateway-model-research\lora-screen-01")
MODEL_DIR = Path(r"C:\wrench-slm-data\weights\Qwen3.5-2B")
INVENTORY = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research\qwen35-2b-local-inventory-iter145.json")
MODEL_CANDIDATE = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research\qwen35-2b-candidate-manifest-iter145.json")
MODEL_CONFIG = MODEL_DIR / "config.json"
MODEL_INDEX = MODEL_DIR / "model.safetensors.index.json"
MODEL_LICENSE = MODEL_DIR / "LICENSE"
APPROVED_ROOT = Path(r"C:\wrench-slm-data")
FIT_ATTEMPT_DIR = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-04-qwen35-2b\fit-03")
OUTPUT = FIT_ATTEMPT_DIR / "adapter"
STAGING_OUTPUT = OUTPUT.parent / "adapter-staging"
RUNNER_SNAPSHOT = FIT_ATTEMPT_DIR / "train_gateway_lora_screen_04_2b_gpu.py"
LOG_ROOT = Path(r"C:\wrench-slm-data\logs\wrench-gateway-model-research")
LOG_DIR = LOG_ROOT / "lora-screen-04-qwen35-2b-fit-03"
PROTOCOL = Path("docs/evals/wrench-gateway-model-research/lora-screen-04-qwen35-2b-gpu-protocol-20260929-preflight03.md")
PREFLIGHT_LOG_DIR = LOG_ROOT / "lora-screen-04-qwen35-2b-preflight-03"
PREFLIGHT_MANIFEST = PREFLIGHT_LOG_DIR / "run-manifest.json"
PREFLIGHT_JOB_ID = "WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-PREFLIGHT-20260929-03"
JOB_CLAIM_ROOT = APPROVED_ROOT / "cache/gateway-lora-screen-04-2b-claims"
FIT_JOB_ID = "WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-FIT-20260929-03"
PREFLIGHT_MIN_RESERVATION_BYTES = 250_000_000
FIT_MIN_RESERVATION_BYTES = 2_000_000_000
PREFLIGHT_MAX_SCRATCH_BYTES = 256 * 1024 * 1024
FIT_MAX_SCRATCH_BYTES = 512 * 1024 * 1024
FIT_START_RAM_FREE_FRACTION = 0.25
MIN_DESTINATION_HEADROOM_BYTES = 5 * 1024 * 1024 * 1024
EXPECTED_REVISION = "15852e8c16360a2fea060d615a32b45270f8a8fc"
EXPECTED_MODEL_ID = "Qwen/Qwen3.5-2B"
EXPECTED_GPU_UUID = "GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021"
EXPECTED_GPU_NAME = "NVIDIA GeForce RTX 5060 Ti"
EXPECTED_PYTHON_EXECUTABLE = Path(
    r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe"
)
EXPECTED_PYTHON_VERSION = (3, 13, 15)
EXPECTED_ADDONS_DIR = Path(r"C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons")
EXPECTED_PACKAGE_VERSIONS = {
    "torch_version": "2.14.0+cu132",
    "transformers_version": "5.17.0",
    "peft_version": "0.21.0",
    "accelerate_version": "1.15.0",
}
MODEL_INVENTORY_SHA256 = "23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5"
MODEL_CANDIDATE_SHA256 = "d4917ef337978b93d2220a9888cb4f640edb63e54c8e49f70f0696b175dd2956"
MODEL_CONFIG_SHA256 = "ed1c1723241f23f7f4e23430759cbd7dcfb4103cbdfe052bfe7626b57c2615b4"
MODEL_INDEX_SHA256 = "aca8afed9da75b0f050b408d270766fd77627f1af401e240f61c3b47d0db02f9"
MODEL_LICENSE_SHA256 = "bbedc3fda3305820b977265f01b8619d87570a6739de3a5582c3464840f1e57a"
DATA_MANIFEST_SHA256 = "11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed"
TRAIN_DATA_SHA256 = "22f45c8b51ef680f9d05e8c42243ebb34e9f596b22d76577c64e371d272a39d2"
DEV_DATA_SHA256 = "ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7"
EXPECTED_FAMILIES = {"evidence_select", "retrieve_stop", "compaction_policy", "route"}
ATTENTION_TARGET_SUFFIXES = {"q_proj", "k_proj", "v_proj", "o_proj"}
EXPECTED_FULL_ATTENTION_LAYER_INDEXES = (3, 7, 11, 15, 19, 23)
EXPECTED_TEXT_LAYER_COUNT = 24
EXPECTED_HIDDEN_SIZE = 2048
EXPECTED_ATTENTION_HEADS = 8
EXPECTED_KEY_VALUE_HEADS = 2
EXPECTED_HEAD_DIM = 256
ADAPTER_PROFILES = {
    "full-attention-qkvo": {
        "target_suffixes": ATTENTION_TARGET_SUFFIXES,
        "attention_parent_only": True,
        "expected_target_count": 24,
        "preflight_job_id": PREFLIGHT_JOB_ID,
        "preflight_log_dir": PREFLIGHT_LOG_DIR,
        "preflight_manifest": PREFLIGHT_MANIFEST,
    },
}
MAX_SEQUENCE_LENGTH = 512
MAX_DATA_SPLIT_BYTES = 64 * 1024 * 1024
EPOCHS = 3
GRAD_ACCUMULATION = 8
EXPECTED_TRAIN_EXAMPLES = 256
EXPECTED_FIT_OPTIMIZER_STEPS = (EXPECTED_TRAIN_EXAMPLES // GRAD_ACCUMULATION) * EPOCHS
LEARNING_RATE = 2e-4
MAX_ADAPTER_BYTES = 100 * 1024 * 1024
MAX_LOG_BYTES = 20 * 1024 * 1024
RAM_FREE_FRACTION = 0.10
VRAM_FREE_FRACTION = 0.10
PINNED_TREE_SOURCE = Path(__file__).resolve().with_name("wrench_windows_pinned_tree.py")
PINNED_TREE_SOURCE_SHA256 = "E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499"
QWEN35_MODELING_SOURCE_SHA256 = "762FEB6C7426A7F15B5BF830DF54C07438BF9E7C27B8CDB23179045920412C3B"
_PINNED_TREE_API: Any | None = None
_ACTIVE_SCRATCH_TREE: Any | None = None
_ACTIVE_RESOURCE_MONITOR: Any | None = None


def canonical_runtime_path(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).resolve(strict=True))).casefold()


def enforce_runtime_bootstrap() -> Path:
    """Reject unapproved interpreters and add-on roots before creating artifacts."""
    if os.name != "nt":
        raise RuntimeError("screen-04 requires the pinned Windows runtime")
    if sys.version_info[:3] != EXPECTED_PYTHON_VERSION:
        raise RuntimeError(
            "screen-04 requires Python " + ".".join(map(str, EXPECTED_PYTHON_VERSION))
        )
    if canonical_runtime_path(sys.executable) != canonical_runtime_path(EXPECTED_PYTHON_EXECUTABLE):
        raise RuntimeError("screen-04 must run with the exact approved Python executable")
    addon_value = os.environ.get("WRENCH_LORA_ADDONS")
    if not addon_value:
        raise RuntimeError("WRENCH_LORA_ADDONS must identify the approved add-on directory")
    addon_path = Path(addon_value).resolve(strict=True)
    require_approved_path(addon_path)
    if (not addon_path.is_dir()
            or canonical_runtime_path(addon_path) != canonical_runtime_path(EXPECTED_ADDONS_DIR)):
        raise RuntimeError("WRENCH_LORA_ADDONS must resolve to the exact approved add-on directory")
    return addon_path


def module_path_under(module: Any, name: str, root: Path) -> str:
    source = Path(getattr(module, "__file__", "")).resolve(strict=True)
    resolved_root = root.resolve(strict=True)
    if not source.is_relative_to(resolved_root):
        raise RuntimeError(f"{name} must load from its pinned runtime directory")
    return str(source)


def enforce_runtime_packages(torch: Any, transformers: Any, peft: Any,
                             accelerate: Any) -> dict[str, str]:
    versions = {
        "torch_version": str(torch.__version__),
        "transformers_version": str(transformers.__version__),
        "peft_version": str(peft.__version__),
        "accelerate_version": str(accelerate.__version__),
    }
    if versions != EXPECTED_PACKAGE_VERSIONS:
        raise RuntimeError("screen-04 package versions differ from the approved runtime")
    runtime_root = EXPECTED_PYTHON_EXECUTABLE.resolve(strict=True).parents[1]
    addon_root = EXPECTED_ADDONS_DIR.resolve(strict=True)
    qwen35_modeling_source = (
        runtime_root / "Lib" / "site-packages" / "transformers" / "models"
        / "qwen3_5" / "modeling_qwen3_5.py"
    )
    if (not qwen35_modeling_source.is_file()
            or hashlib.sha256(qwen35_modeling_source.read_bytes()).hexdigest().upper()
            != QWEN35_MODELING_SOURCE_SHA256):
        raise RuntimeError("pinned Transformers Qwen3.5 modeling source identity mismatch")
    return {
        "python_executable": str(EXPECTED_PYTHON_EXECUTABLE.resolve(strict=True)),
        "python_version": sys.version,
        "python_version_short": ".".join(map(str, sys.version_info[:3])),
        "addons_path": str(addon_root),
        **versions,
        "torch_module_path": module_path_under(torch, "torch", runtime_root),
        "transformers_module_path": module_path_under(transformers, "transformers", runtime_root),
        "qwen35_modeling_source_sha256": QWEN35_MODELING_SOURCE_SHA256,
        "peft_module_path": module_path_under(peft, "peft", addon_root),
        "accelerate_module_path": module_path_under(accelerate, "accelerate", addon_root),
    }


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified_adapter_inventory(directory: Path) -> list[dict[str, Any]]:
    """Hash every regular, single-link adapter file under the approved root."""
    require_approved_path(directory)
    tree = load_pinned_tree_module().PinnedTree(APPROVED_ROOT, allow_writes=False)
    try:
        records = tree.scan(directory, hash_files=True)
        if not records:
            raise RuntimeError("adapter directory contains no files")
        tree.verify_unchanged()
        return [
            {
                "path": relative,
                "size_bytes": record["size_bytes"],
                "sha256": record["sha256"],
            }
            for relative, record in sorted(records.items())
        ]
    finally:
        tree.close()


def finalize_adapter_no_replace(staging: Path, destination: Path) -> None:
    """Atomically rename a candidate directory without replacing a destination."""
    if os.name != "nt":
        raise RuntimeError("candidate finalization requires the pinned Windows host")
    if destination.exists():
        raise FileExistsError(f"candidate destination already exists: {destination}")
    # On Windows os.rename maps to a no-replace rename; unlike Path.replace it
    # cannot clobber a destination created after the check above.
    os.rename(staging, destination)


def minimum_resource_fractions(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        raise RuntimeError("resource summary cannot be computed from an empty log")
    return {
        "minimum_ram_free_fraction": min(row["ram_free_fraction"] for row in rows),
        "minimum_gpu_free_fraction": min(row["gpu_free_fraction"] for row in rows),
    }


def minimum_destination_free_bytes(reservation_bytes: int) -> int:
    if (not isinstance(reservation_bytes, int) or isinstance(reservation_bytes, bool)
            or reservation_bytes < 0):
        raise ValueError("storage reservation bytes must be a nonnegative integer")
    return reservation_bytes + MIN_DESTINATION_HEADROOM_BYTES


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


def read_approved_child_bytes(path: Path, parent: Path, *,
                              max_bytes: int) -> tuple[bytes, str]:
    """Read one approved child via a no-reparse, single-link Windows handle."""
    if os.name != "nt":
        raise RuntimeError("confined Wrench evidence reads require the pinned Windows host")
    if max_bytes <= 0 or Path(os.path.abspath(path.parent)) != Path(os.path.abspath(parent)):
        raise RuntimeError("approved child path or byte limit is invalid")
    approved_root = APPROVED_ROOT.resolve(strict=True)
    if path_is_reparse_point(APPROVED_ROOT):
        raise RuntimeError("approved Wrench root must not be a reparse point")
    lexical_parent = Path(os.path.abspath(parent))
    if not lexical_parent.is_relative_to(approved_root):
        raise RuntimeError("approved child parent is not under Wrench storage")
    current = lexical_parent
    while current != approved_root:
        if path_is_reparse_point(current):
            raise RuntimeError("approved child parent contains a reparse point")
        current = current.parent
    resolved_parent = parent.resolve(strict=True)
    if not resolved_parent.is_relative_to(approved_root):
        raise RuntimeError("approved child parent resolves outside Wrench storage")

    from ctypes import wintypes
    import msvcrt

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time", FileTime), ("last_access_time", FileTime),
            ("last_write_time", FileTime), ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD), ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD), ("file_index_high", wintypes.DWORD),
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

    def handle_final_path(handle: Any) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        length = kernel32.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0)
        if length == 0 or length >= len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)

    def same_path(left: Path, right: Path) -> bool:
        return os.path.normcase(os.path.normpath(str(left))) == os.path.normcase(os.path.normpath(str(right)))

    share_read_write = 0x00000001 | 0x00000002
    share_read_only = 0x00000001
    open_reparse_point = 0x00200000
    file_attribute_reparse_point = 0x00000400
    file_attribute_directory = 0x00000010
    backup_semantics = 0x02000000
    invalid_handle = ctypes.c_void_p(-1).value
    parent_handle = kernel32.CreateFileW(
        str(resolved_parent), 0x00000080, share_read_write, None, 3,
        backup_semantics | open_reparse_point, None,
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
                or not same_path(handle_final_path(parent_handle), resolved_parent)):
            raise RuntimeError("approved evidence parent handle is redirected or not a directory")

        expected_path = resolved_parent / path.name
        file_handle = kernel32.CreateFileW(
            str(expected_path), 0x80000000, share_read_only, None, 3,
            0x00000080 | open_reparse_point, None,
        )
        if not file_handle or file_handle == invalid_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        file_info = ByHandleFileInformation()
        if not kernel32.GetFileInformationByHandle(file_handle, ctypes.byref(file_info)):
            raise ctypes.WinError(ctypes.get_last_error())
        final_path = handle_final_path(file_handle)
        if (file_info.attributes & (file_attribute_reparse_point | file_attribute_directory)
                or file_info.number_of_links != 1
                or not final_path.is_relative_to(approved_root)
                or not same_path(final_path, expected_path)):
            raise RuntimeError("approved evidence file handle is linked or outside its expected path")
        fd = msvcrt.open_osfhandle(int(file_handle), os.O_RDONLY | os.O_BINARY)
        file_handle = None
        try:
            stream = os.fdopen(fd, "rb")
        except BaseException:
            os.close(fd)
            raise
        with stream:
            before = os.fstat(stream.fileno())
            if before.st_size > max_bytes:
                raise RuntimeError("approved evidence file exceeds its bounded read limit")
            payload = stream.read(max_bytes + 1)
            after = os.fstat(stream.fileno())
            if (len(payload) != before.st_size or len(payload) > max_bytes
                    or after.st_size != before.st_size):
                raise RuntimeError("approved evidence file changed or truncated during read")
        return payload, hashlib.sha256(payload).hexdigest()
    finally:
        if file_handle and file_handle != invalid_handle:
            kernel32.CloseHandle(file_handle)
        kernel32.CloseHandle(parent_handle)


def require_active_reservation(job_id: str, minimum_bytes: int) -> dict[str, Any]:
    reservation_path = APPROVED_ROOT / ".budget/reservations" / f"{job_id}.json"
    require_approved_path(reservation_path)
    if not reservation_path.is_file():
        raise RuntimeError(f"active storage reservation is missing: {job_id}")
    reservation = json.loads(reservation_path.read_text(encoding="utf-8"))
    if (reservation.get("schema") != "wrench.storage-reservation.v1"
            or reservation.get("job_id") != job_id
            or not isinstance(reservation.get("reserve_bytes"), int)
            or reservation["reserve_bytes"] < minimum_bytes):
        raise RuntimeError(f"storage reservation identity or size is invalid: {job_id}")
    return {"path": reservation_path, "record": reservation}


def require_reservation_still_active(job_id: str, minimum_bytes: int,
                                     expected_sha256: str | None = None) -> dict[str, Any]:
    active = require_active_reservation(job_id, minimum_bytes)
    reservation_path = active["path"]
    reservation_hash = sha256_file(reservation_path)
    if expected_sha256 is not None and reservation_hash != expected_sha256:
        raise RuntimeError("active storage reservation changed after admission")
    minimum_free_bytes = minimum_destination_free_bytes(active["record"]["reserve_bytes"])
    if shutil.disk_usage(APPROVED_ROOT).free < minimum_free_bytes:
        raise RuntimeError(
            "destination volume free space is below the active reservation plus "
            f"5 GiB operating headroom ({minimum_free_bytes} bytes required)"
        )
    active["sha256"] = reservation_hash
    return active


def claim_job_id(claim_dir: Path) -> Path:
    """Atomically and permanently claim a unique job ID before run artifacts."""
    claim_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        claim_dir.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError(f"job ID is already claimed and cannot be reused: {claim_dir.name}") from exc
    return claim_dir


def require_approved_path(path: Path) -> None:
    approved_root = APPROVED_ROOT.resolve(strict=True)
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(approved_root):
        raise RuntimeError(f"Wrench output path escaped approved storage root: {path}")


def scratch_tree_bytes(root: Path) -> int:
    global _ACTIVE_SCRATCH_TREE
    if not root.exists():
        if _ACTIVE_SCRATCH_TREE is not None:
            raise RuntimeError("pinned runtime scratch root disappeared")
        return 0
    if _ACTIVE_SCRATCH_TREE is None:
        _ACTIVE_SCRATCH_TREE = load_pinned_tree_module().PinnedTree(
            APPROVED_ROOT, allow_writes=True,
        )
    tree = _ACTIVE_SCRATCH_TREE
    try:
        records = tree.scan(root, hash_files=False)
        return sum(record["size_bytes"] for record in records.values())
    finally:
        tree.release_files()


def resolve_manifest_path(root: Path, relative_value: Any) -> Path:
    if not isinstance(relative_value, str) or not relative_value:
        raise RuntimeError("dataset manifest path must be a non-empty relative string")
    windows_path = PureWindowsPath(relative_value)
    candidate = Path(relative_value)
    if (candidate.is_absolute() or windows_path.is_absolute() or windows_path.drive
            or ".." in candidate.parts or ".." in windows_path.parts):
        raise RuntimeError(f"dataset path must stay relative to the approved data root: {relative_value}")
    require_approved_path(root)
    resolved_root = root.resolve(strict=True)
    resolved = (resolved_root / candidate).resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_file():
        raise RuntimeError(f"dataset path escaped the approved data root: {relative_value}")
    return resolved


def verify_model_inventory(inventory: dict[str, Any], candidate: dict[str, Any], *,
                           inventory_sha256: str, candidate_sha256: str) -> Any:
    require_approved_path(INVENTORY)
    require_approved_path(MODEL_DIR)
    if (inventory.get("schema") != "wrench.gateway.model-inventory.v1"
            or inventory.get("status") != "VERIFIED_LOCAL_SNAPSHOT"
            or inventory.get("model_id") != EXPECTED_MODEL_ID
            or inventory.get("revision") != EXPECTED_REVISION
            or inventory.get("file_count") != 13
            or inventory.get("total_bytes") != 4_571_274_023
            or inventory_sha256 != MODEL_INVENTORY_SHA256):
        raise RuntimeError("local snapshot inventory identity is not verified")
    if (candidate.get("schema") != "wrench.gateway.model-candidate.v1"
            or candidate.get("model_id") != EXPECTED_MODEL_ID
            or candidate.get("revision") != EXPECTED_REVISION
            or candidate.get("license") != "Apache-2.0"
            or candidate.get("repository_bytes") != inventory.get("total_bytes")
            or candidate_sha256 != MODEL_CANDIDATE_SHA256):
        raise RuntimeError("pinned Qwen3.5-2B candidate manifest is not verified")
    expected_items = inventory.get("files")
    candidate_items = candidate.get("files")
    if (not isinstance(expected_items, list) or not expected_items
            or not isinstance(candidate_items, list) or not candidate_items):
        raise RuntimeError("local snapshot inventory has no file manifest")
    expected = {item["path"]: item for item in expected_items}
    candidate_files = {item["path"]: item for item in candidate_items}
    if len(expected) != len(expected_items):
        raise RuntimeError("local snapshot inventory contains duplicate paths")
    if len(candidate_files) != len(candidate_items) or set(candidate_files) != set(expected):
        raise RuntimeError("local snapshot file set does not match independently pinned candidate metadata")
    for relative, spec in expected.items():
        upstream = candidate_files[relative]
        if (spec.get("size_bytes") != upstream.get("size_bytes")
                or spec.get("git_blob_id") != upstream.get("git_blob_id")
                or (upstream.get("upstream_sha256") is not None
                    and str(spec.get("sha256", "")).casefold()
                    != str(upstream.get("upstream_sha256", "")).casefold())):
            raise RuntimeError(f"local inventory differs from the pinned upstream identity: {relative}")
    tree = load_pinned_tree_module().PinnedTree(APPROVED_ROOT)
    try:
        model_root = Path(os.path.abspath(MODEL_DIR))
        actual = tree.scan(model_root)
        if set(actual) != set(expected):
            raise RuntimeError("local model file set differs from the pinned inventory")
        total_bytes = 0
        for relative in sorted(expected):
            record = actual[relative]
            spec = expected[relative]
            if (record["size_bytes"] != spec.get("size_bytes")
                    or record["sha256"].casefold() != str(spec.get("sha256", "")).casefold()):
                raise RuntimeError(f"pinned local model file identity mismatch: {relative}")
            total_bytes += record["size_bytes"]
        if total_bytes != inventory.get("total_bytes"):
            raise RuntimeError("pinned local model aggregate byte count mismatch")
        return tree
    except BaseException:
        tree.close()
        raise


def verify_model_config(config: dict[str, Any], config_sha256: str) -> list[int]:
    """Validate the pinned Qwen3.5-2B text/vision layout before target selection."""
    text = config.get("text_config")
    if (config_sha256 != MODEL_CONFIG_SHA256
            or config.get("model_type") != "qwen3_5"
            or "Qwen3_5ForConditionalGeneration" not in config.get("architectures", [])
            or not isinstance(text, dict)
            or text.get("model_type") != "qwen3_5_text"
            or text.get("hidden_size") != EXPECTED_HIDDEN_SIZE
            or text.get("num_hidden_layers") != EXPECTED_TEXT_LAYER_COUNT
            or text.get("num_attention_heads") != EXPECTED_ATTENTION_HEADS
            or text.get("num_key_value_heads") != EXPECTED_KEY_VALUE_HEADS
            or text.get("head_dim") != EXPECTED_HEAD_DIM
            or text.get("full_attention_interval") != 4
            or text.get("dtype") != "bfloat16"
            or not isinstance(config.get("vision_config"), dict)):
        raise RuntimeError("pinned Qwen3.5-2B config does not match the reviewed text/vision architecture")
    layer_types = text.get("layer_types")
    if (not isinstance(layer_types, list)
            or len(layer_types) != EXPECTED_TEXT_LAYER_COUNT
            or tuple(i for i, kind in enumerate(layer_types) if kind == "full_attention")
            != EXPECTED_FULL_ATTENTION_LAYER_INDEXES
            or any(kind not in {"full_attention", "linear_attention"} for kind in layer_types)
            or sum(kind == "linear_attention" for kind in layer_types) != 18):
        raise RuntimeError("Qwen3.5-2B layer_types differ from the pinned six-full-attention layout")
    return list(EXPECTED_FULL_ATTENTION_LAYER_INDEXES)


def expected_target_module_names() -> list[str]:
    return sorted(
        f"model.language_model.layers.{index}.self_attn.{suffix}"
        for index in EXPECTED_FULL_ATTENTION_LAYER_INDEXES
        for suffix in ATTENTION_TARGET_SUFFIXES
    )


def expected_lora_parameter_count(rank: int = 8) -> int:
    kv_width = EXPECTED_KEY_VALUE_HEADS * EXPECTED_HEAD_DIM
    q_width = EXPECTED_ATTENTION_HEADS * EXPECTED_HEAD_DIM * 2
    attention_width = EXPECTED_ATTENTION_HEADS * EXPECTED_HEAD_DIM
    hidden = EXPECTED_HIDDEN_SIZE
    per_layer = sum(rank * (hidden + output_width) for output_width in
                    (q_width, kv_width, kv_width, attention_width))
    return len(EXPECTED_FULL_ATTENTION_LAYER_INDEXES) * per_layer


def verify_successful_preflight(protocol_hash: str, dataset_hash: str, inventory_hash: str,
                                data_manifest: dict[str, Any], runner_hash: str,
                                device_name: str, runtime_identity: dict[str, str],
                                adapter_profile_name: str,
                                adapter_profile: dict[str, Any],
                                target_modules: list[str],
                                candidate_sha256: str, config_sha256: str, index_sha256: str,
                                license_sha256: str) -> dict[str, str]:
    if adapter_profile_name != "full-attention-qkvo":
        raise RuntimeError("full fit is admitted only for the reviewed Qwen3.5 full-attention profile")
    preflight_job_id = adapter_profile["preflight_job_id"]
    preflight_manifest = Path(adapter_profile["preflight_manifest"])
    preflight_reservation = APPROVED_ROOT / ".budget/reservations" / f"{preflight_job_id}.json"
    if preflight_reservation.exists():
        raise RuntimeError("preflight reservation must be released before the fit is admitted")
    preflight_bytes, preflight_manifest_sha256 = read_approved_child_bytes(
        preflight_manifest, preflight_manifest.parent, max_bytes=MAX_LOG_BYTES,
    )
    preflight = json.loads(preflight_bytes.decode("utf-8"))
    if not isinstance(preflight, dict):
        raise RuntimeError("successful one-step GPU preflight receipt must be a JSON object")
    expected = {
        "schema": "wrench.gateway_lora_screen_04_2b.run.v1",
        "status": "PREFLIGHT_COMPLETED",
        "job_id": preflight_job_id,
        "optimizer_steps": 1,
        "heldout_opened_by_runner": False,
        "adapter_profile": adapter_profile_name,
        "matched_target_count": adapter_profile["expected_target_count"],
        "matched_target_modules": target_modules,
        "trainable_parameter_count": expected_lora_parameter_count(),
        "model_config_sha256": config_sha256,
        "model_index_sha256": index_sha256,
        "model_license_sha256": license_sha256,
        "preflight_only": True,
        "output_dir": None,
        "model_id": EXPECTED_MODEL_ID,
        "model_revision": EXPECTED_REVISION,
        "model_inventory_sha256": inventory_hash,
        "model_candidate_sha256": candidate_sha256,
        "protocol_sha256": protocol_hash,
        "dataset_manifest_sha256": dataset_hash,
        "train_sha256": data_manifest["files"]["train"]["sha256"],
        "dev_sha256": data_manifest["files"]["dev"]["sha256"],
        "runner_sha256": runner_hash,
        "device": "cuda:0",
        "device_name": device_name,
        "device_uuid": EXPECTED_GPU_UUID,
        "precision": "bfloat16",
        "storage_reservation_job_id": preflight_job_id,
    }
    if any(preflight.get(key) != value for key, value in expected.items()):
        raise RuntimeError("preflight receipt does not match this runner, protocol, model, data, and GPU")
    trainable_count = preflight.get("trainable_parameter_count")
    if (not isinstance(trainable_count, int) or isinstance(trainable_count, bool)
            or trainable_count <= 0):
        raise RuntimeError("preflight receipt lacks its instantiated LoRA trainable count")
    if not isinstance(preflight.get("chat_template_sha256"), str) or len(preflight["chat_template_sha256"]) != 64:
        raise RuntimeError("preflight receipt lacks its chat-template identity")
    if preflight.get("runtime_identity") != runtime_identity:
        raise RuntimeError("preflight receipt runtime identity differs from the fit runtime")
    if (not isinstance(preflight.get("storage_reservation_bytes"), int)
            or preflight["storage_reservation_bytes"] < PREFLIGHT_MIN_RESERVATION_BYTES
            or not isinstance(preflight.get("storage_reservation_sha256"), str)
            or len(preflight["storage_reservation_sha256"]) != 64):
        raise RuntimeError("preflight receipt does not prove its minimum storage reservation")
    if (preflight.get("runtime_scratch_limit_bytes") != PREFLIGHT_MAX_SCRATCH_BYTES
            or preflight.get("runtime_scratch_bytes_at_finalize", PREFLIGHT_MAX_SCRATCH_BYTES + 1)
            > PREFLIGHT_MAX_SCRATCH_BYTES
            or preflight.get("runtime_scratch_peak_bytes", PREFLIGHT_MAX_SCRATCH_BYTES + 1)
            > PREFLIGHT_MAX_SCRATCH_BYTES):
        raise RuntimeError("preflight receipt does not prove its bounded runtime scratch use")
    if not isinstance(preflight.get("resource_log_finalized_at_utc"), str):
        raise RuntimeError("preflight receipt is missing resource-log finalization evidence")
    resource_log = preflight_manifest.parent / "resources.jsonl"
    declared_resource_log = Path(preflight.get("resource_log", ""))
    if Path(os.path.abspath(declared_resource_log)) != Path(os.path.abspath(resource_log)):
        raise RuntimeError("preflight resource log path differs from its pinned job directory")
    resource_log_bytes, resource_log_sha256 = read_approved_child_bytes(
        resource_log, resource_log.parent, max_bytes=MAX_LOG_BYTES,
    )
    if resource_log_sha256 != preflight.get("resource_log_sha256"):
        raise RuntimeError("preflight resource-log hash mismatch")
    samples = [json.loads(line) for line in resource_log_bytes.decode("utf-8").splitlines() if line]
    if not samples or any(sample.get("ram_free_fraction", 0) < RAM_FREE_FRACTION
                          or sample.get("gpu_free_fraction", 0) < VRAM_FREE_FRACTION
                          or not isinstance(sample.get("runtime_scratch_bytes"), int)
                          or sample["runtime_scratch_bytes"] > PREFLIGHT_MAX_SCRATCH_BYTES
                          or sample.get("gpu_uuid") != EXPECTED_GPU_UUID
                          for sample in samples):
        raise RuntimeError("preflight resource receipt is empty or crossed a 10% floor")
    resource_minima = minimum_resource_fractions(samples)
    if any(preflight.get(key) != value for key, value in resource_minima.items()):
        raise RuntimeError("preflight resource minimum summary differs from its hash-bound samples")
    return {
        "manifest_sha256": preflight_manifest_sha256,
        "resource_log_sha256": resource_log_sha256,
        "trainable_parameter_count": str(trainable_count),
        "chat_template_sha256": str(preflight.get("chat_template_sha256", "")),
    }


def require_reservation_checkpoint(active_reservation: dict[str, Any], job_id: str,
                                   minimum_bytes: int) -> None:
    require_reservation_still_active(job_id, minimum_bytes, active_reservation["sha256"])


def write_json(path: Path, value: Any) -> None:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(payload) > MAX_LOG_BYTES:
        raise RuntimeError(f"JSON receipt exceeds byte cap: {path.name}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def ram_sample() -> tuple[int, int]:
    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError("GlobalMemoryStatusEx failed")
    return int(status.ullAvailPhys), int(status.ullTotalPhys)


def gpu_sample() -> dict[str, Any]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid,pci.bus_id,name,memory.total,memory.free",
         "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    rows = [line.split(",", maxsplit=5) for line in result.stdout.strip().splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 6:
        raise RuntimeError("screen-04 requires exactly one visible NVIDIA GPU for unambiguous monitoring")
    index, uuid, pci_bus_id, name, total_mib, free_mib = [part.strip() for part in rows[0]]
    if index != "0" or uuid != EXPECTED_GPU_UUID or name != EXPECTED_GPU_NAME:
        raise RuntimeError("nvidia-smi GPU identity differs from the pinned screen-04 device")
    return {
        "index": int(index), "uuid": uuid, "pci_bus_id": pci_bus_id, "name": name,
        "total_mib": int(total_mib), "free_mib": int(free_mib),
    }


class ResourceMonitor(threading.Thread):
    def __init__(self, log_path: Path, scratch_root: Path, scratch_limit: int) -> None:
        super().__init__(name="wrench-gateway-resource-monitor", daemon=True)
        self.log_path = log_path
        self.scratch_root = scratch_root
        self.scratch_limit = scratch_limit
        self.stop_event = threading.Event()
        self.breach_reason: str | None = None

    def sample_and_write(self) -> None:
        scratch_bytes = scratch_tree_bytes(self.scratch_root)
        if scratch_bytes > self.scratch_limit:
            self.breach_reason = "RUNTIME_SCRATCH_BYTE_CAP"
            self.stop_event.set()
            return
        ram_free, ram_total = ram_sample()
        gpu = gpu_sample()
        sample = {
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
        line = (json.dumps(sample, sort_keys=True) + "\n").encode("utf-8")
        if self.log_path.stat().st_size + len(line) > MAX_LOG_BYTES:
            self.breach_reason = "RESOURCE_LOG_BYTE_CAP"
            self.stop_event.set()
            return
        with self.log_path.open("ab") as stream:
            stream.write(line)
            stream.flush()
        if sample["ram_free_fraction"] < RAM_FREE_FRACTION:
            self.breach_reason = "RAM_FREE_BELOW_10_PERCENT"
        elif sample["gpu_free_fraction"] < VRAM_FREE_FRACTION:
            self.breach_reason = "VRAM_FREE_BELOW_10_PERCENT"
        if self.breach_reason:
            self.stop_event.set()

    def run(self) -> None:
        try:
            while not self.stop_event.is_set():
                self.sample_and_write()
                if self.breach_reason:
                    _thread.interrupt_main()
                    return
                self.stop_event.wait(1.0)
        except BaseException as exc:
            self.breach_reason = f"RESOURCE_MONITOR_ERROR:{type(exc).__name__}"
            _thread.interrupt_main()


def load_jsonl_bytes(payload: bytes, expected_split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    text = payload.decode("utf-8")
    for line_number, line in enumerate(text.splitlines(), start=1):
        row = json.loads(line)
        if row.get("split") != expected_split or row.get("schema") != "wrench.gateway_lora_screen_01.synthetic.v1":
            raise ValueError(f"split/schema mismatch in {expected_split}:{line_number}")
        if row.get("family") not in EXPECTED_FAMILIES:
            raise ValueError(f"unexpected family in {expected_split}:{line_number}")
        rows.append(row)
    if not rows:
        raise ValueError(f"empty split: {expected_split}")
    return rows


def tokenize_rows(rows: list[dict[str, Any]], tokenizer: Any, split: str) -> list[dict[str, Any]]:
    encoded: list[dict[str, Any]] = []
    for row in rows:
        messages = row["messages"]
        if len(messages) != 3 or messages[0]["role"] != "system" or messages[1]["role"] != "user" or messages[2]["role"] != "assistant":
            raise ValueError(f"invalid chat messages: {row['example_id']}")
        prompt_text = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
        full_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prompt_ids = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        full_ids = tokenizer(full_text, add_special_tokens=False)["input_ids"]
        if full_ids[: len(prompt_ids)] != prompt_ids:
            raise ValueError(f"chat-template prefix mismatch: {row['example_id']}")
        if len(full_ids) > MAX_SEQUENCE_LENGTH:
            raise ValueError(f"sequence exceeds {MAX_SEQUENCE_LENGTH} tokens: {row['example_id']}")
        if len(full_ids) <= len(prompt_ids):
            raise ValueError(f"assistant target is empty: {row['example_id']}")
        labels = [-100] * len(prompt_ids) + full_ids[len(prompt_ids) :]
        encoded.append({"example_id": row["example_id"], "input_ids": full_ids, "labels": labels, "family": row["family"]})
    print(f"tokenized {split}: {len(encoded)} rows; max length {max(len(row['input_ids']) for row in encoded)}")
    return encoded


def as_batch(row: dict[str, Any], torch: Any, device: Any) -> dict[str, Any]:
    input_ids = torch.tensor([row["input_ids"]], dtype=torch.long, device=device)
    labels = torch.tensor([row["labels"]], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_ids)
    return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


def checked_optimizer_step(optimizer: Any, trainable: list[Any], torch: Any) -> float:
    gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, 1.0, error_if_nonfinite=True)
    if not bool(torch.isfinite(gradient_norm).item()):
        raise RuntimeError("gradient norm became non-finite")
    optimizer.step()
    if any(not bool(torch.isfinite(parameter).all().item()) for parameter in trainable):
        raise RuntimeError("optimizer produced a non-finite trainable parameter")
    return float(gradient_norm.detach().item())


def stop_monitor_and_verify(monitor: ResourceMonitor) -> tuple[list[dict[str, Any]], str]:
    monitor.stop_event.set()
    if monitor.is_alive():
        monitor.join(timeout=5)
    if monitor.is_alive():
        raise RuntimeError("resource monitor did not stop cleanly")
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    resource_log_bytes, resource_log_sha256 = read_approved_child_bytes(
        monitor.log_path, monitor.log_path.parent, max_bytes=MAX_LOG_BYTES,
    )
    rows = [json.loads(line) for line in resource_log_bytes.decode("utf-8").splitlines() if line]
    if not rows or any(row.get("ram_free_fraction", 0) < RAM_FREE_FRACTION
                       or row.get("gpu_free_fraction", 0) < VRAM_FREE_FRACTION
                       or not isinstance(row.get("runtime_scratch_bytes"), int)
                       or row["runtime_scratch_bytes"] > monitor.scratch_limit
                       or row.get("gpu_uuid") != EXPECTED_GPU_UUID for row in rows):
        raise RuntimeError("resource log is empty, identifies another GPU, or records a reserve breach")
    return rows, resource_log_sha256


def evaluate_loss(model: Any, rows: list[dict[str, Any]], torch: Any, monitor: ResourceMonitor, device: Any) -> float:
    model.eval()
    token_weighted_loss = 0.0
    token_count = 0
    with torch.no_grad():
        for row in rows:
            if monitor.breach_reason:
                raise KeyboardInterrupt(monitor.breach_reason)
            batch = as_batch(row, torch, device)
            output = model(**batch, use_cache=False)
            tokens = int((batch["labels"] != -100).sum().item())
            token_weighted_loss += float(output.loss.item()) * tokens
            token_count += tokens
    model.train()
    return token_weighted_loss / max(token_count, 1)


def select_lora_targets(named_modules: Any, linear_type: type[Any], profile_name: str) -> list[str]:
    """Select and validate text projection targets for a named adapter profile."""
    try:
        profile = ADAPTER_PROFILES[profile_name]
    except KeyError as exc:
        raise ValueError(f"unknown adapter profile: {profile_name}") from exc
    if profile_name != "full-attention-qkvo":
        raise RuntimeError("screen-04 only admits full-attention q/k/v/o placement")
    modules_by_name = dict(named_modules)
    expected = {
        f"model.language_model.layers.{index}.self_attn.{suffix}"
        for index in EXPECTED_FULL_ATTENTION_LAYER_INDEXES
        for suffix in ATTENTION_TARGET_SUFFIXES
    }
    targets = sorted(name for name in expected if isinstance(modules_by_name.get(name), linear_type))
    if set(targets) != expected or len(expected) != profile["expected_target_count"]:
        absent = sorted(expected - set(targets))
        raise RuntimeError(f"exact Qwen3.5-2B projection layout mismatch; absent={absent}")
    unexpected = [
        name for name, module in named_modules
        if name.startswith("model.language_model.layers.")
        and name.rsplit(".", 1)[-1] in ATTENTION_TARGET_SUFFIXES
        and isinstance(module, linear_type)
        and name not in expected
    ]
    if unexpected:
        raise RuntimeError(f"unexpected attention projection candidates exist: {sorted(unexpected)}")
    expected_dimensions = {
        "q_proj": (
            EXPECTED_HIDDEN_SIZE,
            EXPECTED_ATTENTION_HEADS * EXPECTED_HEAD_DIM * 2,
        ),
        "k_proj": (EXPECTED_HIDDEN_SIZE, EXPECTED_KEY_VALUE_HEADS * EXPECTED_HEAD_DIM),
        "v_proj": (EXPECTED_HIDDEN_SIZE, EXPECTED_KEY_VALUE_HEADS * EXPECTED_HEAD_DIM),
        "o_proj": (EXPECTED_HIDDEN_SIZE, EXPECTED_HIDDEN_SIZE),
    }
    for name in targets:
        module = modules_by_name[name]
        expected_in, expected_out = expected_dimensions[name.rsplit(".", 1)[-1]]
        if (getattr(module, "in_features", None) != expected_in
                or getattr(module, "out_features", None) != expected_out):
            raise RuntimeError(f"projection dimensions changed from the pinned config: {name}")
    expected_count = profile["expected_target_count"]
    if expected_count is not None and len(targets) != expected_count:
        raise RuntimeError(
            f"target count mismatch for {profile_name}; "
            f"expected={expected_count}, observed={len(targets)}"
        )
    return targets


def _run_main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-reservation-job-id", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight-only", action="store_true", help="run one optimizer step and save only a preflight receipt")
    mode.add_argument("--fit", action="store_true", help="run the bounded 96-step BF16 candidate fit")
    parser.add_argument(
        "--adapter-profile", choices=["full-attention-qkvo"], default="full-attention-qkvo",
        help="the only admitted placement for this candidate preflight/fit",
    )
    args = parser.parse_args()

    adapter_profile = ADAPTER_PROFILES[args.adapter_profile]
    preflight_log_dir = adapter_profile["preflight_log_dir"]
    is_fit = args.fit
    if not args.preflight_only and not is_fit:
        raise SystemExit("select exactly one of --preflight-only or --fit")

    try:
        addon_path = enforce_runtime_bootstrap()
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"runtime admission failed before artifact creation: {exc}") from exc

    expected_job_id = adapter_profile["preflight_job_id"] if args.preflight_only else FIT_JOB_ID
    minimum_reservation_bytes = PREFLIGHT_MIN_RESERVATION_BYTES if args.preflight_only else FIT_MIN_RESERVATION_BYTES
    scratch_limit = PREFLIGHT_MAX_SCRATCH_BYTES if args.preflight_only else FIT_MAX_SCRATCH_BYTES
    scratch_root = APPROVED_ROOT / "cache/gateway-lora-screen-04-2b" / expected_job_id
    selected_output_paths = (
        (FIT_ATTEMPT_DIR, OUTPUT, STAGING_OUTPUT, RUNNER_SNAPSHOT, LOG_DIR)
        if is_fit else (preflight_log_dir,)
    )
    if args.storage_reservation_job_id != expected_job_id:
        raise SystemExit(f"reservation job ID must be {expected_job_id} for this mode")
    try:
        active_reservation = require_reservation_still_active(expected_job_id, minimum_reservation_bytes)
        for output_path in (*selected_output_paths, scratch_root, JOB_CLAIM_ROOT / expected_job_id):
            require_approved_path(output_path)
            if output_path.exists():
                raise RuntimeError(f"refusing to reuse an existing candidate path: {output_path}")
        if scratch_root.exists():
            raise RuntimeError("refusing to reuse this job's runtime scratch directory")
        fit_start_ram_free_bytes, fit_start_ram_total_bytes = ram_sample()
        fit_start_ram_free_fraction = fit_start_ram_free_bytes / fit_start_ram_total_bytes
        if (is_fit
                and fit_start_ram_free_fraction < FIT_START_RAM_FREE_FRACTION):
            raise RuntimeError(
                "full-fit admission requires at least "
                f"{FIT_START_RAM_FREE_FRACTION:.0%} free RAM at process start; "
                f"observed {fit_start_ram_free_fraction:.2%}"
            )
        destination_free_bytes = shutil.disk_usage(APPROVED_ROOT).free
        minimum_free_bytes = minimum_destination_free_bytes(
            active_reservation["record"]["reserve_bytes"],
        )
        if destination_free_bytes < minimum_free_bytes:
            raise RuntimeError(
                "job admission requires the reservation plus at least 5 GiB "
                f"operating headroom ({minimum_free_bytes} bytes total); "
                f"observed {destination_free_bytes}"
            )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"job admission failed before artifact creation: {exc}") from exc

    claim_path = JOB_CLAIM_ROOT / expected_job_id
    try:
        claim_job_id(claim_path)
        require_approved_path(claim_path)
        write_json(claim_path / "claim.json", {
            "schema": "wrench.gateway.job-claim.v1",
            "job_id": expected_job_id,
            "pid": os.getpid(),
            "runner_sha256": sha256_file(Path(__file__).resolve()),
            "claimed_at_utc": utc_now(),
        })
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"exclusive job claim failed before run artifacts: {exc}") from exc

    if scratch_root.exists():
        raise SystemExit("refusing to reuse or overwrite this job's runtime scratch directory")
    os.environ["HF_HOME"] = str(scratch_root / "huggingface")
    os.environ["HF_HUB_CACHE"] = str(scratch_root / "huggingface/hub")
    os.environ["HF_ASSETS_CACHE"] = str(scratch_root / "huggingface/assets")
    os.environ["HF_DATASETS_CACHE"] = str(scratch_root / "huggingface/datasets")
    os.environ["TRANSFORMERS_CACHE"] = str(scratch_root / "huggingface/transformers")
    os.environ["TORCH_HOME"] = str(scratch_root / "torch")
    os.environ["XDG_CACHE_HOME"] = str(scratch_root / "xdg")
    os.environ["TEMP"] = str(scratch_root / "tmp")
    os.environ["TMP"] = os.environ["TEMP"]
    os.environ["TMPDIR"] = os.environ["TEMP"]
    os.environ["TORCH_EXTENSIONS_DIR"] = str(scratch_root / "torch-extensions")
    os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(scratch_root / "torch-inductor")
    os.environ["TRITON_CACHE_DIR"] = str(scratch_root / "triton")
    os.environ["CUDA_CACHE_PATH"] = str(scratch_root / "cuda")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    sys.path.insert(0, str(addon_path))
    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices not in (None, "", EXPECTED_GPU_UUID):
        raise SystemExit("CUDA_VISIBLE_DEVICES conflicts with the pinned screen-04 GPU UUID")
    os.environ["CUDA_VISIBLE_DEVICES"] = EXPECTED_GPU_UUID
    os.environ.setdefault("CUDA_DEVICE_ORDER", "PCI_BUS_ID")

    for path in (DATA_ROOT, MODEL_DIR, INVENTORY, MODEL_CANDIDATE,
                 MODEL_CONFIG, MODEL_INDEX, MODEL_LICENSE):
        try:
            require_approved_path(path)
        except RuntimeError as exc:
            raise SystemExit(f"required Wrench input escaped approved storage: {exc}") from exc
    for path in (DATA_ROOT, MODEL_DIR, INVENTORY, MODEL_CANDIDATE,
                 MODEL_CONFIG, MODEL_INDEX, MODEL_LICENSE, PROTOCOL):
        if not path.exists():
            raise SystemExit(f"required input missing: {path}")
    run_log_dir = preflight_log_dir if args.preflight_only else LOG_DIR
    for path in selected_output_paths:
        require_approved_path(path)
    active_reservation = require_reservation_still_active(
        expected_job_id, minimum_reservation_bytes, active_reservation["sha256"]
    )
    resource_log = run_log_dir / "resources.jsonl"
    monitor = ResourceMonitor(resource_log, scratch_root, scratch_limit)
    owns_artifact_dir = False
    global _ACTIVE_RESOURCE_MONITOR
    _ACTIVE_RESOURCE_MONITOR = monitor
    base_manifest = {
        "schema": "wrench.gateway_lora_screen_04_2b.run.v1",
        "status": "RUNNING_SETUP",
        "job_id": args.storage_reservation_job_id,
        "job_claim_dir": str(claim_path),
        "started_at_utc": utc_now(),
        "model_id": EXPECTED_MODEL_ID,
        "model_revision": EXPECTED_REVISION,
        "model_inventory_sha256": None,
        "pinned_tree_source_sha256": PINNED_TREE_SOURCE_SHA256,
        "model_candidate_sha256": MODEL_CANDIDATE_SHA256,
        "model_config_sha256": MODEL_CONFIG_SHA256,
        "model_index_sha256": MODEL_INDEX_SHA256,
        "model_license_sha256": MODEL_LICENSE_SHA256,
        "protocol_sha256": None,
        "dataset_manifest_sha256": None,
        "train_sha256": TRAIN_DATA_SHA256,
        "dev_sha256": DEV_DATA_SHA256,
        "heldout_opened_by_runner": False,
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "device": "cuda:0",
        "device_index": 0,
        "device_name": EXPECTED_GPU_NAME,
        "device_uuid": EXPECTED_GPU_UUID,
        "device_pci_bus_id": None,
        "cuda_version": None,
        "threads": 4,
        "precision": "bfloat16",
        "epochs": EPOCHS,
        "gradient_accumulation": GRAD_ACCUMULATION,
        "learning_rate": LEARNING_RATE,
        "seed": 20260927,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "optimizer": "AdamW",
        "weight_decay": 0.0,
        "gradient_norm_cap": 1.0,
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "adapter_profile": args.adapter_profile,
        "target_suffix_allowlist": sorted(adapter_profile["target_suffixes"]),
        "expected_full_attention_layer_indexes": list(EXPECTED_FULL_ATTENTION_LAYER_INDEXES),
        "expected_target_modules": expected_target_module_names(),
        "expected_target_count": adapter_profile["expected_target_count"],
        "expected_trainable_parameter_count": expected_lora_parameter_count(),
        "resource_log": str(resource_log),
        "storage_reservation_job_id": expected_job_id,
        "storage_reservation_bytes": active_reservation["record"]["reserve_bytes"],
        "storage_reservation_sha256": active_reservation["sha256"],
        "fit_start_ram_free_fraction_required": FIT_START_RAM_FREE_FRACTION if is_fit else None,
        "fit_start_ram_free_fraction_observed": fit_start_ram_free_fraction,
        "destination_free_bytes_at_admission": destination_free_bytes,
        "runtime_scratch_limit_bytes": scratch_limit,
        "output_dir": None if args.preflight_only else str(OUTPUT),
        "preflight_only": args.preflight_only,
        "fit_mode": is_fit,
        "expected_fit_optimizer_steps": EXPECTED_FIT_OPTIMIZER_STEPS if is_fit else None,
    }
    run_manifest_path = run_log_dir / "run-manifest.json"
    model_tree: Any | None = None

    try:
        run_log_dir.mkdir(parents=True, exist_ok=False)
        owns_artifact_dir = True
        resource_log.write_bytes(b"")
        write_json(run_manifest_path, base_manifest)
        monitor.sample_and_write()
        if monitor.breach_reason:
            raise KeyboardInterrupt(monitor.breach_reason)
        scratch_root.mkdir(parents=True, exist_ok=False)
        require_approved_path(scratch_root)
        Path(os.environ["TEMP"]).mkdir(parents=True, exist_ok=False)
        require_approved_path(Path(os.environ["TEMP"]))
        if scratch_tree_bytes(scratch_root) > scratch_limit:
            raise RuntimeError("runtime scratch exceeded its cap before monitor start")
        monitor.start()

        import torch
        import accelerate
        import peft
        import transformers
        from peft import LoraConfig, TaskType, get_peft_model
        from torch import nn
        from transformers import AutoModelForImageTextToText, AutoTokenizer

        runtime_identity = enforce_runtime_packages(torch, transformers, peft, accelerate)
        base_manifest["runtime_identity"] = runtime_identity
        write_json(run_manifest_path, base_manifest)
        torch.set_num_threads(4)
        if (not torch.cuda.is_available() or torch.cuda.device_count() != 1):
            raise RuntimeError("the pinned single GPU is unavailable or ambiguous")
        device = torch.device("cuda:0")
        torch.cuda.set_device(device)
        if torch.cuda.current_device() != 0:
            raise RuntimeError("CUDA logical device is not the pinned cuda:0")
        gpu = gpu_sample()
        device_name = torch.cuda.get_device_name(device)
        if (device_name != EXPECTED_GPU_NAME or gpu["uuid"] != EXPECTED_GPU_UUID
                or gpu["index"] != 0):
            raise RuntimeError("PyTorch device does not match the monitored pinned GPU")
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError("pinned GPU/runtime does not report BF16 support")
        random.seed(20260927)
        torch.manual_seed(20260927)

        candidate_bytes, candidate_hash = read_approved_child_bytes(
            MODEL_CANDIDATE, MODEL_CANDIDATE.parent, max_bytes=MAX_LOG_BYTES,
        )
        candidate = json.loads(candidate_bytes.decode("utf-8"))
        inventory_bytes, inventory_hash = read_approved_child_bytes(
            INVENTORY, INVENTORY.parent, max_bytes=MAX_LOG_BYTES,
        )
        inventory = json.loads(inventory_bytes.decode("utf-8"))
        config_bytes, config_hash = read_approved_child_bytes(
            MODEL_CONFIG, MODEL_DIR, max_bytes=MAX_LOG_BYTES,
        )
        index_bytes, index_hash = read_approved_child_bytes(
            MODEL_INDEX, MODEL_DIR, max_bytes=MAX_DATA_SPLIT_BYTES,
        )
        license_bytes, license_hash = read_approved_child_bytes(
            MODEL_LICENSE, MODEL_DIR, max_bytes=MAX_LOG_BYTES,
        )
        if (config_hash != MODEL_CONFIG_SHA256 or index_hash != MODEL_INDEX_SHA256
                or license_hash != MODEL_LICENSE_SHA256):
            raise RuntimeError("pinned model config, index, or license hash mismatch")
        model_config = json.loads(config_bytes.decode("utf-8"))
        full_attention_layers = verify_model_config(model_config, config_hash)
        if full_attention_layers != list(EXPECTED_FULL_ATTENTION_LAYER_INDEXES):
            raise RuntimeError("validated full-attention layers differ from the review profile")
        model_tree = verify_model_inventory(
            inventory, candidate, inventory_sha256=inventory_hash,
            candidate_sha256=candidate_hash,
        )
        data_manifest_path = resolve_manifest_path(DATA_ROOT, "manifest.json")
        data_manifest_bytes, data_manifest_hash = read_approved_child_bytes(
            data_manifest_path, data_manifest_path.parent, max_bytes=MAX_LOG_BYTES,
        )
        if data_manifest_hash != DATA_MANIFEST_SHA256:
            raise RuntimeError("dataset manifest differs from the independently pinned synthetic split")
        data_manifest = json.loads(data_manifest_bytes.decode("utf-8"))
        if (not data_manifest.get("synthetic_only")
                or str(data_manifest["files"]["train"].get("sha256", "")).casefold() != TRAIN_DATA_SHA256
                or str(data_manifest["files"]["dev"].get("sha256", "")).casefold() != DEV_DATA_SHA256):
            raise RuntimeError("pinned synthetic split manifest identity mismatch")
        split_rows: dict[str, list[dict[str, Any]]] = {}
        for split in ("train", "dev"):
            spec = data_manifest["files"][split]
            path = resolve_manifest_path(DATA_ROOT, spec.get("path"))
            expected_hash = TRAIN_DATA_SHA256 if split == "train" else DEV_DATA_SHA256
            if (not isinstance(spec.get("size_bytes"), int)
                    or spec["size_bytes"] <= 0
                    or spec["size_bytes"] > MAX_DATA_SPLIT_BYTES
                    or str(spec.get("sha256", "")).casefold() != expected_hash):
                raise RuntimeError(f"pinned synthetic data hash mismatch: {split}")
            split_bytes, split_hash = read_approved_child_bytes(
                path, path.parent, max_bytes=MAX_DATA_SPLIT_BYTES,
            )
            if (len(split_bytes) != spec["size_bytes"]
                    or split_hash.casefold() != expected_hash):
                raise RuntimeError(f"pinned synthetic data hash mismatch: {split}")
            split_rows[split] = load_jsonl_bytes(split_bytes, split)
        protocol_hash = sha256_file(PROTOCOL)
        runner_hash = sha256_file(Path(__file__).resolve())
        fit_preflight_evidence: dict[str, str] = {}
        if is_fit:
            fit_preflight_evidence = verify_successful_preflight(
                protocol_hash, data_manifest_hash, inventory_hash, data_manifest,
                runner_hash, device_name, runtime_identity, args.adapter_profile,
                adapter_profile, expected_target_module_names(), candidate_hash, config_hash,
                index_hash, license_hash,
            )
        train_rows = split_rows["train"]
        dev_rows = split_rows["dev"]
        if len(train_rows) != EXPECTED_TRAIN_EXAMPLES or len(dev_rows) != 64:
            raise RuntimeError("unexpected train/dev count")
        base_manifest.update({
            "status": "RUNNING",
            "model_inventory_sha256": inventory_hash,
            "model_config_sha256": config_hash,
            "model_index_sha256": index_hash,
            "model_license_sha256": license_hash,
            "protocol_sha256": protocol_hash,
            "dataset_manifest_sha256": data_manifest_hash,
            "device_pci_bus_id": gpu["pci_bus_id"],
            "cuda_version": torch.version.cuda,
            "torch_version": torch.__version__,
            "python_version": sys.version,
            "runtime_identity": runtime_identity,
            "fit_preflight_manifest_sha256": fit_preflight_evidence.get("manifest_sha256"),
            "fit_preflight_resource_log_sha256": fit_preflight_evidence.get("resource_log_sha256"),
        })
        write_json(run_manifest_path, base_manifest)
        require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
        if not args.preflight_only:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(__file__).resolve(), RUNNER_SNAPSHOT)

        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True, trust_remote_code=False)
        if tokenizer.pad_token_id is None:
            if tokenizer.eos_token is None:
                raise RuntimeError("tokenizer has neither a pad token nor an EOS token")
            tokenizer.pad_token = tokenizer.eos_token
        base_model = AutoModelForImageTextToText.from_pretrained(
            MODEL_DIR,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            device_map={"": device},
        )
        model_tree.verify_unchanged()
        model_tree.close()
        model_tree = None
        if any(parameter.device.type != "cuda" for parameter in base_model.parameters()):
            raise RuntimeError("GPU run unexpectedly placed model parameters off cuda:0")
        if getattr(base_model.config, "model_type", None) != "qwen3_5":
            raise RuntimeError("loaded model type is not qwen3_5")
        base_model.config.use_cache = False
        if getattr(base_model.config, "text_config", None) is not None:
            base_model.config.text_config.use_cache = False
        base_model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        if hasattr(base_model, "enable_input_require_grads"):
            base_model.enable_input_require_grads()

        named = list(base_model.named_modules())
        targets = select_lora_targets(named, nn.Linear, args.adapter_profile)
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            target_modules=targets,
            task_type=TaskType.CAUSAL_LM,
        )
        model = get_peft_model(base_model, lora_config)
        trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
        trainable_count = sum(parameter.numel() for parameter in trainable)
        total_count = sum(parameter.numel() for parameter in model.parameters())
        if (not trainable_count or trainable_count / total_count > 0.05
                or trainable_count != expected_lora_parameter_count()):
            raise RuntimeError("unexpected LoRA trainable parameter count")
        if (targets != expected_target_module_names()
                or len(targets) != adapter_profile["expected_target_count"]):
            raise RuntimeError(
                "instantiated adapter does not match the reviewed full-attention profile; "
                f"targets={len(targets)}, trainable_parameters={trainable_count}"
            )
        trainable_names = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
        if (not trainable_names or any("lora_" not in name for name in trainable_names)
                or any(parameter.requires_grad for name, parameter in model.named_parameters()
                       if "vision" in name.casefold())):
            raise RuntimeError("non-LoRA or vision parameters are unexpectedly trainable")
        if is_fit and (str(trainable_count) != fit_preflight_evidence.get("trainable_parameter_count")
                       or hashlib.sha256(str(tokenizer.chat_template).encode("utf-8")).hexdigest()
                       != fit_preflight_evidence.get("chat_template_sha256")):
            raise RuntimeError("fit adapter count or tokenizer template differs from successful preflight")
        base_manifest.update({
            "status": "RUNNING_TRAINING",
            "matched_target_modules": targets,
            "matched_target_count": len(targets),
            "trainable_parameter_count": trainable_count,
            "total_parameter_count": total_count,
            "trainable_fraction": trainable_count / total_count,
            "chat_template_sha256": hashlib.sha256(str(tokenizer.chat_template).encode("utf-8")).hexdigest(),
            "peft_version": peft.__version__,
            "accelerate_version": accelerate.__version__,
            "transformers_version": transformers.__version__,
            "torch_version": torch.__version__,
            "python_version": sys.version,
        })
        write_json(run_manifest_path, base_manifest)

        train_data = tokenize_rows(train_rows, tokenizer, "train")
        dev_data = tokenize_rows(dev_rows, tokenizer, "dev")
        optimizer = torch.optim.AdamW(trainable, lr=LEARNING_RATE, weight_decay=0.0)
        metrics_path = run_log_dir / "epoch-metrics.jsonl"
        optimizer_step = 0
        expected_fit_steps = (
            ((len(train_data) + GRAD_ACCUMULATION - 1) // GRAD_ACCUMULATION) * EPOCHS
        )
        if is_fit and expected_fit_steps != EXPECTED_FIT_OPTIMIZER_STEPS:
            raise RuntimeError(
                "tokenized train split implies an unexpected fit step count: "
                f"{expected_fit_steps}"
            )
        model.train()
        if args.preflight_only:
            optimizer.zero_grad(set_to_none=True)
            require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
            preflight_group = train_data[:GRAD_ACCUMULATION]
            preflight_loss_sum = 0.0
            for row in preflight_group:
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
                batch = as_batch(row, torch, device)
                output = model(**batch, use_cache=False)
                if not torch.isfinite(output.loss):
                    raise RuntimeError("non-finite preflight loss")
                preflight_loss_sum += float(output.loss.detach().item())
                (output.loss / len(preflight_group)).backward()
            preflight_gradient_norm = checked_optimizer_step(optimizer, trainable, torch)
            optimizer_step = 1
            require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
            if monitor.breach_reason:
                raise KeyboardInterrupt(monitor.breach_reason)
            _, resource_log_sha256 = stop_monitor_and_verify(monitor)
            base_manifest.update({
                "status": "PREFLIGHT_COMPLETED",
                "completed_at_utc": utc_now(),
                "optimizer_steps": optimizer_step,
                "preflight_gradient_norm": preflight_gradient_norm,
                "preflight_examples": len(preflight_group),
                "preflight_loss_mean": preflight_loss_sum / len(preflight_group),
                "resource_log_sha256": resource_log_sha256,
            })
            write_json(run_manifest_path, base_manifest)
            print(json.dumps({
                "status": "PREFLIGHT_COMPLETED",
                "optimizer_steps": optimizer_step,
                "run_manifest": str(run_manifest_path),
            }, sort_keys=True), flush=True)
            return 0
        for epoch in range(1, EPOCHS + 1):
            require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
            order = list(range(len(train_data)))
            random.Random(20260927 + epoch).shuffle(order)
            epoch_losses: list[float] = []
            for group_start in range(0, len(order), GRAD_ACCUMULATION):
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
                optimizer.zero_grad(set_to_none=True)
                require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
                group = order[group_start : group_start + GRAD_ACCUMULATION]
                for index in group:
                    if monitor.breach_reason:
                        raise KeyboardInterrupt(monitor.breach_reason)
                    batch = as_batch(train_data[index], torch, device)
                    output = model(**batch, use_cache=False)
                    loss = output.loss
                    if not torch.isfinite(loss):
                        raise RuntimeError(f"non-finite training loss at epoch {epoch}")
                    epoch_losses.append(float(loss.detach().item()))
                    (loss / len(group)).backward()
                if optimizer_step >= EXPECTED_FIT_OPTIMIZER_STEPS:
                    raise RuntimeError("fit exceeded its hard optimizer-step limit")
                gradient_norm = checked_optimizer_step(optimizer, trainable, torch)
                optimizer_step += 1
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
            dev_loss = evaluate_loss(model, dev_data, torch, monitor, device)
            record = {
                "epoch": epoch,
                "optimizer_step": optimizer_step,
                "train_loss_mean": sum(epoch_losses) / len(epoch_losses),
                "dev_loss": dev_loss,
                "last_gradient_norm": gradient_norm,
                "dev_is_selection_metric": False,
                "time_utc": utc_now(),
            }
            with metrics_path.open("ab") as stream:
                line = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
                if metrics_path.stat().st_size + len(line) > MAX_LOG_BYTES:
                    raise RuntimeError("epoch metric log exceeded byte cap")
                stream.write(line)
                stream.flush()
            print(json.dumps(record, sort_keys=True), flush=True)

        if optimizer_step != expected_fit_steps:
            raise RuntimeError(
                "fit ended with an unexpected optimizer-step count; "
                f"expected={expected_fit_steps}, observed={optimizer_step}"
            )
        if monitor.breach_reason:
            raise KeyboardInterrupt(monitor.breach_reason)
        require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
        if trainable_count * 4 + 10 * 1024 * 1024 > MAX_ADAPTER_BYTES:
            raise RuntimeError("bounded pre-save adapter-size estimate exceeds the 100 MB cap")
        require_approved_path(STAGING_OUTPUT)
        model.save_pretrained(STAGING_OUTPUT, safe_serialization=True)
        adapter_files = verified_adapter_inventory(STAGING_OUTPUT)
        adapter_total = sum(item["size_bytes"] for item in adapter_files)
        if adapter_total > MAX_ADAPTER_BYTES:
            raise RuntimeError("adapter output exceeded 100 MB cap")
        _, resource_log_sha256 = stop_monitor_and_verify(monitor)
        require_reservation_checkpoint(active_reservation, expected_job_id, minimum_reservation_bytes)
        finalize_adapter_no_replace(STAGING_OUTPUT, OUTPUT)
        finalized_adapter_files = verified_adapter_inventory(OUTPUT)
        if finalized_adapter_files != adapter_files:
            raise RuntimeError("final adapter files differ from the verified staging inventory")
        if STAGING_OUTPUT.exists():
            raise RuntimeError("adapter staging directory remains after atomic candidate finalization")
        base_manifest.update({
            "status": "COMPLETED",
            "completed_at_utc": utc_now(),
            "optimizer_steps": optimizer_step,
            "expected_optimizer_steps": expected_fit_steps,
            "adapter_total_bytes": adapter_total,
            "adapter_files": finalized_adapter_files,
            "epoch_metrics_sha256": sha256_file(metrics_path),
            "resource_log_sha256": resource_log_sha256,
        })
        write_json(run_manifest_path, base_manifest)
        print(json.dumps({
            "status": "COMPLETED",
            "adapter_dir": str(OUTPUT),
            "adapter_bytes": adapter_total,
            "optimizer_steps": optimizer_step,
            "run_manifest": str(run_manifest_path),
        }, sort_keys=True), flush=True)
        return 0
    except KeyboardInterrupt:
        base_manifest.update({
            "status": "ABORTED_RESOURCE_OR_INTERRUPT",
            "abort_reason": monitor.breach_reason or "INTERRUPTED",
            "ended_at_utc": utc_now(),
        })
        if owns_artifact_dir and run_log_dir.is_dir():
            try:
                write_json(run_manifest_path, base_manifest)
            except BaseException as receipt_error:
                print(f"failed to write abort receipt: {type(receipt_error).__name__}", file=sys.stderr, flush=True)
        print(json.dumps({"status": base_manifest["status"], "reason": base_manifest["abort_reason"]}, sort_keys=True), flush=True)
        return 2
    except BaseException as exc:
        base_manifest.update({
            "status": "FAILED",
            "failure_type": type(exc).__name__,
            "failure_message": str(exc)[:1000],
            "ended_at_utc": utc_now(),
        })
        if owns_artifact_dir and run_log_dir.is_dir():
            try:
                write_json(run_manifest_path, base_manifest)
            except BaseException as receipt_error:
                print(f"failed to write failure receipt: {type(receipt_error).__name__}", file=sys.stderr, flush=True)
        raise
    finally:
        if model_tree is not None:
            model_tree.close()
        monitor.stop_event.set()
        if monitor.is_alive():
            monitor.join(timeout=3)
        if (owns_artifact_dir and run_manifest_path.exists()
                and resource_log.exists() and not monitor.is_alive()):
            try:
                manifest_bytes, _ = read_approved_child_bytes(
                    run_manifest_path, run_log_dir, max_bytes=MAX_LOG_BYTES,
                )
                final_manifest = json.loads(manifest_bytes.decode("utf-8"))
                resource_log_bytes, resource_log_sha256 = read_approved_child_bytes(
                    resource_log, run_log_dir, max_bytes=MAX_LOG_BYTES,
                )
                resource_rows = [
                    json.loads(line) for line in resource_log_bytes.decode("utf-8").splitlines() if line
                ]
                if not resource_rows:
                    raise RuntimeError("resource log has no samples at finalization")
                resource_minima = minimum_resource_fractions(resource_rows)
                floor_breach = (
                    any(
                        row.get("ram_free_fraction", 0) < RAM_FREE_FRACTION
                        or row.get("gpu_free_fraction", 0) < VRAM_FREE_FRACTION
                        or row.get("gpu_uuid") != EXPECTED_GPU_UUID
                        for row in resource_rows
                    )
                )
                scratch_bytes_at_finalize = scratch_tree_bytes(scratch_root)
                scratch_peak_bytes = max(
                    [scratch_bytes_at_finalize,
                     *(row.get("runtime_scratch_bytes", 0) for row in resource_rows)]
                )
                scratch_breach = (
                    scratch_bytes_at_finalize > scratch_limit
                    or any(row.get("runtime_scratch_bytes", 0) > scratch_limit for row in resource_rows)
                )
                finalization_failed = (
                    bool(monitor.breach_reason) or floor_breach or scratch_breach
                ) and final_manifest.get("status") in {"COMPLETED", "PREFLIGHT_COMPLETED"}
                final_manifest["runtime_scratch_bytes_at_finalize"] = scratch_bytes_at_finalize
                final_manifest["runtime_scratch_peak_bytes"] = scratch_peak_bytes
                final_manifest.update(resource_minima)
                if finalization_failed:
                    final_manifest.update({
                        "status": "FAILED_RESOURCE_FINALIZATION",
                        "abort_reason": (monitor.breach_reason or
                                         ("RUNTIME_SCRATCH_BYTE_CAP" if scratch_breach else
                                          "RESOURCE_LOG_FLOOR_OR_IDENTITY_FAILURE")),
                        "ended_at_utc": utc_now(),
                    })
                final_manifest["resource_log_sha256"] = resource_log_sha256
                final_manifest["resource_log_finalized_at_utc"] = utc_now()
                write_json(run_manifest_path, final_manifest)
                if finalization_failed:
                    raise RuntimeError("resource finalization detected a floor or scratch-cap breach")
            except BaseException as finalize_error:
                try:
                    failed_manifest_bytes, _ = read_approved_child_bytes(
                        run_manifest_path, run_log_dir, max_bytes=MAX_LOG_BYTES,
                    )
                    failed_manifest = json.loads(failed_manifest_bytes.decode("utf-8"))
                    if failed_manifest.get("status") in {"COMPLETED", "PREFLIGHT_COMPLETED"}:
                        failed_manifest.update({
                            "status": "FAILED_RESOURCE_FINALIZATION",
                            "abort_reason": f"RESOURCE_FINALIZATION_ERROR:{type(finalize_error).__name__}",
                            "ended_at_utc": utc_now(),
                        })
                        write_json(run_manifest_path, failed_manifest)
                except BaseException as receipt_error:
                    print(f"failed to write finalization failure receipt: {type(receipt_error).__name__}",
                          file=sys.stderr, flush=True)
                raise RuntimeError("resource finalization failed; run is not eligible for success") from finalize_error


def main() -> int:
    try:
        return _run_main()
    finally:
        monitor = _ACTIVE_RESOURCE_MONITOR
        if monitor is not None:
            monitor.stop_event.set()
            if monitor.is_alive():
                monitor.join(timeout=30)
        if (_ACTIVE_SCRATCH_TREE is not None
                and (monitor is None or not monitor.is_alive())):
            _ACTIVE_SCRATCH_TREE.close()


if __name__ == "__main__":
    raise SystemExit(main())
