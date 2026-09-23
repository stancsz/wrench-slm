"""Read pretrained Qwen output rows against saved unsealed prompt features.

No model load, GPU job, test suite, or sealed evaluation is involved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safetensors import safe_open
import torch
from transformers import AutoTokenizer


PAIRS = {
    "not_vs_abstain_first": ("NOT_ABSTAIN", "ABSTAIN"),
    "yes_vs_no": (" yes", " no"),
    "YES_vs_NO": ("YES", "NO"),
    "A_vs_B": ("A", "B"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--features", type=Path, required=True)
    args = parser.parse_args()
    data = torch.load(args.features, weights_only=True, map_location="cpu")
    x = data["features"].float()
    y = data["labels"]
    ci = data["calibration_indexes"]
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    index = json.loads((args.model / "model.safetensors.index.json").read_text(encoding="utf-8"))
    shard = args.model / index["weight_map"]["lm_head.weight"]
    rows = {}
    with safe_open(shard, framework="pt", device="cpu") as stream:
        weight = stream.get_slice("lm_head.weight")
        for name, (positive, negative) in PAIRS.items():
            a = tokenizer.encode(positive, add_special_tokens=False)[0]
            b = tokenizer.encode(negative, add_special_tokens=False)[0]
            rows[name] = (a, b, weight[a:a+1].float()[0], weight[b:b+1].float()[0])
    report = {}
    for name, (a, b, pos, neg) in rows.items():
        margin = x[ci] @ (pos-neg)
        pred = margin >= 0
        target = y[ci].bool()
        plain = torch.tensor([i % 2 == 1 for i in ci])
        report[name] = {"positive_token": a, "negative_token": b}
        for suffix, keep in (("all", torch.ones_like(plain, dtype=torch.bool)), ("plain", plain)):
            p, t = pred[keep], target[keep]
            report[name][suffix] = {"accuracy": float((p==t).float().mean()),
                                    "wrench_coverage": float(p[t].float().mean()),
                                    "false_wrench": int(p[~t].sum()), "rows": int(len(t))}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
