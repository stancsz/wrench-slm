#!/usr/bin/env python3
"""Score current deterministic route coverage against frontier-token mass.

This is a diagnostic join between the current route implementation, a case
fixture, and an already captured teacher trace manifest. It does not call a
provider, execute a proposal, or claim workflow success. The teacher token
mass is only a denominator for identifying where a deterministic route could
save frontier work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness.mechanical import mechanical_route


def _read_cases(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{path}:{line_number}: case id is required")
        if identifier in rows:
            raise ValueError(f"{path}:{line_number}: duplicate case id {identifier}")
        if not isinstance(row.get("prompt"), str):
            raise ValueError(f"{path}:{line_number}: prompt is required")
        rows[identifier] = row
    if not rows:
        raise ValueError(f"{path}: no cases")
    return rows


def _number(value: Any, field: str, identifier: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{identifier}: {field} must be numeric")
    if value < 0 or (positive and value == 0):
        raise ValueError(f"{identifier}: {field} must be {'positive' if positive else 'non-negative'}")
    return float(value)


def _trace_rows(manifest: dict[str, Any], cases: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    traces = manifest.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ValueError("trace manifest must contain traces")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for trace in traces:
        if not isinstance(trace, dict) or not isinstance(trace.get("id"), str):
            raise ValueError("each trace needs a string id")
        identifier = trace["id"]
        if identifier in seen:
            raise ValueError(f"duplicate trace id {identifier}")
        seen.add(identifier)
        if identifier not in cases:
            raise ValueError(f"trace id {identifier} is missing from the case fixture")
        teacher = trace.get("arms", {}).get("minimax_teacher_only")
        if not isinstance(teacher, dict):
            raise ValueError(f"{identifier}: minimax_teacher_only arm is required")
        weight = _number(trace.get("workload_weight"), "workload_weight", identifier, positive=True)
        frontier_tokens = _number(teacher.get("frontier_tokens"), "frontier_tokens", identifier)
        case = cases[identifier]
        candidate = mechanical_route(case["prompt"])
        rows.append(
            {
                "id": identifier,
                "family": case.get("family", "unknown"),
                "category": case.get("category"),
                "workload_weight": weight,
                "teacher_frontier_tokens": frontier_tokens,
                "mechanical_route": candidate is not None,
                "route_kind": "mechanical" if candidate is not None else "fallback_required",
            }
        )
    return rows


def score(cases_path: Path, trace_path: Path) -> dict[str, Any]:
    cases = _read_cases(cases_path)
    trace_bytes = trace_path.read_bytes()
    manifest = json.loads(trace_bytes.decode("utf-8"))
    rows = _trace_rows(manifest, cases)
    eligible = [row for row in rows if row["category"] == "eligible"]
    if not eligible:
        raise ValueError("trace manifest has no eligible cases")

    total_mass = sum(row["workload_weight"] * row["teacher_frontier_tokens"] for row in eligible)
    covered_mass = sum(
        row["workload_weight"] * row["teacher_frontier_tokens"]
        for row in eligible
        if row["mechanical_route"]
    )
    total_weight = sum(row["workload_weight"] for row in eligible)
    covered_weight = sum(row["workload_weight"] for row in eligible if row["mechanical_route"])
    by_family: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "eligible_cases": 0,
            "mechanical_cases": 0,
            "eligible_workload_weight": 0.0,
            "mechanical_workload_weight": 0.0,
            "teacher_frontier_token_mass": 0.0,
            "mechanical_frontier_token_mass": 0.0,
        }
    )
    for row in eligible:
        family = str(row["family"])
        bucket = by_family[family]
        mass = row["workload_weight"] * row["teacher_frontier_tokens"]
        bucket["eligible_cases"] += 1
        bucket["eligible_workload_weight"] += row["workload_weight"]
        bucket["teacher_frontier_token_mass"] += mass
        if row["mechanical_route"]:
            bucket["mechanical_cases"] += 1
            bucket["mechanical_workload_weight"] += row["workload_weight"]
            bucket["mechanical_frontier_token_mass"] += mass

    for bucket in by_family.values():
        bucket["case_rate"] = bucket["mechanical_cases"] / bucket["eligible_cases"]
        bucket["frontier_mass_rate"] = (
            bucket["mechanical_frontier_token_mass"] / bucket["teacher_frontier_token_mass"]
            if bucket["teacher_frontier_token_mass"]
            else 0.0
        )

    return {
        "schema": "wrench.deterministic-route-frontier-score.v1",
        "status": "DIAGNOSTIC_WEIGHTED_ROUTE_ONLY",
        "cases_path": str(cases_path.resolve()),
        "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "trace_manifest_path": str(trace_path.resolve()),
        "trace_manifest_sha256": hashlib.sha256(trace_bytes).hexdigest(),
        "trace_count": len(rows),
        "eligible_trace_count": len(eligible),
        "mechanical_route_count_all_categories": sum(row["mechanical_route"] for row in rows),
        "mechanical_route_count_eligible": sum(row["mechanical_route"] for row in eligible),
        "eligible_case_rate": covered_weight / total_weight if total_weight else 0.0,
        "eligible_frontier_token_mass": {
            "teacher_total": total_mass,
            "mechanical_covered": covered_mass,
            "coverage_rate": covered_mass / total_mass if total_mass else 0.0,
        },
        "family_metrics": dict(sorted(by_family.items())),
        "quality_claim": False,
        "workflow_success_claim": False,
        "release_authorization": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--trace-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = score(args.cases, args.trace_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "eligible_case_rate": receipt["eligible_case_rate"],
        "eligible_frontier_mass_rate": receipt["eligible_frontier_token_mass"]["coverage_rate"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
