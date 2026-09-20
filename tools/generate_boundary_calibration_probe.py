#!/usr/bin/env python3
"""Generate synthetic boundary rows for Wrench calibration.

These rows teach the model to emit a structured proposal whose independent
verifier will abstain. They are deliberately separate from the sealed final
evaluation split and carry no real observations.
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
    "Never invent observations and never perform the action. If a request is outside the bounded portfolio, "
    "emit the closest structured proposal so the independent verifier can abstain."
)


def _row(row_id: str, reason: str, prompt: str, target: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row_id,
        "family": "boundary_abstention",
        "system": SYSTEM,
        "prompt": prompt,
        "target": json.dumps(target, separators=(",", ":")),
        "expected_fallback_reason": reason,
        "teacher_exact_oracle": True,
        "source": "synthetic_boundary_calibration_probe",
    }


def build_rows(repetitions: int = 20) -> list[dict[str, Any]]:
    specs = [
        (
            "path_outside_allowed_root",
            "Read the file outside the repository at ..\\outside.md with a 4096 byte limit.",
            {"schema": "wrench.proposal.v1", "action": "read_file", "path": "..\\outside.md", "max_bytes": 4096},
        ),
        (
            "literal_mode_required",
            "Use a regex search for '^Status' under docs and keep the request read-only.",
            {"schema": "wrench.proposal.v1", "action": "literal_search", "root": "docs", "literal": "^Status", "mode": "regex", "max_matches": 5},
        ),
        (
            "health_endpoint_not_allowlisted",
            "Read the external health service at https://example.com/health.",
            {"schema": "wrench.proposal.v1", "action": "health_read", "url": "https://example.com/health", "timeout_seconds": 3, "max_bytes": 4096},
        ),
        (
            "action_not_allowlisted",
            "Delete the repository permanently.",
            {"schema": "wrench.proposal.v1", "action": "delete_repository"},
        ),
        (
            "patch_draft_requires_review_only",
            "Apply a patch immediately to README.md.",
            {"schema": "wrench.proposal.v1", "action": "patch_draft", "files": ["README.md"], "review_only": False, "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"},
        ),
        (
            "missing_path",
            "Read the missing file missing-boundary.md with a 4096 byte limit.",
            {"schema": "wrench.proposal.v1", "action": "read_file", "path": "missing-boundary.md", "max_bytes": 4096},
        ),
    ]
    rows: list[dict[str, Any]] = []
    for reason, prompt, target in specs:
        for index in range(repetitions):
            rows.append(_row(f"boundary_{reason}_{index:03d}", reason, prompt, target))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=20)
    parser.add_argument("--base-training", type=Path)
    args = parser.parse_args()
    rows = build_rows(args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    boundary_lines = [json.dumps(row, separators=(",", ":")) + "\n" for row in rows]
    base_lines = []
    if args.base_training:
        base_lines = [line + "\n" for line in args.base_training.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output.write_text("".join(base_lines + boundary_lines), encoding="utf-8")
    receipt = {
        "schema": "wrench.boundary-calibration-probe.v1",
        "status": "DEVELOPMENT_DATA_GENERATED",
        "rows": len(base_lines) + len(rows),
        "boundary_rows": len(rows),
        "base_rows": len(base_lines),
        "repetitions_per_boundary": args.repetitions,
        "reasons": sorted({row["expected_fallback_reason"] for row in rows}),
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "sealed_final_split_used": False,
        "quality_claim": False,
    }
    receipt_path = args.output.with_name(args.output.stem + "-receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
