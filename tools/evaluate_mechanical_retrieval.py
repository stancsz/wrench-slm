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
import time
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


def _monster_messages(case_id: int, target_tokens: int) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Build one large cold reference plus a current intent.

    The size uses the same cheap whitespace estimate as the mechanical
    prefill. This is intentionally a data-engineering stress case, not a
    language-model quality benchmark.
    """

    target = {
        "role": "assistant",
        "content": (
            f"ARCHIVE target-{case_id:03d} src/services/worker_{case_id:03d}.py "
            f"class Worker{case_id:03d} def handle_{case_id:03d} "
            f"error signature ERR-{case_id:03d}-7 timeout\n"
        ),
    }
    filler_unit = (
        "stale lookup telemetry record status observed unrelated historical "
        "reference material no instruction authority; "
    )
    filler_tokens = max(1, target_tokens - target["content"].count(" ") - 64)
    filler = filler_unit * ((filler_tokens + filler_unit.count(" ") - 1) // filler_unit.count(" "))
    target["content"] += filler
    current = {
        "role": "user",
        "content": f"Find src/services/worker_{case_id:03d}.py and class Worker{case_id:03d}.",
    }
    return [
        {"role": "system", "content": "bounded read-only worker"},
        target,
        current,
    ], target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=220)
    parser.add_argument(
        "--payload-tokens",
        type=int,
        default=0,
        help="Run monster-payload mode with one cold reference near this estimated size.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.cases < 1:
        raise SystemExit("--cases must be positive")

    if args.payload_tokens < 0:
        raise SystemExit("--payload-tokens must be non-negative")
    if args.payload_tokens and args.cases != 1:
        raise SystemExit("monster-payload mode requires --cases 1")

    hits = 0
    current_intent_preserved = 0
    hash_bound = 0
    raw_token_counts: list[int] = []
    model_token_counts: list[int] = []
    ingest_ms_values: list[float] = []
    selection_ms_values: list[float] = []
    for case_id in range(args.cases):
        messages, target = (
            _monster_messages(case_id, args.payload_tokens)
            if args.payload_tokens
            else _messages(case_id)
        )
        index = MechanicalPrefillIndex()
        ingest_started = time.perf_counter()
        index.add_all(messages)
        ingest_ms_values.append(round((time.perf_counter() - ingest_started) * 1000, 3))
        selection_started = time.perf_counter()
        _, receipt = build_dynamic_prefill(
            messages,
            model_prefill_budget=64_000,
            hot_token_budget=400,
            reference_index_budget=16_000,
            mechanical_index=index,
        )
        selection_ms_values.append(round((time.perf_counter() - selection_started) * 1000, 3))
        raw_token_counts.append(int(receipt["raw_token_count"]))
        model_token_counts.append(int(receipt["model_prefill_token_count"]))
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
        "payload_mode": "monster_single_cold_reference" if args.payload_tokens else "historical_small_cases",
        "requested_payload_tokens": args.payload_tokens or None,
        "raw_token_count": raw_token_counts[0] if len(raw_token_counts) == 1 else None,
        "model_prefill_token_count": model_token_counts[0] if len(model_token_counts) == 1 else None,
        "cold_ingest_ms": ingest_ms_values[0] if len(ingest_ms_values) == 1 else None,
        "hot_selection_ms": selection_ms_values[0] if len(selection_ms_values) == 1 else None,
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
