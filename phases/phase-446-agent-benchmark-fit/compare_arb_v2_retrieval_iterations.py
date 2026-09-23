"""Compare two saved ARB V2 Wrench retrieval runs by identical sample ID."""
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import Any


PHASE = Path(__file__).resolve().parent
EXTERNAL = PHASE / "external" / "agent-retrieval-bench"
DEFAULT_BASELINE = EXTERNAL / "runs" / "wrench-context-ledger-ranked-v1"


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return {row["sample_id"]: row for row in (json.loads(line) for line in stream if line.strip())}


def paired_cluster_delta(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
    metric: str,
    *,
    bcy: bool,
    reps: int,
    seed: int,
) -> dict[str, Any]:
    ids = sorted(set(baseline) & set(candidate))
    if not ids:
        raise ValueError(f"no paired rows for {metric}")
    by_repo: dict[str, list[float]] = {}
    for sample_id in ids:
        old, new = baseline[sample_id], candidate[sample_id]
        repo = str(new.get("repo") or old.get("repo") or "")
        if not repo:
            raise ValueError(f"missing repo for sample {sample_id}")
        if bcy:
            old_value = float((old.get("bcy") or {}).get(metric) or 0.0)
            new_value = float((new.get("bcy") or {}).get(metric) or 0.0)
        else:
            old_value = float((old.get("metrics") or {}).get(metric) or 0.0)
            new_value = float((new.get("metrics") or {}).get(metric) or 0.0)
        by_repo.setdefault(repo, []).append(new_value - old_value)
    repos = sorted(by_repo)
    deltas = [delta for repo in repos for delta in by_repo[repo]]
    rng = random.Random(seed)
    draws = []
    for _ in range(reps):
        selected = [rng.choice(repos) for _ in repos]
        values = [value for repo in selected for value in by_repo[repo]]
        draws.append(statistics.mean(values))
    draws.sort()
    return {
        "paired_rows": len(ids),
        "repo_clusters": len(repos),
        "candidate_minus_baseline_mean": statistics.mean(deltas),
        "repository_cluster_bootstrap_95_ci": [draws[int(0.025 * (reps - 1))], draws[int(0.975 * (reps - 1))]],
        "bootstrap_replicates": reps,
        "seed": seed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    if args.bootstrap_replicates < 1:
        raise ValueError("bootstrap replicates must be positive")

    old_positive = {
        key: row for key, row in read_jsonl(args.baseline_dir / "details.jsonl").items()
        if row.get("label") == "positive"
    }
    new_positive = {
        key: row for key, row in read_jsonl(args.candidate_dir / "details.jsonl").items()
        if row.get("label") == "positive"
    }
    old_bcy = read_jsonl(args.baseline_dir / "canonical-bcy-details.jsonl")
    new_bcy = read_jsonl(args.candidate_dir / "canonical-bcy-details.jsonl")
    metrics = {
        name: paired_cluster_delta(
            old_positive,
            new_positive,
            name,
            bcy=False,
            reps=args.bootstrap_replicates,
            seed=44610 + index,
        )
        for index, name in enumerate(("Recall@5", "Recall@10", "Recall@20", "MRR", "Precision@20"))
    }
    metrics.update({
        f"BCY@{budget}": paired_cluster_delta(
            old_bcy,
            new_bcy,
            str(budget),
            bcy=True,
            reps=args.bootstrap_replicates,
            seed=44620 + index,
        )
        for index, budget in enumerate((4000, 8000, 16000, 32000))
    })
    baseline_summary_path = args.baseline_dir / "summary.json"
    candidate_summary_path = args.candidate_dir / "summary.json"
    baseline_summary = json.loads(baseline_summary_path.read_text(encoding="utf-8"))
    candidate_summary = json.loads(candidate_summary_path.read_text(encoding="utf-8"))
    report = {
        "schema": "wrench.arb-v2.retrieval-iteration-comparison.v1",
        "benchmark": "Agent Retrieval Bench V2 selective natural",
        "comparison": "candidate minus pre-change Wrench run, paired by sample ID and repository-cluster bootstrap",
        "baseline_dir": str(args.baseline_dir.relative_to(PHASE)),
        "candidate_dir": str(args.candidate_dir.relative_to(PHASE)),
        "baseline_source_git_blob_sha1": "0dc7e14e6e1e3f656c7b340e18c5c620d2e89476",
        "candidate_source_sha256": candidate_summary.get("component_source_sha256"),
        "baseline_ranker": baseline_summary.get("ranker", "pre-change raw term hits"),
        "candidate_ranker": candidate_summary.get("ranker"),
        "metrics": metrics,
        "interpretation": "Component comparison only. It does not measure Wrench gate accuracy, client workflow success, or model-level performance.",
    }
    output_path = args.candidate_dir / "iteration-comparison.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
