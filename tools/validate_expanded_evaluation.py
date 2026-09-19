#!/usr/bin/env python3
"""Validate the expanded evaluation suite and its deterministic boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_model_output


FAMILIES = {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft", "out_of_domain"}
SPLITS = {"calibration", "development", "final"}


def validate(path: Path, root: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors: list[str] = []
    ids = [row.get("id") for row in rows]
    if len(rows) != 220:
        errors.append(f"expected 220 rows, got {len(rows)}")
    if len(set(ids)) != len(ids):
        errors.append("case IDs are not unique")
    if any(row.get("family") not in FAMILIES for row in rows):
        errors.append("unknown family present")
    if any(row.get("split") not in SPLITS for row in rows):
        errors.append("unknown split present")
    templates: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        templates[row["template_id"]].add(row["split"])
        try:
            target = json.loads(row["target"])
        except (KeyError, TypeError, json.JSONDecodeError):
            errors.append(f"invalid target for {row.get('id')}")
            continue
        if target.get("schema") != "wrench.proposal.v1":
            errors.append(f"invalid proposal schema for {row.get('id')}")
        if row.get("expected_status") == "abstain" and not row.get("expected_fallback_reason"):
            errors.append(f"boundary case lacks fallback reason: {row.get('id')}")
    reused_templates = [template for template, splits in templates.items() if len(splits) != 1]
    if reused_templates:
        errors.append(f"template groups cross splits: {reused_templates}")

    results = []
    for row in rows:
        target = json.loads(row["target"])
        if row["execution_scope"] == "proposal_only":
            results.append({"id": row["id"], "status": "skipped_live_execution"})
            continue
        observed = execute_model_output(
            json.dumps(target, separators=(",", ":")),
            root,
            request_prompt=row["prompt"],
        )
        status_ok = observed.get("status") == row["expected_status"]
        reason_ok = row.get("expected_fallback_reason") is None or observed.get("fallback_reason") == row["expected_fallback_reason"]
        if not status_ok or not reason_ok:
            errors.append(f"verifier mismatch for {row['id']}: expected {row['expected_status']}/{row.get('expected_fallback_reason')}, got {observed}")
        results.append({"id": row["id"], "status": "pass" if status_ok and reason_ok else "fail"})

    counts = {
        "case_count": len(rows),
        "eligible_case_count": sum(row["category"] == "eligible" for row in rows),
        "boundary_case_count": sum(row["category"] == "boundary" for row in rows),
        "out_of_domain_case_count": sum(row["category"] == "out_of_domain" for row in rows),
        "family_counts": dict(sorted(Counter(row["family"] for row in rows).items())),
        "split_counts": dict(sorted(Counter(row["split"] for row in rows).items())),
        "live_execution_skipped": sum(result["status"] == "skipped_live_execution" for result in results),
        "offline_execution_checked": sum(result["status"] in {"pass", "fail"} for result in results),
    }
    return {
        "schema": "wrench.expanded-evaluation-validation.v1",
        "status": "PASS_EXPANDED_EVALUATION_MANIFEST" if not errors else "FAIL_EXPANDED_EVALUATION_MANIFEST",
        "quality_claim": False,
        "counts": counts,
        "errors": errors,
        "limitations": [
            "Live health endpoints were not exercised by this offline validation.",
            "Passing this validator proves manifest integrity and verifier behavior, not model quality.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = validate(args.cases.resolve(), args.root.resolve())
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], **receipt["counts"], "errors": len(receipt["errors"])}, indent=2))
    return 0 if receipt["status"] == "PASS_EXPANDED_EVALUATION_MANIFEST" else 1


if __name__ == "__main__":
    raise SystemExit(main())
