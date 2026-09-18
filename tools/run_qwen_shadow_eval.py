#!/usr/bin/env python3
"""Run a small real-Qwen proposal shadow evaluation through the adapter."""

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
    parser.add_argument("cases", type=Path)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/v1/chat/completions")
    parser.add_argument("--model", default="Qwen3.6-35B-A3B-NVFP4")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.cases.read_text(encoding="utf-8"))
    cases = [case for case in manifest["cases"] if case["expected_status"] == "accepted"]
    results = []
    for case in cases:
        expected = json.dumps(case["proposal"], separators=(",", ":"))
        messages = [
            {"role": "system", "content": "Output only one valid JSON object and no markdown."},
            {"role": "user", "content": f"Return exactly this proposal JSON for case {case['id']}: {expected}"},
        ]
        started = time.perf_counter()
        result = execute_local_qwen(args.endpoint, args.model, messages, str(args.root.resolve()), max_tokens=128)
        wall_ms = round((time.perf_counter() - started) * 1000, 3)
        results.append(
            {
                "id": case["id"],
                "family": case["family"],
                "status": result.get("status"),
                "fallback_reason": result.get("fallback_reason"),
                "model": result.get("model"),
                "usage": result.get("usage"),
                "wall_time_ms": wall_ms,
            }
        )
    passed = sum(1 for result in results if result["status"] == "accepted")
    receipt = {
        "schema": "wrench.qwen-shadow-portfolio-eval.v1",
        "status": "PASS_SHADOW_ONLY" if passed == len(results) else "OBSERVED_ABSTENTIONS",
        "case_count": len(results),
        "accepted": passed,
        "results": results,
        "scope": "real local Qwen shadow proposals; not approved final evaluation",
        "quality_claim": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "case_count": len(results), "accepted": passed}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
