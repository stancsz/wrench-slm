"""Verify that the trusted-data prerequisite is satisfied before M3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(receipt_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    declared_reasons = receipt.get("readiness_reasons", [])
    reasons = list(declared_reasons) if isinstance(declared_reasons, list) and all(isinstance(item, str) for item in declared_reasons) else ["INVALID_READINESS_REASONS"]
    required = ("source", "source_event_records", "profile_events", "replay_capabilities", "usage_coverage", "cost_status", "duration_unit_status")
    reasons.extend(f"MISSING_{key.upper()}" for key in required if key not in receipt)
    if not isinstance(receipt.get("source_event_records"), int) or not isinstance(receipt.get("profile_events"), int):
        reasons.append("INVALID_EVENT_COUNTS")
    elif receipt["source_event_records"] < 0 or receipt["profile_events"] < 0:
        reasons.append("INVALID_EVENT_COUNTS")
    elif receipt["source_event_records"] != receipt["profile_events"]:
        reasons.append("EVENT_COUNT_MISMATCH")
    if receipt.get("event_count_match") is not True:
        reasons.append("EVENT_COUNT_MATCH_FLAG_FALSE")
    if not isinstance(receipt.get("replay_capabilities"), dict):
        reasons.append("INVALID_REPLAY_CAPABILITIES")
    coverage = receipt.get("usage_coverage")
    if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 1:
        reasons.append("INVALID_USAGE_COVERAGE")
    if receipt.get("cost_status") not in {"CALCULATED", "PRICE_LEDGER_REQUIRED"}:
        reasons.append("INVALID_COST_STATUS")
    if receipt.get("duration_unit_status") not in {"UNVERIFIED", "UNVERIFIED_SECONDS", "MIXED_OR_OUTLIER"}:
        reasons.append("INVALID_DURATION_STATUS")
    if receipt.get("schema") != "production-readiness-receipt-v1":
        reasons.append("INVALID_RECEIPT_SCHEMA")
    if receipt.get("read_only") is not True:
        reasons.append("NOT_READ_ONLY")
    if receipt.get("raw_content_written") is not False:
        reasons.append("RAW_CONTENT_OUTPUT_FLAGGED")
    if receipt.get("event_count_match") is not True:
        reasons.append("EVENT_COUNT_MISMATCH")
    if receipt.get("replay_ready") is not True:
        reasons.append("REPLAY_NOT_READY")
    result = {
        "schema": "trusted-readiness-gate-v1",
        "status": "PASS" if not reasons else "REJECTED",
        "receipt": str(receipt_path.resolve()),
        "reasons": sorted(set(reasons)),
        "scope": "Prerequisite check only; does not authorize provider spending or prove production value.",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.receipt)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
