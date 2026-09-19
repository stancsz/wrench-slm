"""Benchmark the provider-free logical-context ledger.

This measures retention, indexing, retrieval, assembly, and receipt hashing.
It deliberately does not call a model or claim native 2M attention support.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import ContextLedger


def _milliseconds(start: float, end: float) -> float:
    return round((end - start) * 1000, 3)


def benchmark(
    *,
    segments: int,
    tokens_per_segment: int,
    active_token_budget: int,
    materialize: bool,
) -> dict[str, object]:
    if segments < 1 or tokens_per_segment < 1 or active_token_budget < 1:
        raise ValueError("benchmark sizes must be positive")
    if materialize and tokens_per_segment < 6:
        raise ValueError("materialized benchmark needs at least 6 tokens per segment")
    logical_tokens = segments * tokens_per_segment
    ledger = ContextLedger(max_logical_tokens=logical_tokens)

    ingest_start = time.perf_counter()
    for index in range(segments):
        marker_words = ["needle", "verifier", "evidence"] if index == segments // 2 else ["routine", "context", "payload"]
        if materialize:
            words = ["segment", str(index), "contains", *marker_words]
            words.extend(["context"] * (tokens_per_segment - len(words)))
            text = " ".join(words)
            explicit_count = None
        else:
            text = f"segment {index} contains {' '.join(marker_words)}"
            explicit_count = tokens_per_segment
        ledger.add_segment(
            f"segment-{index:08d}",
            text,
            index,
            token_count=explicit_count,
            role="context",
        )
    ingest_end = time.perf_counter()

    search_start = time.perf_counter()
    matches = ledger.search("needle verifier evidence", limit=8)
    search_end = time.perf_counter()
    if not matches:
        raise RuntimeError("indexed query returned no match")

    hash_start = time.perf_counter()
    session_hash = ledger.session_hash()
    hash_end = time.perf_counter()

    assemble_start = time.perf_counter()
    assembly = ledger.assemble(
        "needle verifier evidence",
        active_token_budget=active_token_budget,
        preserve_ids=[matches[0].segment_id],
        receipt_detail="summary",
    )
    assemble_end = time.perf_counter()

    return {
        "schema": "wrench.logical-context-ledger-benchmark.v1",
        "status": "PASS_LOGICAL_CONTEXT_MECHANICS_ONLY",
        "provider_called": False,
        "model_called": False,
        "native_attention_tested": False,
        "materialized_content": materialize,
        "token_counter_name": assembly["token_counter_name"],
        "segments": ledger.segment_count,
        "logical_token_count": ledger.logical_token_count,
        "active_token_budget": active_token_budget,
        "selected_token_count": assembly["selected_token_count"],
        "omitted_segment_count": assembly["omitted_segment_count"],
        "top_match": matches[0].segment_id,
        "session_hash": session_hash,
        "timing_ms": {
            "ingest_and_index": _milliseconds(ingest_start, ingest_end),
            "indexed_search": _milliseconds(search_start, search_end),
            "cold_session_hash": _milliseconds(hash_start, hash_end),
            "warm_bounded_assembly_and_receipt": _milliseconds(assemble_start, assemble_end),
        },
        "evidence_boundary": [
            "This is a provider-free ledger benchmark.",
            (
                "Materialized mode uses the word_estimate_v1 counter, not the target model tokenizer."
                if materialize
                else "Explicit token counts represent logical accounting, not materialized tokenizer output."
            ),
            "It does not establish model quality, native 2M attention, provider latency, or production value.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments", type=int, default=20_000)
    parser.add_argument("--tokens-per-segment", type=int, default=100)
    parser.add_argument("--active-token-budget", type=int, default=4_000)
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = benchmark(
        segments=args.segments,
        tokens_per_segment=args.tokens_per_segment,
        active_token_budget=args.active_token_budget,
        materialize=args.materialize,
    )
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
