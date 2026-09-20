#!/usr/bin/env python3
"""Measure the package worker's deterministic monster-payload staging path."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_payload(target_tokens: int) -> tuple[list[dict[str, str]], str]:
    marker = "old reference symbol=run_worker path=src/wrench_harness/worker.py line=218\n"
    filler = "stale lookup telemetry record status observed unrelated historical reference-only data; "
    current = (
        'CURRENT INTENT: inspect the source for symbol "run_worker" and return '
        "one bounded proposal for the active task."
    )
    filler_tokens = max(1, target_tokens - marker.count(" ") - current.count(" ") - 64)
    old = marker + filler * ((filler_tokens + filler.count(" ") - 1) // filler.count(" "))
    return [
        {"role": "system", "content": "bounded worker"},
        {"role": "user", "content": old + current},
    ], marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-tokens", type=int, default=4_000_000)
    parser.add_argument("--package-dir", type=Path, help="probe the bundled package runtime instead of source")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.payload_tokens < 1:
        raise SystemExit("--payload-tokens must be positive")

    if args.package_dir is not None:
        sys.path.insert(0, str(args.package_dir.resolve()))
        from wrench_runtime.worker import _dynamic_prefill_messages
    else:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from wrench_harness.worker import _dynamic_prefill_messages

    messages, marker = _build_payload(args.payload_tokens)
    started = time.perf_counter()
    staged, receipt = _dynamic_prefill_messages(messages)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    rendered = json.dumps(staged, ensure_ascii=False, separators=(",", ":"))
    target_reference_preserved = (
        "src/wrench_harness/worker.py" in rendered and "run_worker" in rendered
    )
    result = {
        "schema": "wrench.embedded-worker-prefill-probe.v1",
        "status": (
            "PASS_EMBEDDED_MONSTER_PREFILL"
            if receipt is not None
            and receipt.get("mode") == "staged_single_pass"
            and receipt.get("pipeline") == "map_reduce_dynamic_native"
            and receipt.get("model_prefill_token_count", args.payload_tokens + 1) <= 64_000
            and receipt.get("evidence_window_count", 0) >= 1
            and target_reference_preserved
            else "FAIL"
        ),
        "quality_claim": False,
        "requested_payload_tokens": args.payload_tokens,
        "raw_payload_chars": sum(len(message["content"]) for message in messages),
        "elapsed_ms": elapsed_ms,
        "model_calls": 0,
        "target_reference_sha256": hashlib.sha256(marker.encode("utf-8")).hexdigest(),
        "target_reference_preserved": target_reference_preserved,
        "pipeline": receipt.get("pipeline") if isinstance(receipt, dict) else None,
        "evidence_window_count": receipt.get("evidence_window_count", 0) if isinstance(receipt, dict) else 0,
        "receipt": receipt,
        "staged_message_count": len(staged),
        "notes": [
            "Deterministic package prefill only; no model generation was called.",
            "This proves bounded working-context staging, not native dense 4M attention quality.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "elapsed_ms": elapsed_ms, "model_calls": 0}))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
