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
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVED_ROOT = Path(r"C:\wrench-slm-data")
DATA_ROOT = APPROVED_ROOT / "datasets/wrench-gateway-model-research/lora-screen-01"
MODEL_DIR = APPROVED_ROOT / "weights/Qwen3.5-0.8B"
MODEL_CANDIDATE = REPO_ROOT / "docs/northstar/model-candidate.json"
MODEL_INVENTORY = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-01-model-inventory.json"
TRAIN_LOG_DIR = APPROVED_ROOT / "logs/wrench-gateway-model-research/lora-screen-01"
TRAIN_MANIFEST = TRAIN_LOG_DIR / "run-manifest.json"
TRAIN_PROTOCOL = REPO_ROOT / "docs/evals/wrench-gateway-model-research/lora-screen-01-protocol-20260927.md"
EVAL_PROTOCOL = REPO_ROOT / "docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md"
GENERATOR_SOURCE = REPO_ROOT / "tools/generate_gateway_lora_screen_01.py"
EVALUATOR_SOURCE = Path(__file__).resolve()
TRAIN_SOURCE_SNAPSHOT = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-01/train_gateway_lora_screen_01.fit-source.py"
ADAPTER_DIR = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-01/adapter"
EVAL_ARTIFACTS = APPROVED_ROOT / "artifacts/wrench-gateway-model-research/lora-screen-01-eval"
EVAL_LOGS = APPROVED_ROOT / "logs/wrench-gateway-model-research/lora-screen-01-eval"
GLOBAL_HELDOUT_MARKER = EVAL_ARTIFACTS / "heldout-access.started.json"
GLOBAL_HELDOUT_LOCK = EVAL_ARTIFACTS / "heldout-scoring.lock"
ADDON_DIR = APPROVED_ROOT / "envs/wrench-gateway-lora-screen-01-addons"
MODEL_ID = "Qwen/Qwen3.5-0.8B"
MODEL_REVISION = "2fc06364715b967f1860aea9cf38778875588b17"
TRAIN_JOB_ID = "WRENCH-GATEWAY-LORA-SCREEN-01-FIT-20260927-01"
EXPECTED_STEPS = 96
MAX_NEW_TOKENS = 96
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
MAX_GENERATION_SECONDS = 300
RAM_FLOOR = 0.10
VRAM_FLOOR = 0.10
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


def write_json(path: Path, value: Any) -> None:
    payload = canonical_bytes(value)
    if len(payload) > MAX_OUTPUT_BYTES:
        raise RuntimeError(f"receipt too large: {path.name}")
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


class ResourceMonitor(threading.Thread):
    """Sample host reserves and interrupt the job immediately on a breach."""

    def __init__(self, output: Path) -> None:
        super().__init__(name="wrench-gateway-screen-resource-monitor", daemon=True)
        self.output = output
        self.stop_event = threading.Event()
        self.breach_reason: str | None = None
        self.samples: list[dict[str, Any]] = []

    @staticmethod
    def ram() -> tuple[int, int]:
        import psutil

        memory = psutil.virtual_memory()
        return int(memory.available), int(memory.total)

    @staticmethod
    def gpu() -> tuple[int, int]:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        first = result.stdout.strip().splitlines()[0].split(",")
        return int(first[0].strip()), int(first[1].strip())

    def sample(self) -> None:
        ram_free, ram_total = self.ram()
        gpu_free, gpu_total = self.gpu()
        row = {
            "time_utc": utc_now(),
            "ram_free_bytes": ram_free,
            "ram_total_bytes": ram_total,
            "ram_free_fraction": ram_free / ram_total,
            "gpu_free_mib": gpu_free,
            "gpu_total_mib": gpu_total,
            "gpu_free_fraction": gpu_free / gpu_total,
        }
        line = canonical_bytes(row)
        if self.output.stat().st_size + len(line) > MAX_OUTPUT_BYTES:
            self.breach_reason = "RESOURCE_LOG_BYTE_CAP"
            self.stop_event.set()
            return
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
            return {"sample_count": 0, "breach_reason": self.breach_reason}
        return {
            "sample_count": len(self.samples),
            "minimum_ram_free_bytes": min(row["ram_free_bytes"] for row in self.samples),
            "minimum_ram_free_fraction": min(row["ram_free_fraction"] for row in self.samples),
            "minimum_gpu_free_mib": min(row["gpu_free_mib"] for row in self.samples),
            "minimum_gpu_free_fraction": min(row["gpu_free_fraction"] for row in self.samples),
            "breach_reason": self.breach_reason,
        }


