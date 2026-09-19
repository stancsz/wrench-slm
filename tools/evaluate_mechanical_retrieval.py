#!/usr/bin/env python3
"""Measure deterministic old-lookup recall without calling an LLM.

This is a retrieval-contract diagnostic. It checks that a current intent can
recover a deliberately old, cold reference card while recent context remains
the active working set. It is not a teacher-parity or end-to-end worker score.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness.prefill import MechanicalPrefillIndex, build_dynamic_prefill


def _messages(case_id: int) -> tuple[list[dict[str, str]], dict[str, str]]:
    target = {
        "role": "user",
        "content": (
            f"ARCHIVE target-{case_id:03d} src/services/worker_{case_id:03d}.py "
            f"class Worker{case_id:03d} def handle_{case_id:03d} "
            f"error signature ERR-{case_id:03d}-7 timeout "
            + "historical reference context " * 120
        ),
    }
    history: list[dict[str, str]] = [
        {"role": "system", "content": "bounded read-only worker"},
        target,
    ]
    for distractor_id in range(3):
        history.append(
            {
                "role": "assistant",
                "content": (
                    f"ARCHIVE decoy-{case_id:03d}-{distractor_id:03d} "
                    f"src/other/worker_{case_id:03d}_{distractor_id:03d}.py "
                    f"class Decoy{case_id:03d}_{distractor_id:03d} "
                    + "unrelated stale observation " * 120
                ),
            }
        )
    history.append(
        {
            "role": "user",
            "content": f"Find src/services/worker_{case_id:03d}.py and class Worker{case_id:03d}.",
        }
    )
    return history, target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=220)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.cases < 1:
        raise SystemExit("--cases must be positive")

    hits = 0
    current_intent_preserved = 0
    hash_bound = 0
    for case_id in range(args.cases):
        messages, target = _messages(case_id)
        index = MechanicalPrefillIndex()
        index.add_all(messages)
        _, receipt = build_dynamic_prefill(
            messages,
            model_prefill_budget=64_000,
            hot_token_budget=400,
            reference_index_budget=16_000,
            mechanical_index=index,
        )
        target_card = index.entry(target)["card"]
        if target_card["reference_id"] in receipt["lookup_table_ids"]:
            hits += 1
        if receipt["current_intent_source_index"] == len(messages) - 1:
            current_intent_preserved += 1
        if target_card["source_sha256"] in " ".join(
            index.entry(message)["card"]["source_sha256"] for message in messages
        ):
            hash_bound += 1

    result = {
        "schema": "wrench.mechanical-retrieval-quality.v1",
        "status": "PASS_MECHANICAL_RETRIEVAL_DIAGNOSTIC"
        if hits == args.cases and current_intent_preserved == args.cases and hash_bound == args.cases
        else "FAIL",
        "quality_claim": False,
        "cases": args.cases,
        "target_reference_recall": hits / args.cases,
        "current_intent_preservation": current_intent_preserved / args.cases,
        "hash_bound_reference_rate": hash_bound / args.cases,
        "model_calls": 0,
        "notes": [
            "Mechanical retrieval only. No LLM or teacher was used.",
            "The result does not prove final Wrench task success or MiniMax parity.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
