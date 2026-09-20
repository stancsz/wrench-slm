#!/usr/bin/env python3
"""Derive a safety-filtered calibration set from a teacher trace capture.

Teacher output is useful for style and formatting, but it is not an authority
for safety. This builder trains only on rows whose frozen development oracle
already says ``accepted``. It uses the oracle target rather than copying a
teacher proposal that may contain an unsafe path or action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {
    "read_file",
    "read_lines",
    "literal_search",
    "git_read_status",
    "health_read",
    "patch_draft",
}


def build(input_path: Path, output_path: Path) -> dict[str, Any]:
    capture = json.loads(input_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    teacher_exact_count = 0
    for item in capture.get("results", []):
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.startswith("train_"):
            rejected["not_development_train_id"] += 1
            continue
        if item.get("expected_status") != "accepted":
            rejected["oracle_not_accepted"] += 1
            continue
        if item.get("transport_failure") or item.get("response_invalid"):
            rejected["teacher_capture_invalid"] += 1
            continue
        prompt = item.get("prompt")
        system = item.get("system")
        target_text = item.get("target")
        if not isinstance(prompt, str) or not isinstance(system, str):
            rejected["missing_prompt_or_system"] += 1
            continue
        if not isinstance(target_text, str) or not target_text.strip():
            rejected["missing_oracle_target"] += 1
            continue
        try:
            target = json.loads(target_text)
        except json.JSONDecodeError:
            rejected["oracle_target_invalid_json"] += 1
            continue
        if not isinstance(target, dict) or target.get("schema") != "wrench.proposal.v1":
            rejected["oracle_target_schema_invalid"] += 1
            continue
        if target.get("action") not in ALLOWED_ACTIONS:
            rejected["oracle_target_action_not_allowlisted"] += 1
            continue
        teacher_proposal = item.get("normalized_proposal")
        teacher_exact = teacher_proposal == target
        teacher_exact_count += int(teacher_exact)
        rows.append(
            {
                "id": identifier,
                "family": item.get("family"),
                "system": system,
                "prompt": prompt,
                "target": json.dumps(target, separators=(",", ":"), ensure_ascii=False),
                "teacher_exact_oracle": teacher_exact,
                "teacher_response_model": item.get("response_model"),
                "teacher_finish_reason": item.get("finish_reason"),
            }
        )
    rows.sort(key=lambda row: str(row["id"]))
    encoded = b"".join(
        (json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        for row in rows
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encoded)
    receipt = {
        "schema": "wrench.safe-teacher-calibration.v1",
        "status": "SAFE_DEVELOPMENT_CALIBRATION_READY",
        "input_path": str(input_path.resolve()),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "output_path": str(output_path.resolve()),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_request_count": len(capture.get("results", [])),
        "valid_row_count": len(rows),
        "teacher_exact_oracle_count": teacher_exact_count,
        "family_counts": dict(Counter(str(row.get("family")) for row in rows)),
        "rejected": dict(rejected),
        "final_split_used": False,
        "boundary_rows_used_for_training": False,
        "oracle_targets_used": True,
        "quality_claim": False,
        "training_note": "Use deterministic verifier and mechanical router for boundary behavior; do not train unsafe teacher proposals.",
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args.input, args.output)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "valid_row_count", "teacher_exact_oracle_count")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
