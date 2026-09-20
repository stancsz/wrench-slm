#!/usr/bin/env python3
"""Materialize a no-weight-copy MoE top-k experiment.

The variant keeps the exact checkpoint and parameter count, but changes the
router fan-out in a derived config. It is an experiment until task quality is
recovered with distillation or fine-tuning.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


def materialize(source: Path, target: Path, top_k: int) -> dict[str, object]:
    if not source.is_dir() or not (source / "config.json").is_file():
        raise ValueError(f"source artifact is missing config.json: {source}")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing target: {target}")
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    config = json.loads((source / "config.json").read_text(encoding="utf-8"))
    text_config = config.get("text_config")
    if not isinstance(text_config, dict):
        raise ValueError("config.json is missing text_config")
    num_experts = int(text_config.get("num_experts", 0) or 0)
    if not num_experts or top_k > num_experts:
        raise ValueError(f"top_k={top_k} is outside num_experts={num_experts}")
    original_top_k = int(text_config.get("num_experts_per_tok", 0) or 0)
    target.mkdir(parents=True)
    try:
        for item in sorted(source.iterdir(), key=lambda path: path.name):
            destination = target / item.name
            if item.is_dir():
                shutil.copytree(item, destination)
            elif item.name == "config.json":
                derived = json.loads(json.dumps(config))
                derived["text_config"]["num_experts_per_tok"] = top_k
                destination.write_text(json.dumps(derived, indent=2) + "\n", encoding="utf-8")
            elif item.suffix == ".safetensors":
                try:
                    os.link(item, destination)
                except OSError:
                    shutil.copy2(item, destination)
            else:
                shutil.copy2(item, destination)
        receipt = {
            "schema": "wrench.moe-topk-variant.v1",
            "status": "DERIVED_CONFIG_WEIGHT_IDENTICAL",
            "source": str(source.resolve()),
            "target": str(target.resolve()),
            "num_experts": num_experts,
            "original_num_experts_per_tok": original_top_k,
            "derived_num_experts_per_tok": top_k,
            "weights_changed": False,
            "parameter_count_changed": False,
            "quality_claim": False,
            "next_required": [
                "direct prefill latency comparison",
                "matched mechanical-worker quality comparison",
                "LoRA or distillation recovery before any promotion",
            ],
        }
        (target / "wrench-moe-topk-variant.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        return receipt
    except Exception:
        shutil.rmtree(target)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--top-k", type=int, required=True)
    args = parser.parse_args()
    receipt = materialize(args.source, args.target, args.top_k)
    print(json.dumps({"status": receipt["status"], "target": receipt["target"], "top_k": args.top_k}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
