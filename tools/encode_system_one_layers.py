"""Probe frozen Qwen layer readouts on unsealed prompts only."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from train_qwen_abstain import Guard


LAYERS = (8, 16, 24, 32, 40)


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(args):
    import torch
    from torch.nn import functional as F
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from wrench_harness.qwen_abstain import (POLICY_FEATURE, checkpoint_identity,
                                            encode_messages, sha256_file, text_backbone)
    if args.output.exists():
        raise ValueError("output exists")
    args.output.mkdir(parents=True)
    guard = Guard(args.max_seconds)
    receipt = {"schema": "wrench.system-one-layer-probe-encoding.v1", "status": "RUNNING",
               "layers": LAYERS, "base_weights_updated": False, "suite_cases_read": False,
               "final_split_read": False, "provider_calls": 0, "production_enabled": False,
               "sources": {str(path): sha256_file(path) for path in (args.base, args.new_data)}}
    try:
        old_rows = []
        seen = set()
        for row in rows(args.base):
            norm = " ".join(row["prompt"].casefold().split())
            if norm not in seen:
                seen.add(norm)
                old_rows.append(row)
        all_rows = old_rows + rows(args.new_data)
        if len(all_rows) != 928 or len(old_rows) != 122:
            raise ValueError("unsealed row inventory changed")
        identity = checkpoint_identity(args.model, guard.check)
        checkpoint_bytes = sum((args.model / name).stat().st_size for name in identity
                               if name.endswith(".safetensors"))
        guard.check(extra_ram=checkpoint_bytes + 1_700_000_000,
                    extra_vram=checkpoint_bytes + 1_700_000_000)
        tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
        model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16,
                    local_files_only=True, trust_remote_code=False).to("cuda:0").eval().requires_grad_(False)
        torch.set_num_threads(2)
        backbone = text_backbone(model)
        device = next(backbone.parameters()).device
        vectors = {layer: [] for layer in LAYERS}
        for index, row in enumerate(all_rows):
            batch = encode_messages(tokenizer, [{"role": "user", "content": row["prompt"]}],
                                    max_tokens=1024, max_chars=8192, feature=POLICY_FEATURE)
            batch = {key: value.to(device) for key, value in batch.items()}
            with torch.inference_mode():
                output = backbone(**batch, use_cache=False, output_hidden_states=True,
                                  output_attentions=False, return_dict=True)
                hidden = output.hidden_states
                if len(hidden) != 41:
                    raise ValueError("unexpected Qwen layer count")
                for layer in LAYERS:
                    vectors[layer].append(F.normalize(hidden[layer][:, -1, :].float(), dim=-1).cpu())
            if (index + 1) % 100 == 0:
                guard.check()
                print(f"Encoded {index+1}/{len(all_rows)} unsealed requests", flush=True)
        torch.save({"layers": {layer: torch.cat(values) for layer, values in vectors.items()},
                    "labels": torch.tensor([int(row["expected_status"] == "accepted") for row in all_rows]),
                    "checkpoint_sha256": identity, "source_sha256": receipt["sources"]},
                   args.output / "features.pt")
        receipt.update(status="ENCODED", rows=len(all_rows),
                       checkpoint_sha256=identity,
                       features_sha256=sha256_file(args.output / "features.pt"),
                       gpu=torch.cuda.get_device_name(0))
        guard.check()
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["resource_samples"] = guard.samples
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "rows", "features_sha256")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--base", type=Path, default=Path("evals/wrench-expanded-v2/calibration.jsonl"))
    parser.add_argument("--new-data", type=Path, default=Path("phases/system-one-policy-contrasts-v3-20260922/train.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/system-one-readiness/layer-probe-v3"))
    parser.add_argument("--max-seconds", type=int, default=1800)
    main(parser.parse_args())
