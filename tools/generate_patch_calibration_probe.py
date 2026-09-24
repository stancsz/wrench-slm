#!/usr/bin/env python3
"""Generate a held-out, explicit text-patch calibration probe.

The historical calibration generator taught under-specified patch requests and
paired them with invented ``old``/``new`` diffs.  This probe keeps the target
contract bounded while making the requested operation, file, and text values
explicit.  It is development data only and never reads the sealed evaluation
split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SYSTEM = (
    "You are Wrench, a narrow developer-tool proposal generator. Output exactly one valid JSON object "
    "and nothing else: no markdown, no code fence, no prose. Use schema wrench.proposal.v1. "
    "Allowed actions are read_file, read_lines, literal_search, git_read_status, health_read, and patch_draft. "
    "Never invent observations and never perform the action. For patch_draft, return files as a list, "
    "review_only=true, and a complete unified diff with --- and +++ markers and an @@ hunk. "
    "If the request is outside the bounded portfolio or asks for mutation, emit the closest structured proposal "
    "so the independent verifier can abstain."
)


def _target(path: str, diff: str) -> str:
    return json.dumps(
        {
            "schema": "wrench.proposal.v1",
            "action": "patch_draft",
            "files": [path],
            "review_only": True,
            "diff": diff,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _diff(path: str, old: str, new: str, operation: str) -> str:
    if operation == "append":
        return f"--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,2 @@\n{old}\n+{new}\n"
    if operation == "prepend":
        return f"--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,2 @@\n+{new}\n {old}\n"
    if operation == "insert":
        return f"--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,2 @@\n {old}\n+{new}\n"
    if operation == "remove":
        return f"--- a/{path}\n+++ b/{path}\n@@ -1,2 +1,1 @@\n {old}\n-{new}\n"
    return f"--- a/{path}\n+++ b/{path}\n@@ -1,1 +1,1 @@\n-{old}\n+{new}\n"


def _row(row_id: str, prompt: str, path: str, operation: str, old: str, new: str) -> dict[str, Any]:
    return {
        "id": row_id,
        "family": "patch_draft",
        "system": SYSTEM,
        "prompt": prompt,
        "target": _target(path, _diff(path, old, new, operation)),
        "teacher_exact_oracle": True,
        "source": "explicit_patch_calibration_probe",
    }


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_specs = [
        ("replace", "README.md", "status-{i}", "status-{i}-verified", "Replace \"status-{i}\" with \"status-{i}-verified\" in README.md and draft it for review only."),
        ("append", "GOAL.md", "goal-marker-{i}", "goal-marker-{i}-append", "Append the line \"goal-marker-{i}-append\" to GOAL.md as an unapplied review-only patch."),
        ("prepend", "docs/misc/v1/PROJECT_PLAN.md", "plan-marker-{i}", "plan-marker-{i}-header", "Prepend the line \"plan-marker-{i}-header\" to docs/misc/v1/PROJECT_PLAN.md, leaving the file unchanged."),
        ("insert", "docs/misc/v1/WRENCH_PORTABLE_DISTRIBUTION.md", "anchor-{i}", "inserted-{i}", "Insert \"inserted-{i}\" after the unique text \"anchor-{i}\" in docs/misc/v1/WRENCH_PORTABLE_DISTRIBUTION.md for review."),
        ("remove", "docs/misc/v1/WRENCH_MODEL_TIERS.md", "deprecated-{i}", "deprecated-{i}", "Remove the unique text \"deprecated-{i}\" from docs/misc/v1/WRENCH_MODEL_TIERS.md and return only a review patch."),
    ]
    holdout_specs = [
        ("replace", "GOAL.md", "intent-{i}", "intent-{i}-current", "For review only, replace \"intent-{i}\" with \"intent-{i}-current\" in GOAL.md."),
        ("append", "README.md", "append-old-{i}", "append-new-{i}", "Draft an unapplied append of \"append-new-{i}\" to README.md."),
        ("prepend", "docs/misc/v1/WRENCH_MODEL_TIERS.md", "tier-old-{i}", "tier-new-{i}", "Add \"tier-new-{i}\" before the first line of docs/misc/v1/WRENCH_MODEL_TIERS.md without applying it."),
        ("insert", "docs/misc/v1/PROJECT_PLAN.md", "section-{i}", "detail-{i}", "Draft a change inserting \"detail-{i}\" immediately after \"section-{i}\" in docs/misc/v1/PROJECT_PLAN.md."),
        ("remove", "README.md", "obsolete-{i}", "obsolete-{i}", "Prepare a review-only removal of unique text \"obsolete-{i}\" from README.md."),
    ]
    train: list[dict[str, Any]] = []
    holdout: list[dict[str, Any]] = []
    for op, path, old_template, new_template, prompt_template in train_specs:
        for index in range(32):
            old = old_template.format(i=index)
            new = new_template.format(i=index)
            train.append(_row(f"train_explicit_patch_{op}_{index:03d}", prompt_template.format(i=index), path, op, old, new))
    for op, path, old_template, new_template, prompt_template in holdout_specs:
        for index in range(8):
            old = old_template.format(i=index)
            new = new_template.format(i=index)
            holdout.append(_row(f"holdout_explicit_patch_{op}_{index:03d}", prompt_template.format(i=index), path, op, old, new))
    return train, holdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--base-training",
        type=Path,
        help="optional existing development JSONL to prepend to the explicit patch rows",
    )
    args = parser.parse_args()
    train, holdout = build_rows()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / "train-explicit-patch.jsonl"
    holdout_path = args.output_dir / "holdout-explicit-patch.jsonl"
    train_lines = [json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in train]
    combined_path = train_path
    base_lines: list[str] = []
    if args.base_training:
        base_lines = [line if line.endswith("\n") else line + "\n" for line in args.base_training.read_text(encoding="utf-8").splitlines() if line.strip()]
        combined_path = args.output_dir / "train-safe-plus-explicit-patch.jsonl"
        combined_path.write_text("".join(base_lines + train_lines), encoding="utf-8")
    else:
        train_path.write_text("".join(train_lines), encoding="utf-8")
    holdout_path.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in holdout), encoding="utf-8")
    receipt = {
        "schema": "wrench.explicit-patch-calibration-probe.v1",
        "status": "DEVELOPMENT_DATA_GENERATED",
        "holdout_rows": len(holdout),
        "operations": ["replace", "append", "prepend", "insert", "remove"],
        "train_path": str(combined_path),
        "train_rows": len(train) + (len(base_lines) if args.base_training else 0),
        "train_sha256": hashlib.sha256(combined_path.read_bytes()).hexdigest(),
        "holdout_sha256": hashlib.sha256(holdout_path.read_bytes()).hexdigest(),
        "sealed_final_split_used": False,
        "quality_claim": False,
    }
    (args.output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
