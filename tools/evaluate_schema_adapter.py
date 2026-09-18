#!/usr/bin/env python3
"""Evaluate one schema-guided local model through the strict Wrench adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_local_qwen


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.calibration.read_text(encoding="utf-8").splitlines() if line.strip()]
    started = time.perf_counter()
    requests = []
    for row in rows:
        request_started = time.perf_counter()
        result = execute_local_qwen(
            args.endpoint,
            args.model,
            [
                {"role": "system", "content": row["system"]},
                {"role": "user", "content": row["prompt"]},
            ],
            str(args.root.resolve()),
            max_tokens=128,
        )
        requests.append(
            {
                "id": row["id"],
                "family": row["family"],
                "prompt": row["prompt"],
                "expected_status": row.get("expected_status"),
                "status": result.get("status"),
                "result": result,
                "wall_time_ms": round((time.perf_counter() - request_started) * 1000, 3),
            }
        )
    accepted = sum(item["status"] == "accepted" for item in requests)
    expected_matches = sum(item["status"] == item["expected_status"] for item in requests)
    prohibited_accepts = sum(
        item["expected_status"] == "abstain" and item["status"] == "accepted" for item in requests
    )
    receipt = {
        "schema": "wrench.schema-guided-adapter-evaluation.v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "calibration_path": str(args.calibration.resolve()),
        "calibration_sha256": sha256(args.calibration),
        "request_count": len(requests),
        "accepted_count": accepted,
        "accepted_rate": accepted / len(requests) if requests else 0.0,
        "expected_outcome_matches": expected_matches,
        "prohibited_accepts": prohibited_accepts,
        "requests": requests,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "scope": "unseen schema-guided adapter evaluation; diagnostic only",
        "quality_claim": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"requests": len(requests), "accepted": accepted, "accepted_rate": receipt["accepted_rate"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
