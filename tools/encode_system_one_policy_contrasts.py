"""Encode only new unsealed policy contrasts with the frozen Qwen backbone."""
from __future__ import annotations

import argparse
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
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import (POLICY_FEATURE, checkpoint_identity,
                                            embed, encode_messages, sha256_file)
    if args.output.exists():
        raise ValueError("output exists")
    args.output.mkdir(parents=True)
    guard = Guard(args.max_seconds)
    receipt = {"schema": "wrench.system-one-policy-encoding.v1", "status": "RUNNING",
               "base_weights_updated": False, "final_split_read": False,
               "suite_cases_read": False, "provider_calls": 0, "production_enabled": False,
               "data_sha256": sha256_file(args.data)}
    try:
        guard.check()
        rows = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line]
        if len(rows) != 806 or any(row.get("split") != "training" or
                                   row.get("expected_status") not in {"accepted", "abstain"}
                                   for row in rows):
            raise ValueError("unexpected training rows")
        groups = {row["template_id"] for row in rows}
        if len(groups) != 40:
            raise ValueError("unexpected training groups")
        identity = checkpoint_identity(args.model, guard.check)
        receipt["checkpoint_sha256"] = identity
        checkpoint_bytes = sum((args.model / name).stat().st_size
                               for name in identity if name.endswith(".safetensors"))
        guard.check(extra_ram=checkpoint_bytes + 1_500_000_000,
                    extra_vram=checkpoint_bytes + 1_500_000_000)
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16,
                    local_files_only=True, trust_remote_code=False).to("cuda:0").eval().requires_grad_(False)
        torch.set_num_threads(2)
        receipt["gpu"] = torch.cuda.get_device_name(0)
        vectors = []
        for index, row in enumerate(rows):
            batch = encode_messages(tokenizer, [{"role": "user", "content": row["prompt"]}],
                                    max_tokens=1024, max_chars=8192, feature=POLICY_FEATURE)
            vectors.append(embed(model, batch).cpu())
            if (index + 1) % 100 == 0:
                guard.check()
                print(f"Encoded {index+1}/{len(rows)} new training requests", flush=True)
        torch.save({"features": torch.cat(vectors),
                    "labels": torch.tensor([int(row["expected_status"] == "accepted") for row in rows]),
                    "data_sha256": receipt["data_sha256"],
                    "checkpoint_sha256": identity}, args.output / "features.pt")
        receipt.update(status="ENCODED", rows=len(rows), groups=len(groups),
                       feature_sha256=sha256_file(args.output / "features.pt"))
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "rows", "groups", "feature_sha256")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=1800)
    main(parser.parse_args())
