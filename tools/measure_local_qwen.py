#!/usr/bin/env python3
"""Measure one bounded local Qwen adapter request without benchmark claims."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_local_qwen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/v1/chat/completions")
    parser.add_argument("--model", default="Qwen3.6-35B-A3B-NVFP4")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    messages = [
        {"role": "system", "content": "Output only one valid JSON object and no markdown."},
        {"role": "user", "content": "Return exactly this JSON object: {\"schema\":\"wrench.proposal.v1\",\"action\":\"read_file\",\"path\":\"phases/phase-9-execution-boundary/README.md\",\"max_bytes\":4096}"},
    ]
    started = time.perf_counter()
    result = execute_local_qwen(args.endpoint, args.model, messages, str(args.root.resolve()), max_tokens=128)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    receipt = {
        "schema": "wrench.local-qwen-performance-smoke.v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "wall_time_ms": elapsed_ms,
        "result": result,
        "scope": "one bounded request; diagnostic only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result.get("status"), "wall_time_ms": elapsed_ms, "usage": result.get("usage")}))
    return 0 if result.get("status") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
