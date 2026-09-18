#!/usr/bin/env python3
"""Estimate Qwen expert-pruning sizes from safetensors headers only.

No tensor payloads are loaded. The report is a structural size estimate for
retaining K routed experts per MoE layer, including the corresponding router
rows. It is not a pruning implementation or a quality claim.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from collections import Counter
from pathlib import Path
from typing import Any


DTYPE_BYTES = {
    "BOOL": 1,
    "U8": 1,
    "I8": 1,
    "U16": 2,
    "I16": 2,
    "U32": 4,
    "I32": 4,
    "U64": 8,
    "I64": 8,
    "F8_E4M3": 1,
    "F8_E4M3_UFLOAT": 1,
    "F8_E5M2": 1,
    "F16": 2,
    "BF16": 2,
    "F32": 4,
    "F64": 8,
    "C64": 8,
    "C128": 16,
}


def _numel(shape: list[int]) -> int:
    result = 1
    for dimension in shape:
        result *= int(dimension)
    return result


def read_safetensors_header(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        raw_length = handle.read(8)
        if len(raw_length) != 8:
            raise ValueError(f"truncated safetensors header length: {path}")
        header_length = struct.unpack("<Q", raw_length)[0]
        header = handle.read(header_length)
        if len(header) != header_length:
            raise ValueError(f"truncated safetensors header: {path}")
    return json.loads(header.decode("utf-8"))


def _tensor_records(checkpoint: Path, index: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    by_shard: dict[str, list[str]] = {}
    for name, shard in index["weight_map"].items():
        by_shard.setdefault(shard, []).append(name)

    for shard, expected_names in sorted(by_shard.items()):
        path = checkpoint / shard
        if not path.is_file():
            raise ValueError(f"missing mapped shard: {path}")
        header = read_safetensors_header(path)
        for name in expected_names:
            if name not in header:
                raise ValueError(f"tensor {name} missing from shard header {path}")
            metadata = header[name]
            dtype = str(metadata["dtype"])
            if dtype not in DTYPE_BYTES:
                raise ValueError(f"unsupported safetensors dtype {dtype!r} for {name}")
            shape = [int(dimension) for dimension in metadata["shape"]]
            elements = _numel(shape)
            records.append(
                {
                    "name": name,
                    "shard": shard,
                    "dtype": dtype,
                    "shape": shape,
                    "elements": elements,
                    "bytes": elements * DTYPE_BYTES[dtype],
                }
            )
    return records


def _scenario(
    keep: int,
    num_experts: int,
    total_elements: int,
    total_bytes: int,
    routed_elements: int,
    routed_bytes: int,
    router_elements: int,
    router_bytes: int,
) -> dict[str, Any]:
    if not 1 <= keep <= num_experts:
        raise ValueError(f"keep must be between 1 and {num_experts}: {keep}")
    prunable_elements = routed_elements + router_elements
    prunable_bytes = routed_bytes + router_bytes
    fixed_elements = total_elements - prunable_elements
    fixed_bytes = total_bytes - prunable_bytes
    retained_elements = fixed_elements + (prunable_elements * keep // num_experts)
    retained_bytes = fixed_bytes + (prunable_bytes * keep // num_experts)
    return {
        "keep_experts_per_moe_block": keep,
        "removed_experts_per_moe_block": num_experts - keep,
        "retained_expert_fraction": keep / num_experts,
        "estimated_tensor_elements": retained_elements,
        "estimated_parameters_billions": retained_elements / 1_000_000_000,
        "estimated_bf16_weight_bytes": retained_bytes,
        "estimated_bf16_weight_gib": retained_bytes / (1024**3),
        "ideal_int4_weight_bytes": math.ceil(retained_elements / 2),
        "ideal_int4_weight_gib": math.ceil(retained_elements / 2) / (1024**3),
        "removed_tensor_elements": total_elements - retained_elements,
        "removed_weight_bytes_bf16": total_bytes - retained_bytes,
    }


def analyze_checkpoint(checkpoint: Path, keeps: list[int]) -> dict[str, Any]:
    config = json.loads((checkpoint / "config.json").read_text(encoding="utf-8"))
    text_config = config.get("text_config") or {}
    num_experts = int(text_config.get("num_experts", config.get("num_experts", 0)))
    layers = int(text_config.get("num_hidden_layers", config.get("num_hidden_layers", 0)))
    if num_experts <= 0 or layers <= 0:
        raise ValueError("config must declare positive num_experts and num_hidden_layers")

    index = json.loads((checkpoint / "model.safetensors.index.json").read_text(encoding="utf-8"))
    records = _tensor_records(checkpoint, index)
    routed = [record for record in records if ".mlp.experts." in record["name"]]
    routers = [
        record
        for record in records
        if record["name"].endswith(".mlp.gate.weight")
    ]
    bad_routed = [record for record in routed if not record["shape"] or record["shape"][0] != num_experts]
    bad_routers = [record for record in routers if not record["shape"] or record["shape"][0] != num_experts]
    if bad_routed or bad_routers:
        raise ValueError("routed tensors and router tensors must have num_experts as their first dimension")
    moe_blocks = len(routers)
    if len(routed) != moe_blocks * 2:
        raise ValueError(f"expected two routed expert tensors per MoE block, found {len(routed)} for {moe_blocks} blocks")

    total_elements = sum(record["elements"] for record in records)
    total_bytes = sum(record["bytes"] for record in records)
    routed_elements = sum(record["elements"] for record in routed)
    routed_bytes = sum(record["bytes"] for record in routed)
    router_elements = sum(record["elements"] for record in routers)
    router_bytes = sum(record["bytes"] for record in routers)
    dtype_counts = Counter(record["dtype"] for record in records)
    index_total = int(index.get("metadata", {}).get("total_size", 0))

    return {
        "schema": "wrench.qwen-pruned-size-estimate.v1",
        "checkpoint_path": str(checkpoint),
        "evidence_scope": "safetensors_headers_only_no_tensor_payload_loaded",
        "architecture": {
            "num_hidden_layers": layers,
            "moe_block_count_from_headers": moe_blocks,
            "num_experts": num_experts,
            "num_experts_per_tok": text_config.get("num_experts_per_tok", config.get("num_experts_per_tok")),
        },
        "tensor_inventory": {
            "mapped_tensor_count": len(records),
            "dtype_counts": dict(sorted(dtype_counts.items())),
            "tensor_elements": total_elements,
            "tensor_data_bytes": total_bytes,
            "official_index_total_bytes": index_total,
            "index_total_matches_header_sum": total_bytes == index_total,
        },
        "prunable_groups": {
            "routed_expert_tensor_count": len(routed),
            "routed_expert_elements": routed_elements,
            "routed_expert_bytes": routed_bytes,
            "routed_expert_elements_per_expert": routed_elements // num_experts,
            "router_tensor_count": len(routers),
            "router_elements": router_elements,
            "router_bytes": router_bytes,
            "router_elements_per_expert_row": router_elements // num_experts,
            "combined_prunable_elements": routed_elements + router_elements,
            "combined_prunable_bytes": routed_bytes + router_bytes,
        },
        "scenarios": [_scenario(keep, num_experts, total_elements, total_bytes, routed_elements, routed_bytes, router_elements, router_bytes) for keep in keeps],
        "limitations": [
            "This is a structural size estimate, not a pruning operation.",
            "It excludes quantization scales, metadata, alignment, and runtime overhead from ideal int4 bytes.",
            "It does not select experts, measure routing, prove loadability, or establish task quality.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keep", type=int, nargs="+", default=[8, 16, 32, 64])
    args = parser.parse_args()
    report = analyze_checkpoint(args.checkpoint.resolve(), args.keep)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.output), "scenarios": len(report["scenarios"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
