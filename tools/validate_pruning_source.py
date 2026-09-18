#!/usr/bin/env python3
"""Validate that a Qwen checkpoint is an eligible structural-pruning source.

This validator only inspects metadata and file identity. It never slices or
rewrites weights. It rejects packed FTW/NVFP4 artifacts and any architecture
or shard-index mismatch before a pruning implementation can run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED = {
    "model_type": "qwen3_5_moe",
    "architecture": "Qwen3_5MoeForConditionalGeneration",
    "num_hidden_layers": 40,
    "hidden_size": 2048,
    "num_experts": 256,
    "num_experts_per_tok": 8,
    "total_size": 71_903_645_408,
}


def validate_pruning_source(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "wrench.qwen-pruning-source-validation.v1",
        "checkpoint_path": str(root),
        "eligible": False,
        "checks": {},
        "rejection_reasons": [],
    }
    if not root.is_dir():
        result["rejection_reasons"].append("checkpoint_directory_missing")
        return result

    config_path = root / "config.json"
    if not config_path.is_file():
        result["rejection_reasons"].append("config_missing")
        return result
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result["rejection_reasons"].append("config_unreadable")
        return result
    text_config = config.get("text_config") or {}
    observed = {
        "model_type": config.get("model_type"),
        "architecture": (config.get("architectures") or [None])[0],
        "num_hidden_layers": text_config.get("num_hidden_layers"),
        "hidden_size": text_config.get("hidden_size"),
        "num_experts": text_config.get("num_experts"),
        "num_experts_per_tok": text_config.get("num_experts_per_tok"),
    }
    result["observed_architecture"] = observed
    for key in observed:
        if observed[key] != EXPECTED[key]:
            result["rejection_reasons"].append(f"architecture_mismatch:{key}")
    packed = sorted(path.name for path in root.glob("*.ftw"))
    if packed:
        result["checks"]["packed_ftw_files"] = packed
        result["rejection_reasons"].append("packed_ftw_not_sliceable")
    quant_config = root / "hf_quant_config.json"
    if quant_config.is_file():
        result["checks"]["quant_config_present"] = True
        result["rejection_reasons"].append("quantization_metadata_present")

    index_path = root / "model.safetensors.index.json"
    if not index_path.is_file():
        result["rejection_reasons"].append("safetensors_index_missing")
        return result
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        result["rejection_reasons"].append("safetensors_index_unreadable")
        return result
    metadata = index.get("metadata") or {}
    weight_map = index.get("weight_map") or {}
    mapped_shards = sorted(set(weight_map.values()))
    missing_shards = [name for name in mapped_shards if not (root / name).is_file()]
    non_safetensors = [name for name in mapped_shards if Path(name).suffix.lower() != ".safetensors"]
    result["checks"].update(
        {
            "index_total_size": metadata.get("total_size"),
            "mapped_tensor_count": len(weight_map),
            "shard_count": len(mapped_shards),
            "missing_shards": missing_shards,
            "non_safetensors_shards": non_safetensors,
        }
    )
    if metadata.get("total_size") != EXPECTED["total_size"]:
        result["rejection_reasons"].append("unquantized_size_mismatch")
    if missing_shards:
        result["rejection_reasons"].append("shard_missing")
    if non_safetensors:
        result["rejection_reasons"].append("non_safetensors_shard")
    if not result["rejection_reasons"]:
        result["eligible"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = validate_pruning_source(args.checkpoint.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"eligible": receipt["eligible"], "rejection_reasons": receipt["rejection_reasons"]}, indent=2))
    return 0 if receipt["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
