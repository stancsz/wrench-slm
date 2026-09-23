"""Score the production ContextLedger lexical search path on ARB V2.

This is a component adapter. It uses only the benchmark query and released
candidate corpus, emits ranked files via ContextLedger.search, and delegates
retrieval metric formulas to the pinned ARB evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PHASE = Path(__file__).resolve().parent
EXTERNAL = PHASE / "external" / "agent-retrieval-bench"
UPSTREAM = EXTERNAL / "upstream"
SAMPLES = EXTERNAL / "data" / "benchmark" / "v2_selective_retrieval_natural" / "samples.jsonl"
CORPUS = EXTERNAL / "data" / "corpus" / "v2_selective_mixed"
GATE_PREDICTIONS = EXTERNAL / "runs" / "wrench-binary-gate-v2" / "predictions.jsonl"
DEFAULT_OUT = EXTERNAL / "runs" / "wrench-context-ledger-ranked-v1"
COMPONENT_SOURCE = PHASE.parent.parent / "src" / "wrench_harness" / "context.py"
RESERVE = 0.10


def resource_sample() -> dict[str, Any]:
    import psutil

    vm = psutil.virtual_memory()
    row: dict[str, Any] = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_available_bytes": int(vm.available),
        "ram_total_bytes": int(vm.total),
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        )
        values = [int(part.strip()) for part in output.splitlines()[0].split(",", 1)]
        row["vram_free_bytes"], row["vram_total_bytes"] = [value * 1024 * 1024 for value in values]
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        pass
    return row


def enforce_reserve(row: dict[str, Any]) -> None:
    for name in ("ram", "vram"):
        free, total = row.get(f"{name}_available_bytes"), row.get(f"{name}_total_bytes")
        if name == "vram":
            free, total = row.get("vram_free_bytes"), row.get("vram_total_bytes")
        if not isinstance(free, int) or not isinstance(total, int):
            raise RuntimeError(f"{name.upper()} availability could not be measured")
        if free < total * RESERVE:
            raise RuntimeError(f"10 percent {name.upper()} reserve would be breached")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path):
    """Yield corpus records one at a time so the source corpus is not duplicated in RAM."""
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    for path in (SAMPLES, CORPUS / "corpus_manifest.jsonl", GATE_PREDICTIONS):
        if not path.is_file():
            raise FileNotFoundError(path)

    before = resource_sample()
    enforce_reserve(before)
    os.chdir(EXTERNAL)
    sys.path.insert(0, str(UPSTREAM / "src"))
    sys.path.insert(0, str(PHASE.parent.parent / "src"))
    from wrench_harness.context import ContextLedger
    from agent_retrieval_bench.baseline import (
        gold_file_ranks,
        hard_negative_files,
        load_corpus_manifest,
        query_has_leakage,
        query_text_for_eval,
        sample_metrics,
        target_gold_files,
        unique_ranked_paths,
    )
    from agent_retrieval_bench.io import read_jsonl
    from agent_retrieval_bench.selective_eval import average_positive_metrics

    samples = read_jsonl(SAMPLES)
    gate_rows = {row["id"]: row for row in read_jsonl(GATE_PREDICTIONS)}
    manifest = load_corpus_manifest(CORPUS)
    pending: dict[Path, list[tuple[int, dict[str, Any], list[str], str, bool]]] = defaultdict(list)
    skipped: dict[str, int] = defaultdict(int)
    for index, sample in enumerate(samples):
        gold_files = target_gold_files(sample)
        is_no_gold = (sample.get("gold") or {}).get("no_gold") is True
        if not gold_files and not is_no_gold:
            skipped["no_gold_unlabeled"] += 1
            continue
        query = query_text_for_eval(sample)
        if query_has_leakage(sample, query):
            skipped["query_leakage"] += 1
            continue
        corpus_path = manifest.get((sample.get("repo"), sample.get("base_commit")))
        if corpus_path is None:
            skipped["missing_corpus"] += 1
            continue
        pending[corpus_path].append((index, sample, gold_files, query, is_no_gold))

    details: list[dict[str, Any]] = []
    index_seconds = 0.0
    retrieval_ms: list[float] = []
    resource_samples: list[dict[str, Any]] = [before]
    started = time.perf_counter()
    out_details = args.output_dir / "details.jsonl"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with out_details.open("w", encoding="utf-8") as output:
        for corpus_index, (corpus_path, corpus_samples) in enumerate(pending.items(), start=1):
            resources = resource_sample()
            enforce_reserve(resources)
            resource_samples.append(resources)
            ledger = ContextLedger(max_logical_tokens=1_000_000_000)
            chunk_by_id: dict[str, dict[str, Any]] = {}
            index_started = time.perf_counter()
            chunk_count = 0
            for source_order, chunk in enumerate(iter_jsonl(corpus_path)):
                chunk_count += 1
                if chunk_count % 500 == 0:
                    sample_resources = resource_sample()
                    enforce_reserve(sample_resources)
                    resource_samples.append(sample_resources)
                text = str(chunk.get("text") or "")
                if not text.strip():
                    continue
                if not re.search(r"\w", text, re.UNICODE):
                    continue
                chunk_id = str(chunk.get("chunk_id") or f"chunk-{source_order}")
                segment_id = f"{source_order}:{chunk_id}"
                ledger.add_segment(
                    segment_id,
                    text,
                    source_order,
                    role="context",
                    kind="code_chunk",
                    metadata={"path": str(chunk.get("path") or "")},
                )
                chunk_by_id[segment_id] = chunk
            index_seconds += time.perf_counter() - index_started

            for _, sample, gold_files, query, is_no_gold in corpus_samples:
                lookup_started = time.perf_counter()
                matches = ledger.search(query, limit=10_000)
                retrieval_ms.append((time.perf_counter() - lookup_started) * 1000.0)
                ranked_chunks = [chunk_by_id[item.segment_id] for item in matches]
                ranked_paths = unique_ranked_paths(ranked_chunks)
                gate = gate_rows.get(str(sample.get("id")))
                detail: dict[str, Any] = {
                    "sample_id": sample.get("id"),
                    "repo": sample.get("repo"),
                    "base_commit": sample.get("base_commit"),
                    "task_type": sample.get("task_type"),
                    "candidate_filter": "all_files",
                    "ranker": "wrench_contextledger_search",
                    "label": "no_gold" if is_no_gold else "positive",
                    "gold_files": gold_files,
                    "top_files": ranked_paths[:20],
                    "gate_decision": gate.get("decision") if gate else None,
                    "gate_abstain_probability": (gate.get("probabilities") or {}).get("abstain") if gate else None,
                    "retrieval_ms": retrieval_ms[-1],
                    "candidate_chunk_count": chunk_count,
                    "matched_chunk_count": len(matches),
                    "index_token_estimate": ledger.logical_token_count,
                }
                if gold_files:
                    detail["metrics"] = sample_metrics(
                        gold_files,
                        ranked_chunks,
                        hard_negative_files=hard_negative_files(sample),
                    )
                    detail["gold_ranks"] = gold_file_ranks(gold_files, ranked_chunks)
                    detail["hard_negative_files"] = hard_negative_files(sample)
                output.write(json.dumps(detail, ensure_ascii=False, sort_keys=True) + "\n")
                details.append(detail)
            del ledger, chunk_by_id
            resources = resource_sample()
            enforce_reserve(resources)
            resource_samples.append(resources)
            print(f"[{corpus_index}/{len(pending)}] scored {len(corpus_samples)} queries from {corpus_path.name}", flush=True)

    positives = [row for row in details if row["label"] == "positive"]
    no_gold = [row for row in details if row["label"] == "no_gold"]
    gate_decision_counts: dict[str, int] = defaultdict(int)
    for row in details:
        if row.get("gate_decision"):
            gate_decision_counts[str(row["gate_decision"])] += 1
    positive_continued = [row for row in positives if row.get("gate_decision") == "not_abstain"]
    no_gold_abstained = [row for row in no_gold if row.get("gate_decision") == "abstain"]
    resources_after = resource_sample()
    enforce_reserve(resources_after)
    resource_samples.append(resources_after)
    summary = {
        "schema": "wrench.arb-v2.contextledger-ranked-component.v1",
        "benchmark": "Agent Retrieval Bench V2 selective natural",
        "suite_revision": "07014c986f3deadb1548c62b32c0ffbe6a81465d",
        "dataset_revision": "5901e1ee3aff048290db72edf9c63bc498b79ea3",
        "component_source_sha256": sha256_file(COMPONENT_SOURCE),
        "ranker": "bm25_k1_1.2_b_0.75",
        "metric_scope": "ContextLedger.search ranked-file retrieval component; no task execution or end-to-end client claim",
        "candidate_filter": "all_files",
        "rows": len(details),
        "positive_rows": len(positives),
        "no_gold_rows": len(no_gold),
        "skipped": dict(skipped),
        "positive_retrieval_metrics": average_positive_metrics(positives),
        "selective_gate": {
            "source_predictions": str(GATE_PREDICTIONS.relative_to(PHASE)),
            "decisions": dict(gate_decision_counts),
            "positive_continue_rate": len(positive_continued) / len(positives) if positives else 0.0,
            "no_gold_abstain_rate": len(no_gold_abstained) / len(no_gold) if no_gold else 0.0,
            "accepted_positive_recall_at_20": mean(float((row.get("metrics") or {}).get("Recall@20") or 0.0) for row in positive_continued) if positive_continued else 0.0,
            "accepted_positive_hit_at_20": sum(float((row.get("metrics") or {}).get("Recall@20") or 0.0) > 0 for row in positive_continued) / len(positive_continued) if positive_continued else 0.0,
        },
        "latency_ms": {
            "query_p50": sorted(retrieval_ms)[len(retrieval_ms) // 2] if retrieval_ms else None,
            "query_p95": sorted(retrieval_ms)[min(len(retrieval_ms) - 1, int(len(retrieval_ms) * 0.95))] if retrieval_ms else None,
        },
        "index_build_seconds_total": index_seconds,
        "wall_seconds": time.perf_counter() - started,
        "input_sha256": {"samples": sha256_file(SAMPLES), "corpus_manifest": sha256_file(CORPUS / "corpus_manifest.jsonl"), "gate_predictions": sha256_file(GATE_PREDICTIONS)},
        "details_sha256": sha256_file(out_details),
        "resources_before": before,
        "resources_after": resources_after,
        "resource_samples": resource_samples,
        "minimum_ram_available_bytes": min(int(row["ram_available_bytes"]) for row in resource_samples),
        "minimum_vram_free_bytes": min((int(row["vram_free_bytes"]) for row in resource_samples if isinstance(row.get("vram_free_bytes"), int)), default=None),
        "resource_guard": "minimum 10 percent RAM and VRAM free before and during corpus indexing; corpus JSONL streamed and sampled every 500 chunks",
        "outside_references_same_arb_v2_release": {
            "Lexical": {"Recall@20": 0.493961, "MRR": 0.157415, "BCY@8K": 0.264976},
            "Qwen3-Embedding-4B": {"Recall@20": 0.6306, "MRR": 0.2379, "BCY@8K": 0.3409},
            "Qwen3-Embedding-8B": {"Recall@20": 0.7029, "MRR": 0.2336, "BCY@8K": 0.3732},
            "Jina-code-embeddings-0.5B": {"Recall@20": 0.4823, "MRR": 0.1914, "BCY@8K": 0.2783},
            "BM25": {"Recall@20": 0.4452, "MRR": 0.1520, "BCY@8K": 0.2051},
        },
        "comparability": "Published outside model values are references from the same release, not a new matched rerun. Wrench ranking uses the same released queries, candidate corpus, and official scoring formulas. Retrieval component result does not establish end-to-end Wrench utility.",
    }
    enforce_reserve(summary["resources_after"])
    write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
