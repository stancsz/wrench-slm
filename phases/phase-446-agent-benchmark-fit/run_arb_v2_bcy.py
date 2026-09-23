"""Compute canonical ARB V2 BCY for a saved ranked-file details artifact.

This calls the benchmark's own BCY functions, processing one repository
snapshot at a time so the released corpus does not accumulate in RAM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASE = Path(__file__).resolve().parent
EXTERNAL = PHASE / "external" / "agent-retrieval-bench"
UPSTREAM = EXTERNAL / "upstream"
DATA = EXTERNAL / "data"
DEFAULT_INPUT = DATA / "eval" / "arb-v2" / "natural-lexical-details.jsonl"
DEFAULT_MANIFEST = DATA / "corpus" / "v2_selective_mixed" / "corpus_manifest.jsonl"
DEFAULT_OUT = DATA / "eval" / "arb-v2" / "natural-lexical-canonical-bcy-summary.json"
DEFAULT_CASES = DATA / "eval" / "arb-v2" / "natural-lexical-canonical-bcy-details.jsonl"
RESERVE_FRACTION = 0.10


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_sample() -> dict[str, int | str | None]:
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("psutil is required to enforce the host RAM reserve") from exc
    memory = psutil.virtual_memory()
    sample: dict[str, int | str | None] = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_free_bytes": int(memory.available),
        "ram_total_bytes": int(memory.total),
        "vram_free_bytes": None,
        "vram_total_bytes": None,
    }
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        )
        rows = [line.strip() for line in output.splitlines() if line.strip()]
        if rows:
            free_mib, total_mib = (int(value.strip()) for value in rows[0].split(",", 1))
            sample["vram_free_bytes"] = free_mib * 1024 * 1024
            sample["vram_total_bytes"] = total_mib * 1024 * 1024
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return sample


def enforce_reserve(sample: dict[str, int | str | None]) -> None:
    for kind in ("ram", "vram"):
        free = sample.get(f"{kind}_free_bytes")
        total = sample.get(f"{kind}_total_bytes")
        if isinstance(free, int) and isinstance(total, int) and free < total * RESERVE_FRACTION:
            raise RuntimeError(f"less than 10 percent {kind.upper()} reserve remains")
    if not isinstance(sample.get("ram_free_bytes"), int):
        raise RuntimeError("RAM availability could not be measured")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"expected object at {path}:{line_number}")
                rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--details", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--corpus-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--case-out", type=Path, default=DEFAULT_CASES)
    args = parser.parse_args()
    for path in (args.details, args.corpus_manifest):
        if not path.is_file():
            raise FileNotFoundError(path)

    sys.path.insert(0, str(UPSTREAM / "src"))
    from agent_retrieval_bench.bcy_curve import (  # noqa: E402
        CorpusFileCache,
        evaluate_sample,
        group_rows_by_task,
        load_corpus_manifest,
        summarize_rows,
    )

    before = resource_sample()
    enforce_reserve(before)
    details = read_jsonl(args.details)
    manifest = load_corpus_manifest(args.corpus_manifest)
    budgets = (4_000, 8_000, 16_000, 32_000)
    thresholds = (1, 16, 32, 64, 128)
    ordered = sorted(
        (row for row in details if row.get("gold_files")),
        key=lambda row: (str(row.get("repo", "")), str(row.get("base_commit", "")), str(row.get("sample_id", ""))),
    )
    scored: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    cache: Any | None = None
    cache_key: tuple[str, str] | None = None
    resources = [before]
    for index, detail in enumerate(ordered, start=1):
        current_key = (str(detail.get("repo") or ""), str(detail.get("base_commit") or ""))
        if current_key != cache_key:
            sample = resource_sample()
            enforce_reserve(sample)
            resources.append(sample)
            cache = CorpusFileCache(manifest)
            cache_key = current_key
        assert cache is not None
        result = evaluate_sample(detail, list(detail["gold_files"]), cache, budgets, thresholds)
        scored.append(result)
        case_rows.append(
            {
                "sample_id": result["sample_id"],
                "task_type": result["task_type"],
                "repo": result["repo"],
                "base_commit": result["base_commit"],
                "gold_files": result["gold_files"],
                "ranked_files": result["ranked_files"],
                "bcy": {str(budget): result["packed"][budget]["bcy"] for budget in budgets},
                "used_tokens": {str(budget): result["packed"][budget]["used_tokens"] for budget in budgets},
                "missing_ranked_files": {str(budget): result["packed"][budget]["missing_ranked_files"] for budget in budgets},
            }
        )
        if index % 25 == 0:
            sample = resource_sample()
            enforce_reserve(sample)
            resources.append(sample)

    overall = summarize_rows(scored, budgets, thresholds)
    by_task = {
        task: summarize_rows(rows, budgets, thresholds)
        for task, rows in sorted(group_rows_by_task(scored).items())
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.case_out.parent.mkdir(parents=True, exist_ok=True)
    with args.case_out.open("w", encoding="utf-8", newline="\n") as stream:
        for row in case_rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    after = resource_sample()
    enforce_reserve(after)
    resources.append(after)
    report = {
        "schema": "wrench.arb-v2-canonical-bcy-reproduction.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "Agent Retrieval Bench V2 selective natural positive retrieval",
        "ranker": "upstream official lexical, all_files",
        "evaluator": "pinned upstream agent_retrieval_bench.bcy_curve.evaluate_sample and summarize_rows",
        "upstream_revision": "07014c986f3deadb1548c62b32c0ffbe6a81465d",
        "dataset_revision": "5901e1ee3aff048290db72edf9c63bc498b79ea3",
        "input_details": {"path": str(args.details), "sha256": sha256_file(args.details), "bytes": args.details.stat().st_size},
        "corpus_manifest": {"path": str(args.corpus_manifest), "sha256": sha256_file(args.corpus_manifest), "bytes": args.corpus_manifest.stat().st_size},
        "case_details": {"path": str(args.case_out), "sha256": sha256_file(args.case_out), "bytes": args.case_out.stat().st_size},
        "cases": len(scored),
        "budgets": list(budgets),
        "coverage_thresholds": list(thresholds),
        "tokenizer": "regex_code_tokenizer_v1",
        "overall": overall,
        "by_task": by_task,
        "resources": resources,
        "reserve_fraction": RESERVE_FRACTION,
    }
    report["runner_sha256"] = sha256_file(Path(__file__))
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(scored), "BCY@8K": overall.get("BCY@8000"), "summary": str(args.out), "runner_sha256": report["runner_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
