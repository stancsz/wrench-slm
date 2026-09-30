"""Answer-blind local dev scorer for the inactive Qwen3.5-4B screen-03 LoRA.

The two one-shot modes are ``preflight`` (one dev prompt, base and adapter) and
``score-dev`` (all 64 frozen synthetic dev prompts). This runner is strictly
local, reads no held-out payload, gives the model prompt messages only, and
seals raw predictions before opening references. It is a diagnostic, not a
product-utility or frontier-savings measurement.
"""

from __future__ import annotations

import argparse
import base64
import _thread
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
ROOT = Path(r"C:\wrench-slm-data")
PROJECTIONS = ROOT / "artifacts/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-projections-iter169"
PROMPT_FILE = PROJECTIONS / "prompt-only.jsonl"
PROMPT_MANIFEST = PROJECTIONS / "prompt-manifest.json"
ORACLE_FILE = PROJECTIONS / "oracle-only.jsonl"
ORACLE_MANIFEST = PROJECTIONS / "oracle-manifest.json"
MODEL = ROOT / r"weights/qwen35-4b-hf-cache/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
INVENTORY = ROOT / "artifacts/wrench-gateway-model-research/iter156-qwen35-4b-local-inventory.json"
FIT_LOG = ROOT / "logs/wrench-gateway-model-research/lora-screen-03-qwen35-4b-fit-01"
FIT_MANIFEST = FIT_LOG / "run-manifest.json"
FIT_RESOURCE_LOG = FIT_LOG / "resources.jsonl"
FIT_EPOCHS = FIT_LOG / "epoch-metrics.jsonl"
TRAINER = REPO / "tools/train_gateway_lora_screen_03_4b_gpu.py"
TRAIN_PROTOCOL = REPO / "docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-gpu-protocol-20260928.md"
EVAL_PROTOCOL = REPO / "docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-schema-contract-protocol-20260929.md"
ADAPTER = ROOT / "artifacts/wrench-gateway-model-research/lora-screen-03-qwen35-4b/fit-01/adapter"
ADDONS = ROOT / "envs/wrench-gateway-lora-screen-01-addons"
PYTHON = ROOT / r"envs/wrench-local-synthetic-cp313/Scripts/python.exe"
ARTIFACTS = ROOT / "artifacts/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval"
LOGS = ROOT / "logs/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval"
RESERVATIONS = ROOT / ".budget/reservations"
SCRATCH_PARENT = ROOT / "cache/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval"
PINNED_TREE = REPO / "tools/wrench_windows_pinned_tree.py"

EXPECTED_HEAD = "af01304824f079a64b6c3902397a2034b843511a"
FIT_JOB = "WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-FIT-20260928-01"
MODEL_ID = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
GPU_UUID = "GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021"
GPU_NAME = "NVIDIA GeForce RTX 5060 Ti"
GPU_TOTAL_MIB = 16311
PYTHON_VERSION = (3, 13, 15)
PYTHON_FULL_VERSION = "3.13.15 (tags/v3.13.15:4061bc4, Aug  5 2026, 13:05:39) [MSC v.1944 64 bit (AMD64)]"
VERSIONS = {"torch": "2.14.0+cu132", "transformers": "5.17.0", "peft": "0.21.0", "accelerate": "1.15.0"}
EXPECTED_RUNTIME_IDENTITY = {
    "python_executable": str(PYTHON), "python_version_short": "3.13.15", "python_version": PYTHON_FULL_VERSION,
    "torch_version": VERSIONS["torch"],
    "torch_module_path": r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Lib\site-packages\torch\__init__.py",
    "transformers_version": VERSIONS["transformers"],
    "transformers_module_path": r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Lib\site-packages\transformers\__init__.py",
    "peft_version": VERSIONS["peft"], "peft_module_path": r"C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons\peft\__init__.py",
    "accelerate_version": VERSIONS["accelerate"], "accelerate_module_path": r"C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons\accelerate\__init__.py",
    "addons_path": r"C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons",
}
FIT_MANIFEST_SHA = "d39a9335fbdd107390f053f2460a34845ce3efe2ea473f73060c6eae85278f0e"
FIT_RESOURCES_SHA = "5812cd2be242b407cba8efe8e04813d6973bcb2b9cd61a958849b491b7dfb781"
FIT_EPOCHS_SHA = "889f5fca08faa5c5845bf2c8f2168a371f91108adbfcad55fe28b9d384aa765d"
ADAPTER_MODEL_SHA = "051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c"
ADAPTER_CONFIG_SHA = "f77ecf3c2e87b2586563f3ca6017b74f62b180c31f67260a590ccff85453531f"
ADAPTER_README_SHA = "d402f188ebe4aa2abeb5929611ee4c919d4daee9b69751e499696f871f82dc96"
TRAINER_SHA = "1d7ccbb42af72c41066d52a4cb6448d000c07d395657cae475daaa79363b49b5"
TRAIN_PROTOCOL_SHA = "4b123714bb3c669a98b4d892bd127d69a10adcdb6763cc4059b66fae128e9893"
PREFLIGHT_MANIFEST_SHA = "6ea37a8ba9a1b75cc1e4749085e7eb50e456bfae039faf6e74417ef3dcc353c4"
PREFLIGHT_RESOURCES_SHA = "0629b827e4704445bf3e456b331a8c917c0b135460c019fa99c88d514a769732"
MODEL_INVENTORY_SHA = "30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a"
MODEL_CONFIG_SHA = "ddc63e1c717afa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670"
DATA_MANIFEST_SHA = "11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed"
DEV_SHA = "ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7"
PROMPT_PROJECTION_SHA = "6be3c1e65342711af8fcb7c6f44ed53b5986d31ad93fe0c9ee1542e537268baf"
PROMPT_MANIFEST_SHA = "dc4c3b605f7cc2ac62aa283bdd90b55fbcda7cb4bf526441306ec25508167939"
ORACLE_PROJECTION_SHA = "b6ac5d5c81a1390cc8a9a12d065e8c58cd62242a3308c754641424b1cf783701"
ORACLE_MANIFEST_SHA = "b23449ae7809432b1c5ead7d915b7e8d635ef48fe882cbb7fbcdf8742e1c675e"
PREP_HELPER_SHA = "92e90f2f323bac9f917c06de318fa3b4e89ec0fd5fc7dc00989e2a7ef3ed88b8"
PINNED_TREE_SHA = "e7bfca60adbe5e4284392c878bf9ee6b401c5b92c396ff631ae4d4abbbf3d499"
EXPECTED_CHAT_TEMPLATE_SHA = "a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715"
PREFLIGHT_PREFIX = "WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-"
SCORE_PREFIX = "WRENCH-QWEN35-4B-DEV-SCORE-20260929-"
PREFLIGHT_MIN_RESERVE = 500_000_000
SCORE_MIN_RESERVE = 1_000_000_000
MIN_DESTINATION_FREE = 5 * 1024**3
RAM_FLOOR = VRAM_FLOOR = 0.10
MAX_DEV_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
MAX_TOTAL_OUTPUT_BYTES = 128 * 1024 * 1024
PREFLIGHT_SCRATCH = 256 * 1024**2
SCORE_SCRATCH = 512 * 1024**2
MAX_NEW_TOKENS = 96
MAX_GENERATION_SECONDS = 300
EXPECTED_FAMILIES = {"evidence_select", "retrieve_stop", "compaction_policy", "route"}
FIELDS = {"route", "operation", "selected_evidence_ids", "retrieve_more", "reason_code"}
ROUTES = {"LOCAL_MECHANICAL", "LOCAL_COMPACTION", "FRONTIER", "ABSTAIN"}
OPERATIONS = {"EXACT_RETRIEVE", "COMPACT", "NOOP"}
REASONS = {"EXACT_CURRENT_MATCH", "ENOUGH_CURRENT_EVIDENCE", "REFRESH_STALE_EVIDENCE", "EXACT_EVIDENCE_MISSING", "PRESERVE_HOT_RETRIEVE_COLD", "BOUNDED_EXACT_OPERATION", "OPEN_ENDED_ENGINEERING", "REQUIREMENTS_OR_EVIDENCE_MISSING"}
OUTPUT_SCHEMA_CONTRACT = (
    "Allowed values: route is one of LOCAL_MECHANICAL, LOCAL_COMPACTION, FRONTIER, ABSTAIN; "
    "operation is one of EXACT_RETRIEVE, COMPACT, NOOP; reason_code is one of "
    "EXACT_CURRENT_MATCH, ENOUGH_CURRENT_EVIDENCE, REFRESH_STALE_EVIDENCE, "
    "EXACT_EVIDENCE_MISSING, PRESERVE_HOT_RETRIEVE_COLD, BOUNDED_EXACT_OPERATION, "
    "OPEN_ENDED_ENGINEERING, REQUIREMENTS_OR_EVIDENCE_MISSING. "
    "selected_evidence_ids must contain only IDs shown in the request; retrieve_more must be a boolean."
)
AUTHORITY_KEYS = {"tool", "command", "shell", "permissions", "execute", "modify_file", "write_file"}
_PINNED_TREES: list[Any] = []
_FAILURE_CONTEXT: dict[str, Any] | None = None


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, timeout=5, check=True)
    return result.stdout.strip()


