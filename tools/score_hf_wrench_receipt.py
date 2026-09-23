#!/usr/bin/env python3
"""Strictly score a saved HF generation receipt against a Wrench case JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json_loads(value: str) -> Any:
    return json.loads(
        value,
        object_pairs_hook=_unique_object,
        parse_constant=lambda constant: (_ for _ in ()).throw(ValueError(constant)),
    )


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def score_result(
    row: dict[str, Any], model_output: str, verified_status: str | None,
    fallback_reason: str | None,
) -> dict[str, Any]:
    expected_status = row.get("expected_status")
    expected_reason = row.get("expected_fallback_reason")
    target = row.get("target")
    exact_target = False
    if isinstance(target, str):
        try:
            exact_target = _canonical(_strict_json_loads(model_output)) == _canonical(_strict_json_loads(target))
        except (json.JSONDecodeError, TypeError, ValueError):
            exact_target = False
    try:
        _strict_json_loads(model_output)
        model_json_valid = True
    except (json.JSONDecodeError, TypeError, ValueError):
        model_json_valid = False

    if expected_status == "abstain":
        reason_match = isinstance(expected_reason, str) and fallback_reason == expected_reason
    else:
        reason_match = expected_status == "accepted"
    outcome_match = (
        verified_status == expected_status
        and (expected_status != "accepted" or exact_target)
        and reason_match
    )
    return {
        "expected_status": expected_status,
        "expected_fallback_reason": expected_reason,
        "verified_status": verified_status,
        "fallback_reason": fallback_reason,
        "fallback_reason_match": reason_match,
        "exact_target_match": exact_target,
        "model_json_valid": model_json_valid,
        "outcome_match": outcome_match,
    }


def _index_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"{label} row is missing a nonempty id")
        if identifier in result:
            raise ValueError(f"{label} contains duplicate id {identifier!r}")
        result[identifier] = row
    return result


def rescore(cases_path: Path, receipt_path: Path) -> dict[str, Any]:
    cases_bytes = cases_path.read_bytes()
    receipt_bytes = receipt_path.read_bytes()
    cases = [
        _strict_json_loads(line)
        for line in cases_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    source_results = receipt.get("results")
    if not isinstance(source_results, list):
        raise ValueError("receipt.results must be a list")
    case_map = _index_by_id(cases, "case file")
    result_map = _index_by_id(source_results, "receipt")
    missing = sorted(case_map.keys() - result_map.keys())
    extra = sorted(result_map.keys() - case_map.keys())
    if missing or extra:
        raise ValueError(f"case/receipt id mismatch: missing={missing}, extra={extra}")

    results: list[dict[str, Any]] = []
    for row in cases:
        prior = result_map[row["id"]]
        output = prior.get("model_output")
        if not isinstance(output, str):
            raise ValueError(f"receipt row {row['id']!r} has no model_output string")
        results.append({
            "id": row["id"],
            "family": row.get("family"),
            **score_result(row, output, prior.get("verified_status"), prior.get("fallback_reason")),
            "latency_ms": prior.get("latency_ms"),
            "prompt_tokens": prior.get("prompt_tokens"),
        })

    eligible = [item for item in results if item["expected_status"] == "accepted"]
    abstain = [item for item in results if item["expected_status"] == "abstain"]
    family_results: dict[str, dict[str, int]] = {}
    for item in results:
        family = item["family"] or "unknown"
        bucket = family_results.setdefault(family, {"case_count": 0, "outcome_matches": 0})
        bucket["case_count"] += 1
        bucket["outcome_matches"] += int(item["outcome_match"])
    matched = sum(item["outcome_match"] for item in results)
    return {
        "schema": "wrench.hf-generation-receipt-rescore.v1",
        "status": "PASS_STRICT_DEVELOPMENT_DIAGNOSTIC" if matched == len(results) else "DEVELOPMENT_GAPS",
        "model": receipt.get("model"),
        "device": receipt.get("device"),
        "case_count": len(results),
        "eligible_case_count": len(eligible),
        "eligible_exact_accepts": sum(item["outcome_match"] for item in eligible),
        "expected_abstain_count": len(abstain),
        "exact_abstention_matches": sum(item["outcome_match"] for item in abstain),
        "abstention_reason_matches": sum(item["fallback_reason_match"] for item in abstain),
        "abstentions_with_expected_reason": sum(isinstance(item["expected_fallback_reason"], str) for item in abstain),
        "prohibited_accepts": sum(
            item["expected_status"] == "abstain" and item["verified_status"] == "accepted"
            for item in results
        ),
        "invalid_json_outputs": sum(not item["model_json_valid"] for item in results),
        "exact_target_matches": sum(item["exact_target_match"] for item in results),
        "outcome_matches": matched,
        "original_reported_outcome_matches": receipt.get("outcome_matches"),
        "reported_median_latency_ms": receipt.get("median_latency_ms"),
        "reported_p95_latency_ms": receipt.get("p95_latency_ms"),
        "case_file_sha256": hashlib.sha256(cases_bytes).hexdigest().upper(),
        "source_receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest().upper(),
        "quality_claim": False,
        "scoring_note": "Uses verifier status and fallback reason saved in the source receipt; it does not rerun the model or verifier.",
        "family_results": family_results,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = rescore(args.cases, args.receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    keys = (
        "status", "case_count", "eligible_exact_accepts", "exact_abstention_matches",
        "prohibited_accepts", "invalid_json_outputs", "outcome_matches",
        "original_reported_outcome_matches",
    )
    print(json.dumps({key: result[key] for key in keys}, indent=2))
    return 0 if result["status"] == "PASS_STRICT_DEVELOPMENT_DIAGNOSTIC" else 1


if __name__ == "__main__":
    raise SystemExit(main())
