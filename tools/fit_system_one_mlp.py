"""Fit a small MLP classifier on frozen Qwen features from unsealed data.

This command never opens the 5,600-case diagnostic suite, the 60-case
independent set, or the repository's sealed final split.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import random
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from train_qwen_abstain import Guard, messages, read_rows


def bounded_training(path: Path) -> tuple[list[dict], str]:
    with path.open("rb") as stream:
        raw = stream.read(4_000_001)
    if len(raw) > 4_000_000:
        raise ValueError("training data too large")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not 2 <= len(rows) <= 2048:
        raise ValueError("training row count invalid")
    for row in rows:
        if (row.get("split") != "training" or row.get("expected_status") not in {"accepted", "abstain"}
                or not str(row.get("template_id", "")).startswith("extra_template_")
                or not isinstance(row.get("prompt"), str) or not 1 <= len(row["prompt"]) <= 4096):
            raise ValueError("invalid training row")
    return rows, hashlib.sha256(raw).hexdigest()


def rates(logits, targets):
    prediction = logits.argmax(-1)
    positive = targets == 1
    return {"rows": int(len(targets)), "accuracy": float((prediction == targets).float().mean()),
            "wrench_coverage": float((prediction[positive] == 1).float().mean()),
            "unsafe_classifier_passes": int((prediction[~positive] == 1).sum()),
            "abstain_rows": int((~positive).sum()), "wrench_rows": int(positive.sum())}


def run(args):
    import torch
    import transformers
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import (POLICY, POLICY_FEATURE, checkpoint_identity,
                                            embed, encode_messages, save_mlp_head, sha256_file)

    args.output.mkdir(parents=True, exist_ok=False)
    guard = Guard(args.max_seconds)
    root = Path(__file__).resolve().parents[1]
    source_paths = [Path(__file__), root / "tools/augment_system_one_training.py",
                    root / "src/wrench_harness/qwen_abstain.py", root / "tools/train_qwen_abstain.py"]
    receipt = {"schema": "wrench.system-one-mlp-fit.v1", "status": "RUNNING",
               "provider_calls": 0, "generated_tokens": 0, "base_weights_updated": False,
               "independent_60_read": False, "suite_5600_read": False, "final_split_read": False,
               "production_enabled": False,
               "environment": {"torch": torch.__version__, "transformers": transformers.__version__},
               "source_sha256": {str(path.relative_to(root)): sha256_file(path) for path in source_paths}}
    try:
        guard.check()
        rows, base_sha = read_rows(root / "evals/wrench-expanded-v2/calibration.jsonl", "calibration")
        extra, extra_sha = bounded_training(args.training_extra)
        for row in extra:
            row["system"] = rows[0]["system"]
        rows.extend(extra)
        seen, retained = {}, []
        for row in rows:
            norm = " ".join(row["prompt"].casefold().split())
            prior = seen.get(norm)
            if prior is not None:
                if prior != row["expected_status"]:
                    raise ValueError("conflicting duplicate training labels")
                continue
            seen[norm] = row["expected_status"]
            retained.append(row)
        rows = retained
        groups = defaultdict(list)
        for index, row in enumerate(rows):
            groups[row["template_id"]].append(index)
        train_ids, cal_ids = [], []
        families = {name.rsplit("_template_", 1)[0] for name in groups}
        for family in sorted(families):
            names = sorted(name for name in groups if name.rsplit("_template_", 1)[0] == family)
            random.Random(47).shuffle(names)
            held = set(names[:max(1, len(names)//4)])
            for name in names:
                (cal_ids if name in held else train_ids).extend(groups[name])
        for ids in (train_ids, cal_ids):
            if {rows[i]["expected_status"] for i in ids} != {"accepted", "abstain"}:
                raise ValueError("both labels required in train and calibration")
        receipt.update(data_sha256={"base_calibration": base_sha, "augmented": extra_sha},
                       unique_rows=len(rows), training_rows=len(train_ids), calibration_rows=len(cal_ids),
                       train_groups=sorted({rows[i]["template_id"] for i in train_ids}),
                       cal_groups=sorted({rows[i]["template_id"] for i in cal_ids}),
                       policy_sha256=hashlib.sha256(POLICY.encode()).hexdigest())
        print("Hashing existing Qwen checkpoint", flush=True)
        identity = checkpoint_identity(args.model, guard.check)
        receipt["checkpoint_sha256"] = identity
        checkpoint_bytes = sum((args.model / name).stat().st_size for name in identity if name.endswith(".safetensors"))
        guard.check(extra_ram=checkpoint_bytes + 1_500_000_000,
                    extra_vram=checkpoint_bytes + 1_500_000_000)
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16,
                    local_files_only=True, trust_remote_code=False).to("cuda:0").eval().requires_grad_(False)
        torch.set_num_threads(2)
        torch.manual_seed(47)
        receipt["environment"]["gpu"] = torch.cuda.get_device_name(0)
        receipt["backbone_parameter_bytes"] = sum(p.numel()*p.element_size() for p in model.parameters())
        receipt["backbone_allocated_vram_bytes"] = torch.cuda.memory_allocated(0)
        features = []
        for index, row in enumerate(rows):
            for plain in (False, True):
                batch = encode_messages(tokenizer, messages(row, plain), max_tokens=1024,
                                        max_chars=8192, feature=POLICY_FEATURE)
                features.append(embed(model, batch).cpu())
            guard.check()
            if (index + 1) % 100 == 0:
                print(f"Encoded {index+1}/{len(rows)} unsealed requests", flush=True)
        x = torch.cat(features).clone()
        y = torch.tensor([int(row["expected_status"] == "accepted") for row in rows for _ in (0, 1)])
        ti = [index*2 + variant for index in train_ids for variant in (0, 1)]
        ci = [index*2 + variant for index in cal_ids for variant in (0, 1)]
        head = torch.nn.Sequential(torch.nn.Linear(x.shape[-1], 32), torch.nn.GELU(),
                                   torch.nn.Linear(32, 2))
        optimizer = torch.optim.AdamW(head.parameters(), lr=.003, weight_decay=.01)
        for step in range(500):
            loss = torch.nn.functional.cross_entropy(head(x[ti]), y[ti])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            if step % 50 == 0:
                guard.check()
        head.eval()
        with torch.inference_mode():
            cal_logits = head(x[ci])
        plain_indexes = [j for j, index in enumerate(ci) if index % 2 == 1]
        receipt["calibration"] = {"all_formats": rates(cal_logits, y[ci]),
                                  "plain_user": rates(cal_logits[plain_indexes], y[ci][plain_indexes])}
        artifact = args.output / "qwen-abstain-head.json"
        save_mlp_head(artifact, head, identity=identity, threshold=.5, max_tokens=1024,
                      metadata={"data_sha256": receipt["data_sha256"], "base_weights_frozen": True,
                                "real_workflow_validated": False})
        receipt.update(artifact_sha256=sha256_file(artifact), artifact_bytes=artifact.stat().st_size,
                       head_parameters=sum(p.numel() for p in head.parameters()),
                       head_raw_bytes=sum(p.numel()*p.element_size() for p in head.parameters()),
                       threshold=.5, independent_evaluation_unopened=True)
        torch.save({"features": x, "labels": y, "train_indexes": ti,
                    "calibration_indexes": ci, "checkpoint_sha256": identity},
                   args.output / "training-features.pt")
        if receipt["source_sha256"] != {str(path.relative_to(root)): sha256_file(path) for path in source_paths}:
            raise RuntimeError("source changed during training")
        receipt["status"] = "CALIBRATED_HEAD_READY"
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "training_rows", "calibration_rows",
                                                   "calibration", "artifact_bytes", "head_parameters")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--training-extra", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=1800)
    args = parser.parse_args()
    if args.run:
        run(args)
    else:
        parser.print_help()
