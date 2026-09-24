#!/usr/bin/env python3
"""Build a path-diverse router calibration set without touching held-out evals."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .generate_wrench_calibration import SYSTEM_EXPLICIT, row
except ImportError:
    from generate_wrench_calibration import SYSTEM_EXPLICIT, row


READ_PATHS = (
    "src/wrench_harness/server.py",
    "src/wrench_harness/worker.py",
    "src/wrench_harness/prefill.py",
    "src/wrench_harness/mechanical.py",
    "tests/test_wrench_server.py",
    "tests/test_embedded_worker.py",
    "tools/score_mechanical_worker.py",
    "tools/run_package_220_replay.py",
    "docs/misc/v1/WRENCH_PORTABLE_DISTRIBUTION.md",
    "docs/misc/v1/WRENCH_MECHANICAL_WORKER_EVALUATION.md",
    "AGENTS.md",
    "AGENTS.local.md",
    "phases/phase-264-current-source-4m-prefill/README.md",
    "phases/phase-270-portable-claude-launcher/README.md",
    "config/wrench-routing-policy.json",
    "pyproject.toml",
)


def _read_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"calibration input is empty: {path}")
    if any(row.get("split") != "calibration" for row in rows):
        raise ValueError("input contains a non-calibration split")
    return rows


def _augmented_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(READ_PATHS):
        for variant, limit in enumerate((262144, 262144)):
            prompt = (
                f"Prepare a bounded read proposal for {path} with a {limit} byte ceiling."
                if variant == 0
                else f"Inspect {path} read-only and cap the response at {limit} bytes."
            )
            item = row(
                f"router_v2_read_file_{index:02d}_{variant:02d}",
                "read_file",
                prompt,
                {"action": "read_file", "path": path, "max_bytes": limit},
                "accepted",
                system=SYSTEM_EXPLICIT,
            )
            item.update({"category": "eligible", "split": "calibration", "source": "path_diversity_v2"})
            rows.append(item)
        start = 1 + (index % 7)
        end = start + 7
        item = row(
            f"router_v2_read_lines_{index:02d}",
            "read_lines",
            f"Read {path} inclusively from line {start} through {end}.",
            {"action": "read_lines", "path": path, "start": start, "end": end},
            "accepted",
            system=SYSTEM_EXPLICIT,
        )
        item.update({"category": "eligible", "split": "calibration", "source": "path_diversity_v2"})
        rows.append(item)
    return rows


def build(input_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = _read_rows(input_path)
    augmented = _augmented_rows()
    rows = base + augmented
    payload = "".join(json.dumps(item, separators=(",", ":"), ensure_ascii=False) + "\n" for item in rows)
    manifest = {
        "schema": "wrench.router-calibration-v2.v1",
        "status": "EXPERIMENTAL_TRAINING_INPUT",
        "input_path": str(input_path.resolve()),
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "base_row_count": len(base),
        "augmented_row_count": len(augmented),
        "augmented_path_count": len(READ_PATHS),
        "split_policy": "calibration_only; development and final are never read",
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "quality_claim": False,
    }
    return rows, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    rows, manifest = build(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        "".join(json.dumps(item, separators=(",", ":"), ensure_ascii=False) + "\n" for item in rows).encode("utf-8")
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
