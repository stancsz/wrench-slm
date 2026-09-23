"""Encode the owner-authorized synthetic 5k suite for binary head training.

The suite is retired as an evaluation set when this encoder is used. No
sealed final split, provider, proposal, or tool execution is involved.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from train_qwen_abstain import Guard


def main(args):
    import torch
    from torch.nn import functional as F
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import (LAYER8_FEATURE, checkpoint_identity,
                                            encode_messages, sha256_file, text_backbone)

    if args.output.exists():
        raise ValueError("output exists")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    raw = args.cases.read_bytes()
    case_hash = hashlib.sha256(raw).hexdigest()
    if case_hash != manifest.get("cases_sha256"):
        raise ValueError("suite hash mismatch")
    cases = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if (len(cases) != 5600 or Counter(case.get("label") for case in cases)
            != {"abstain": 5000, "wrench": 600}
            or len({case.get("id") for case in cases}) != 5600):
        raise ValueError("training suite inventory mismatch")
    args.output.mkdir(parents=True)
    guard = Guard(args.max_seconds)
    receipt = {"schema": "wrench.system-one-authorized-5k-encoding.v1",
               "status": "RUNNING", "source_sha256": case_hash,
               "source_role": "owner-authorized synthetic training; former test suite retired",
               "labels": dict(Counter(case["label"] for case in cases)),
               "base_weights_updated": False, "sealed_final_read": False,
               "provider_calls": 0, "tool_actions": 0, "production_enabled": False}
    try:
        identity = checkpoint_identity(args.model, guard.check)
        checkpoint_bytes = sum((args.model / name).stat().st_size for name in identity
                               if name.endswith(".safetensors"))
        guard.check(extra_ram=checkpoint_bytes + 1_700_000_000,
                    extra_vram=checkpoint_bytes + 1_700_000_000)
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True,
                                                   trust_remote_code=False)
        model = AutoModelForImageTextToText.from_pretrained(
            args.model, dtype=torch.bfloat16, local_files_only=True,
            trust_remote_code=False).to("cuda:0").eval().requires_grad_(False)
        torch.set_num_threads(2)
        backbone = text_backbone(model)
        device = next(backbone.parameters()).device
        vectors = []
        for index, case in enumerate(cases):
            batch = encode_messages(tokenizer, [{"role": "user", "content": case["prompt"]}],
                                    max_tokens=1024, max_chars=8192,
                                    feature=LAYER8_FEATURE)
            batch = {key: value.to(device) for key, value in batch.items()}
            with torch.inference_mode():
                result = backbone(**batch, use_cache=False,
                                  output_hidden_states=True,
                                  output_attentions=False, return_dict=True)
                if len(result.hidden_states) != 41:
                    raise ValueError("unexpected Qwen layer count")
                vectors.append(F.normalize(result.hidden_states[8][:, -1, :].float(),
                                           dim=-1).cpu())
            if (index + 1) % 100 == 0:
                guard.check()
            if (index + 1) % 500 == 0:
                print(f"Encoded {index + 1}/5600 training requests", flush=True)
        feature_path = args.output / "features.pt"
        torch.save({"layer": 8, "features": torch.cat(vectors),
                    "labels": torch.tensor([int(case["label"] == "wrench") for case in cases]),
                    "ids": [case["id"] for case in cases],
                    "checkpoint_sha256": identity, "source_sha256": case_hash}, feature_path)
        receipt.update(status="ENCODED", rows=len(cases),
                       checkpoint_sha256=identity,
                       features_sha256=sha256_file(feature_path),
                       gpu=torch.cuda.get_device_name(0))
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                    encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "rows", "features_sha256")},
                     indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=Path("phases/system-one-binary-5k-20260922/cases.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("phases/system-one-binary-5k-20260922/manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=1800)
    main(parser.parse_args())
