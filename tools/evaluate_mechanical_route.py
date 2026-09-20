#!/usr/bin/env python3
"""Replay the deterministic Wrench route without starting a model server."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness.mechanical import mechanical_route


def _exact(result: dict[str, Any], target: str) -> bool:
    if result.get("status") != "accepted":
        return False
    try:
        proposal = json.loads(target)
    except (TypeError, json.JSONDecodeError):
        return False
    return result.get("action") == proposal.get("action") and result.get("observation") is not None


def replay(cases: Path, root: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    results: list[dict[str, Any]] = []
    started = time.perf_counter()
    for row in rows:
        prompt = row.get("prompt", "")
        candidate = mechanical_route(prompt, allowed_root=root)
        if candidate is None:
            observed = {"status": "model_fallback_required", "fallback_reason": "mechanical_route_miss"}
            fast_path = False
        elif candidate.get("status") == "abstain":
            observed = candidate
            fast_path = True
        else:
            # Do not execute filesystem search, Git, or health requests here.
            # This replay measures route coverage only. The full verifier and
            # real execution belong to the separate workflow-arm evaluation.
            observed = {"status": "accepted", "action": candidate.get("action")}
            fast_path = True
        expected_status = row.get("expected_status")
        expected_reason = row.get("expected_fallback_reason")
        outcome_match = observed.get("status") == expected_status and (
            expected_reason is None or observed.get("fallback_reason") == expected_reason
        )
        results.append(
            {
                "id": row.get("id"),
                "family": row.get("family"),
                "category": row.get("category"),
                "expected_status": expected_status,
                "observed_status": observed.get("status"),
                "observed_fallback_reason": observed.get("fallback_reason"),
                "mechanical_fast_path": fast_path,
                "outcome_match": outcome_match,
                "exact_action_and_execution": _exact(observed, row.get("target")),
                "prohibited_accept": expected_status == "abstain" and observed.get("status") == "accepted",
            }
        )
    elapsed_ms = (time.perf_counter() - started) * 1000
    family_counts: dict[str, dict[str, int]] = {}
    for family in sorted({str(row.get("family")) for row in results}):
        family_rows = [row for row in results if str(row.get("family")) == family]
        family_counts[family] = {
            "requests": len(family_rows),
            "mechanical_fast_path": sum(row["mechanical_fast_path"] for row in family_rows),
            "outcome_matches": sum(row["outcome_match"] for row in family_rows),
            "prohibited_accepts": sum(row["prohibited_accept"] for row in family_rows),
        }
    raw = cases.read_bytes()
    return {
        "schema": "wrench.mechanical-route-replay.v1",
        "status": "DIAGNOSTIC_DETERMINISTIC_ROUTE_ONLY",
        "cases_path": str(cases.resolve()),
        "cases_sha256": hashlib.sha256(raw).hexdigest(),
        "request_count": len(results),
        "mechanical_fast_path_requests": sum(row["mechanical_fast_path"] for row in results),
        "mechanical_fast_path_rate": sum(row["mechanical_fast_path"] for row in results) / len(results) if results else 0.0,
        "outcome_matches": sum(row["outcome_match"] for row in results),
        "exact_action_and_execution": sum(row["exact_action_and_execution"] for row in results),
        "prohibited_accepts": sum(row["prohibited_accept"] for row in results),
        "model_calls": sum(not row["mechanical_fast_path"] for row in results),
        "elapsed_ms": round(elapsed_ms, 3),
        "family_counts": family_counts,
        "quality_claim": False,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = replay(args.cases, args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("request_count", "mechanical_fast_path_requests", "outcome_matches", "prohibited_accepts", "elapsed_ms")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
