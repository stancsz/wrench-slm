#!/usr/bin/env python3
"""Create an evidence receipt for a local Qwen3.6 checkpoint.

This deliberately inspects metadata and file identity only. It never loads model
weights and it never edits the checkpoint. Packed quantized weights are reported
as unsuitable for structural tensor slicing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_FILES = {
    "config.json",
    "configuration.json",
    "generation_config.json",
    "hf_quant_config.json",
    "preprocessor_config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.json",
    "chat_template.jinja",
    "video_preprocessor_config.json",
    "freetoken_weight.json",
    "freetoken_weight.json.bak",
    "README.md",
}


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def front_matter(readme: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not readme.startswith("---"):
        return result
    header = readme.split("---", 2)[1]
    for line in header.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line.strip())
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def quantization_summary(config: dict[str, Any], hf_quant: dict[str, Any]) -> dict[str, Any]:
    quant = hf_quant or config.get("quantization_config") or {}
    nested = quant.get("quantization") or {}
    layers = nested.get("quantized_layers") or {}
    algorithms = Counter(
        str(value.get("quant_algo", "unknown"))
        for value in layers.values()
        if isinstance(value, dict)
    )
    return {
        "producer": nested.get("producer", quant.get("producer")),
        "quant_algo": nested.get("quant_algo"),
        "quantized_layer_count": len(layers),
        "quantized_algorithm_counts": dict(sorted(algorithms.items())),
        "exclude_modules": nested.get("exclude_modules", []),
    }


def inspect_checkpoint(root: Path, hash_weights: bool) -> dict[str, Any]:
    config_path = root / "config.json"
    readme_path = root / "README.md"
    if not root.is_dir():
        raise ValueError(f"checkpoint directory does not exist: {root}")
    if not config_path.is_file():
        raise ValueError(f"missing config.json: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    hf_quant_path = root / "hf_quant_config.json"
    hf_quant = json.loads(hf_quant_path.read_text(encoding="utf-8")) if hf_quant_path.is_file() else {}
    text_config = config.get("text_config") or {}
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""

    files = []
    for path in sorted(p for p in root.iterdir() if p.is_file()):
        is_weight = path.suffix.lower() in {".ftw", ".safetensors", ".bin", ".gguf"}
        entry: dict[str, Any] = {
            "name": path.name,
            "bytes": path.stat().st_size,
            "kind": "weight" if is_weight else "metadata",
        }
        if not is_weight or hash_weights:
            entry["sha256"] = sha256_file(path)
        else:
            entry["sha256"] = None
        files.append(entry)

    weight_paths = [
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".ftw", ".safetensors", ".bin", ".gguf"}
    ]
    has_safetensors_index = (root / "model.safetensors.index.json").is_file()
    source_is_packed_quantized = bool(hf_quant) or any(
        path.suffix.lower() in {".ftw", ".gguf"} for path in weight_paths
    )
    safe_for_structural_tensor_slicing = bool(weight_paths) and not source_is_packed_quantized and (
        has_safetensors_index or any(path.suffix.lower() == ".safetensors" for path in weight_paths)
    )
    if safe_for_structural_tensor_slicing:
        pruning_reason = "Unquantized safetensors with a local tensor index are eligible for structural slicing after architecture checks."
    elif source_is_packed_quantized:
        pruning_reason = "This local candidate contains packed or quantized weights; obtain and verify an unquantized checkpoint before slicing tensors."
    else:
        pruning_reason = "A verified unquantized safetensors checkpoint with a matching tensor index is required before slicing tensors."

    return {
        "schema": "wrench.qwen-checkpoint-facts.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint_path": str(root),
        "evidence_scope": "local_metadata_and_file_identity",
        "model_card_front_matter": front_matter(readme),
        "config": {
            "architectures": config.get("architectures", []),
            "model_type": config.get("model_type"),
            "dtype": config.get("dtype"),
            "transformers_version": config.get("transformers_version"),
            "text_config": {
                key: text_config.get(key)
                for key in (
                    "model_type",
                    "num_hidden_layers",
                    "hidden_size",
                    "num_experts",
                    "num_experts_per_tok",
                    "moe_intermediate_size",
                    "shared_expert_intermediate_size",
                    "vocab_size",
                    "max_position_embeddings",
                    "layer_types",
                )
            },
        },
        "quantization": quantization_summary(config, hf_quant),
        "files": files,
        "pruning_assessment": {
            "source_is_packed_quantized": source_is_packed_quantized,
            "safe_for_structural_tensor_slicing": safe_for_structural_tensor_slicing,
            "reason": pruning_reason,
            "required_source": "verified unquantized checkpoint with matching architecture and license",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--hash-weights",
        action="store_true",
        help="hash large weight files; otherwise only metadata files are hashed",
    )
    args = parser.parse_args()
    receipt = inspect_checkpoint(args.checkpoint.resolve(), args.hash_weights)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.output), "files": len(receipt["files"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
