#!/usr/bin/env python3
"""Probe explicit, review-only patch routing against temporary files.

This is a mechanical-route probe, not a model-quality claim. Every request
contains the exact bounded text operation, and the temporary root is removed
after the receipt is written. The probe proves that Wrench can construct a
review-only diff without mutating the workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness import execute_model_output
from wrench_harness.mechanical import mechanical_route


def _cases() -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    specs = [
        (
            "replace",
            "Replace \"old-{i}\" with \"new-{i}\" in files/replace-{i}.txt and leave the file unchanged for review only.",
            "old-{i}\nkeep-{i}\n",
        ),
        (
            "append",
            "Append \"new-{i}\" to files/append-{i}.txt as an unapplied review-only patch.",
            "keep-{i}\n",
        ),
        (
            "prepend",
            "Prepend \"new-{i}\" to files/prepend-{i}.txt, leaving the file unchanged.",
            "keep-{i}\n",
        ),
        (
            "insert",
            "Insert \"new-{i}\" after the unique text \"anchor-{i}\" in files/insert-{i}.txt for review.",
            "before-{i}\nanchor-{i}\nafter-{i}\n",
        ),
        (
            "remove",
            "Remove \"obsolete-{i}\" from files/remove-{i}.txt and return only a review patch.",
            "keep-{i}\nobsolete-{i}\nend-{i}\n",
        ),
    ]
    for operation, prompt_template, content_template in specs:
        for index in range(4):
            cases.append(
                {
                    "id": f"explicit_patch_{operation}_{index:02d}",
                    "operation": operation,
                    "prompt": prompt_template.format(i=index),
                    "path": f"files/{operation}-{index}.txt",
                    "content": content_template.format(i=index),
                }
            )
    return cases


def run(output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="wrench-explicit-patch-") as temporary:
        root = Path(temporary)
        for case in _cases():
            path = root / case["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(case["content"], encoding="utf-8")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            route_started = time.perf_counter()
            proposal = mechanical_route(case["prompt"], allowed_root=root)
            route_ms = (time.perf_counter() - route_started) * 1000
            observed = execute_model_output(
                json.dumps(proposal, ensure_ascii=False, separators=(",", ":")),
                root,
                request_prompt=case["prompt"],
            ) if proposal is not None else {"status": "no_route"}
            after = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(
                {
                    "id": case["id"],
                    "operation": case["operation"],
                    "status": observed.get("status"),
                    "route_ms": round(route_ms, 3),
                    "model_calls": 0,
                    "workspace_unchanged": before == after,
                    "proposal": proposal,
                    "observed": observed,
                }
            )
    passed = all(
        row["status"] == "accepted"
        and row["workspace_unchanged"]
        and isinstance(row["proposal"], dict)
        and row["proposal"].get("action") == "patch_draft"
        for row in rows
    )
    receipt = {
        "schema": "wrench.explicit-patch-route-probe.v1",
        "status": "PASS_EXPLICIT_PATCH_MECHANICAL_ROUTE" if passed else "FAIL_EXPLICIT_PATCH_MECHANICAL_ROUTE",
        "case_count": len(rows),
        "accepted_count": sum(row["status"] == "accepted" for row in rows),
        "workspace_unchanged_count": sum(row["workspace_unchanged"] for row in rows),
        "model_calls": 0,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "operations": sorted({row["operation"] for row in rows}),
        "quality_claim": False,
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.output)
    print(json.dumps({key: receipt[key] for key in ("status", "case_count", "accepted_count", "workspace_unchanged_count", "elapsed_ms")}))
    return 0 if receipt["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
