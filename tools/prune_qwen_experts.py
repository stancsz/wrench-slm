#!/usr/bin/env python3
"""Stream a structural Qwen MoE expert prune into a new safetensors checkpoint.

The source is never modified. Only tensors whose first dimension is the
declared expert count are sliced: routed expert banks and router output rows.
All other tensors are copied unchanged, one tensor at a time, so the full
checkpoint does not need to fit in RAM.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import re
from pathlib import Path
from typing import Any

import torch
from safetensors.torch import save_file
from safetensors import safe_open


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_prunable(name: str, num_experts: int, shape: list[int]) -> bool:
    return bool(shape) and shape[0] == num_experts and (
        ".mlp.experts." in name or name.endswith(".mlp.gate.weight")
    )


def _route_key(name: str) -> str:
    """Map checkpoint tensor names to the runtime router prefix."""
    key = name.replace("model.language_model.layers.", "model.layers.")
    match = re.match(r"(.+?\.mlp)(?:\.experts\..*|\.gate\.weight)$", key)
    if not match:
        raise ValueError(f"cannot derive router route key from prunable tensor: {name}")
    return match.group(1)


def _save_chunk(
    output: Path,
    tensors: dict[str, torch.Tensor],
    chunk_number: int,
    manifest: dict[str, str],
) -> int:
    if not tensors:
        return 0
    path = output / f"chunk-{chunk_number:05d}.safetensors"
    save_file(tensors, str(path), metadata={"format": "pt"})
    for name in tensors:
        manifest[name] = path.name
    return path.stat().st_size


def prune_checkpoint(
    source: Path,
    output: Path,
    expert_indices: list[int] | None = None,
    chunk_limit_bytes: int = 1 << 30,
    selection_receipt: Path | None = None,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"refusing to overwrite existing output: {output}")
    config = _load_json(source / "config.json")
    text_config = config.get("text_config") or {}
    num_experts = int(text_config.get("num_experts", 0))
    top_k = int(text_config.get("num_experts_per_tok", 0))
    if num_experts <= 0 or top_k <= 0:
        raise ValueError("source config must declare positive num_experts and num_experts_per_tok")
    if (expert_indices is None) == (selection_receipt is None):
        raise ValueError("provide exactly one of expert_indices or selection_receipt")
    route_selections: dict[str, list[int]] = {}
    if selection_receipt is not None:
        selection = _load_json(selection_receipt)
        if selection.get("status") != "PASS_ROUTER_SELECTION_DERIVED":
            raise ValueError("selection receipt is not a derived pass receipt")
        if int(selection.get("source_num_experts", -1)) != num_experts:
            raise ValueError("selection receipt source expert count does not match checkpoint")
        route_selections = {str(key): [int(value) for value in values] for key, values in selection["routes"].items()}
        default_indices = [int(value) for value in selection.get("default_indices", [])]
        if not default_indices:
            raise ValueError("selection receipt must include default_indices for unprofiled routes")
        route_selections["__default__"] = default_indices
        counts = {len(values) for values in route_selections.values()}
        if len(counts) != 1:
            raise ValueError("all routes must retain the same expert count")
        retained_count = counts.pop()
        target_top_k = int(selection.get("target_num_experts_per_tok", top_k))
        if target_top_k <= 0 or target_top_k > retained_count:
            raise ValueError("target_num_experts_per_tok must be positive and no greater than retained experts")
        if retained_count < top_k and "target_num_experts_per_tok" not in selection:
            raise ValueError("retained expert count must not be below num_experts_per_tok")
        if any(len(set(values)) != len(values) for values in route_selections.values()):
            raise ValueError("selection receipt contains duplicate expert indices")
        if any(not values or min(values) < 0 or max(values) >= num_experts for values in route_selections.values()):
            raise ValueError("selection receipt contains an expert outside the source range")
        expert_indices = None
    else:
        assert expert_indices is not None
        if len(set(expert_indices)) != len(expert_indices):
            raise ValueError("expert indices must be unique")
        if not expert_indices or min(expert_indices) < 0 or max(expert_indices) >= num_experts:
            raise ValueError("expert indices must be in the source expert range")
        target_top_k = top_k
        if len(expert_indices) < top_k:
            raise ValueError("retained expert count must not be below num_experts_per_tok")
        retained_count = len(expert_indices)

    index = _load_json(source / "model.safetensors.index.json")
    output.mkdir(parents=True)
    tensors_by_shard: dict[str, list[str]] = {}
    for name, shard in index["weight_map"].items():
        tensors_by_shard.setdefault(shard, []).append(name)

    output_manifest: dict[str, str] = {}
    output_total_size = 0
    output_data_size = 0
    source_prunable = 0
    retained_prunable = 0
    chunk_number = 1
    chunk: dict[str, torch.Tensor] = {}
    chunk_bytes = 0
    pruned_names: list[str] = []

    for shard, names in sorted(tensors_by_shard.items()):
        with safe_open(str(source / shard), framework="pt", device="cpu") as handle:
            for name in sorted(names):
                tensor_slice = handle.get_slice(name)
                shape = tensor_slice.get_shape()
                prunable = _is_prunable(name, num_experts, shape)
                selected_indices = expert_indices
                if prunable and selection_receipt is not None:
                    route = _route_key(name)
                    try:
                        selected_indices = route_selections.get(route, route_selections["__default__"])
                    except KeyError as exc:
                        raise ValueError(f"selection receipt has no route or default for {route}") from exc
                tensor = tensor_slice[selected_indices] if prunable else tensor_slice[:]
                tensor = tensor.contiguous()
                if prunable:
                    source_elements = 1
                    for dimension in shape:
                        source_elements *= int(dimension)
                    source_prunable += source_elements
                    retained_prunable += tensor.numel()
                    pruned_names.append(name)
                tensor_bytes = tensor.numel() * tensor.element_size()
                if chunk and chunk_bytes + tensor_bytes > chunk_limit_bytes:
                    saved = _save_chunk(output, chunk, chunk_number, output_manifest)
                    output_total_size += saved
                    chunk_number += 1
                    chunk = {}
                    chunk_bytes = 0
                chunk[name] = tensor
                chunk_bytes += tensor_bytes
                output_data_size += tensor_bytes
    if chunk:
        saved = _save_chunk(output, chunk, chunk_number, output_manifest)
        output_total_size += saved
        chunk_number += 1

    output_chunks = sorted(output.glob("chunk-*.safetensors"))
    chunk_count = len(output_chunks)
    final_manifest: dict[str, str] = {}
    for number, old_path in enumerate(output_chunks, start=1):
        new_name = f"model-{number:05d}-of-{chunk_count:05d}.safetensors"
        new_path = output / new_name
        old_path.rename(new_path)
        for tensor_name, shard_name in output_manifest.items():
            if shard_name == old_path.name:
                final_manifest[tensor_name] = new_name

    output_config = copy.deepcopy(config)
    output_config.setdefault("text_config", {})["num_experts"] = retained_count
    output_config["text_config"]["num_experts_per_tok"] = target_top_k
    (output / "config.json").write_text(json.dumps(output_config, indent=2) + "\n", encoding="utf-8")
    for path in source.iterdir():
        if not path.is_file() or path.name in {"config.json", "model.safetensors.index.json"} or path.suffix == ".safetensors":
            continue
        shutil.copy2(path, output / path.name)
    output_index = {
        "metadata": {"total_size": output_data_size},
        "weight_map": final_manifest,
    }
    (output / "model.safetensors.index.json").write_text(json.dumps(output_index, indent=2) + "\n", encoding="utf-8")

    return {
        "schema": "wrench.qwen-structural-prune.v1",
        "source": str(source),
        "output": str(output),
        "selection_rule": "per-route router telemetry" if selection_receipt is not None else "explicit_expert_indices",
        "expert_indices": expert_indices,
        "selection_receipt": str(selection_receipt.resolve()) if selection_receipt is not None else None,
        "route_selection_count": len(route_selections) - (1 if selection_receipt is not None else 0),
        "route_selections": route_selections if selection_receipt is not None else None,
        "source_num_experts": num_experts,
        "retained_num_experts": retained_count,
        "num_experts_per_tok": top_k,
        "prunable_source_elements": source_prunable,
        "retained_prunable_elements": retained_prunable,
        "output_tensor_data_bytes": output_data_size,
        "output_safetensors_bytes": output_total_size,
        "output_shard_count": chunk_count,
        "sliced_tensor_count": len(pruned_names),
        "weights_modified": False,
        "status": "EXPERIMENTAL_UNCALIBRATED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--indices", type=int, nargs="+")
    group.add_argument("--selection-receipt", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = prune_checkpoint(
        args.source.resolve(),
        args.output.resolve(),
        args.indices,
        selection_receipt=args.selection_receipt.resolve() if args.selection_receipt else None,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "output": str(args.output), "shards": receipt["output_shard_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
