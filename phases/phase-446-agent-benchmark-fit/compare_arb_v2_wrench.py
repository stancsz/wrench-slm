"""Matched per-sample comparison of Wrench ContextLedger retrieval and ARB Lexical."""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path
from typing import Any


PHASE = Path(__file__).resolve().parent
EXTERNAL = PHASE / "external" / "agent-retrieval-bench"
WRENCH = EXTERNAL / "runs" / "wrench-context-ledger-ranked-v1"
LEXICAL_DETAILS = EXTERNAL / "data" / "eval" / "arb-v2" / "natural-lexical-details.jsonl"
LEXICAL_BCY = EXTERNAL / "data" / "eval" / "arb-v2" / "natural-lexical-canonical-bcy-details.jsonl"
WRENCH_BCY = WRENCH / "canonical-bcy-details.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def summarize(delta: list[float], repos: list[str], *, reps: int = 10_000, seed: int = 44609) -> dict[str, Any]:
    if not delta:
        return {"n": 0}
    rows_by_repo: dict[str, list[float]] = {}
    for repo, value in zip(repos, delta):
        rows_by_repo.setdefault(repo, []).append(value)
    names = sorted(rows_by_repo)
    point = statistics.mean(delta)
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(reps):
        chosen = [rng.choice(names) for _ in names]
        values = [value for repo in chosen for value in rows_by_repo[repo]]
        samples.append(statistics.mean(values))
    samples.sort()
    return {
        "n": len(delta),
        "repo_clusters": len(names),
        "wrench_minus_lexical_mean": point,
        "repository_cluster_bootstrap_95_ci": [samples[int(0.025 * (reps - 1))], samples[int(0.975 * (reps - 1))]],
        "bootstrap_replicates": reps,
        "seed": seed,
    }


def main() -> int:
    wrench = {row["sample_id"]: row for row in read_jsonl(WRENCH / "details.jsonl") if row.get("label") == "positive"}
    lexical = {row["sample_id"]: row for row in read_jsonl(LEXICAL_DETAILS) if row.get("gold_files")}
    wrench_bcy = {row["sample_id"]: row for row in read_jsonl(WRENCH_BCY)}
    lexical_bcy = {row["sample_id"]: row for row in read_jsonl(LEXICAL_BCY)}
    ids = sorted(set(wrench) & set(lexical) & set(wrench_bcy) & set(lexical_bcy))
    if len(ids) != 345:
        raise RuntimeError(f"expected 345 matched positive cases, got {len(ids)}")
    repos = [str(wrench[sample_id]["repo"]) for sample_id in ids]
    metrics = ["Recall@5", "Recall@10", "Recall@20", "MRR", "Precision@20"]
    comparison: dict[str, Any] = {key: summarize([
        float((wrench[sample_id].get("metrics") or {}).get(key) or 0.0)
        - float((lexical[sample_id].get("metrics") or {}).get(key) or 0.0)
        for sample_id in ids
    ], repos) for key in metrics}
    comparison.update({
        f"BCY@{budget}": summarize([
            float((wrench_bcy[sample_id].get("bcy") or {}).get(str(budget)) or 0.0)
            - float((lexical_bcy[sample_id].get("bcy") or {}).get(str(budget)) or 0.0)
            for sample_id in ids
        ], repos)
        for budget in (4000, 8000, 16000, 32000)
    })
    report = {
        "schema": "wrench.arb-v2-matched-retrieval-comparison.v1",
        "comparison": "Wrench ContextLedger.search minus reproduced official Lexical, paired by sample ID",
        "cases": len(ids),
        "repo_clusters": len(set(repos)),
        "metrics": comparison,
        "lexical_reference": {
            "Recall@20": 0.493961,
            "MRR": 0.157415,
            "BCY@8K": 0.264976,
        },
        "outside_model_references_same_release": {
            "Qwen3-Embedding-4B": {"Recall@20": 0.6306, "MRR": 0.2379, "BCY@8K": 0.3409},
            "Qwen3-Embedding-8B": {"Recall@20": 0.7029, "MRR": 0.2336, "BCY@8K": 0.3732},
            "Jina-code-embeddings-0.5B": {"Recall@20": 0.4823, "MRR": 0.1914, "BCY@8K": 0.2783},
            "BM25": {"Recall@20": 0.4452, "MRR": 0.1520, "BCY@8K": 0.2051},
        },
        "interpretation": "Lexical comparison is paired and case-matched. Published embedding-model rows share the ARB V2 release but do not provide per-case outputs here, so they are benchmark references rather than a paired Wrench-versus-model test.",
    }
    out = WRENCH / "matched-comparison.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
