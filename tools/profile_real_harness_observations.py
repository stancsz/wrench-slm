#!/usr/bin/env python3
"""Profile metadata-only real harness observations without copying prompts.

The resulting receipt is an inventory input for human portfolio review. It is
not a training set, final evaluation set, or quality claim.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


MUTATION_SURFACE = {
    "bash",
    "pwsh",
    "write",
    "edit",
    "str_replace_editor",
    "patch",
    "delete",
    "rm",
    "shell",
}
READ_SURFACE = {"read", "Read", "glob", "grep", "Grep", "search", "literal_search"}


def _rows(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"observation at {path}:{line_number} is not an object")
            yield row


def _profile(path: Path) -> dict[str, Any]:
    protocol = collections.Counter()
    status = collections.Counter()
    backend = collections.Counter()
    fallback = collections.Counter()
    tools = collections.Counter()
    route_sources = collections.Counter()
    raw_tokens = []
    payload_hashes: set[str] = set()
    rows = 0
    model_calls = 0
    mechanical_rows = 0
    read_surface_rows = 0
    mutation_surface_rows = 0
    for row in _rows(path):
        rows += 1
        protocol[str(row.get("protocol", "unknown"))] += 1
        status[str(row.get("status", "unknown"))] += 1
        backend[str(row.get("backend", "unknown"))] += 1
        fallback_reason = row.get("fallback_reason")
        if fallback_reason:
            fallback[str(fallback_reason)] += 1
        route = row.get("context_gate")
        if isinstance(route, dict) and route.get("route_source"):
            route_sources[str(route["route_source"])] += 1
        names = row.get("tool_names")
        normalized_names = {
            str(name)
            for name in names
            if isinstance(names, list) and isinstance(name, str)
        }
        tools.update(normalized_names)
        read_surface_rows += bool(normalized_names & READ_SURFACE)
        mutation_surface_rows += bool(normalized_names & MUTATION_SURFACE)
        if row.get("mechanical_fast_path") is True:
            mechanical_rows += 1
        try:
            token_count = int(row.get("raw_input_tokens_estimate", 0))
        except (TypeError, ValueError):
            token_count = 0
        raw_tokens.append(max(0, token_count))
        digest = row.get("raw_payload_sha256")
        if isinstance(digest, str) and digest:
            payload_hashes.add(digest)
        try:
            model_calls += max(0, int(row.get("model_calls", 0)))
        except (TypeError, ValueError):
            pass
    return {
        "rows": rows,
        "protocols": dict(protocol),
        "statuses": dict(status),
        "backends": dict(backend),
        "fallback_reasons": dict(fallback),
        "route_sources": dict(route_sources),
        "top_tool_names": tools.most_common(30),
        "read_surface_rows": read_surface_rows,
        "mutation_surface_rows": mutation_surface_rows,
        "mechanical_fast_path_rows": mechanical_rows,
        "model_calls": model_calls,
        "raw_input_tokens": {
            "sum": sum(raw_tokens),
            "max": max(raw_tokens, default=0),
            "nonzero_rows": sum(value > 0 for value in raw_tokens),
        },
        "unique_payload_hashes": len(payload_hashes),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    sources = [path.resolve() for path in args.source]
    profiles = {str(path): _profile(path) for path in sources}
    combined = {
        "rows": sum(item["rows"] for item in profiles.values()),
        "raw_input_tokens": sum(item["raw_input_tokens"]["sum"] for item in profiles.values()),
        "model_calls": sum(item["model_calls"] for item in profiles.values()),
        "mechanical_fast_path_rows": sum(item["mechanical_fast_path_rows"] for item in profiles.values()),
        "read_surface_rows": sum(item["read_surface_rows"] for item in profiles.values()),
        "mutation_surface_rows": sum(item["mutation_surface_rows"] for item in profiles.values()),
    }
    manifest = json.dumps(profiles, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt: dict[str, Any] = {
        "schema": "wrench.real-harness-metadata-inventory.v1",
        "status": "DRAFT_INVENTORY_FOR_HUMAN_PORTFOLIO_REVIEW",
        "quality_claim": False,
        "training_use": False,
        "final_evaluation_use": False,
        "sources": profiles,
        "combined": combined,
        "inventory_sha256": hashlib.sha256(manifest).hexdigest(),
        "classification_policy": {
            "read_surface": sorted(READ_SURFACE),
            "mutation_surface": sorted(MUTATION_SURFACE),
            "note": "tool names describe client context; they do not prove that Wrench accepted or executed a mutation",
        },
        "required_review": [
            "redact or exclude user-sensitive traces before any human approval",
            "assign stable task-family labels and workload weights",
            "separate calibration/development/final families without leakage",
            "define independent outcome oracles and prohibited-accept policy",
            "freeze the approved manifest before candidate tuning",
        ],
    }
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], "rows": receipt["combined"]["rows"], "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
