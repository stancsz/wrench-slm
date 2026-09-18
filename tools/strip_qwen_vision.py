#!/usr/bin/env python3
"""Create a text-only Qwen export by removing unused vision tensors."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def strip_vision(source: Path, output: Path) -> dict:
    from safetensors import safe_open
    from safetensors.torch import save_file

    if output.exists():
        raise ValueError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    source_index = json.loads((source / "model.safetensors.index.json").read_text(encoding="utf-8"))
    source_files = sorted(set(source_index["weight_map"].values()))
    weight_map: dict[str, str] = {}
    removed: list[str] = []
    total_size = 0
    for source_name in source_files:
        source_file = source / source_name
        target_name = source_name
        tensors = {}
        metadata = None
        with safe_open(source_file, framework="pt", device="cpu") as reader:
            metadata = reader.metadata()
            for name in reader.keys():
                if name.startswith("model.visual."):
                    removed.append(name)
                    continue
                tensors[name] = reader.get_tensor(name)
                weight_map[name] = target_name
                total_size += tensors[name].numel() * tensors[name].element_size()
        if tensors:
            save_file(tensors, output / target_name, metadata=metadata or {"format": "pt"})

    # Preserve model/tokenizer/quantization metadata, but replace the index and
    # add a receipt that makes the text-only scope explicit.
    for source_file in source.iterdir():
        if not source_file.is_file() or source_file.name in source_files or source_file.name == "model.safetensors.index.json":
            continue
        shutil.copy2(source_file, output / source_file.name)
    index = {"metadata": {"total_size": total_size}, "weight_map": weight_map}
    (output / "model.safetensors.index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "schema": "wrench.qwen-text-only-pack.v1",
        "status": "PASS_TEXT_ONLY_VISION_STRIP",
        "source": str(source.resolve()),
        "output": str(output.resolve()),
        "removed_tensor_prefix": "model.visual.",
        "removed_tensor_count": len(removed),
        "removed_tensor_names_sha256": __import__("hashlib").sha256("\n".join(removed).encode()).hexdigest(),
        "remaining_weight_bytes": total_size,
        "quality_claim": False,
    }
    (output / "wrench-text-only-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(strip_vision(args.source.resolve(), args.output.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
