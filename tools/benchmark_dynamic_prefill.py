#!/usr/bin/env python3
"""Measure the cheap staged prefill reducer without calling a model."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness.prefill import MechanicalPrefillIndex, build_dynamic_prefill


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old-messages", type=int, default=64)
    parser.add_argument("--words-per-old-message", type=int, default=2_000)
    parser.add_argument("--hot-budget", type=int, default=48_000)
    parser.add_argument("--model-budget", type=int, default=64_000)
    args = parser.parse_args()
    messages = [
        {"role": "system", "content": "bounded read-only mechanical worker"},
        *[
            {
                "role": "user" if index % 2 == 0 else "assistant",
                "content": (
                    f"reference lookup src/service_{index}.py class Worker{index} "
                    f"AssertionError timeout test_worker_{index} "
                    f"path=src/tests/test_worker_{index}.py commit=abc{index:03d} "
                ) * max(1, args.words_per_old_message // 12),
            }
            for index in range(args.old_messages)
        ],
        {"role": "user", "content": "read the newest file and return a bounded proposal"},
    ]
    ingest_started = time.perf_counter()
    index = MechanicalPrefillIndex()
    index.add_all(messages)
    ingest_ms = (time.perf_counter() - ingest_started) * 1000
    started = time.perf_counter()
    _, receipt = build_dynamic_prefill(
        messages,
        model_prefill_budget=args.model_budget,
        hot_token_budget=args.hot_budget,
        reference_index_budget=max(1, args.model_budget - args.hot_budget - 4_000),
        mechanical_index=index,
    )
    receipt["ingest_ms"] = round(ingest_ms, 3)
    receipt["selection_ms"] = round((time.perf_counter() - started) * 1000, 3)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
