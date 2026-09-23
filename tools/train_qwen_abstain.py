"""Fit only a two-output head on the existing frozen Qwen checkpoint.

Runs locally with explicit --run. No base-weight update, generation, provider
calls or sealed-final access. Development evaluation is diagnostic only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class Guard:
    def __init__(self, seconds):
        self.started, self.seconds, self.samples = time.monotonic(), seconds, []

    def check(self, extra_ram=0, extra_vram=0):
        if sys.platform == "win32":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                    (name, ctypes.c_ulonglong) for name in (
                        "total", "available", "total_page", "available_page",
                        "total_virtual", "available_virtual", "extended")]
            memory = MemoryStatus()
            memory.length = ctypes.sizeof(memory)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                raise RuntimeError("cannot read host memory reserve")
        else:
            import psutil
            memory = psutil.virtual_memory()
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.total,memory.free",
                              "--format=csv,noheader,nounits"], check=True,
                             capture_output=True, text=True, timeout=10)
        total, free = map(float, gpu.stdout.strip().splitlines()[0].split(","))
        sample = {"elapsed_s": time.monotonic() - self.started,
                  "ram_free": memory.available, "ram_total": memory.total,
                  "vram_free_mib": free, "vram_total_mib": total}
        self.samples.append(sample)
        if memory.available - extra_ram < memory.total * .1 or free * 1048576 - extra_vram < total * 1048576 * .1:
            raise RuntimeError("resource_unsafe: cannot preserve 10% RAM and VRAM reserves")
        if sample["elapsed_s"] > self.seconds:
            raise TimeoutError("training time budget exceeded")


def read_rows(path, expected_split):
    # Only these two unsealed split names are accepted by this tool.
    if expected_split not in {"calibration", "development"} or path.name != expected_split + ".jsonl":
        raise ValueError("only named unsealed calibration/development files are allowed")
    with path.open("rb") as stream:
        raw = stream.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("dataset too large")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not 2 <= len(rows) <= 512:
        raise ValueError("dataset row budget exceeded")
    for row in rows:
        if (row.get("split") != expected_split or row.get("expected_status") not in {"accepted", "abstain"}
                or not isinstance(row.get("prompt"), str) or len(row["prompt"]) > 4096
                or not isinstance(row.get("system", ""), str) or len(row.get("system", "")) > 4096
                or not isinstance(row.get("template_id"), str)):
            raise ValueError("invalid dataset row")
    return rows, hashlib.sha256(raw).hexdigest()


def messages(row, plain=False):
    result = [] if plain or not row.get("system") else [{"role": "system", "content": row["system"]}]
    return result + [{"role": "user", "content": row["prompt"]}]


def metrics(rows):
    eligible = [r for r in rows if r["expected"] == "not_abstain"]
    unsafe = [r for r in rows if r["expected"] == "abstain"]
    eligible_passes = sum(r["decision"] == "not_abstain" for r in eligible)
    unsafe_passes = sum(r["decision"] == "not_abstain" for r in unsafe)
    return {"rows": len(rows), "eligible": len(eligible), "ineligible": len(unsafe),
            "eligible_passes": eligible_passes,
            "eligible_coverage": eligible_passes / len(eligible) if eligible else None,
            "unsafe_classifier_passes": unsafe_passes,
            "unsafe_miss_rate": unsafe_passes / len(unsafe) if unsafe else None,
            "scope": "classifier decisions only; no tool execution"}


def run(args):
    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import (QwenAbstainGate, checkpoint_identity, embed,
                                            encode_messages, save_head, sha256_file)

    if args.output.exists():
        raise FileExistsError("use a new output directory to preserve existing evidence")
    args.output.mkdir(parents=True)
    guard = Guard(args.max_seconds)
    receipt = {"schema": "wrench.qwen-binary-training.v1", "status": "RUNNING",
               "provider_calls": 0, "base_weights_updated": False, "generated_tokens": 0,
               "production_enabled": False, "quality_claim": False, "final_split_read": False}
    try:
        guard.check()
        rows, data_sha = read_rows(args.data / "calibration.jsonl", "calibration")
        dev, dev_sha = read_rows(args.data / "development.jsonl", "development")
        calibration_groups = {row["template_id"] for row in rows}
        development_groups = {row["template_id"] for row in dev}
        if calibration_groups & development_groups:
            raise ValueError("calibration/development template groups overlap")
        dev_prompts = {r["prompt"].strip().casefold() for r in dev}
        seen, retained, excluded = set(), [], []
        for row in rows:
            text = row["prompt"].strip().casefold()
            if text in dev_prompts or text in seen:
                excluded.append(row["id"])
                continue
            seen.add(text)
            retained.append(row)
        rows = retained
        receipt["excluded_duplicate_or_dev_overlap_ids"] = excluded
        receipt["data_sha256"] = {"calibration": data_sha, "development": dev_sha}
        groups = defaultdict(list)
        for i, row in enumerate(rows):
            groups[row["template_id"]].append(i)
        train_ids, calibration_ids = [], []
        families = {g.rsplit("_template_", 1)[0] for g in groups}
        for family in sorted(families):
            names = sorted(g for g in groups if g.rsplit("_template_", 1)[0] == family)
            if len(names) < 3:
                raise ValueError("need three template groups per family")
            random.Random(23).shuffle(names)
            held_out = set(names[:max(1, len(names) // 4)])
            for group in names:
                (calibration_ids if group in held_out else train_ids).extend(groups[group])
        for indexes in (train_ids, calibration_ids):
            if {rows[i]["expected_status"] for i in indexes} != {"accepted", "abstain"}:
                raise ValueError("both labels required in training and calibration")
        receipt["train_ids"] = [rows[i]["id"] for i in train_ids]
        receipt["threshold_calibration_ids"] = [rows[i]["id"] for i in calibration_ids]
        print("Hashing the existing Qwen checkpoint", flush=True)
        identity = checkpoint_identity(args.model, guard.check)
        receipt["checkpoint_sha256"] = identity
        receipt["model_directory"] = str(args.model.resolve())
        weight_bytes = sum((args.model / name).stat().st_size for name in identity if name.endswith(".safetensors"))
        # Allocate headroom for loading and bounded single-request activation.
        guard.check(extra_ram=weight_bytes + 1_500_000_000, extra_vram=weight_bytes + 1_500_000_000)
        if not torch.cuda.is_available():
            raise RuntimeError("this bounded training command requires the configured CUDA runtime")
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        print("Loading one Qwen model; backbone frozen", flush=True)
        model = AutoModelForImageTextToText.from_pretrained(
            args.model, dtype=torch.bfloat16, local_files_only=True, trust_remote_code=False).to("cuda:0")
        model.eval().requires_grad_(False)
        torch.cuda.synchronize()
        receipt["backbone_parameter_bytes"] = sum(
            parameter.numel() * parameter.element_size() for parameter in model.parameters())
        receipt["backbone_vram_allocated_bytes_after_load"] = torch.cuda.memory_allocated(0)
        guard.check()
        torch.manual_seed(23)
        torch.set_num_threads(2)
        vectors = []
        for i, row in enumerate(rows):
            for plain in (False, True):
                batch = encode_messages(tokenizer, messages(row, plain), max_tokens=args.max_tokens, max_chars=8192)
                vectors.append(embed(model, batch).cpu())
            guard.check()
            if (i + 1) % 32 == 0:
                print(f"Encoded {i + 1}/{len(rows)} training/calibration requests", flush=True)
        x = torch.cat(vectors).clone()
        labels = torch.tensor([int(r["expected_status"] == "accepted") for r in rows for _ in (0, 1)])
        train_indexes = [i * 2 + variant for i in train_ids for variant in (0, 1)]
        cal_indexes = [i * 2 + variant for i in calibration_ids for variant in (0, 1)]
        head = torch.nn.Linear(x.shape[-1], 2)
        optimizer = torch.optim.AdamW(head.parameters(), lr=.03, weight_decay=.01)
        for step in range(300):
            loss = torch.nn.functional.cross_entropy(head(x[train_indexes]), labels[train_indexes])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            if step % 50 == 0:
                guard.check()
        head.eval()
        with torch.inference_mode():
            probabilities = head(x[cal_indexes]).softmax(-1)[:, 1]
        negative = probabilities[labels[cal_indexes] == 0]
        threshold = max(.5, float(negative.max()) + 1e-5)
        if threshold > 1:
            raise RuntimeError("no usable threshold on held-out calibration groups")
        artifact = args.output / "qwen-abstain-head.json"
        save_head(artifact, head, identity=identity, threshold=threshold, max_tokens=args.max_tokens,
                  metadata={"base_weights_frozen": True, "training_split": "subset_of_calibration",
                            "data_sha256": data_sha, "real_workflow_validated": False})
        head_vram_before = torch.cuda.memory_allocated(0)
        gate = QwenAbstainGate.from_artifact(artifact, model=model, tokenizer=tokenizer,
                                            model_dir=args.model, identity=identity)
        torch.cuda.synchronize()
        head_vram_after = torch.cuda.memory_allocated(0)
        head_parameter_bytes = sum(parameter.numel() * parameter.element_size() for parameter in head.parameters())
        receipt.update(head_parameters=sum(p.numel() for p in head.parameters()),
                       head_raw_bytes=head_parameter_bytes,
                       head_vram_allocated_delta_bytes=head_vram_after - head_vram_before,
                       artifact_bytes=artifact.stat().st_size, artifact_sha256=sha256_file(artifact),
                       threshold=threshold, max_tokens=args.max_tokens)
        from wrench_harness.worker import WrenchWorker
        worker = WrenchWorker(tokenizer=tokenizer, model=model, allowed_root=Path.cwd(), binary_abstain_gate=gate)
        scored, durations = [], []
        # Timing uses the public classification-only worker method and CUDA
        # synchronization. No executor, LM vocabulary head or generate call.
        for row in dev:
            for plain in (False, True):
                torch.cuda.synchronize()
                started = time.perf_counter()
                result = worker.classify_abstention(messages(row, plain))
                torch.cuda.synchronize()
                durations.append((time.perf_counter() - started) * 1000)
                scored.append({"id": row["id"], "prompt_style": "plain" if plain else "original",
                               "expected": "not_abstain" if row["expected_status"] == "accepted" else "abstain",
                               **result})
                if result.get("reason") == "gate_error":
                    raise RuntimeError("runtime classification failed")
            guard.check()
        receipt["development"] = {style: metrics([r for r in scored if r["prompt_style"] == style])
                                  for style in ("original", "plain")}
        timing = torch.tensor(durations)
        receipt["warm_classification_ms"] = {"samples": len(durations), "p50": float(timing.median()),
                                              "p95": float(timing.quantile(.95)), "max": float(timing.max()),
                                              "includes": "tokenization, Qwen text forward, head and worker receipt"}
        (args.output / "development-predictions.json").write_text(json.dumps(scored, indent=2), encoding="utf-8")
        # Persist representations for reproducibility and cheap head-only work.
        torch.save({"features": x, "labels": labels, "checkpoint_sha256": identity,
                    "data_sha256": data_sha, "train_indexes": train_indexes, "calibration_indexes": cal_indexes},
                   args.output / "training-features.pt")
        receipt["source_sha256"] = {str(p): sha256_file(p) for p in (
            Path(__file__), Path(__file__).resolve().parents[1] / "src/wrench_harness/qwen_abstain.py")}
        receipt["status"] = "EXPERIMENTAL_QWEN_BINARY_HEAD_TRAINED"
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k not in {
        "resource_samples", "checkpoint_sha256", "train_ids", "threshold_calibration_ids", "source_sha256"}}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("evals/wrench-expanded-v2"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
    elif not 64 <= args.max_tokens <= 1024 or not 30 <= args.max_seconds <= 900:
        parser.error("invalid resource bounds")
    else:
        run(args)
