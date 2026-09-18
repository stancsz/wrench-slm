#!/usr/bin/env python3
"""Run one schema-guided Wrench request through the real local adapter."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_local_qwen


SYSTEM = (
    "You are Wrench, a narrow developer-tool proposal generator. Output exactly one valid JSON object and nothing else: "
    "no markdown, no code fence, no prose. Always include schema wrench.proposal.v1 and exactly one allowed action. "
    "Never invent observations and never perform the action. Use these field forms exactly, replacing only values: "
    "read_file={schema,action:read_file,path,max_bytes}; read_lines={schema,action:read_lines,path,start,end}; "
    "literal_search={schema,action:literal_search,root,literal,max_matches}; "
    "git_read_status={schema,action:git_read_status,repo_root}; "
    "health_read={schema,action:health_read,url,timeout_seconds,max_bytes}; "
    "patch_draft={schema,action:patch_draft,files,review_only,diff}. "
    "Use JSON strings, arrays, booleans, and numbers with no duplicated keys. "
    "If a request is outside the portfolio, still emit a wrench.proposal.v1 object with the closest intended action so the independent verifier can abstain."
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Prepare a bounded read of README.md with a 4096 byte ceiling."},
    ]
    started = time.perf_counter()
    result = execute_local_qwen(
        args.endpoint,
        args.model,
        messages,
        str(args.root.resolve()),
        max_tokens=128,
    )
    receipt = {
        "schema": "wrench.schema-guided-adapter-smoke.v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "wall_time_ms": round((time.perf_counter() - started) * 1000, 3),
        "request": {"path": "README.md", "max_bytes": 4096, "thinking_disabled": True},
        "result": result,
        "scope": "one schema-guided local adapter request; diagnostic only",
        "quality_claim": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": result.get("status"), "wall_time_ms": receipt["wall_time_ms"], "usage": result.get("usage")}))
    return 0 if result.get("status") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
