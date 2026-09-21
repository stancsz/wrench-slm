#!/usr/bin/env python3
"""Probe bundled Wrench retrieval from large reference-only payloads.

This is a deterministic package-local diagnostic. It does not load model
weights and does not claim dense-native attention quality. Each case places a
unique lookup needle at a different offset in a 2M or 4M raw payload, then
asks the embedded route to recover the path and byte limit from the old
reference while keeping the newest intent in the suffix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


FILLER = "stale historical lookup telemetry unrelated reference-only record; "


def _token_estimate(value: str) -> int:
    return max(1, value.count(" ") + value.count("\n") + 1)


def _payload(target_tokens: int, placement: float, case_index: int) -> tuple[list[dict[str, str]], str, str]:
    needle = f"wrench_retrieval_needle_{target_tokens}_{case_index}"
    anchor = (
        f"REFERENCE_ONLY needle={needle} path=src/wrench_harness/worker.py "
        f"symbol={needle} evidence=read-only lookup.\n"
    )
    current = (
        f'CURRENT INTENT: inspect the source for symbol "{needle}" and return '
        "one bounded read proposal with a 65536 byte limit."
    )
    available = max(1, target_tokens - _token_estimate(anchor) - _token_estimate(current) - 8)
    filler_count = max(1, available // max(1, _token_estimate(FILLER)))
    filler = FILLER * filler_count
    offset = int(max(0.0, min(1.0, placement)) * len(filler))
    payload = filler[:offset] + anchor + filler[offset:] + current
    return [{"role": "user", "content": payload}], needle, current


def _run_case(package_dir: Path, target_tokens: int, placement: float, case_index: int) -> dict[str, object]:
    from wrench_worker import WrenchWorker

    messages, needle, current = _payload(target_tokens, placement, case_index)
    started = time.perf_counter()
    worker = WrenchWorker.from_pretrained(package_dir, allowed_root=Path.cwd(), load_model=False)
    result = worker.propose(messages)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    proposal = result.get("parsed_proposal")
    if proposal is None and isinstance(result.get("raw_model_output"), str):
        try:
            proposal = json.loads(result["raw_model_output"])
        except json.JSONDecodeError:
            proposal = None
    expected = {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "src/wrench_harness/worker.py",
        "max_bytes": 65536,
    }
    passed = result.get("status") == "accepted" and proposal == expected
    return {
        "target_tokens": target_tokens,
        "placement": placement,
        "case_index": case_index,
        "needle": needle,
        "raw_payload_chars": len(messages[0]["content"]),
        "raw_payload_sha256": hashlib.sha256(messages[0]["content"].encode("utf-8")).hexdigest(),
        "current_intent_chars": len(current),
        "elapsed_ms": elapsed_ms,
        "status": result.get("status"),
        "backend": result.get("backend"),
        "mechanical_fast_path": result.get("mechanical_fast_path"),
        "context_gate": result.get("context_gate"),
        "model_calls": result.get("model_calls", 0),
        "fallback_reason": result.get("fallback_reason"),
        "proposal": proposal,
        "expected_proposal": expected,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    if not package_dir.is_dir():
        raise SystemExit(f"package directory does not exist: {package_dir}")
    sys.path.insert(0, str(package_dir))
    cases = [
        _run_case(package_dir, 2_000_000, 0.01, 0),
        _run_case(package_dir, 2_000_000, 0.50, 1),
        _run_case(package_dir, 2_000_000, 0.99, 2),
        _run_case(package_dir, 4_000_000, 0.01, 3),
        _run_case(package_dir, 4_000_000, 0.50, 4),
        _run_case(package_dir, 4_000_000, 0.99, 5),
    ]
    receipt = {
        "schema": "wrench.package-retrieval-quality-probe.v1",
        "status": "PASS_PACKAGE_RETRIEVAL_2M_4M" if all(item["passed"] for item in cases) else "FAIL",
        "package_dir": str(package_dir),
        "model_calls": sum(int(item["model_calls"]) for item in cases),
        "cases": cases,
        "quality_claim": False,
        "scope": "deterministic embedded retrieval diagnostic; not dense-native attention quality",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "cases": len(cases), "model_calls": receipt["model_calls"]}))
    return 0 if receipt["status"] == "PASS_PACKAGE_RETRIEVAL_2M_4M" else 1


if __name__ == "__main__":
    raise SystemExit(main())
