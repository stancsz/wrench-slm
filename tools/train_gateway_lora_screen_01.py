"""Train one bounded synthetic-only Wrench gateway LoRA candidate on CPU.

This runner is offline, loads only the pinned local Qwen3.5-0.8B snapshot,
reads train/dev (never heldout), and writes one adapter plus bounded receipts
under C:\\wrench-slm-data. It grants no tool or mutation authority.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import random
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_ROOT = Path(r"C:\wrench-slm-data\datasets\wrench-gateway-model-research\lora-screen-01")
MODEL_DIR = Path(r"C:\wrench-slm-data\weights\Qwen3.5-0.8B")
INVENTORY = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-01-model-inventory.json")
OUTPUT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-01\adapter")
LOG_DIR = Path(r"C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-01")
PROTOCOL = Path("docs/evals/wrench-gateway-model-research/lora-screen-01-protocol-20260927.md")
EXPECTED_REVISION = "2fc06364715b967f1860aea9cf38778875588b17"
EXPECTED_MODEL_ID = "Qwen/Qwen3.5-0.8B"
EXPECTED_FAMILIES = {"evidence_select", "retrieve_stop", "compaction_policy", "route"}
TARGET_SUFFIXES = {
    "q_proj", "k_proj", "v_proj", "o_proj", "in_proj_qkv", "in_proj_z",
    "in_proj_a", "in_proj_b", "out_proj", "gate_proj", "up_proj", "down_proj",
}
MAX_SEQUENCE_LENGTH = 512
EPOCHS = 3
GRAD_ACCUMULATION = 8
LEARNING_RATE = 2e-4
MAX_ADAPTER_BYTES = 100 * 1024 * 1024
MAX_LOG_BYTES = 20 * 1024 * 1024
RAM_FREE_FRACTION = 0.10
VRAM_FREE_FRACTION = 0.10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def gpu_sample() -> tuple[int, int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.total,memory.free", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    first = result.stdout.strip().splitlines()[0]
    total_mib, free_mib = (int(part.strip()) for part in first.split(",", maxsplit=1))
    return free_mib, total_mib


class ResourceMonitor(threading.Thread):
    def __init__(self, log_path: Path) -> None:
        super().__init__(name="wrench-gateway-resource-monitor", daemon=True)
        self.log_path = log_path
        self.stop_event = threading.Event()
        self.breach_reason: str | None = None

    def sample_and_write(self) -> None:
        ram_free, ram_total = ram_sample()
        gpu_free_mib, gpu_total_mib = gpu_sample()
        sample = {
            "time_utc": utc_now(),
            "ram_free_bytes": ram_free,
            "ram_total_bytes": ram_total,
            "ram_free_fraction": ram_free / ram_total,
            "gpu_free_mib": gpu_free_mib,
            "gpu_total_mib": gpu_total_mib,
            "gpu_free_fraction": gpu_free_mib / gpu_total_mib,
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
                    threading.interrupt_main()
                    return
                self.stop_event.wait(1.0)
        except BaseException as exc:
            self.breach_reason = f"RESOURCE_MONITOR_ERROR:{type(exc).__name__}"
            threading.interrupt_main()


def load_jsonl(path: Path, expected_split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            row = json.loads(line)
            if row.get("split") != expected_split or row.get("schema") != "wrench.gateway_lora_screen_01.synthetic.v1":
                raise ValueError(f"split/schema mismatch in {path.name}:{line_number}")
            if row.get("family") not in EXPECTED_FAMILIES:
                raise ValueError(f"unexpected family in {path.name}:{line_number}")
            rows.append(row)
    if not rows:
        raise ValueError(f"empty split: {path}")
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


def as_batch(row: dict[str, Any], torch: Any) -> dict[str, Any]:
    input_ids = torch.tensor([row["input_ids"]], dtype=torch.long)
    labels = torch.tensor([row["labels"]], dtype=torch.long)
    attention_mask = torch.ones_like(input_ids)
    return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


def evaluate_loss(model: Any, rows: list[dict[str, Any]], torch: Any, monitor: ResourceMonitor) -> float:
    model.eval()
    token_weighted_loss = 0.0
    token_count = 0
    with torch.no_grad():
        for row in rows:
            if monitor.breach_reason:
                raise KeyboardInterrupt(monitor.breach_reason)
            batch = as_batch(row, torch)
            output = model(**batch, use_cache=False)
            tokens = int((batch["labels"] != -100).sum().item())
            token_weighted_loss += float(output.loss.item()) * tokens
            token_count += tokens
    model.train()
    return token_weighted_loss / max(token_count, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-reservation-job-id", required=True)
    parser.add_argument("--preflight-only", action="store_true", help="run one optimizer step and save only a preflight receipt")
    args = parser.parse_args()

    os.environ["HF_HOME"] = r"C:\wrench-slm-data\cache\huggingface\gateway-lora-screen-01"
    os.environ["TORCH_HOME"] = r"C:\wrench-slm-data\cache\torch\gateway-lora-screen-01"
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("MKL_NUM_THREADS", "4")
    addon_path = os.environ.get("WRENCH_LORA_ADDONS")
    if addon_path:
        sys.path.insert(0, addon_path)

    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from torch import nn
    from transformers import AutoModelForImageTextToText, AutoTokenizer

    torch.set_num_threads(4)
    random.seed(20260927)
    torch.manual_seed(20260927)

    for path in (DATA_ROOT, MODEL_DIR, INVENTORY):
        if not path.exists():
            raise SystemExit(f"required input missing: {path}")
    run_log_dir = LOG_DIR.parent / "lora-screen-01-preflight" if args.preflight_only else LOG_DIR
    if (not args.preflight_only and OUTPUT.exists()) or run_log_dir.exists():
        raise SystemExit("refusing to overwrite an existing output or log directory")
    if not Path(r"C:\wrench-slm-data").resolve() in OUTPUT.resolve().parents:
        raise SystemExit("adapter output escaped the approved storage root")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    if inventory.get("status") != "VERIFIED_LOCAL_SNAPSHOT" or inventory.get("revision") != EXPECTED_REVISION:
        raise SystemExit("local snapshot inventory is not verified for the pinned revision")
    data_manifest_path = DATA_ROOT / "manifest.json"
    data_manifest = json.loads(data_manifest_path.read_text(encoding="utf-8"))
    if not data_manifest.get("synthetic_only") or data_manifest.get("files", {}).get("heldout", {}).get("count") != 128:
        raise SystemExit("synthetic split manifest mismatch")
    for split in ("train", "dev"):
        spec = data_manifest["files"][split]
        path = DATA_ROOT / spec["path"]
        if path.stat().st_size != spec["size_bytes"] or sha256_file(path) != spec["sha256"]:
            raise SystemExit(f"data hash mismatch: {split}")
    protocol_hash = sha256_file(PROTOCOL)
    data_manifest_hash = sha256_file(data_manifest_path)
    inventory_hash = sha256_file(INVENTORY)
    train_rows = load_jsonl(DATA_ROOT / data_manifest["files"]["train"]["path"], "train")
    dev_rows = load_jsonl(DATA_ROOT / data_manifest["files"]["dev"]["path"], "dev")
    if len(train_rows) != 256 or len(dev_rows) != 64:
        raise SystemExit("unexpected train/dev count")

    run_log_dir.mkdir(parents=True, exist_ok=False)
    if not args.preflight_only:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    resource_log = run_log_dir / "resources.jsonl"
    resource_log.write_bytes(b"")
    monitor = ResourceMonitor(resource_log)
    monitor.sample_and_write()
    if monitor.breach_reason:
        raise SystemExit(monitor.breach_reason)

    base_manifest = {
        "schema": "wrench.gateway_lora_screen_01.run.v1",
        "status": "RUNNING",
        "job_id": args.storage_reservation_job_id,
        "started_at_utc": utc_now(),
        "model_id": EXPECTED_MODEL_ID,
        "model_revision": EXPECTED_REVISION,
        "model_inventory_sha256": inventory_hash,
        "protocol_sha256": protocol_hash,
        "dataset_manifest_sha256": data_manifest_hash,
        "train_sha256": data_manifest["files"]["train"]["sha256"],
        "dev_sha256": data_manifest["files"]["dev"]["sha256"],
        "heldout_sha256": data_manifest["files"]["heldout"]["sha256"],
        "heldout_opened_by_runner": False,
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "device": "cpu",
        "threads": 4,
        "precision": "float32",
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
        "target_suffix_allowlist": sorted(TARGET_SUFFIXES),
        "resource_log": str(resource_log),
        "output_dir": None if args.preflight_only else str(OUTPUT),
        "preflight_only": args.preflight_only,
    }
    run_manifest_path = run_log_dir / "run-manifest.json"
    write_json(run_manifest_path, base_manifest)

    try:
        monitor.start()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, local_files_only=True, trust_remote_code=False)
        if tokenizer.pad_token_id is None:
            if tokenizer.eos_token is None:
                raise RuntimeError("tokenizer has neither a pad token nor an EOS token")
            tokenizer.pad_token = tokenizer.eos_token
        base_model = AutoModelForImageTextToText.from_pretrained(
            MODEL_DIR,
            local_files_only=True,
            trust_remote_code=False,
            torch_dtype=torch.float32,
        )
        if any(parameter.device.type != "cpu" for parameter in base_model.parameters()):
            raise RuntimeError("CPU-only run unexpectedly placed model parameters off CPU")
        if getattr(base_model.config, "model_type", None) != "qwen3_5":
            raise RuntimeError("loaded model type is not qwen3_5")
        base_model.config.use_cache = False
        if getattr(base_model.config, "text_config", None) is not None:
            base_model.config.text_config.use_cache = False
        base_model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        if hasattr(base_model, "enable_input_require_grads"):
            base_model.enable_input_require_grads()

        named = list(base_model.named_modules())
        targets = [
            name for name, module in named
            if name.startswith("model.language_model.layers.")
            and name.rsplit(".", 1)[-1] in TARGET_SUFFIXES
            and isinstance(module, nn.Linear)
        ]
        matched_suffixes = {name.rsplit(".", 1)[-1] for name in targets}
        if matched_suffixes != TARGET_SUFFIXES:
            raise RuntimeError(f"target module mismatch; missing={sorted(TARGET_SUFFIXES - matched_suffixes)}")
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
        if not trainable_count or trainable_count / total_count > 0.05:
            raise RuntimeError("unexpected LoRA trainable parameter count")
        base_manifest.update({
            "status": "RUNNING_TRAINING",
            "matched_target_modules": targets,
            "matched_target_count": len(targets),
            "trainable_parameter_count": trainable_count,
            "total_parameter_count": total_count,
            "trainable_fraction": trainable_count / total_count,
            "chat_template_sha256": hashlib.sha256(str(tokenizer.chat_template).encode("utf-8")).hexdigest(),
            "peft_version": __import__("peft").__version__,
            "accelerate_version": __import__("accelerate").__version__,
            "transformers_version": __import__("transformers").__version__,
            "torch_version": torch.__version__,
            "python_version": sys.version,
        })
        write_json(run_manifest_path, base_manifest)

        train_data = tokenize_rows(train_rows, tokenizer, "train")
        dev_data = tokenize_rows(dev_rows, tokenizer, "dev")
        optimizer = torch.optim.AdamW(trainable, lr=LEARNING_RATE, weight_decay=0.0)
        metrics_path = run_log_dir / "epoch-metrics.jsonl"
        optimizer_step = 0
        model.train()
        if args.preflight_only:
            optimizer.zero_grad(set_to_none=True)
            preflight_group = train_data[:GRAD_ACCUMULATION]
            preflight_loss_sum = 0.0
            for row in preflight_group:
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
                batch = as_batch(row, torch)
                output = model(**batch, use_cache=False)
                if not torch.isfinite(output.loss):
                    raise RuntimeError("non-finite preflight loss")
                preflight_loss_sum += float(output.loss.detach().item())
                (output.loss / len(preflight_group)).backward()
            torch.nn.utils.clip_grad_norm_(trainable, 1.0)
            optimizer.step()
            optimizer_step = 1
            if monitor.breach_reason:
                raise KeyboardInterrupt(monitor.breach_reason)
            base_manifest.update({
                "status": "PREFLIGHT_COMPLETED",
                "completed_at_utc": utc_now(),
                "optimizer_steps": optimizer_step,
                "preflight_examples": len(preflight_group),
                "preflight_loss_mean": preflight_loss_sum / len(preflight_group),
                "resource_log_sha256": sha256_file(resource_log),
            })
            write_json(run_manifest_path, base_manifest)
            print(json.dumps({
                "status": "PREFLIGHT_COMPLETED",
                "optimizer_steps": optimizer_step,
                "run_manifest": str(run_manifest_path),
            }, sort_keys=True), flush=True)
            return 0
        for epoch in range(1, EPOCHS + 1):
            order = list(range(len(train_data)))
            random.Random(20260927 + epoch).shuffle(order)
            epoch_losses: list[float] = []
            for group_start in range(0, len(order), GRAD_ACCUMULATION):
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
                optimizer.zero_grad(set_to_none=True)
                group = order[group_start : group_start + GRAD_ACCUMULATION]
                for index in group:
                    if monitor.breach_reason:
                        raise KeyboardInterrupt(monitor.breach_reason)
                    batch = as_batch(train_data[index], torch)
                    output = model(**batch, use_cache=False)
                    loss = output.loss
                    if not torch.isfinite(loss):
                        raise RuntimeError(f"non-finite training loss at epoch {epoch}")
                    epoch_losses.append(float(loss.detach().item()))
                    (loss / len(group)).backward()
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optimizer.step()
                optimizer_step += 1
                if monitor.breach_reason:
                    raise KeyboardInterrupt(monitor.breach_reason)
            dev_loss = evaluate_loss(model, dev_data, torch, monitor)
            record = {
                "epoch": epoch,
                "optimizer_step": optimizer_step,
                "train_loss_mean": sum(epoch_losses) / len(epoch_losses),
                "dev_loss": dev_loss,
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

        if monitor.breach_reason:
            raise KeyboardInterrupt(monitor.breach_reason)
        model.save_pretrained(OUTPUT, safe_serialization=True)
        adapter_files = []
        adapter_total = 0
        for path in sorted(OUTPUT.rglob("*")):
            if path.is_file():
                size = path.stat().st_size
                adapter_total += size
                adapter_files.append({"path": path.relative_to(OUTPUT).as_posix(), "size_bytes": size, "sha256": sha256_file(path)})
        if adapter_total > MAX_ADAPTER_BYTES:
            raise RuntimeError("adapter output exceeded 100 MB cap")
        base_manifest.update({
            "status": "COMPLETED",
            "completed_at_utc": utc_now(),
            "optimizer_steps": optimizer_step,
            "adapter_total_bytes": adapter_total,
            "adapter_files": adapter_files,
            "epoch_metrics_sha256": sha256_file(metrics_path),
            "resource_log_sha256": sha256_file(resource_log),
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
        write_json(run_manifest_path, base_manifest)
        print(json.dumps({"status": base_manifest["status"], "reason": base_manifest["abort_reason"]}, sort_keys=True), flush=True)
        return 2
    except BaseException as exc:
        base_manifest.update({
            "status": "FAILED",
            "failure_type": type(exc).__name__,
            "failure_message": str(exc)[:1000],
            "ended_at_utc": utc_now(),
        })
        write_json(run_manifest_path, base_manifest)
        raise
    finally:
        monitor.stop_event.set()
        if monitor.is_alive():
            monitor.join(timeout=3)
        if run_manifest_path.exists() and not monitor.is_alive():
            try:
                final_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
                final_manifest["resource_log_sha256"] = sha256_file(resource_log)
                final_manifest["resource_log_finalized_at_utc"] = utc_now()
                write_json(run_manifest_path, final_manifest)
            except BaseException as finalize_error:
                print(f"failed to finalize resource log hash: {type(finalize_error).__name__}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
