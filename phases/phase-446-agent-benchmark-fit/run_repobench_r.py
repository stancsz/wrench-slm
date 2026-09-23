from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import psutil
from transformers import AutoTokenizer


PHASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PHASE_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.wrench_harness.context import ContextLedger  # noqa: E402


DATASET_ID = "tianyang/repobench-r"
DATASET_REVISION = "b631bd4ce1215cd604c78eb095babebcba6e22de"
OFFICIAL_REPO_REVISION = "ccacd12a68783ca27e9997c3b754d3e9e0d958da"
JACCARD_TOKENIZER_ID = "Salesforce/codegen-350M-multi"
JACCARD_TOKENIZER_REVISION = "b25de779e2044ed5e7707505dea0e5a9bb08556a"
WORD_RE = re.compile(r"\w+", re.UNICODE)


def gpu_snapshot() -> dict[str, int] | None:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        total, used, free = (int(value.strip()) for value in result.stdout.splitlines()[0].split(","))
    except (IndexError, ValueError):
        return None
    return {"total_mib": total, "used_mib": used, "free_mib": free}


def resource_snapshot() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    return {
        "ram_total_bytes": memory.total,
        "ram_available_bytes": memory.available,
        "gpu": gpu_snapshot(),
    }


def enforce_reserves(snapshot: dict[str, Any]) -> None:
    if snapshot["ram_available_bytes"] < snapshot["ram_total_bytes"] * 0.10:
        raise RuntimeError("RAM free reserve fell below 10%; stopping RepoBench-R run")
    gpu = snapshot["gpu"]
    if gpu and gpu["free_mib"] < gpu["total_mib"] * 0.10:
        raise RuntimeError("VRAM free reserve fell below 10%; stopping RepoBench-R run")


def last_lines(code: str, count: int = 3) -> str:
    lines = code.split("\n")
    return "\n".join(lines[-count:])


def jaccard_rank(query: str, candidates: list[str], tokenizer: Any) -> list[int]:
    query_tokens = set(tokenizer.tokenize(query))
    scored: list[tuple[int, float]] = []
    for index, candidate in enumerate(candidates):
        candidate_tokens = set(tokenizer.tokenize(candidate))
        union = query_tokens.union(candidate_tokens)
        score = len(query_tokens.intersection(candidate_tokens)) / len(union) if union else 0.0
        scored.append((index, score))
    # The official RepoBench implementation sorts descending with Python's
    # stable sort, so equal-score candidates retain their input order.
    scored.sort(key=lambda item: item[1], reverse=True)
    return [index for index, _ in scored]


def accuracy_at_k(ranks: list[int], gold: int, k: int) -> bool:
    return gold in ranks[:k]