_ACTIVE_MONITOR: ResourceMonitor | None = None
_ACTIVE_ARTIFACT_DIR: Path | None = None
_ACTIVE_HELDOUT_LOCK: Any | None = None


class HeldoutRunLock:
    """Cross-process Windows lock that prevents concurrent held-out scoring."""

    def __init__(self, path: Path, job_id: str) -> None:
        self.path = path
        self.job_id = job_id
        self.handle: Any | None = None

    def acquire(self) -> None:
        import msvcrt

        handle = self.path.open("a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            handle.close()
            raise RuntimeError("another held-out scoring process owns the global lock") from exc
        self.handle = handle
        try:
            handle.seek(1)
            handle.truncate(1)
            handle.write(canonical_bytes({"job_id": self.job_id, "pid": os.getpid(), "locked_at_utc": utc_now()}))
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


def require_storage_reservation(job_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", job_id):
        raise RuntimeError("invalid storage reservation job ID")
    path = APPROVED_ROOT / ".budget/reservations" / f"{job_id}.json"
    if not path.is_file():
        raise RuntimeError(f"storage reservation missing: {job_id}")
    record = load_json(path)
    if record.get("schema") != "wrench.storage-reservation.v1" or record.get("job_id") != job_id:
        raise RuntimeError("storage reservation identity/schema mismatch")
    if not isinstance(record.get("reserve_bytes"), int) or record["reserve_bytes"] <= 0:
        raise RuntimeError("storage reservation must be positive")
    return record


def verify_resource_log(path: Path, expected: dict[str, Any]) -> None:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise RuntimeError("preflight resource log is empty")
    actual = {
        "sample_count": len(rows),
        "minimum_ram_free_bytes": min(row["ram_free_bytes"] for row in rows),
        "minimum_ram_free_fraction": min(row["ram_free_fraction"] for row in rows),
        "minimum_gpu_free_mib": min(row["gpu_free_mib"] for row in rows),
        "minimum_gpu_free_fraction": min(row["gpu_free_fraction"] for row in rows),
        "breach_reason": None,
    }
    for key, value in actual.items():
        if expected.get(key) != value:
            raise RuntimeError(f"preflight resource summary mismatch: {key}")
    if actual["minimum_ram_free_fraction"] < RAM_FLOOR or actual["minimum_gpu_free_fraction"] < VRAM_FLOOR:
        raise RuntimeError("preflight resource log records a breached 10% reserve")


def verify_training_and_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    reservation_path = APPROVED_ROOT / ".budget/reservations" / f"{TRAIN_JOB_ID}.json"
    if reservation_path.exists():
        raise RuntimeError("training reservation must be released after the run stops and outputs are accounted")
    run = load_json(TRAIN_MANIFEST)
    if run.get("schema") != "wrench.gateway_lora_screen_01.run.v1" or run.get("job_id") != TRAIN_JOB_ID:
        raise RuntimeError("training manifest identity mismatch")
    if run.get("status") != "COMPLETED" or run.get("optimizer_steps") != EXPECTED_STEPS:
        raise RuntimeError("held-out access requires the exact completed 96-step training run")
    if run.get("heldout_opened_by_runner") is not False:
        raise RuntimeError("training receipt reports held-out access")
    if run.get("model_id") != MODEL_ID or run.get("model_revision") != MODEL_REVISION:
        raise RuntimeError("base model identity mismatch")
    if sha256_file(TRAIN_PROTOCOL) != run.get("protocol_sha256"):
        raise RuntimeError("frozen training protocol hash mismatch")
    if sha256_file(TRAIN_SOURCE_SNAPSHOT) != run.get("runner_sha256"):
        raise RuntimeError("frozen training runner source hash mismatch")
    if sha256_file(TRAIN_LOG_DIR / "resources.jsonl") != run.get("resource_log_sha256"):
        raise RuntimeError("final training resource-log hash mismatch")

    inventory = load_json(MODEL_INVENTORY)
    if (inventory.get("status") != "VERIFIED_LOCAL_SNAPSHOT"
            or inventory.get("model_id") != MODEL_ID
            or inventory.get("revision") != MODEL_REVISION
            or sha256_file(MODEL_INVENTORY) != run.get("model_inventory_sha256")):
        raise RuntimeError("frozen model inventory mismatch")
    candidate = load_json(MODEL_CANDIDATE)
    expected = {item["path"]: item for item in candidate.get("files", [])}
    if (candidate.get("model_id") != MODEL_ID or candidate.get("revision") != MODEL_REVISION
            or not expected):
        raise RuntimeError("pinned model candidate manifest mismatch")
    actual = {path.relative_to(MODEL_DIR).as_posix(): path for path in MODEL_DIR.rglob("*") if path.is_file()}
    if set(actual) != set(expected):
        raise RuntimeError("pinned local model file set changed")
    verified_files = []
    for relative in sorted(expected):
        path, spec = actual[relative], expected[relative]
        size = path.stat().st_size
        if size != spec.get("size_bytes"):
            raise RuntimeError(f"pinned model size changed: {relative}")
        digest = hashlib.sha256()
        git_blob = hashlib.sha1(f"blob {size}\0".encode("ascii"))
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(block)
                git_blob.update(block)
        content_sha = digest.hexdigest()
        if spec.get("upstream_sha256"):
            if content_sha != spec["upstream_sha256"]:
                raise RuntimeError(f"pinned model content hash changed: {relative}")
        elif git_blob.hexdigest() != spec.get("git_blob_id"):
            raise RuntimeError(f"pinned model Git blob changed: {relative}")
        verified_files.append({"path": relative, "size_bytes": size, "sha256": content_sha})
    if verified_files != [
        {"path": item["path"], "size_bytes": item["size_bytes"], "sha256": item["sha256"]}
        for item in inventory.get("files", [])
    ]:
        raise RuntimeError("current model files differ from the run's hash-bound inventory")

    adapter_expected = {item["path"]: item for item in run.get("adapter_files", [])}
    adapter_actual = {path.relative_to(ADAPTER_DIR).as_posix(): path for path in ADAPTER_DIR.rglob("*") if path.is_file()}
    if not adapter_expected or set(adapter_actual) != set(adapter_expected):
        raise RuntimeError("adapter file set does not match completed run receipt")
    adapter_bytes = 0
    for relative, path in adapter_actual.items():
        spec = adapter_expected[relative]
        size = path.stat().st_size
        if size != spec.get("size_bytes") or sha256_file(path) != spec.get("sha256"):
            raise RuntimeError(f"adapter file hash mismatch: {relative}")
        adapter_bytes += size
    if adapter_bytes != run.get("adapter_total_bytes") or adapter_bytes > 100 * 1024 * 1024:
        raise RuntimeError("adapter aggregate size does not match receipt or cap")

    data_manifest_path = DATA_ROOT / "manifest.json"
    data = load_json(data_manifest_path)
    if (not data.get("synthetic_only")
            or sha256_file(data_manifest_path) != run.get("dataset_manifest_sha256")
            or data.get("files", {}).get("heldout", {}).get("count") != 128
            or data["files"]["heldout"].get("sha256") != run.get("heldout_sha256")):
        raise RuntimeError("sealed dataset manifest identity mismatch")
    if sha256_file(GENERATOR_SOURCE) != data.get("generator_sha256"):
        raise RuntimeError("synthetic corpus generator source hash mismatch")
    for split, field in (("train", "train_sha256"), ("dev", "dev_sha256")):
        spec = data["files"][split]
        path = DATA_ROOT / spec["path"]
        if (path.stat().st_size != spec["size_bytes"] or sha256_file(path) != spec["sha256"]
                or run.get(field) != spec["sha256"]):
            raise RuntimeError(f"training dataset identity mismatch: {split}")
    return run, inventory, data


def read_prompt_split(path: Path, expected_name: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Verify a split and project only IDs plus system/user messages."""
    if path.stat().st_size != spec["size_bytes"] or sha256_file(path) != spec["sha256"]:
        raise RuntimeError(f"{expected_name} split size/hash mismatch")
    prompts: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
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


def read_references(path: Path, expected_name: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Read labels and family metadata only after raw predictions are sealed."""
    if path.stat().st_size != spec["size_bytes"] or sha256_file(path) != spec["sha256"]:
        raise RuntimeError(f"{expected_name} split size/hash mismatch on label pass")
    references = []
    with path.open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
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
    os.environ["HF_HOME"] = str(APPROVED_ROOT / "cache/huggingface/gateway-screen-01")
    os.environ["TORCH_HOME"] = str(APPROVED_ROOT / "cache/torch/gateway-screen-01")
    os.environ["TEMP"] = str(APPROVED_ROOT / "cache/tmp/gateway-screen-01")
    os.environ["TMP"] = os.environ["TEMP"]
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    Path(os.environ["TEMP"]).mkdir(parents=True, exist_ok=True)
    import torch
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    torch.set_num_threads(4)
    return torch, PeftModel, (AutoModelForImageTextToText, AutoTokenizer)


def load_base(torch: Any, auto_classes: Any, device: str, dtype_name: str) -> tuple[Any, Any]:
    model_class, tokenizer_class = auto_classes
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


def create_global_heldout_marker(job_id: str, run: dict[str, Any], data: dict[str, Any]) -> None:
    payload = canonical_bytes({
        "schema": "wrench.gateway_lora_screen_01.heldout_global_access.v1",
        "status": "ACCESS_STARTED_ONCE", "job_id": job_id, "pid": os.getpid(),
        "model_id": run.get("model_id"), "model_revision": run.get("model_revision"),
        "training_protocol_sha256": run.get("protocol_sha256"),
        "repo_head": git_head(), "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_manifest_sha256": sha256_file(TRAIN_MANIFEST),
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(DATA_ROOT / "manifest.json"),
        "heldout_sha256": data["files"]["heldout"]["sha256"], "time_utc": utc_now(),
    })
    fd = os.open(str(GLOBAL_HELDOUT_MARKER), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def run_preflight(args: argparse.Namespace, job: dict[str, Any]) -> int:
    global _ACTIVE_ARTIFACT_DIR, _ACTIVE_MONITOR
    run, inventory, data = verify_training_and_inputs()
    dev_spec = data["files"]["dev"]
    dev_inputs = read_prompt_split(DATA_ROOT / dev_spec["path"], "dev", dev_spec)
    messages = dev_inputs[0]["messages"]
    out, log_out = output_dirs_for("preflight", args.storage_reservation_job_id)
    out.mkdir(parents=True)
    _ACTIVE_ARTIFACT_DIR = out.resolve()
    log_out.mkdir(parents=True)
    resource_path = log_out / "resources.jsonl"
    resource_path.write_bytes(b"")
    monitor = ResourceMonitor(resource_path)
    _ACTIVE_MONITOR = monitor
    monitor.sample()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    monitor.start()
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
    if monitor.is_alive():
        raise RuntimeError("resource monitor did not stop cleanly")
    if not choices:
        receipt = {"schema": "wrench.gateway_lora_screen_01.preflight.v1", "status": "FAILED",
                   "job_id": args.storage_reservation_job_id, "training_manifest_sha256": sha256_file(TRAIN_MANIFEST),
                   "attempts": attempts, "resource_summary": monitor.summary(), "resource_log_sha256": sha256_file(resource_path)}
        write_json(out / "preflight.json", receipt)
        return 2
    selected_device, selected_dtype = choices[0]
    receipt = {
        "schema": "wrench.gateway_lora_screen_01.preflight.v1", "status": "COMPLETED",
        "job_id": args.storage_reservation_job_id, "created_at_utc": utc_now(),
        "repo_head": git_head(),
        "training_manifest_sha256": sha256_file(TRAIN_MANIFEST),
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_protocol_sha256": run["protocol_sha256"],
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(DATA_ROOT / "manifest.json"),
        "model_inventory_sha256": sha256_file(MODEL_INVENTORY),
        "adapter_files": run["adapter_files"], "device": selected_device, "dtype": selected_dtype,
        "max_new_tokens": MAX_NEW_TOKENS, "decoding": {"do_sample": False, "num_beams": 1},
        "attempts": attempts, "resource_summary": monitor.summary(),
        "resource_log": str(resource_path), "resource_log_sha256": sha256_file(resource_path),
    }
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
    global _ACTIVE_ARTIFACT_DIR, _ACTIVE_HELDOUT_LOCK, _ACTIVE_MONITOR
    if _ACTIVE_HELDOUT_LOCK is not None:
        raise RuntimeError("this process already owns a held-out scoring lock")
    run, inventory, data = verify_training_and_inputs()
    preflight_path = args.preflight_receipt.resolve(strict=True)
    if EVAL_ARTIFACTS.resolve() not in preflight_path.parents:
        raise RuntimeError("preflight receipt must be under the approved evaluation artifact root")
    preflight = load_json(preflight_path)
    if (preflight.get("schema") != "wrench.gateway_lora_screen_01.preflight.v1"
            or preflight.get("status") != "COMPLETED"
            or preflight.get("repo_head") != git_head()
            or preflight.get("training_manifest_sha256") != sha256_file(TRAIN_MANIFEST)
            or preflight.get("evaluator_sha256") != sha256_file(EVALUATOR_SOURCE)
            or preflight.get("training_protocol_sha256") != run.get("protocol_sha256")
            or preflight.get("eval_protocol_sha256") != sha256_file(EVAL_PROTOCOL)
            or preflight.get("dataset_manifest_sha256") != sha256_file(DATA_ROOT / "manifest.json")
            or preflight.get("model_inventory_sha256") != sha256_file(MODEL_INVENTORY)
            or preflight.get("adapter_files") != run.get("adapter_files")
            or preflight.get("device") not in {"cpu", "cuda"}
            or preflight.get("dtype") not in {"float32", "bfloat16", "float16"}
            or preflight.get("max_new_tokens") != MAX_NEW_TOKENS
            or preflight.get("decoding") != {"do_sample": False, "num_beams": 1}):
        raise RuntimeError("device/dtype preflight receipt identity mismatch")
    preflight_log = Path(preflight.get("resource_log", "")).resolve(strict=True)
    if (APPROVED_ROOT.resolve() not in preflight_log.parents
            or sha256_file(preflight_log) != preflight.get("resource_log_sha256")):
        raise RuntimeError("preflight resource log is outside approved storage or hash-mismatched")
    resource_summary = preflight.get("resource_summary", {})
    verify_resource_log(preflight_log, resource_summary)
    if (resource_summary.get("minimum_ram_free_fraction", 0) < RAM_FLOOR
            or resource_summary.get("minimum_gpu_free_fraction", 0) < VRAM_FLOOR
            or resource_summary.get("breach_reason") is not None):
        raise RuntimeError("preflight did not maintain the 10% system resource reserves")

    if GLOBAL_HELDOUT_MARKER.exists():
        raise RuntimeError("the global sealed held-out split already has an access claim")
    if EVAL_ARTIFACTS.exists():
        prior_attempts = [path for path in EVAL_ARTIFACTS.glob("heldout-*")
                          if (path / "heldout-access.started.json").is_file()]
        if prior_attempts:
            raise RuntimeError("the sealed held-out split already has a recorded scoring attempt")
    out, log_out = output_dirs_for("heldout", args.storage_reservation_job_id)
    out.mkdir(parents=True)
    _ACTIVE_ARTIFACT_DIR = out.resolve()
    log_out.mkdir(parents=True)
    heldout_lock = HeldoutRunLock(GLOBAL_HELDOUT_LOCK, args.storage_reservation_job_id)
    heldout_lock.acquire()
    _ACTIVE_HELDOUT_LOCK = heldout_lock
    if GLOBAL_HELDOUT_MARKER.exists():
        raise RuntimeError("the global sealed held-out split already has an access claim")

    # Load both model arms under monitoring before consuming the held-out file.
    resource_path = log_out / "resources.jsonl"
    resource_path.write_bytes(b"")
    monitor = ResourceMonitor(resource_path)
    _ACTIVE_MONITOR = monitor
    monitor.sample()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)
    monitor.start()
    started = time.perf_counter()
    torch, PeftModel, classes = prepare_runtime(ADDON_DIR)
    device, dtype = preflight["device"], preflight["dtype"]
    model, tokenizer = load_base(torch, classes, device, dtype)
    template_hash = hashlib.sha256(str(tokenizer.chat_template).encode("utf-8")).hexdigest()
    if template_hash != run.get("chat_template_sha256"):
        raise RuntimeError("chat template hash differs from training receipt")
    adapted = PeftModel.from_pretrained(model, ADAPTER_DIR, local_files_only=True, is_trainable=False)
    adapted.eval()
    if monitor.breach_reason:
        raise RuntimeError(monitor.breach_reason)

    create_global_heldout_marker(args.storage_reservation_job_id, run, data)
    write_json(out / "heldout-access.started.json", {
        "schema": "wrench.gateway_lora_screen_01.heldout_access.v1",
        "status": "ACCESS_STARTED_ONCE", "job_id": args.storage_reservation_job_id,
        "repo_head": git_head(),
        "training_manifest_sha256": sha256_file(TRAIN_MANIFEST),
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "global_marker_sha256": sha256_file(GLOBAL_HELDOUT_MARKER),
        "preflight_receipt_sha256": sha256_file(preflight_path),
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL), "time_utc": utc_now(),
    })

    heldout_spec = data["files"]["heldout"]
    # This is the first operation in the scorer that opens sealed examples.
    inputs = read_prompt_split(DATA_ROOT / heldout_spec["path"], "heldout", heldout_spec)
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
    with deterministic_path.open("xb") as stream:
        for item in inputs:
            value = predictions["deterministic"][item["example_id"]]
            value["example_id"] = item["example_id"]
            value["input_sha256"] = hashlib.sha256(canonical_bytes(item["messages"])).hexdigest()
            stream.write(canonical_bytes(value))

    def run_arm(arm: str, active_model: Any) -> None:
        path = out / f"{arm}-predictions.jsonl"
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
    monitor.stop_event.set()
    monitor.join(timeout=5)

    # Seal every prediction file before joining any family/gold reference.
    if monitor.is_alive():
        raise RuntimeError("resource monitor did not stop cleanly")
    prediction_hashes = {path.name: sha256_file(path) for path in sorted(out.glob("*-predictions.jsonl"))}
    # Re-open labels only after all arms are written and their hashes are sealed.
    reference_rows = read_references(DATA_ROOT / heldout_spec["path"], "heldout", heldout_spec)
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
    result = {
        "schema": "wrench.gateway_lora_screen_01.heldout_result.v1",
        "status": "COMPLETED_DIAGNOSTIC_ONLY", "job_id": args.storage_reservation_job_id,
        "created_at_utc": utc_now(), "repo_head": git_head(), "training_job_id": TRAIN_JOB_ID,
        "training_manifest_sha256": sha256_file(TRAIN_MANIFEST),
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "training_resource_log_sha256": run["resource_log_sha256"],
        "training_protocol_sha256": run["protocol_sha256"],
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "dataset_manifest_sha256": sha256_file(DATA_ROOT / "manifest.json"),
        "heldout_sha256": heldout_spec["sha256"], "model_inventory_sha256": sha256_file(MODEL_INVENTORY),
        "heldout_access_marker_sha256": sha256_file(out / "heldout-access.started.json"),
        "global_heldout_access_marker_sha256": sha256_file(GLOBAL_HELDOUT_MARKER),
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
        "resource_log_sha256": sha256_file(resource_path), "resource_summary": monitor.summary(),
        "limitations": [
            "synthetic policy diagnostic only; not representative engineering workload",
            "deterministic-arm token counts are tokenizer-equivalent and are not model usage",
            "predicted route share is not real local task completion or frontier call usage",
            "does not establish 95/5/95, token savings, dollar savings, or all-day engineering",
            "the corpus has a frozen 104/8/16 local/frontier/abstain label mix",
        ],
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(out / "result.json", result)
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
    if resource_path.is_file() and APPROVED_ROOT.resolve() in resource_path.resolve().parents:
        resource = {"path": str(resource_path), "size_bytes": resource_path.stat().st_size,
                    "sha256": sha256_file(resource_path),
                    "monitor_stopped": monitor is None or not monitor.is_alive()}
    write_json(failure_path, {
        "schema": "wrench.gateway_lora_screen_01.failure.v1",
        "status": "FAILED",
        "mode": args.mode,
        "job_id": args.storage_reservation_job_id,
        "time_utc": utc_now(),
        "repo_head": git_head(),
        "evaluator_sha256": sha256_file(EVALUATOR_SOURCE),
        "eval_protocol_sha256": sha256_file(EVAL_PROTOCOL),
        "heldout_access_started": marker.is_file(),
        "heldout_access_marker_sha256": sha256_file(marker) if marker.is_file() else None,
        "global_heldout_access_claimed": GLOBAL_HELDOUT_MARKER.is_file(),
        "global_heldout_access_marker_sha256": sha256_file(GLOBAL_HELDOUT_MARKER) if GLOBAL_HELDOUT_MARKER.is_file() else None,
        "resource_log": resource,
        "resource_breach_reason": monitor.breach_reason if monitor is not None else None,
        "error_type": type(exc).__name__,
        "error": str(exc)[:1000],
    })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "score-heldout"), required=True)
    parser.add_argument("--storage-reservation-job-id", required=True)
    parser.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument("--preflight-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "score-heldout" and args.preflight_receipt is None:
        parser.error("--preflight-receipt is required for score-heldout")
    job = require_storage_reservation(args.storage_reservation_job_id)
    # Output directories are created only after identities and reservations pass.
    if not all(path.is_dir() for path in (APPROVED_ROOT, DATA_ROOT, MODEL_DIR)):
        raise SystemExit("an approved root or required local input is missing")
    os.environ["HF_HOME"] = str(APPROVED_ROOT / "cache/huggingface/gateway-screen-01")
    os.environ["TORCH_HOME"] = str(APPROVED_ROOT / "cache/torch/gateway-screen-01")
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
            release_heldout_lock()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
