#!/usr/bin/env python3
"""Score a provisional tier receipt through the independent Wrench verifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_model_output


def score(receipt_path: Path, cases_path: Path, root: Path, output: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    cases = {row["id"]: row for row in (json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip())}
    results = []
    for observed in receipt.get("requests", []):
        case = cases.get(observed["id"])
        if case is None:
            continue
        parsed = execute_model_output(observed.get("response_content", ""), str(root.resolve()))
        expected_status = case["expected_status"]
        expected_reason = case.get("expected_fallback_reason")
        status_match = parsed.get("status") == expected_status
        reason_match = expected_reason is None or parsed.get("fallback_reason") == expected_reason
        results.append(
            {
                "id": observed["id"],
                "family": case["family"],
                "expected_status": expected_status,
                "expected_fallback_reason": expected_reason,
                "observed_status": parsed.get("status"),
                "observed_fallback_reason": parsed.get("fallback_reason"),
                "status_match": status_match,
                "reason_match": reason_match,
                "usage": observed.get("usage"),
                "wall_seconds": observed.get("wall_seconds"),
            }
        )
    exact = sum(item["status_match"] and item["reason_match"] for item in results)
    result = {
        "schema": "wrench.provisional-tier-development-score.v1",
        "status": "PASS_PROVISIONAL_VERIFIER_SCORE" if exact == len(results) else "OBSERVED_PROVISIONAL_MISMATCHES",
        "receipt": str(receipt_path.resolve()),
        "cases": str(cases_path.resolve()),
        "case_count": len(results),
        "exact_matches": exact,
        "results": results,
        "scope": "development-only synthetic templates; portfolio pending human approval; not final quality evidence",
        "quality_claim": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = score(args.receipt.resolve(), args.cases.resolve(), args.root.resolve(), args.output.resolve())
    print(json.dumps({"status": result["status"], "case_count": result["case_count"], "exact_matches": result["exact_matches"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