def summarize_cells(rows: dict[tuple[str, ...], dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, accumulator in sorted(rows.items()):
        count = accumulator["count"]
        method_summary = {}
        for method in ("context_ledger", "official_jaccard"):
            method_rows = accumulator[method]
            method_summary[method] = {
                "acc_at_1": method_rows["hits"][1] / count,
                "acc_at_3": method_rows["hits"][3] / count,
                "acc_at_5": method_rows["hits"][5] / count,
            }
        output["/".join(key)] = {"rows": count, "metrics": method_summary}
    return output


def stable_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Wrench retrieval and RepoBench's Jaccard baseline on RepoBench-R.")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=PHASE_DIR / "external" / "repobench-r" / "data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PHASE_DIR / "external" / "repobench-r" / "runs" / "wrench-context-ledger-v1",
    )
    parser.add_argument("--batch-size", type=int, default=96)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    initial_resources = resource_snapshot()
    enforce_reserves(initial_resources)
    tokenizer = AutoTokenizer.from_pretrained(
        JACCARD_TOKENIZER_ID,
        revision=JACCARD_TOKENIZER_REVISION,
    )

    files = sorted(args.data_root.glob("*_c??/test_*/????.parquet"))
    if len(files) != 9:
        raise SystemExit(f"Expected the 9 pinned test shards, found {len(files)} under {args.data_root}")

    rows: dict[tuple[str, ...], dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "context_ledger": {"hits": defaultdict(int)},
            "official_jaccard": {"hits": defaultdict(int)},
        }
    )
    prediction_path = args.output_dir / "predictions.jsonl"
    resumed = prediction_path.exists()
    completed_case_ids: set[str] = set()
    invalid_data_rows: list[dict[str, Any]] = []
    if resumed:
        with prediction_path.open("r", encoding="utf-8") as prior_predictions:
            for line in prior_predictions:
                record = json.loads(line)
                case_id = record["case_id"]
                completed_case_ids.add(case_id)
                relative = case_id.rsplit("#", 1)[0]
                parts = relative.split("/")
                language, setting = parts[0].split("_")
                difficulty = parts[1].removeprefix("test_")
                if record.get("invalid_reason"):
                    invalid_data_rows.append(
                        {"case_id": case_id, "reason": record["invalid_reason"]}
                    )
                    continue
                cell = rows[(language, setting, difficulty)]
                cell["count"] += 1
                for method, key in (
                    ("context_ledger", "context_ledger_top5"),
                    ("official_jaccard", "official_jaccard_top5"),
                ):
                    rank = record[key]
                    for k in (1, 3, 5):
                        cell[method]["hits"][k] += int(
                            accuracy_at_k(rank, int(record["gold_index"]), k)
                        )
    dataset_hashes: list[dict[str, Any]] = []
    total_rows = 0
    started = time.perf_counter()

    with prediction_path.open("a" if resumed else "w", encoding="utf-8", newline="\n") as predictions:
        for path in files:
            relative = path.relative_to(args.data_root).as_posix()
            parts = relative.split("/")
            language, setting = parts[0].split("_")
            difficulty = parts[1].removeprefix("test_")
            dataset_hashes.append(
                {"path": relative, "sha256": stable_file_hash(path), "bytes": path.stat().st_size}
            )
            parquet = pq.ParquetFile(path)
            row_offset = 0
            for batch in parquet.iter_batches(
                batch_size=args.batch_size,
                columns=["context", "code", "gold_snippet_index"],
            ):
                enforce_reserves(resource_snapshot())
                for row in batch.to_pylist():
                    case_id = f"{relative}#{row_offset}"
                    total_rows += 1
                    if case_id in completed_case_ids:
                        row_offset += 1
                        continue

                    candidates = row["context"]
                    query = last_lines(row["code"], 3)
                    gold_value = row["gold_snippet_index"]
                    if not candidates:
                        invalid_reason = "empty_candidate_list"
                    elif gold_value is None:
                        invalid_reason = "null_gold_index"
                    else:
                        gold = int(gold_value)
                        invalid_reason = (
                            "gold_index_out_of_range"
                            if not 0 <= gold < len(candidates)
                            else None
                        )
                    if invalid_reason:
                        invalid_data_rows.append({"case_id": case_id, "reason": invalid_reason})
                        predictions.write(
                            json.dumps(
                                {
                                    "case_id": case_id,
                                    "candidate_count": 0 if candidates is None else len(candidates),
                                    "gold_index": gold_value,
                                    "invalid_reason": invalid_reason,
                                },
                                separators=(",", ":"),
                            )
                            + "\n"
                        )
                        completed_case_ids.add(case_id)
                        row_offset += 1
                        continue

                    wrench_start = time.perf_counter()
                    ledger = ContextLedger()
                    for index, candidate in enumerate(candidates):
                        candidate_text = candidate if candidate else "\u200b"
                        token_count = max(1, len(WORD_RE.findall(candidate_text)))
                        ledger.add_segment(
                            f"candidate-{index}",
                            candidate_text,
                            index,
                            token_count=token_count,
                        )
                    matches = ledger.search(query, limit=max(1, len(candidates)))
                    wrench_rank = [int(match.segment_id.rsplit("-", 1)[1]) for match in matches]

                    baseline_rank = jaccard_rank(query, candidates, tokenizer)
                    _ = time.perf_counter() - wrench_start

                    cell = rows[(language, setting, difficulty)]
                    cell["count"] += 1
                    for method, rank in (
                        ("context_ledger", wrench_rank),
                        ("official_jaccard", baseline_rank),
                    ):
                        for k in (1, 3, 5):
                            cell[method]["hits"][k] += int(accuracy_at_k(rank, gold, k))

                    predictions.write(
                        json.dumps(
                            {
                                "case_id": case_id,
                                "gold_index": gold,
                                "candidate_count": len(candidates),
                                "context_ledger_top5": wrench_rank[:5],
                                "official_jaccard_top5": baseline_rank[:5],
                            },
                            separators=(",", ":"),
                        )
                        + "\n"
                    )
                    completed_case_ids.add(case_id)
                    row_offset += 1
                    if total_rows % 2000 == 0:
                        print(
                            f"processed {total_rows} RepoBench-R rows, "
                            f"scored {sum(cell['count'] for cell in rows.values())} valid rows, "
                            f"{len(invalid_data_rows)} invalid rows",
                            flush=True,
                        )

    elapsed_seconds = time.perf_counter() - started
    final_resources = resource_snapshot()
    enforce_reserves(final_resources)
    summary = {
        "schema": "wrench.repobench-r.component-run.v1",
        "dataset_id": DATASET_ID,
        "dataset_revision": DATASET_REVISION,
        "official_repository_revision": OFFICIAL_REPO_REVISION,
        "wrench_component": "src/wrench_harness/context.py::ContextLedger.search",
        "wrench_component_is_end_to_end_agent": False,
        "wrench_retrieval": {
            "query": "last three lines of the in-file code field",
            "index": "one ContextSegment per benchmark candidate",
            "ranking": "native ContextLedger term overlap, source-order tie break descending",
            "zero_match_behavior": "candidates with zero lexical overlap are not returned",
        },
        "direct_external_baseline": {
            "name": "RepoBench official Jaccard baseline",
            "tokenizer_id": JACCARD_TOKENIZER_ID,
            "tokenizer_revision": JACCARD_TOKENIZER_REVISION,
            "tokenization": "set of tokenizer tokens; official stable score-descending ordering",
        },
        "raw_case_count": total_rows,
        "scored_case_count": sum(cell["count"] for cell in rows.values()),
        "invalid_case_count": len(invalid_data_rows),
        "invalid_cases": invalid_data_rows,
        "resumed_from_prediction_checkpoint": resumed,
        "data_shards": dataset_hashes,
        "metrics_by_language_setting_difficulty": summarize_cells(rows),
        "wall_seconds_this_invocation": elapsed_seconds,
        "system": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "python": sys.version,
            "runtime_device": "CPU; this Python torch build has no CUDA",
            "initial_resources": initial_resources,
            "final_resources": final_resources,
            "resource_guard": "stop if available RAM or VRAM falls below 10% of total",
        },
        "predictions_file": prediction_path.name,
        "predictions_sha256": stable_file_hash(prediction_path),
        "comparability": "Wrench and official Jaccard were scored on the same valid cases from the pinned HF release. Two rows have out-of-range gold indices and are excluded for both methods. Published paper model scores use the original 72K-row split and are references only.",
    }
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "raw_case_count": total_rows,
                "scored_case_count": summary["scored_case_count"],
                "invalid_case_count": summary["invalid_case_count"],
                "wall_seconds_this_invocation": elapsed_seconds,
                "summary": str(summary_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