def confined_read(path: Path, maximum: int) -> bytes:
    """Read one regular single-link child through a no-reparse Windows handle."""
    if os.name != "nt" or path.parent.resolve(strict=True) != path.parent.absolute():
        raise RuntimeError("confined evidence reads require a plain Windows parent")
    root = ROOT.resolve(strict=True)
    parent = path.parent.resolve(strict=True)
    if not parent.is_relative_to(root) or path.parent.is_symlink():
        raise RuntimeError("evidence parent escaped approved storage or is linked")
    current = path.parent.absolute()
    while current != root:
        if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
            raise RuntimeError("evidence parent contains a reparse point")
        current = current.parent
    import ctypes
    import msvcrt
    from ctypes import wintypes

    class FT(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]
    class Info(ctypes.Structure):
        _fields_ = [("attrs", wintypes.DWORD), ("c", FT), ("a", FT), ("w", FT),
                    ("volume", wintypes.DWORD), ("size_hi", wintypes.DWORD), ("size_lo", wintypes.DWORD),
                    ("links", wintypes.DWORD), ("index_hi", wintypes.DWORD), ("index_lo", wintypes.DWORD)]
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k.CreateFileW.restype = wintypes.HANDLE
    k.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]
    k.GetFileInformationByHandle.restype = wintypes.BOOL
    k.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    k.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.CloseHandle.restype = wintypes.BOOL
    invalid = ctypes.c_void_p(-1).value

    def final(handle: Any) -> Path:
        buf = ctypes.create_unicode_buffer(32768)
        n = k.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        if n == 0 or n >= len(buf):
            raise ctypes.WinError(ctypes.get_last_error())
        value = buf.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)

    parent_handle = k.CreateFileW(str(parent), 0x80, 1, None, 3, 0x02000000 | 0x00200000, None)
    if not parent_handle or parent_handle == invalid:
        raise ctypes.WinError(ctypes.get_last_error())
    file_handle = None
    try:
        info = Info()
        if not k.GetFileInformationByHandle(parent_handle, ctypes.byref(info)) or info.attrs & 0x400 or not info.attrs & 0x10 or final(parent_handle) != parent:
            raise RuntimeError("evidence parent handle changed or is a reparse point")
        target = parent / path.name
        file_handle = k.CreateFileW(str(target), 0x80000000, 1, None, 3, 0x80 | 0x00200000, None)
        if not file_handle or file_handle == invalid:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Info()
        if not k.GetFileInformationByHandle(file_handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.attrs & (0x400 | 0x10) or info.links != 1 or final(file_handle) != target:
            raise RuntimeError("evidence file is linked, redirected, or non-regular")
        fd = msvcrt.open_osfhandle(int(file_handle), os.O_RDONLY | os.O_BINARY)
        file_handle = None
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if before.st_size > maximum:
                raise RuntimeError("evidence file exceeds its byte cap")
            payload = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
            if len(payload) != before.st_size or len(payload) > maximum or after.st_size != before.st_size or getattr(after, "st_nlink", 1) != 1:
                raise RuntimeError("evidence changed while being read")
            return payload
    finally:
        if file_handle and file_handle != invalid:
            k.CloseHandle(file_handle)
        k.CloseHandle(parent_handle)


def load_pinned_tree() -> Any:
    if sha_file(PINNED_TREE) != PINNED_TREE_SHA:
        raise RuntimeError("pinned-tree helper source hash mismatch")
    import types
    module = types.ModuleType("wrench_dev_eval_pinned_tree")
    source = PINNED_TREE.read_bytes()
    exec(compile(source, str(PINNED_TREE), "exec"), module.__dict__)
    return module


def verify_tree(path: Path, expected: dict[str, str] | None = None) -> Any:
    api = load_pinned_tree()
    tree = api.PinnedTree(ROOT)
    actual = tree.scan(path)
    if expected is not None:
        if set(actual) != set(expected):
            tree.close()
            raise RuntimeError(f"pinned tree file set mismatch: {path}")
        for name, digest in expected.items():
            if actual[name]["sha256"].casefold() != digest.casefold():
                tree.close()
                raise RuntimeError(f"pinned tree hash mismatch: {path / name}")
    return tree


def path_is_reparse(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & flag) or bool(getattr(path, "is_junction", lambda: False)())


def require_root_path(path: Path, *, allow_missing: bool = False) -> Path:
    """Check every extant component under ROOT; this is cooperative, not a lock."""
    root = Path(os.path.abspath(ROOT))
    target = Path(os.path.abspath(path))
    if target != root and not target.is_relative_to(root):
        raise RuntimeError(f"path escaped approved Wrench root: {path}")
    if path_is_reparse(root) or not root.is_dir() or Path(root.resolve(strict=True)) != root:
        raise RuntimeError("approved Wrench root is missing, redirected, or linked")
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if path_is_reparse(current):
            raise RuntimeError(f"path contains a symlink, junction, or reparse point: {current}")
        if current.exists():
            resolved = Path(current.resolve(strict=True))
            if not resolved.is_relative_to(root) or resolved != current:
                raise RuntimeError(f"path component resolves outside its approved location: {current}")
        elif not allow_missing:
            raise RuntimeError(f"required path does not exist: {current}")
    return target


def guarded_mkdir(path: Path) -> None:
    target = require_root_path(path, allow_missing=True)
    root = Path(os.path.abspath(ROOT))
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        require_root_path(current, allow_missing=True)
        if not current.exists():
            current.mkdir()
        require_root_path(current)
        if not current.is_dir():
            raise RuntimeError(f"expected an approved directory: {current}")


def write_new_bytes(path: Path, payload: bytes) -> None:
    if len(payload) > MAX_OUTPUT_BYTES:
        raise RuntimeError("output file exceeded per-file byte cap")
    require_root_path(path.parent)
    require_root_path(path, allow_missing=True)
    with path.open("xb") as stream:
        require_root_path(path)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    require_root_path(path)
    if path.stat().st_size != len(payload):
        raise RuntimeError("output changed after write")


def require_reservation(job_id: str, mode: str) -> dict[str, Any]:
    prefix, minimum = (PREFLIGHT_PREFIX, PREFLIGHT_MIN_RESERVE) if mode == "preflight" else (SCORE_PREFIX, SCORE_MIN_RESERVE)
    if not re.fullmatch(re.escape(prefix) + r"[0-9]{2}", job_id):
        raise RuntimeError("reservation job ID must use the unique mode prefix and two-digit suffix")
    path = require_root_path(RESERVATIONS / f"{job_id}.json")
    record = json.loads(confined_read(path, 64 * 1024).decode("utf-8"))
    if record.get("schema") != "wrench.storage-reservation.v1" or record.get("job_id") != job_id or record.get("storage_root") != str(ROOT) or type(record.get("reserve_bytes")) is not int or record["reserve_bytes"] < minimum:
        raise RuntimeError("active storage reservation identity, root, or size is invalid")
    digest = sha_file(path)
    if shutil.disk_usage(ROOT).free < record["reserve_bytes"] + MIN_DESTINATION_FREE:
        raise RuntimeError("destination volume lacks reservation plus 5 GiB free headroom")
    return {"job_id": job_id, "path": path, "sha256": digest, "record": record,
            "record_bytes": confined_read(path, MAX_OUTPUT_BYTES)}


def check_reservation(reservation: dict[str, Any]) -> None:
    require_root_path(reservation["path"])
    if sha_file(reservation["path"]) != reservation["sha256"]:
        raise RuntimeError("storage reservation changed or disappeared")
    if shutil.disk_usage(ROOT).free < reservation["record"]["reserve_bytes"] + MIN_DESTINATION_FREE:
        raise RuntimeError("destination volume fell below reservation plus 5 GiB headroom")


def load_fit_receipt() -> tuple[dict[str, Any], str]:
    raw = confined_read(FIT_MANIFEST, MAX_OUTPUT_BYTES)
    manifest_digest = sha_bytes(raw)
    if manifest_digest != FIT_MANIFEST_SHA:
        raise RuntimeError("exact fit manifest hash mismatch")
    run = json.loads(raw.decode("utf-8"))
    if run.get("status") != "COMPLETED" or run.get("schema") != "wrench.gateway_lora_screen_03_4b.run.v1" or run.get("job_id") != FIT_JOB or run.get("optimizer_steps") != 96 or run.get("heldout_opened_by_runner") is not False or run.get("model_id") != MODEL_ID or run.get("model_revision") != REVISION:
        raise RuntimeError("fit receipt is not the exact completed inactive screen-03 candidate")
    for path, expected_digest, label in ((FIT_RESOURCE_LOG, FIT_RESOURCES_SHA, "fit resource log"), (FIT_EPOCHS, FIT_EPOCHS_SHA, "fit epoch metrics")):
        if sha_bytes(confined_read(path, MAX_OUTPUT_BYTES)).casefold() != expected_digest:
            raise RuntimeError(f"{label} identity mismatch")
    for path, expected_digest, label in ((TRAINER, TRAINER_SHA, "trainer"), (TRAIN_PROTOCOL, TRAIN_PROTOCOL_SHA, "training protocol")):
        if sha_file(path).casefold() != expected_digest:
            raise RuntimeError(f"{label} identity mismatch")
    if (run.get("resource_log_sha256", "").casefold() != FIT_RESOURCES_SHA
            or run.get("model_inventory_sha256") != MODEL_INVENTORY_SHA
            or run.get("model_config_sha256") != MODEL_CONFIG_SHA
            or run.get("dataset_manifest_sha256") != DATA_MANIFEST_SHA
            or run.get("dev_sha256") != DEV_SHA
            or run.get("runner_sha256") != TRAINER_SHA
            or run.get("protocol_sha256") != TRAIN_PROTOCOL_SHA
            or run.get("chat_template_sha256") != EXPECTED_CHAT_TEMPLATE_SHA
            or run.get("adapter_files") != [
                {"path": "README.md", "sha256": ADAPTER_README_SHA, "size_bytes": 5396},
                {"path": "adapter_config.json", "sha256": ADAPTER_CONFIG_SHA, "size_bytes": 1280},
                {"path": "adapter_model.safetensors", "sha256": ADAPTER_MODEL_SHA, "size_bytes": 6_300_864},
            ]):
        raise RuntimeError("fit manifest does not bind the pinned resource log")
    if (run.get("optimizer_steps") != 96
            or run.get("adapter_profile") != "full-attention-qkvo"
            or run.get("matched_target_count") != 32
            or run.get("trainable_parameter_count") != 1_572_864
            or run.get("fit_mode") is not True
            or run.get("preflight_only") is not False):
        raise RuntimeError("fit receipt does not identify the reviewed 96-step full-attention candidate")
    samples = [json.loads(line) for line in confined_read(FIT_RESOURCE_LOG, MAX_OUTPUT_BYTES).decode("utf-8").splitlines() if line]
    if not samples or any(row.get("gpu_uuid") != GPU_UUID or row.get("gpu_name") != GPU_NAME or row.get("ram_free_fraction", 0) < RAM_FLOOR or row.get("gpu_free_fraction", 0) < VRAM_FLOOR for row in samples):
        raise RuntimeError("fit resource log is empty or records a device/resource-floor mismatch")
    if run.get("adapter_total_bytes") != 6_307_540:
        raise RuntimeError("fit adapter total size differs from the frozen report")
    adapter_expected = {"adapter_model.safetensors": (6_300_864, ADAPTER_MODEL_SHA), "adapter_config.json": (1_280, ADAPTER_CONFIG_SHA), "README.md": (5_396, ADAPTER_README_SHA)}
    tree = verify_tree(ADAPTER, {key: value[1] for key, value in adapter_expected.items()})
    for name, (size, _) in adapter_expected.items():
        if tree.files[name]["size_bytes"] != size:
            tree.close()
            raise RuntimeError(f"adapter size mismatch: {name}")
    tree.verify_unchanged()
    _PINNED_TREES.append(tree)
    return run, manifest_digest


def load_prompt_projection() -> tuple[str, list[dict[str, Any]]]:
    """Load only prompt manifest and prompt-only bytes; never read oracle files."""
    manifest_bytes = confined_read(PROMPT_MANIFEST, MAX_OUTPUT_BYTES)
    if sha_bytes(manifest_bytes) != PROMPT_MANIFEST_SHA:
        raise RuntimeError("prompt projection manifest hash mismatch")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    expected = {"schema": "wrench.gateway_lora_screen_03_4b.dev-projection.v1", "status": "PREPARED_OFFLINE",
                "job_id": "WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929", "projection": "prompt_only",
                "payload_path": "prompt-only.jsonl", "payload_sha256": PROMPT_PROJECTION_SHA,
                "row_count": 64, "source_sha256": DEV_SHA, "source_rows": 64,
                "projection_helper_sha256": PREP_HELPER_SHA, "storage_root": str(ROOT)}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise RuntimeError("prompt projection manifest does not match the pinned dev preparation")
    if (manifest.get("reservation_job_id") != "WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929"
            or manifest.get("reservation_bytes", 0) < 5_000_000
            or not isinstance(manifest.get("reservation_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", manifest["reservation_sha256"])):
        raise RuntimeError("prompt projection lacks its exact storage reservation identity")
    payload = confined_read(PROMPT_FILE, MAX_DEV_BYTES)
    if len(payload) != manifest.get("payload_size_bytes") or sha_bytes(payload) != PROMPT_PROJECTION_SHA:
        raise RuntimeError("prompt-only projection size/hash mismatch")
    prompts = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        messages = row.get("messages")
        if (set(row) != {"example_id", "messages"} or not isinstance(row.get("example_id"), str)
                or not isinstance(messages, list) or len(messages) != 2
                or [m.get("role") for m in messages] != ["system", "user"]
                or any(set(m) != {"role", "content"} or not isinstance(m.get("content"), str) for m in messages)):
            raise RuntimeError(f"prompt-only row contract failed at line {number}")
        model_messages = [{"role": message["role"], "content": message["content"]} for message in messages]
        model_messages[0]["content"] += "\n" + OUTPUT_SCHEMA_CONTRACT
        prompts.append({"example_id": row["example_id"], "messages": model_messages})
    if len(prompts) != 64 or len({row["example_id"] for row in prompts}) != 64:
        raise RuntimeError("prompt projection must contain exactly 64 unique rows")
    return sha_bytes(manifest_bytes), prompts


def load_oracle_projection() -> tuple[str, dict[str, dict[str, Any]]]:
    """Read oracle manifest/payload only after the prediction files are sealed."""
    manifest_bytes = confined_read(ORACLE_MANIFEST, MAX_OUTPUT_BYTES)
    if sha_bytes(manifest_bytes) != ORACLE_MANIFEST_SHA:
        raise RuntimeError("oracle projection manifest hash mismatch")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    expected = {"schema": "wrench.gateway_lora_screen_03_4b.dev-projection.v1", "status": "PREPARED_OFFLINE",
                "job_id": "WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929", "projection": "oracle_only",
                "payload_path": "oracle-only.jsonl", "payload_sha256": ORACLE_PROJECTION_SHA,
                "row_count": 64, "source_sha256": DEV_SHA, "source_rows": 64,
                "projection_helper_sha256": PREP_HELPER_SHA, "storage_root": str(ROOT)}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise RuntimeError("oracle projection manifest does not match the pinned dev preparation")
    if (manifest.get("reservation_job_id") != "WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929"
            or manifest.get("reservation_bytes", 0) < 5_000_000
            or not isinstance(manifest.get("reservation_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", manifest["reservation_sha256"])):
        raise RuntimeError("oracle projection lacks its exact storage reservation identity")
    payload = confined_read(ORACLE_FILE, MAX_DEV_BYTES)
    if len(payload) != manifest.get("payload_size_bytes") or sha_bytes(payload) != ORACLE_PROJECTION_SHA:
        raise RuntimeError("oracle-only projection size/hash mismatch")
    refs: dict[str, dict[str, Any]] = {}
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        if (set(row) != {"example_id", "family", "gold"} or not isinstance(row.get("example_id"), str)
                or row.get("family") not in EXPECTED_FAMILIES or not isinstance(row.get("gold"), dict)
                or row["example_id"] in refs):
            raise RuntimeError(f"oracle-only row contract failed at line {number}")
        refs[row["example_id"]] = {"family": row["family"], "gold": row["gold"]}
    if len(refs) != 64:
        raise RuntimeError("oracle projection must contain exactly 64 unique rows")
    return ORACLE_PROJECTION_SHA, refs


def bootstrap_ci(success: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    # Exact Wilson 95% interval for a binomial proportion.
    z = 1.959963984540054
    p = success / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    margin = z * ((p*(1-p)/n + z*z/(4*n*n)) ** 0.5) / den
    return [max(0.0, center-margin), min(1.0, center+margin)]


def extract_records(user: str) -> list[dict[str, Any]]:
    marker = "Records: "
    pos = user.rfind(marker)
    if pos < 0:
        return []
    try:
        result = json.loads(user[pos + len(marker):])
        return result if isinstance(result, list) and all(isinstance(item, dict) for item in result) else []
    except json.JSONDecodeError:
        return []


def validate(raw: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"valid": False, "errors": ["INVALID_JSON"], "parsed": None, "visible_ids": []}
    records = extract_records(messages[-1]["content"])
    visible = [item["id"] for item in records if isinstance(item.get("id"), str)]
    errors = []
    if not isinstance(value, dict):
        return {"valid": False, "errors": ["NOT_OBJECT"], "parsed": None, "visible_ids": visible}
    if set(value) != FIELDS: errors.append("FIELD_SET")
    if not isinstance(value.get("route"), str) or value.get("route") not in ROUTES: errors.append("ROUTE_ENUM")
    if not isinstance(value.get("operation"), str) or value.get("operation") not in OPERATIONS: errors.append("OPERATION_ENUM")
    if not isinstance(value.get("reason_code"), str) or value.get("reason_code") not in REASONS: errors.append("REASON_ENUM")
    if not isinstance(value.get("retrieve_more"), bool): errors.append("RETRIEVE_TYPE")
    selected = value.get("selected_evidence_ids")
    if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected): errors.append("SOURCE_LIST_TYPE")
    else:
        if len(selected) != len(set(selected)): errors.append("DUPLICATE_SOURCE")
        if any(x not in visible for x in selected): errors.append("INVALID_SOURCE")
    authority = any(str(k).casefold() in AUTHORITY_KEYS for k in value)
    return {"valid": not errors, "errors": errors, "parsed": value, "visible_ids": visible, "authority_violation": authority}


class Monitor(threading.Thread):
    def __init__(self, path: Path, scratch: Path, limit: int, reservation: dict[str, Any]) -> None:
        super().__init__(daemon=True, name="wrench-qwen35-4b-dev-resource-monitor")
        self.path, self.scratch, self.limit, self.reservation = path, scratch, limit, reservation
        self.stop_event = threading.Event()
        self.breach: str | None = None
        self.rows: list[dict[str, Any]] = []

    def sample(self) -> None:
        check_reservation(self.reservation)
        require_root_path(self.scratch, allow_missing=False)
        require_root_path(self.path.parent)
        require_root_path(self.path)
        import psutil
        mem = psutil.virtual_memory()
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=index,uuid,name,memory.total,memory.free", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3, check=True).stdout.strip().split(",")
        if len(gpu) != 5 or gpu[0].strip() != "0" or gpu[1].strip() != GPU_UUID or gpu[2].strip() != GPU_NAME or int(gpu[3]) != GPU_TOTAL_MIB:
            raise RuntimeError("resource monitor found a different GPU identity")
        scratch = 0
        if self.scratch.exists():
            t = load_pinned_tree().PinnedTree(ROOT, allow_writes=True)
            try:
                snap = t.scan(self.scratch, hash_files=False)
                scratch = sum(x["size_bytes"] for x in snap.values())
            finally:
                t.close()
        total, free = int(gpu[3]), int(gpu[4])
        row = {"time_utc": utc_now(), "ram_free_bytes": int(mem.available), "ram_total_bytes": int(mem.total), "ram_free_fraction": mem.available/mem.total,
               "gpu_index": 0, "gpu_uuid": GPU_UUID, "gpu_name": GPU_NAME, "gpu_total_mib": total, "gpu_free_mib": free, "gpu_free_fraction": free/total, "scratch_bytes": scratch}
        line = canonical(row)
        if self.path.stat().st_size + len(line) > MAX_OUTPUT_BYTES:
            raise RuntimeError("resource log exceeded its cap")
        require_root_path(self.path)
        with self.path.open("ab") as f:
            f.write(line); f.flush()
            require_root_path(self.path)
        self.rows.append(row)
        if row["ram_free_fraction"] < RAM_FLOOR: self.breach = "RAM_FREE_BELOW_10_PERCENT"
        elif row["gpu_free_fraction"] < VRAM_FLOOR: self.breach = "VRAM_FREE_BELOW_10_PERCENT"
        elif scratch > self.limit: self.breach = "SCRATCH_CAP_EXCEEDED"
        if self.breach:
            self.stop_event.set()
            _thread.interrupt_main()

    def run(self) -> None:
        try:
            while not self.stop_event.is_set():
                self.sample()
                if self.breach: return
                self.stop_event.wait(1.0)
        except BaseException as e:
            self.breach = f"MONITOR_ERROR:{type(e).__name__}:{str(e)[:200]}"
            self.stop_event.set()
            _thread.interrupt_main()

    def summary(self) -> dict[str, Any]:
        return {"sample_count": len(self.rows), "minimum_ram_free_fraction": min((r["ram_free_fraction"] for r in self.rows), default=None),
                "minimum_gpu_free_fraction": min((r["gpu_free_fraction"] for r in self.rows), default=None),
                "minimum_gpu_free_mib": min((r["gpu_free_mib"] for r in self.rows), default=None),
                "scratch_peak_bytes": max((r["scratch_bytes"] for r in self.rows), default=0), "breach": self.breach}


def summarize_resource_samples(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"sample_count": len(rows),
            "minimum_ram_free_fraction": min((r.get("ram_free_fraction") for r in rows), default=None),
            "minimum_gpu_free_fraction": min((r.get("gpu_free_fraction") for r in rows), default=None),
            "minimum_gpu_free_mib": min((r.get("gpu_free_mib") for r in rows), default=None),
            "scratch_peak_bytes": max((r.get("scratch_bytes", 0) for r in rows), default=0),
            "breach": None}


def generation_success_issues(prediction: dict[str, Any]) -> list[str]:
    """Minimum observable success contract for a one-row local generation."""
    issues: list[str] = []
    if prediction.get("error"):
        issues.append("GENERATION_ERROR")
    if prediction.get("cooperative_limit_exceeded"):
        issues.append("COOPERATIVE_MAX_TIME_EXCEEDED")
    latency = prediction.get("latency_seconds")
    if not isinstance(latency, (int, float)) or latency < 0 or latency >= MAX_GENERATION_SECONDS:
        issues.append("GENERATION_TIME_BUDGET_OVERRUN")
    if not isinstance(prediction.get("raw_output"), str) or not prediction.get("raw_output", "").strip():
        issues.append("EMPTY_GENERATION")
    prompt_tokens = prediction.get("prompt_tokens_local")
    if type(prompt_tokens) is not int or prompt_tokens <= 0:
        issues.append("PROMPT_ENCODING_EMPTY")
    completion_tokens = prediction.get("completion_tokens_local")
    if type(completion_tokens) is not int or completion_tokens <= 0:
        issues.append("COMPLETION_EMPTY")
    elif completion_tokens >= MAX_NEW_TOKENS:
        issues.append("GENERATION_TOKEN_CAP_REACHED")
    validation = prediction.get("validation")
    if not isinstance(validation, dict) or validation.get("valid") is not True:
        issues.append("OUTPUT_SCHEMA_INVALID")
    return issues


def read_sealed_preflight_arm(path: Path, expected_sha: str) -> dict[str, Any]:
    payload = confined_read(path, MAX_OUTPUT_BYTES)
    if sha_bytes(payload) != expected_sha:
        raise RuntimeError(f"sealed preflight prediction hash mismatch: {path.name}")
    rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError(f"preflight prediction file must contain exactly one JSON object: {path.name}")
    return rows[0]


def check_output_budget(roots: list[Path], additional: int = 0) -> None:
    total = 0
    for root in roots:
        require_root_path(root, allow_missing=True)
        if not root.exists(): continue
        if root.is_symlink() or not root.resolve(strict=True).is_relative_to(ROOT.resolve(strict=True)):
            raise RuntimeError("evaluation output root is redirected or outside approved storage")
        for item in root.rglob("*"):
            if item.is_symlink() or not item.resolve(strict=True).is_relative_to(root.resolve(strict=True)):
                raise RuntimeError("evaluation output contains a link or redirected path")
            if item.is_file(): total += item.stat().st_size
    if total + additional > MAX_TOTAL_OUTPUT_BYTES:
        raise RuntimeError("aggregate output cap exceeded")


def write_json(path: Path, value: Any, reservation: dict[str, Any], roots: list[Path]) -> None:
    check_reservation(reservation)
    payload = canonical(value)
    if len(payload) > MAX_OUTPUT_BYTES: raise RuntimeError("receipt exceeds per-file output cap")
    check_output_budget(roots, len(payload))
    temp = path.with_suffix(path.suffix + ".tmp")
    require_root_path(path.parent)
    require_root_path(temp, allow_missing=True)
    require_root_path(path, allow_missing=True)
    with temp.open("xb") as stream:
        require_root_path(temp)
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    require_root_path(temp)
    require_root_path(path, allow_missing=True)
    temp.replace(path)
    require_root_path(path)


def bootstrap_runtime() -> None:
    if os.name != "nt" or Path(sys.executable).resolve() != PYTHON.resolve() or sys.version_info[:3] != PYTHON_VERSION:
        raise RuntimeError("the pinned Windows Python 3.13.15 runtime is required")
    sys.path.insert(0, str(ADDONS))
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = GPU_UUID
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["OMP_NUM_THREADS"] = "4"
    os.environ["MKL_NUM_THREADS"] = "4"


def prepare_model() -> tuple[Any, Any, Any, Any, Any, Any]:
    bootstrap_runtime()
    import torch
    import transformers
    import peft
    import accelerate
    if {"torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__, "accelerate": accelerate.__version__} != VERSIONS:
        raise RuntimeError("pinned runtime package version mismatch")
    if (Path(torch.__file__).resolve() != Path(r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Lib\site-packages\torch\__init__.py").resolve()
            or Path(transformers.__file__).resolve() != Path(r"C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Lib\site-packages\transformers\__init__.py").resolve()
            or Path(peft.__file__).resolve() != ADDONS / "peft/__init__.py"
            or Path(accelerate.__file__).resolve() != ADDONS / "accelerate/__init__.py"):
        raise RuntimeError("runtime module origins differ from the fit receipt")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        raise RuntimeError("the pinned single CUDA BF16 device is unavailable")
    torch.cuda.set_device(0); torch.set_num_threads(4)
    if torch.cuda.get_device_name(0) != GPU_NAME:
        raise RuntimeError("PyTorch device name differs from pinned GPU")
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False)
    if tok.pad_token_id is None: tok.pad_token = tok.eos_token
    device = torch.device("cuda:0")
    base = AutoModelForImageTextToText.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16, low_cpu_mem_usage=True, device_map={"": device})
    if any(parameter.device.type != "cuda" for parameter in base.parameters()):
        raise RuntimeError("GPU preflight unexpectedly placed base model parameters off cuda:0")
    base.eval()
    if hashlib.sha256(str(tok.chat_template).encode("utf-8")).hexdigest() != EXPECTED_CHAT_TEMPLATE_SHA:
        raise RuntimeError("tokenizer chat template does not match the fit receipt")
    adapted = PeftModel.from_pretrained(base, ADAPTER, local_files_only=True, is_trainable=False)
    if any(parameter.device.type != "cuda" for parameter in adapted.parameters()):
        raise RuntimeError("GPU preflight unexpectedly placed adapter model parameters off cuda:0")
    adapted.eval()
    return torch, transformers, peft, base, tok, adapted


def generate(torch: Any, model: Any, tokenizer: Any, messages: list[dict[str, str]]) -> dict[str, Any]:
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    encoded = tokenizer(prompt, add_special_tokens=False, return_tensors="pt")
    count = int(encoded["input_ids"].shape[-1])
    encoded = {k: v.to("cuda:0") for k, v in encoded.items() if k in {"input_ids", "attention_mask"}}
    start = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(**encoded, do_sample=False, num_beams=1, max_new_tokens=MAX_NEW_TOKENS, max_time=MAX_GENERATION_SECONDS, use_cache=True, pad_token_id=tokenizer.pad_token_id)
    elapsed = time.perf_counter() - start
    tokens = output[0, count:]
    return {"raw_output": tokenizer.decode(tokens, skip_special_tokens=True).strip(), "prompt_tokens_local": count,
            "completion_tokens_local": int(tokens.numel()), "latency_seconds": elapsed,
            "cooperative_limit_exceeded": elapsed >= MAX_GENERATION_SECONDS}


def score_predictions(refs: dict[str, dict[str, Any]], preds: dict[str, dict[str, Any]], tokenizer: Any) -> dict[str, Any]:
    n = len(refs); exact = valid = route = invalid_ref = duplicate = authority = truncated = timeout = 0
    routes = {name: 0 for name in sorted(ROUTES | {"INVALID", "COOPERATIVE_LIMIT", "ERROR"})}
    families: dict[str, list[int]] = {}; failures = []; prompt_tokens = output_tokens = 0
    for example, ref in refs.items():
        p = preds[example]; validation = p["validation"]; value = validation.get("parsed"); gold = ref["gold"]
        is_valid = bool(validation.get("valid")) and not p.get("cooperative_limit_exceeded") and not p.get("error")
        valid += int(is_valid); exact += int(is_valid and value == gold); route += int(is_valid and value.get("route") == gold.get("route"))
        prompt_tokens += p.get("prompt_tokens_local", 0); output_tokens += p.get("completion_tokens_local", 0)
        timeout += int(bool(p.get("cooperative_limit_exceeded"))); truncated += int(p.get("completion_tokens_local") == MAX_NEW_TOKENS)
        selected = value.get("selected_evidence_ids", []) if isinstance(value, dict) else []
        visible = validation.get("visible_ids", [])
        invalid_ref += int(any(x not in visible for x in selected) if isinstance(selected, list) else True)
        duplicate += int("DUPLICATE_SOURCE" in validation.get("errors", []))
        authority += int(bool(validation.get("authority_violation")))
        category = "COOPERATIVE_LIMIT" if p.get("cooperative_limit_exceeded") else "ERROR" if p.get("error") else value.get("route") if isinstance(value, dict) and value.get("route") in ROUTES else "INVALID"
        routes[category] += 1
        bin_ = families.setdefault(ref["family"], [0, 0]); bin_[0] += int(is_valid and value == gold); bin_[1] += 1
        if p.get("error"): failures.append({"example_id": example, "failure": p["error"]})
        elif p.get("cooperative_limit_exceeded"): failures.append({"example_id": example, "failure": "COOPERATIVE_TIME_BUDGET_EXCEEDED"})
        elif not validation.get("valid"): failures.append({"example_id": example, "failure": validation.get("errors")})
        elif not (is_valid and value == gold): failures.append({"example_id": example, "failure": "DECISION_MISMATCH", "expected": gold, "predicted": value})
    return {"n": n, "exact_decision_accuracy": {"successes": exact, "total": n, "rate": exact/n if n else None, "wilson_ci95": bootstrap_ci(exact,n)},
            "valid_schema_rate": {"successes": valid, "total": n, "rate": valid/n if n else None, "wilson_ci95": bootstrap_ci(valid,n)},
            "route_accuracy": {"successes": route, "total": n, "rate": route/n if n else None, "wilson_ci95": bootstrap_ci(route,n)},
            "route_counts": routes, "invalid_reference_rate": {"count": invalid_ref, "total": n}, "duplicate_source_count": duplicate,
            "authority_violation_count": authority, "generation_limit_hit_count": truncated, "timeout_count": timeout,
            "by_family": {k: {"successes": v[0], "total": v[1], "rate": v[0]/v[1] if v[1] else None} for k,v in sorted(families.items())},
        "cooperative_time_budget_exceeded_count": timeout,
        "mean_latency_seconds": sum(p.get("latency_seconds",0) for p in preds.values())/n if n else None,
            "p95_latency_seconds_nearest_rank": sorted(p.get("latency_seconds",0) for p in preds.values())[max(0, int(0.95*n+0.999999)-1)] if n else None,
            "local_tokenizer_prompt_count": prompt_tokens, "local_tokenizer_completion_count": output_tokens, "local_tokenizer_total_count": prompt_tokens+output_tokens,
            "token_count_interpretation": "Local tokenizer counts only; not Frontier API usage, billing, or token savings.", "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "score-dev"), required=True)
    parser.add_argument("--storage-reservation-job-id", required=True)
    parser.add_argument("--preflight-receipt", type=Path)
    args = parser.parse_args()
    mode = args.mode
    if mode == "score-dev" and args.preflight_receipt is None: parser.error("score-dev requires --preflight-receipt")
    if git_head() != EXPECTED_HEAD: raise RuntimeError("repository HEAD differs from the reviewed package base")
    reservation = require_reservation(args.storage_reservation_job_id, mode)
    evaluator_sha = sha_file(Path(__file__).resolve())
    eval_protocol_sha = sha_file(EVAL_PROTOCOL)
    run, fit_sha = load_fit_receipt()
    inv_raw = confined_read(INVENTORY, MAX_OUTPUT_BYTES)
    if sha_bytes(inv_raw) != MODEL_INVENTORY_SHA: raise RuntimeError("model inventory hash mismatch")
    inventory = json.loads(inv_raw.decode("utf-8"))
    if inventory.get("repository") != MODEL_ID or inventory.get("revision") != REVISION or inventory.get("file_count") != 14 or inventory.get("total_bytes") != 9_342_907_469: raise RuntimeError("local base inventory identity mismatch")
    model_tree = verify_tree(MODEL, {item["file"]: item["sha256"] for item in inventory["files"]})
    _PINNED_TREES.append(model_tree)
    if sha_file(MODEL / "config.json") != MODEL_CONFIG_SHA: raise RuntimeError("pinned model config hash mismatch")
    if sha_file(PINNED_TREE) != PINNED_TREE_SHA or sha_file(TRAINER) != TRAINER_SHA or sha_file(TRAIN_PROTOCOL) != TRAIN_PROTOCOL_SHA: raise RuntimeError("code or model helper identity mismatch")
    eval_protocol_sha = sha_file(EVAL_PROTOCOL)
    if not ROOT.is_dir() or not PROJECTIONS.is_dir() or not MODEL.is_dir() or not ADDONS.is_dir(): raise RuntimeError("required approved local inputs are missing")

    preflight_dir = ARTIFACTS / f"preflight-{args.storage_reservation_job_id}"
    score_dir = ARTIFACTS / f"score-{args.storage_reservation_job_id}"
    out = preflight_dir if mode == "preflight" else score_dir
    log = LOGS / f"{mode}-{args.storage_reservation_job_id}"
    if out.exists() or log.exists(): raise RuntimeError("job output path already exists; job IDs are one-shot")
    check_reservation(reservation)
    scratch = SCRATCH_PARENT / args.storage_reservation_job_id
    resource_path = log / "resources.jsonl"
    result_path = out / ("preflight.json" if mode == "preflight" else "result.json")
    cache_dirs = [scratch / name for name in (
        "hf_home", "hf_hub_cache", "hf_assets_cache", "transformers_cache", "torch_home",
        "xdg_cache_home", "temp", "tmp", "tmpdir", "torch_extensions_dir",
        "torchinductor_cache_dir", "triton_cache_dir", "cuda_cache_path")]
    intended_paths = [ARTIFACTS, LOGS, SCRATCH_PARENT, out, log, scratch,
                      resource_path, result_path, out / "base-predictions.jsonl",
                      out / "lora-predictions.jsonl", *cache_dirs]
    for path in intended_paths:
        require_root_path(path, allow_missing=True)
    guarded_mkdir(ARTIFACTS); guarded_mkdir(LOGS); guarded_mkdir(SCRATCH_PARENT)
    guarded_mkdir(out); guarded_mkdir(log); guarded_mkdir(scratch)
    for path in cache_dirs:
        require_root_path(path, allow_missing=True)
        guarded_mkdir(path)
    global _FAILURE_CONTEXT
    _FAILURE_CONTEXT = {"out": out, "resource_path": log / "resources.jsonl", "mode": mode, "job_id": args.storage_reservation_job_id,
                        "reservation": reservation, "evaluator_sha256": evaluator_sha, "protocol_sha256": eval_protocol_sha}
    write_new_bytes(resource_path, b"")
    for key in ("HF_HOME", "HF_HUB_CACHE", "HF_ASSETS_CACHE", "TRANSFORMERS_CACHE", "TORCH_HOME", "XDG_CACHE_HOME", "TEMP", "TMP", "TMPDIR", "TORCH_EXTENSIONS_DIR", "TORCHINDUCTOR_CACHE_DIR", "TRITON_CACHE_DIR", "CUDA_CACHE_PATH"):
        os.environ[key] = str(scratch / key.lower())
    monitor = Monitor(resource_path, scratch, PREFLIGHT_SCRATCH if mode == "preflight" else SCORE_SCRATCH, reservation)
    monitor.sample()
    if monitor.breach: raise RuntimeError(monitor.breach)
    monitor.start()
    started = time.perf_counter()
    preflight_receipt_sha = None
    if mode == "score-dev":
        preflight_path = Path(os.path.abspath(args.preflight_receipt))
        expected_preflight = ARTIFACTS / f"preflight-{args.preflight_receipt.parent.name.removeprefix('preflight-')}" / "preflight.json"
        if preflight_path != expected_preflight.absolute() or not preflight_path.is_file():
            raise RuntimeError("score-dev requires the exact completed preflight receipt path")
        receipt_bytes = confined_read(preflight_path, MAX_OUTPUT_BYTES)
        preflight_receipt_sha = sha_bytes(receipt_bytes)
        preflight = json.loads(receipt_bytes.decode("utf-8"))
        if (preflight.get("schema") != "wrench.gateway_lora_screen_03_4b.dev-eval.v1"
                or preflight.get("mode") != "preflight"
                or not re.fullmatch(re.escape(PREFLIGHT_PREFIX) + r"[0-9]{2}", str(preflight.get("job_id", "")))
                or preflight.get("prompt_n") != 1
                or preflight.get("evaluator_sha256") != evaluator_sha
                or preflight.get("evaluation_protocol_sha256") != eval_protocol_sha
                or preflight.get("training_manifest_sha256") != fit_sha
                or preflight.get("training_protocol_sha256") != TRAIN_PROTOCOL_SHA
                or preflight.get("training_job_id") != FIT_JOB
                or preflight.get("model_id") != MODEL_ID
                or preflight.get("model_revision") != REVISION
                or preflight.get("model_config_sha256") != MODEL_CONFIG_SHA
                or preflight.get("dataset_manifest_sha256") != DATA_MANIFEST_SHA
                or preflight.get("model_inventory_sha256") != MODEL_INVENTORY_SHA
                or preflight.get("dev_sha256") != DEV_SHA
                or preflight.get("adapter_sha256") != ADAPTER_MODEL_SHA
                or preflight.get("prompt_projection_sha256") != PROMPT_PROJECTION_SHA
                or preflight.get("prompt_manifest_sha256") != PROMPT_MANIFEST_SHA
                or preflight.get("runtime_identity") != EXPECTED_RUNTIME_IDENTITY
                or preflight.get("gpu_uuid") != GPU_UUID
                or preflight.get("gpu_name") != GPU_NAME
                or preflight.get("gpu_total_mib") != GPU_TOTAL_MIB
                or preflight.get("reservation_job_id") != preflight.get("job_id")
                or preflight.get("reservation_sha256") != preflight.get("reservation_identity", {}).get("sha256")
                or preflight.get("chat_template_sha256") != EXPECTED_CHAT_TEMPLATE_SHA
                or preflight.get("frontier_calls") != 0):
            raise RuntimeError("preflight receipt does not match the current exact scorer package and inputs")
        prior_reservation = preflight.get("reservation_identity")
        if not isinstance(prior_reservation, dict):
            raise RuntimeError("preflight receipt has no reservation identity record")
        prior_id = preflight.get("job_id")
        try:
            prior_bytes = base64.b64decode(prior_reservation["record_bytes_base64"], validate=True)
        except Exception as exc:
            raise RuntimeError("preflight reservation record encoding is invalid") from exc
        prior_record = json.loads(prior_bytes.decode("utf-8"))
        prior_hash = sha_bytes(prior_bytes)
        if (prior_reservation.get("job_id") != prior_id
                or prior_reservation.get("storage_root") != str(ROOT)
                or prior_reservation.get("reserve_bytes", 0) < PREFLIGHT_MIN_RESERVE
                or prior_reservation.get("sha256") != prior_hash
                or prior_record.get("job_id") != prior_id
                or prior_record.get("schema") != "wrench.storage-reservation.v1"
                or prior_record.get("storage_root") != str(ROOT)
                or prior_record.get("reserve_bytes") != prior_reservation.get("reserve_bytes")):
            raise RuntimeError("preflight reservation identity or hash is invalid")
        active_preflight_reservation = RESERVATIONS / f"{prior_id}.json"
        if active_preflight_reservation.exists():
            require_root_path(active_preflight_reservation)
            if sha_bytes(confined_read(active_preflight_reservation, MAX_OUTPUT_BYTES)) != prior_hash:
                raise RuntimeError("active preflight reservation differs from its receipt")
        preflight_predictions = preflight.get("prediction_hashes")
        if not isinstance(preflight_predictions, dict) or set(preflight_predictions) != {"base-predictions.jsonl", "lora-predictions.jsonl"}:
            raise RuntimeError("preflight does not bind one sealed prediction file per model arm")
        preflight_arm_rows = {
            arm: read_sealed_preflight_arm(preflight_path.parent / f"{arm}-predictions.jsonl",
                                           preflight_predictions[f"{arm}-predictions.jsonl"])
            for arm in ("base", "lora")
        }
        prediction_ids = {arm: row.get("example_id") for arm, row in preflight_arm_rows.items()}
        if (not isinstance(prediction_ids["base"], str) or not prediction_ids["base"]
                or prediction_ids["base"] != prediction_ids["lora"]
                or preflight.get("prediction_example_ids") != prediction_ids):
            raise RuntimeError("preflight sealed predictions do not identify the same recorded prompt")
        preflight_prediction_issues = {
            arm: generation_success_issues(row) for arm, row in preflight_arm_rows.items()
        }
        preflight_resource = Path(preflight.get("resource_log", ""))
        expected_resource = LOGS / f"preflight-{preflight.get('job_id')}" / "resources.jsonl"
        if preflight_resource != expected_resource:
            raise RuntimeError("preflight resource log path differs from the receipt job identity")
        resource_bytes = confined_read(expected_resource, MAX_OUTPUT_BYTES)
        if sha_bytes(resource_bytes) != preflight.get("resource_log_sha256"):
            raise RuntimeError("preflight resource log hash mismatch")
        prior_samples = [json.loads(line) for line in resource_bytes.decode("utf-8").splitlines() if line]
        if not prior_samples or any(r.get("gpu_uuid") != GPU_UUID or r.get("gpu_name") != GPU_NAME or r.get("gpu_index") != 0 or r.get("gpu_total_mib") != GPU_TOTAL_MIB or r.get("ram_free_fraction", 0) < RAM_FLOOR or r.get("gpu_free_fraction", 0) < VRAM_FLOOR or r.get("scratch_bytes", SCORE_SCRATCH + 1) > PREFLIGHT_SCRATCH for r in prior_samples):
            raise RuntimeError("preflight resource log is empty or breaches a resource floor")
        prior_summary = preflight.get("resource_samples")
        if prior_summary != summarize_resource_samples(prior_samples):
            raise RuntimeError("preflight resource summary differs from its pinned samples")
        if (preflight.get("status") != "PREFLIGHT_COMPLETED"
                or any(preflight_prediction_issues.values())
                or preflight.get("preflight_failures") not in (None, [], {})):
            raise RuntimeError("score-dev rejects a failed, errored, timed-out, or over-budget preflight after verifying its sealed predictions and resources")
    prompt_manifest_sha, prompts = load_prompt_projection()
    if mode == "preflight": prompts = prompts[:1]
    template_hash = run.get("chat_template_sha256")
    if not isinstance(template_hash, str) or len(template_hash) != 64: raise RuntimeError("fit receipt lacks tokenizer template identity")
    torch, transformers, peft, base, tokenizer, adapted = prepare_model()
    runtime_identity = {
        **EXPECTED_RUNTIME_IDENTITY,
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": sys.version,
        "torch_module_path": str(Path(torch.__file__).resolve()),
        "transformers_module_path": str(Path(transformers.__file__).resolve()),
        "peft_module_path": str(Path(peft.__file__).resolve()),
    }
    import accelerate
    runtime_identity["accelerate_module_path"] = str(Path(accelerate.__file__).resolve())
    if runtime_identity != EXPECTED_RUNTIME_IDENTITY:
        raise RuntimeError("loaded runtime identity differs from the exact pinned runtime")
    predictions: dict[str, dict[str, Any]] = {"base": {}, "lora": {}}
    for arm, model in (("base", adapted), ("lora", adapted)):
        if arm == "base": adapter_context = adapted.disable_adapter()
        else: adapter_context = __import__("contextlib").nullcontext()
        with adapter_context:
            for item in prompts:
                check_reservation(reservation)
                start_one = time.perf_counter()
                try:
                    value = generate(torch, model, tokenizer, item["messages"])
                    value["error"] = None
                except Exception as exc:
                    value = {"raw_output": "", "prompt_tokens_local": 0, "completion_tokens_local": 0,
                             "latency_seconds": time.perf_counter()-start_one, "cooperative_limit_exceeded": False,
                             "error": f"{type(exc).__name__}:{str(exc)[:400]}"}
                value.update({"example_id": item["example_id"], "input_sha256": sha_bytes(canonical(item["messages"])),
                              "validation": validate(value["raw_output"], item["messages"])})
                predictions[arm][item["example_id"]] = value
                if monitor.breach: raise RuntimeError(monitor.breach)
        if arm == "base": continue
    # Raw outputs are sealed and hashed before the oracle-only file is opened.
    prediction_hashes = {}
    for arm in ("base", "lora"):
        path = out / f"{arm}-predictions.jsonl"
        require_root_path(path, allow_missing=True)
        require_root_path(path.parent)
        with path.open("xb") as stream:
            for item in prompts:
                line = canonical(predictions[arm][item["example_id"]])
                if path.stat().st_size + len(line) > MAX_OUTPUT_BYTES: raise RuntimeError("prediction file cap exceeded")
                check_reservation(reservation); check_output_budget([ARTIFACTS, LOGS], len(line)); require_root_path(path); stream.write(line); stream.flush(); require_root_path(path)
                if path.stat().st_size > MAX_OUTPUT_BYTES: raise RuntimeError("prediction file exceeded its byte cap")
        prediction_hashes[path.name] = sha_file(path)
    if monitor.breach: raise RuntimeError(monitor.breach)
    preflight_failures: dict[str, list[str]] = {}
    if mode == "preflight":
        for arm in ("base", "lora"):
            example_id = prompts[0]["example_id"]
            issues = generation_success_issues(predictions[arm][example_id])
            if issues:
                preflight_failures[arm] = issues
    summary = None
    refs_sha = None
    paired = None
    if mode == "score-dev":
        refs_sha, refs = load_oracle_projection()
        if set(refs) != {item["example_id"] for item in prompts}:
            raise RuntimeError("prompt prediction IDs and post-seal oracle IDs differ")
        summary = {arm: score_predictions(refs, predictions[arm], tokenizer) for arm in ("base", "lora")}
        differences = [
            int(predictions["lora"][k]["validation"].get("valid") and not predictions["lora"][k].get("cooperative_limit_exceeded") and not predictions["lora"][k].get("error") and predictions["lora"][k]["validation"].get("parsed") == refs[k]["gold"])
            - int(predictions["base"][k]["validation"].get("valid") and not predictions["base"][k].get("cooperative_limit_exceeded") and not predictions["base"][k].get("error") and predictions["base"][k]["validation"].get("parsed") == refs[k]["gold"])
            for k in refs
        ]
        paired = {"mean_lora_minus_base_exact_accuracy": sum(differences)/len(differences), "paired_cases": len(differences), "paired_differences": differences}
    monitor.stop_event.set(); monitor.join(timeout=5)
    if monitor.is_alive() or monitor.breach: raise RuntimeError(monitor.breach or "resource monitor failed to stop")
    if not monitor.rows or min(r["ram_free_fraction"] for r in monitor.rows) < RAM_FLOOR or min(r["gpu_free_fraction"] for r in monitor.rows) < VRAM_FLOOR: raise RuntimeError("recorded resource floor violation")
    for tree in reversed(_PINNED_TREES):
        tree.verify_unchanged(); tree.close()
    _PINNED_TREES.clear()
    output = {"schema": "wrench.gateway_lora_screen_03_4b.dev-eval.v1",
              "status": ("PREFLIGHT_FAILED" if preflight_failures else "PREFLIGHT_COMPLETED") if mode == "preflight" else "DEV_DIAGNOSTIC_COMPLETED",
              "mode": mode, "job_id": args.storage_reservation_job_id, "created_at_utc": utc_now(), "repo_head": git_head(),
              "evaluator_sha256": evaluator_sha, "evaluation_protocol_sha256": eval_protocol_sha,
              "training_job_id": FIT_JOB, "training_manifest_sha256": fit_sha, "training_resource_log_sha256": FIT_RESOURCES_SHA,
              "training_epoch_metrics_sha256": FIT_EPOCHS_SHA, "training_protocol_sha256": TRAIN_PROTOCOL_SHA,
              "trainer_sha256": TRAINER_SHA, "preflight_manifest_sha256": PREFLIGHT_MANIFEST_SHA, "preflight_resources_sha256": PREFLIGHT_RESOURCES_SHA,
              "model_id": MODEL_ID, "model_revision": REVISION, "model_inventory_sha256": MODEL_INVENTORY_SHA, "model_config_sha256": MODEL_CONFIG_SHA,
              "dataset_manifest_sha256": DATA_MANIFEST_SHA, "dev_sha256": DEV_SHA,
              "prompt_projection_sha256": PROMPT_PROJECTION_SHA, "prompt_manifest_sha256": prompt_manifest_sha,
              "oracle_projection_sha256_after_prediction_seal": refs_sha, "oracle_manifest_sha256_after_prediction_seal": ORACLE_MANIFEST_SHA if refs_sha else None,
              "adapter_sha256": ADAPTER_MODEL_SHA,
              "chat_template_sha256": template_hash, "runtime": {"python": sys.version, "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__},
              "runtime_identity": runtime_identity,
              "gpu_uuid": GPU_UUID, "gpu_name": GPU_NAME, "gpu_total_mib": GPU_TOTAL_MIB,
              "decoding": {"do_sample": False, "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS,
                           "max_time_seconds_cooperative_only": MAX_GENERATION_SECONDS,
                           "external_hard_job_timeout_seconds": 900 if mode == "preflight" else 14_400},
              "prompt_n": len(prompts), "dev_n": 64, "prediction_hashes": prediction_hashes,
              "prediction_example_ids": {arm: next(iter(predictions[arm])) for arm in ("base", "lora")},
              "preflight_failures": preflight_failures if mode == "preflight" else None,
              "reference_sha256_after_prediction_seal": refs_sha,
              "arms": summary, "paired_lora_minus_base_exact_accuracy": paired, "resource_samples": monitor.summary(),
              "reservation_job_id": reservation["job_id"], "reservation_sha256": reservation["sha256"],
              "reservation_identity": {"job_id": reservation["job_id"], "storage_root": str(ROOT),
                                       "reserve_bytes": reservation["record"]["reserve_bytes"],
                                       "sha256": reservation["sha256"],
                                       "record_bytes_base64": base64.b64encode(reservation["record_bytes"]).decode("ascii")},
              "resource_log": str(resource_path), "resource_log_sha256": sha_file(resource_path), "preflight_receipt_sha256": preflight_receipt_sha,
              "elapsed_seconds": time.perf_counter()-started, "frontier_calls": 0,
              "limitations": ["synthetic development split diagnostic only", "no held-out payload was opened", "not representative coding-engineering effectiveness", "local tokenizer counts are not Frontier API usage or savings", "no provider request or billed usage occurred", "does not establish 95/5/95 or all-day engineering acceptance"]}
    write_json(out / ("preflight.json" if mode == "preflight" else "result.json"), output, reservation, [ARTIFACTS, LOGS])
    if mode == "preflight" and preflight_failures:
        raise RuntimeError("preflight generated a sealed PREFLIGHT_FAILED receipt")
    _FAILURE_CONTEXT = None
    return 0


def write_failure(exc: BaseException) -> None:
    context = _FAILURE_CONTEXT
    if context is None:
        return
    out = context["out"]
    failure = out / "failure.json"
    if failure.exists():
        return
    monitor = globals().get("monitor")
    if monitor is not None:
        monitor.stop_event.set()
        if monitor.is_alive(): monitor.join(timeout=5)
    try:
        resources = confined_read(context["resource_path"], MAX_OUTPUT_BYTES)
        resource_info = {"path": str(context["resource_path"]), "sha256": sha_bytes(resources), "size_bytes": len(resources)}
    except BaseException as resource_error:
        resource_info = {"read_error": f"{type(resource_error).__name__}:{str(resource_error)[:300]}"}
    payload = canonical({"schema": "wrench.gateway_lora_screen_03_4b.dev-eval-failure.v1", "status": "FAILED",
                         "mode": context["mode"], "job_id": context["job_id"], "time_utc": utc_now(),
                         "repo_head": git_head(), "evaluator_sha256": context["evaluator_sha256"],
                         "evaluation_protocol_sha256": context["protocol_sha256"], "resource_log": resource_info,
                         "error_type": type(exc).__name__, "error": str(exc)[:1000]})
    if len(payload) <= MAX_OUTPUT_BYTES:
        try:
            reservation = context.get("reservation")
            if reservation is None:
                return
            check_reservation(reservation)
            check_output_budget([ARTIFACTS, LOGS], len(payload))
            require_root_path(out)
            require_root_path(failure, allow_missing=True)
            write_new_bytes(failure, payload)
        except OSError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        write_failure(exc)
        raise
