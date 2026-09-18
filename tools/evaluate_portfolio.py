#!/usr/bin/env python3
"""Run a deterministic, non-model boundary evaluation from a case manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_proposal


def evaluate(cases: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    results = []
    for case in cases:
        observed = execute_proposal(case["proposal"], root)
        expected_status = case["expected_status"]
        expected_reason = case.get("expected_fallback_reason")
        status_match = observed.get("status") == expected_status
        reason_match = expected_reason is None or observed.get("fallback_reason") == expected_reason
        results.append(
            {
                "id": case["id"],
                "family": case["family"],
                "expected_status": expected_status,
                "observed_status": observed.get("status"),
                "expected_fallback_reason": expected_reason,
                "observed_fallback_reason": observed.get("fallback_reason"),
                "pass": status_match and reason_match,
            }
        )
    passed = sum(1 for result in results if result["pass"])
    prohibited_accepts = sum(
        1
        for case, result in zip(cases, results)
        if case["expected_status"] == "abstain" and result["observed_status"] == "accepted"
    )
    return {
        "schema": "wrench.portfolio-boundary-evaluation.v1",
        "evaluation_scope": "deterministic verifier cases; no model generation",
        "case_count": len(results),
        "passed_cases": passed,
        "failed_cases": len(results) - passed,
        "prohibited_accepts": prohibited_accepts,
        "status": "PASS_BOUNDARY_ONLY" if passed == len(results) and prohibited_accepts == 0 else "FAIL",
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.cases.read_text(encoding="utf-8"))
    receipt = evaluate(manifest["cases"], args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "case_count", "passed_cases", "prohibited_accepts")}))
    return 0 if receipt["status"] == "PASS_BOUNDARY_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
