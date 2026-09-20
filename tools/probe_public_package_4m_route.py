#!/usr/bin/env python3
"""Exercise the downloaded package worker on a raw monster payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def _build_payload(target_tokens: int) -> tuple[list[dict[str, str]], str]:
    marker = "old reference symbol=run_worker path=src/wrench_harness/worker.py line=218\n"
    filler = "stale lookup telemetry record status observed unrelated historical reference-only data; "
    current = (
        'CURRENT INTENT: inspect the source for symbol "run_worker" and return '
        "one bounded read proposal with a 65536 byte limit."
    )
    filler_tokens = max(1, target_tokens - marker.count(" ") - current.count(" ") - 64)
    old = marker + filler * ((filler_tokens + filler.count(" ") - 1) // filler.count(" "))
    return [{"role": "user", "content": old + current}], marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--payload-tokens", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.payload_tokens < 1:
        raise SystemExit("--payload-tokens must be positive")
    sys.path.insert(0, str(args.package_dir.resolve()))
    from wrench_worker import WrenchWorker

    messages, marker = _build_payload(args.payload_tokens)
    started = time.perf_counter()
    worker = WrenchWorker.from_pretrained(args.package_dir, allowed_root=args.allowed_root, load_model=False)
    result = worker.propose(messages)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    receipt = {
        "schema": "wrench.public-package-4m-route-probe.v1",
        "status": (
            "PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE"
            if result.get("status") == "accepted"
            and result.get("backend") == "embedded-mechanical"
            and result.get("mechanical_fast_path") is True
            else "FAIL"
        ),
        "package_dir": str(args.package_dir.resolve()),
        "requested_payload_tokens": args.payload_tokens,
        "raw_payload_chars": sum(len(message["content"]) for message in messages),
        "elapsed_ms": elapsed_ms,
        "model_calls": 0,
        "target_reference_sha256": hashlib.sha256(marker.encode("utf-8")).hexdigest(),
        "result": result,
        "quality_claim": False,
        "scope": "direct downloaded-package worker route; not native dense attention quality",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "elapsed_ms": elapsed_ms, "model_calls": 0}))
    return 0 if receipt["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
