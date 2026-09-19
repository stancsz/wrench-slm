#!/usr/bin/env python3
"""Build development calibration rows from valid MiniMax proposal traces.

The raw teacher output remains preserved in the capture receipt. This derived
JSONL contains only structurally valid, allowlisted proposal targets and is
intended for development calibration, never for a sealed final split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ALLOWED_ACTIONS = {
    "read_file",
    "read_lines",
    "literal_search",
    "git_read_status",
    "health_read",
    "patch_draft",
}


def build(input_path: Path, output_path: Path) -> dict[str, object]:
    capture = json.loads(input_path.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    rejected: dict[str, int] = {}
    for item in capture.get("results", []):
        proposal = item.get("normalized_proposal")
        action = proposal.get("action") if isinstance(proposal, dict) else None
        if item.get("transport_failure"):
            rejected["transport_failure"] = rejected.get("transport_failure", 0) + 1
            continue
        if not isinstance(proposal, dict) or proposal.get("schema") != "wrench.proposal.v1" or action not in ALLOWED_ACTIONS:
            rejected["invalid_or_unallowlisted_proposal"] = rejected.get("invalid_or_unallowlisted_proposal", 0) + 1
            continue
        prompt = item.get("prompt")
        system = item.get("system")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.startswith("train_"):
            rejected["non_training_split_row"] = rejected.get("non_training_split_row", 0) + 1
            continue
        if not isinstance(prompt, str) or not isinstance(system, str):
            rejected["missing_prompt_or_system"] = rejected.get("missing_prompt_or_system", 0) + 1
            continue
        rows.append(
            {
                "id": identifier,
                "family": item.get("family"),
                "system": system,
                "prompt": prompt,
                "target": json.dumps(proposal, separators=(",", ":"), ensure_ascii=False),
                "teacher_response_model": item.get("response_model"),
                "teacher_finish_reason": item.get("finish_reason"),
            }
        )
    rows.sort(key=lambda row: str(row.get("id")))
    encoded = "".join(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n" for row in rows).encode("utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encoded)
    receipt = {
        "schema": "wrench.teacher-calibration.v1",
        "status": "DEVELOPMENT_TEACHER_CALIBRATION_READY",
        "input_path": str(input_path.resolve()),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "output_path": str(output_path.resolve()),
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
        "source_request_count": len(capture.get("results", [])),
        "valid_row_count": len(rows),
        "rejected": rejected,
        "sealed_final_split": False,
        "quality_claim": False,
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = build(args.input, args.output)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
