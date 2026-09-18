#!/usr/bin/env python3
"""Verify the two-tier Wrench model catalog from current local artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def summarize(path: Path, label: str, parameter_count: int, task_accept: str, safety: str) -> dict:
    if not path.is_dir():
        raise FileNotFoundError(path)
    index = json.loads((path / "model.safetensors.index.json").read_text(encoding="utf-8"))
    config = json.loads((path / "config.json").read_text(encoding="utf-8"))
    text_config = config.get("text_config", config)
    files = [item for item in path.rglob("*") if item.is_file()]
    directory_bytes = sum(item.stat().st_size for item in files)
    packed_bytes = index.get("metadata", {}).get("total_size")
    if not isinstance(packed_bytes, int) or packed_bytes <= 0:
        raise ValueError(f"missing packed weight size in {path}")
    return {
        "label": label,
        "artifact": str(path.resolve()),
        "directory_bytes": directory_bytes,
        "directory_gib": round(directory_bytes / (1 << 30), 3),
        "packed_weight_bytes": packed_bytes,
        "packed_weight_gib": round(packed_bytes / (1 << 30), 3),
        "parameter_count": parameter_count,
        "model_type": config.get("model_type"),
        "num_experts": text_config.get("num_experts"),
        "experts_per_token": text_config.get("num_experts_per_tok"),
        "quantization_receipt": json.loads((path / "wrench-quantization-receipt.json").read_text(encoding="utf-8")),
        "text_only_receipt": json.loads((path / "wrench-text-only-receipt.json").read_text(encoding="utf-8")),
        "task_acceptance": task_accept,
        "safety_evidence": safety,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compact", type=Path, required=True)
    parser.add_argument("--larger", type=Path, required=True)
    parser.add_argument("--safety-larger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = {
        "schema": "wrench.dual-tier-model-catalog.v1",
        "status": "EXPERIMENTAL_TWO_TIER_ARTIFACTS_VERIFIED",
        "quality_claim": False,
        "recommendation": {
            "compact": "safety-calibrated 8E for the smallest local tier",
            "larger": "prior 16E for the more useful larger tier, behind strict verifier and fallback",
            "safety_larger": "16E safety candidate, not promoted because task acceptance regressed",
        },
        "tiers": [
            summarize(args.compact, "compact_8E_safety", 3881244016, "8/20 unseen; 4/9 holdout", "0 prohibited accepts on unseen and holdout"),
            summarize(args.larger, "larger_16E", 4888532336, "8/20 unseen", "1 prohibited accept on unseen"),
            summarize(args.safety_larger, "larger_16E_safety_candidate", 4888532336, "6/20 unseen", "0 prohibited accepts on unseen"),
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": catalog["status"], "tiers": len(catalog["tiers"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
