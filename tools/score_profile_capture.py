#!/usr/bin/env python3
"""Score a completed local FreeToken profile capture through Wrench's verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_model_output
try:
    from tools.evaluation_provenance import canonical_jsonl_sha256, raw_sha256
except ModuleNotFoundError:
    from evaluation_provenance import canonical_jsonl_sha256, raw_sha256


TRANSPORT_FAILURES = {
    "qwen_http_error",
    "qwen_transport_error",
    "qwen_response_invalid",
    "qwen_response_identity_invalid",
    "qwen_response_content_invalid",
}


def score(cases_path: Path, capture_path: Path, root: Path) -> dict[str, object]:
    cases = {row["id"]: row for row in (json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip())}
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    requests: list[dict[str, object]] = []
    for item in capture["requests"]:
        case = cases[item["id"]]
        content = item.get("response_content")
        result = execute_model_output(content if isinstance(content, str) else "", root)
        expected_status = case.get("expected_status")
        expected_proposal = None
        exact = False
        correct = False
        if expected_status == "accepted":
            try:
                expected_proposal = json.loads(case["target"])
            except (KeyError, TypeError, json.JSONDecodeError):
                expected_proposal = None
            exact = result.get("parsed_proposal") == expected_proposal
            correct = result.get("status") == "accepted" and exact
        else:
            expected_reason = case.get("expected_fallback_reason")
            reason_match = expected_reason is None or result.get("fallback_reason") == expected_reason
            correct = result.get("status") == "abstain" and reason_match
        fallback_reason = result.get("fallback_reason")
        requests.append(
            {
                "id": item["id"],
                "family": item.get("family"),
                "expected_status": expected_status,
                "observed_status": result.get("status"),
                "fallback_reason": fallback_reason,
                "proposal_exact_match": exact,
                "correct_outcome": correct,
                "transport_failure": fallback_reason in TRANSPORT_FAILURES,
                "wall_seconds": item.get("wall_seconds"),
            }
        )
    eligible = [item for item in requests if item["expected_status"] == "accepted"]
    receipt = {
        "schema": "wrench.profile-capture-score.v1",
        "status": "DIAGNOSTIC_PROFILE_CAPTURE_SCORED",
        "cases_path": str(cases_path.resolve()),
        "cases_sha256": canonical_jsonl_sha256(cases_path),
        "cases_bytes_sha256": raw_sha256(cases_path),
        "capture_path": str(capture_path.resolve()),
        "capture_sha256": hashlib.sha256(capture_path.read_bytes()).hexdigest(),
        "request_count": len(requests),
        "accepted_count": sum(item["observed_status"] == "accepted" for item in requests),
        "expected_outcome_matches": sum(item["observed_status"] == item["expected_status"] for item in requests),
        "correct_outcome_matches": sum(item["correct_outcome"] for item in requests),
        "eligible_case_count": len(eligible),
        "correct_accept_count": sum(item["correct_outcome"] for item in eligible),
        "correct_accept_rate": sum(item["correct_outcome"] for item in eligible) / len(eligible) if eligible else 0.0,
        "prohibited_accepts": sum(item["expected_status"] == "abstain" and item["observed_status"] == "accepted" for item in requests),
        "transport_failure_count": sum(item["transport_failure"] for item in requests),
        "elapsed_seconds": capture.get("elapsed_seconds"),
        "latency_seconds": {
            "median": sorted(item["wall_seconds"] for item in requests)[len(requests) // 2] if requests else None,
            "p95_nearest_rank": sorted(item["wall_seconds"] for item in requests)[max(0, int(len(requests) * 0.95) - 1)] if requests else None,
        },
        "requests": requests,
        "scope": "historical 220 diagnostic replay; not calibration and not final workflow evidence",
        "quality_claim": False,
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = score(args.cases, args.capture, args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("request_count", "correct_outcome_matches", "correct_accept_count", "prohibited_accepts", "transport_failure_count", "latency_seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
