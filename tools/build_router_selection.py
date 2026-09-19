#!/usr/bin/env python3
"""Derive a reproducible per-layer expert selection from router telemetry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_selection(profile_path: Path, output_path: Path, keep: int, target_top_k: int | None = None) -> dict[str, Any]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("status") != "PASS_ROUTER_ACTIVATION_PROFILE":
        raise ValueError(f"router profile is not a pass receipt: {profile.get('status')!r}")
    if keep <= 0:
        raise ValueError("keep must be positive")

    routes: dict[str, list[int]] = {}
    aggregate: list[int] | None = None
    expert_count: int | None = None
    top_k: int | None = None
    for route_key, stats in sorted(profile.get("layers", {}).items()):
        counts = [int(value) for value in stats["expert_activation_counts"]]
        width = int(stats["expert_count"])
        if width != len(counts):
            raise ValueError(f"route {route_key} count width mismatch")
        if expert_count is None:
            expert_count = width
        elif expert_count != width:
            raise ValueError("router profile mixes expert widths")
        route_top_k = int(stats["top_k"])
        if top_k is None:
            top_k = route_top_k
        elif top_k != route_top_k:
            raise ValueError("router profile mixes top-k values")
        if target_top_k is None and keep < route_top_k:
            raise ValueError(f"keep={keep} is below the teacher top-k={route_top_k}")
        ranked = sorted(range(width), key=lambda expert: (-counts[expert], expert))
        routes[route_key] = ranked[:keep]
        if aggregate is None:
            aggregate = [0] * width
        aggregate = [left + right for left, right in zip(aggregate, counts)]

    if not routes or expert_count is None or top_k is None or aggregate is None:
        raise ValueError("router profile has no layer telemetry")
    default_indices = sorted(range(expert_count), key=lambda expert: (-aggregate[expert], expert))[:keep]
    effective_top_k = route_top_k if target_top_k is None else target_top_k
    if effective_top_k <= 0 or effective_top_k > keep:
        raise ValueError("target_top_k must be positive and no greater than keep")
    receipt = {
        "schema": "wrench.qwen-router-selection.v1",
        "status": "PASS_ROUTER_SELECTION_DERIVED",
        "profile": str(profile_path.resolve()),
        "profile_status": profile["status"],
        "selection_rule": "per-route descending top-k activation count, ties by lower source expert id",
        "source_num_experts": expert_count,
        "num_experts_per_tok": top_k,
        "target_num_experts_per_tok": effective_top_k,
        "retained_num_experts": keep,
        "route_count": len(routes),
        "routes": routes,
        "unprofiled_route_rule": "aggregate profile ranking",
        "default_indices": default_indices,
        "quality_claim": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--keep", type=int, required=True)
    parser.add_argument("--target-top-k", type=int)
    args = parser.parse_args()
    receipt = build_selection(args.profile.resolve(), args.output.resolve(), args.keep, args.target_top_k)
    print(json.dumps({"status": receipt["status"], "routes": receipt["route_count"], "keep": receipt["retained_num_experts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
