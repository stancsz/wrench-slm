"""Run a predeclared, phase-local SWE-Explore pilot with official metrics.

Wrench is represented by the actual ContextLedger.search retrieval component.
The released successful-trajectory reads are scored as outside explorer
references on the same sampled task IDs. This is not a full-suite leaderboard
submission or an end-to-end patch-solving evaluation.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from statistics import mean

import httpx
import psutil


PHASE = Path(__file__).resolve().parent
EXT = PHASE / "external" / "swe-explore-bench"
UPSTREAM = EXT / "upstream"
DATA = EXT / "data"
BENCH_FILE = DATA / "bench.final.public.jsonl"
ISSUE_MAP_FILE = DATA / "issue_map_and_commits.json"
RUN_DIR = EXT / "runs" / "wrench-contextledger-pilot-18-final"
SCRATCH_ROOT = Path(os.environ.get("WRENCH_SWE_TMP", str(PHASE / "_swe_tmp")))
SAMPLE_FILE = RUN_DIR / "sample-manifest.json"
PREDICTIONS_FILE = RUN_DIR / "predictions.jsonl"
DETAILS_FILE = RUN_DIR / "details.jsonl"
SUMMARY_FILE = RUN_DIR / "summary.json"
SEED = 446
PER_SOURCE = 6
TOP_K_REGIONS = 20
CHUNK_LINES = 32
MAX_ARCHIVE_BYTES = 2 * 1024**3
RESERVE = 0.10
SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resource_sample() -> dict[str, int | str | None]:
    memory = psutil.virtual_memory()
    row: dict[str, int | str | None] = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_free_bytes": int(memory.available),
        "ram_total_bytes": int(memory.total),
        "vram_free_bytes": None,
        "vram_total_bytes": None,
        "disk_free_bytes": shutil.disk_usage(PHASE.drive or Path.cwd()).free,
    }
    output = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
        text=True,
        timeout=5,
    )
    free_mib, total_mib = [int(part.strip()) for part in output.splitlines()[0].split(",", 1)]
    row["vram_free_bytes"] = free_mib * 1024 * 1024
    row["vram_total_bytes"] = total_mib * 1024 * 1024
    return row


def enforce_reserve(row: dict[str, int | str | None]) -> None:
    ram_free, ram_total = row["ram_free_bytes"], row["ram_total_bytes"]
    vram_free, vram_total = row["vram_free_bytes"], row["vram_total_bytes"]
    if not all(isinstance(value, int) for value in (ram_free, ram_total, vram_free, vram_total)):
        raise RuntimeError("Could not measure RAM and VRAM; refusing to run")
    if ram_free < ram_total * RESERVE or vram_free < vram_total * RESERVE:
        raise RuntimeError("10 percent RAM or VRAM reserve would be breached")


def load_rows() -> tuple[list[dict], dict[str, dict]]:
    rows = [json.loads(line) for line in BENCH_FILE.read_text(encoding="utf-8").splitlines()]
    issue_map = json.loads(ISSUE_MAP_FILE.read_text(encoding="utf-8"))
    return rows, issue_map


def source_name(issue: dict) -> str:
    return str(issue["source"]).split("@", 1)[0]


def make_sample(rows: list[dict], issue_map: dict[str, dict], *, full_suite: bool) -> list[dict]:
    if SAMPLE_FILE.exists():
        sample_data = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
        if sample_data.get("full_suite") is not full_suite:
            raise RuntimeError("Existing sample manifest differs from requested evaluation scope")
        return sample_data["cases"]

    if full_suite:
        selected = []
        for row in sorted(rows, key=lambda item: item["instance_id"]):
            iid = row["instance_id"]
            issue = issue_map[iid]
            model_names = {
                read["traj_path"].split("/")[2]
                for regions in row.get("read_step_info", {}).values()
                for read in regions
            }
            selected.append(
                {
                    "instance_id": iid,
                    "source": source_name(issue),
                    "repo": str(issue["repo"]),
                    "base_commit": issue["base_commit"],
                    "outside_trajectory_models": sorted(model_names),
                }
            )
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        sample_receipt = {
            "protocol": "complete SWE-Explore public release",
            "full_suite": True,
            "official_rows": len(rows),
            "selection": "all rows in the pinned benchmark release sorted by instance_id",
            "cases": selected,
        }
        SAMPLE_FILE.write_text(json.dumps(sample_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return selected

    source_ids = sorted({source_name(issue) for issue in issue_map.values()})
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        iid = row["instance_id"]
        issue = issue_map[iid]
        if row.get("ground_truth", {}).get("read_core_regions") and row.get("read_step_info"):
            grouped[source_name(issue)].append(row)

    rng = random.Random(SEED)
    for source in source_ids:
        grouped[source].sort(key=lambda row: row["instance_id"])
        rng.shuffle(grouped[source])

    # Choose six per source, with at most one task from each repository across
    # the complete slice, so a repo cannot dominate the small pilot.
    selected: list[dict] = []
    used_repos: set[str] = set()
    for source in source_ids:
        source_selected = 0
        for row in grouped[source]:
            iid = row["instance_id"]
            issue = issue_map[iid]
            repo = str(issue["repo"])
            if repo in used_repos:
                continue
            model_names = {
                read["traj_path"].split("/")[2]
                for regions in row["read_step_info"].values()
                for read in regions
            }
            selected.append(
                {
                    "instance_id": iid,
                    "source": source,
                    "repo": repo,
                    "base_commit": issue["base_commit"],
                    "outside_trajectory_models": sorted(model_names),
                }
            )
            used_repos.add(repo)
            source_selected += 1
            if source_selected >= PER_SOURCE:
                break
        if source_selected != PER_SOURCE:
            raise RuntimeError(f"Could only select {source_selected} cases for {source}")

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    sample_receipt = {
        "protocol": "SWE-Explore official public rows; 18-case pilot, 6 per source dataset",
        "full_suite": False,
        "seed": SEED,
        "per_source": PER_SOURCE,
        "one_case_per_repo_across_slice": True,
        "selection_uses": ["source dataset", "repository uniqueness", "seeded shuffle"],
        "selection_excludes": ["ground-truth scores", "outside-model scores", "Wrench scores"],
        "cases": selected,
    }
    SAMPLE_FILE.write_text(json.dumps(sample_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return selected


def safe_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, mode="r:gz") as tar:
        members = tar.getmembers()
        if not members:
            raise RuntimeError("GitHub archive was empty")
        # Python's data filter rejects absolute paths and traversal members.
        tar.extractall(destination, members=members, filter="data")
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"Expected one archive root, found {len(roots)}")
    return roots[0]


def fetch_snapshot(client: httpx.Client, repo: str, commit: str, scratch: Path) -> Path:
    owner, name = repo.split("/", 1)
    url = f"https://github.com/{owner}/{name}/archive/{commit}.tar.gz"
    archive = scratch / "snapshot.tar.gz"
    size = 0
    with client.stream("GET", url, timeout=180.0) as response:
        response.raise_for_status()
        with archive.open("wb") as output:
            for chunk in response.iter_bytes(1024 * 1024):
                size += len(chunk)
                if size > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("archive exceeded the 2 GiB per-case safety cap")
                output.write(chunk)
    return safe_extract(archive, scratch / "repo")


def iter_text_files(repo_root: Path):
    for base, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(base) / filename
            try:
                if path.is_symlink() or path.stat().st_size > 1_000_000:
                    continue
                raw = path.read_bytes()
                if b"\0" in raw:
                    continue
                text = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            relpath = path.relative_to(repo_root).as_posix()
            lines = text.splitlines()
            if lines:
                yield relpath, lines


def count_lines(repo_root: Path, paths: set[str]) -> dict[str, int]:
    """Count all benchmark-referenced file lines, including files too large to index."""
    counts: dict[str, int] = {}
    for relpath in paths:
        candidate = repo_root.joinpath(*PurePosixPath(relpath).parts)
        try:
            if not candidate.is_file() or candidate.is_symlink():
                counts[relpath] = 0
                continue
            line_count = 0
            final_byte: bytes = b""
            with candidate.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    line_count += block.count(b"\n")
                    final_byte = block[-1:]
            if final_byte and final_byte != b"\n":
                line_count += 1
            counts[relpath] = line_count
        except OSError:
            counts[relpath] = 0
    return counts


def wrench_predictions(repo_root: Path, issue: str, needed_paths: set[str]):
    from wrench_harness.context import ContextLedger

    ledger = ContextLedger(max_logical_tokens=1_000_000_000)
    segment_meta: dict[str, tuple[str, int, int]] = {}
    line_counts: dict[str, int] = {}
    source_order = 0
    candidate_files = 0
    for relpath, lines in iter_text_files(repo_root):
        line_counts[relpath] = len(lines)
        candidate_files += 1
        for start_idx in range(0, len(lines), CHUNK_LINES):
            chunk = lines[start_idx : start_idx + CHUNK_LINES]
            text = "\n".join(chunk)
            if not re.search(r"\w", text, re.UNICODE):
                continue
            start_line = start_idx + 1
            end_line = start_idx + len(chunk)
            segment_id = f"{source_order}:{relpath}:{start_line}"
            ledger.add_segment(
                segment_id,
                text,
                source_order,
                role="context",
                kind="repository_line_window",
                metadata={"path": relpath, "start": str(start_line), "end": str(end_line)},
            )
            segment_meta[segment_id] = (relpath, start_line, end_line)
            source_order += 1
    ranked = ledger.search(issue, limit=10_000)
    preds = [segment_meta[row.segment_id] for row in ranked[:TOP_K_REGIONS]]
    line_counts.update(count_lines(repo_root, needed_paths))
    return preds, line_counts, {"candidate_files": candidate_files, "candidate_regions": source_order, "matched_regions": len(ranked), "index_tokens": ledger.logical_token_count}


def outside_trajectories(bench_row: dict) -> dict[str, list[tuple[str, int, int]]]:
    grouped: dict[str, dict[int, tuple[str, int, int]]] = defaultdict(dict)
    for path, reads in bench_row.get("read_step_info", {}).items():
        for read in reads:
            trajectory = str(read["traj_path"])
            model = trajectory.split("/")[2]
            step = int(read["step_idx"])
            start, end = int(read["start"]), int(read["end"])
            key = (path, start, end)
            grouped[model].setdefault(step * 1_000_000 + len(grouped[model]), key)
    result = {}
    for model, by_order in grouped.items():
        unique: list[tuple[str, int, int]] = []
        seen: set[tuple[str, int, int]] = set()
        for _, region in sorted(by_order.items()):
            if region not in seen:
                seen.add(region)
                unique.append(region)
            if len(unique) >= TOP_K_REGIONS:
                break
        result[model] = unique
    return result


def evaluate_regions(evaluator, iid: str, line_counts: dict[str, int], regions: list[tuple[str, int, int]]) -> dict[str, float]:
    evaluator._current_instance_id = iid
    evaluator._current_file_line_counts = line_counts
    gt = evaluator.bench_data_dict[iid]["ground_truth"]
    metric_names = [
        "precision", "recall", "f1_score", "hit_file_rate", "hit_region_rate",
        "noise_file_rate", "noise_region_rate", "weighted_core_coverage",
        "context_efficiency", "ndcg_at_100", "ndcg_at_300", "ndcg_at_500",
        "recall_at_100", "recall_at_300", "recall_at_500", "first_useful_hit",
    ]
    return {name: getattr(evaluator, f"evaluate_{name}")(regions, gt) for name in metric_names}


def paired_cluster_intervals(case_values: dict[str, dict[str, dict[str, float]]], reference: str, repo_by_iid: dict[str, str]) -> dict[str, dict[str, float | list[float]]]:
    common = [
        iid for iid, systems in case_values.items()
        if "wrench_contextledger_search" in systems and reference in systems
    ]
    if not common:
        return {}
    grouped: dict[str, list[str]] = defaultdict(list)
    for iid in common:
        grouped[repo_by_iid[iid]].append(iid)
    repo_names = sorted(grouped)
    rng = random.Random(SEED)
    out: dict[str, dict[str, float | list[float]]] = {}
    metric_names = ["precision", "recall", "f1_score", "hit_file_rate", "hit_region_rate", "context_efficiency", "ndcg_at_500"]
    for metric in metric_names:
        diffs_by_repo = {
            repo: [case_values[iid]["wrench_contextledger_search"][metric] - case_values[iid][reference][metric] for iid in grouped[repo]]
            for repo in repo_names
        }
        diffs = [value for repo_diffs in diffs_by_repo.values() for value in repo_diffs]
        bootstrap_means = []
        for _ in range(10_000):
            drawn_repos = [repo_names[rng.randrange(len(repo_names))] for _ in repo_names]
            sample = [value for repo in drawn_repos for value in diffs_by_repo[repo]]
            bootstrap_means.append(mean(sample))
        bootstrap_means.sort()
        out[metric] = {
            "n_paired": len(diffs),
            "mean_wrench_minus_reference": mean(diffs),
            "bootstrap_95_ci": [bootstrap_means[249], bootstrap_means[9749]],
            "bootstrap": f"paired repo-cluster bootstrap, 10000 resamples, seed {SEED}; {len(repo_names)} unique repos",
        }
    return out


def main() -> int:
    global RUN_DIR, SAMPLE_FILE, PREDICTIONS_FILE, DETAILS_FILE, SUMMARY_FILE
    import argparse

    wrench_source = PHASE.parent.parent / "src" / "wrench_harness" / "context.py"
    wrench_source_sha256_at_start = sha256_file(wrench_source)
    wrench_source_git_blob_at_start = subprocess.check_output(
        ["git", "-C", str(PHASE.parent.parent), "hash-object", str(wrench_source)], text=True
    ).strip()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-suite", action="store_true", help="score all 848 official tasks sequentially")
    args = parser.parse_args()
    if args.full_suite:
        RUN_DIR = EXT / "runs" / "wrench-contextledger-full848-v1"
        SAMPLE_FILE = RUN_DIR / "sample-manifest.json"
        PREDICTIONS_FILE = RUN_DIR / "predictions.jsonl"
        DETAILS_FILE = RUN_DIR / "details.jsonl"
        SUMMARY_FILE = RUN_DIR / "summary.json"
    before = resource_sample()
    enforce_reserve(before)
    rows, issue_map = load_rows()
    bench_by_id = {row["instance_id"]: row for row in rows}
    sample = make_sample(rows, issue_map, full_suite=args.full_suite)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(PHASE.parent.parent / "src"))
    sys.path.insert(0, str(UPSTREAM))
    from eval import ExploreEvaluator

    evaluator = ExploreEvaluator(BENCH_FILE)
    metrics_by_method: dict[str, list[dict[str, float]]] = defaultdict(list)
    metrics_by_case: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    receipts: list[dict] = []
    errors: list[dict[str, str]] = []
    started = time.perf_counter()
    with PREDICTIONS_FILE.open("w", encoding="utf-8") as predictions_out, DETAILS_FILE.open("w", encoding="utf-8") as details_out, httpx.Client(follow_redirects=True, headers={"User-Agent": "Wrench-SWE-Explore-Evaluation/1.0"}) as client:
        for case_idx, selected in enumerate(sample, start=1):
            iid = selected["instance_id"]
            issue = issue_map[iid]
            bench_row = bench_by_id[iid]
            resources = resource_sample()
            enforce_reserve(resources)
            if int(resources["disk_free_bytes"] or 0) < 5 * 1024**3:
                raise RuntimeError("Less than 5 GiB disk free; refusing to fetch repository snapshot")
            case_started = time.perf_counter()
            try:
                with tempfile.TemporaryDirectory(prefix="s-", dir=SCRATCH_ROOT) as scratch_name:
                    scratch = Path(scratch_name)
                    repo_root = fetch_snapshot(client, issue["repo"], issue["base_commit"], scratch)
                    outside = outside_trajectories(bench_row)
                    needed_paths = set(bench_row.get("ground_truth", {}).get("read_core_files", []))
                    ground_truth = bench_row.get("ground_truth", {})
                    for region in ground_truth.get("read_core_regions", []):
                        needed_paths.add(str(region["path"]))
                    for regions in (ground_truth.get("read_optional_regions_map", {}) or {}).values():
                        for region in regions:
                            needed_paths.add(str(region["path"]))
                    for regions in outside.values():
                        needed_paths.update(region[0] for region in regions)
                    wrench_regions, line_counts, index_receipt = wrench_predictions(repo_root, issue["problem_statement"], needed_paths)
                    wrench_metrics = evaluate_regions(evaluator, iid, line_counts, wrench_regions)
                    metrics_by_method["wrench_contextledger_search"].append(wrench_metrics)
                    metrics_by_case[iid]["wrench_contextledger_search"] = wrench_metrics
                    out_row = {
                        "instance_id": iid,
                        "system": "wrench_contextledger_search",
                        "regions": wrench_regions,
                        "metrics": wrench_metrics,
                    }
                    predictions_out.write(json.dumps(out_row, ensure_ascii=False) + "\n")

                    case_outside = {}
                    for model, regions in outside.items():
                        values = evaluate_regions(evaluator, iid, line_counts, regions)
                        method = f"trajectory:{model}"
                        metrics_by_method[method].append(values)
                        metrics_by_case[iid][method] = values
                        case_outside[model] = {"regions": regions, "metrics": values}
                        predictions_out.write(json.dumps({"instance_id": iid, "system": method, "regions": regions, "metrics": values}, ensure_ascii=False) + "\n")
                    detail = {
                        **selected,
                        "problem_statement_sha256": hashlib.sha256(issue["problem_statement"].encode("utf-8")).hexdigest(),
                        "snapshot_source": f"https://github.com/{issue['repo']}/archive/{issue['base_commit']}.tar.gz",
                        "file_line_count": len(line_counts),
                        "index": index_receipt,
                        "wrench": {"regions": wrench_regions, "metrics": wrench_metrics},
                        "outside_trajectories": case_outside,
                        "elapsed_seconds": time.perf_counter() - case_started,
                        "resources_before": resources,
                    }
                    details_out.write(json.dumps(detail, ensure_ascii=False) + "\n")
                    receipts.append({"instance_id": iid, "status": "scored", "repo": issue["repo"], "base_commit": issue["base_commit"], "elapsed_seconds": detail["elapsed_seconds"], **index_receipt})
            except Exception as exc:
                errors.append({"instance_id": iid, "repo": issue["repo"], "base_commit": issue["base_commit"], "error": f"{type(exc).__name__}: {exc}"})
                details_out.write(json.dumps({**selected, "status": "error", "error": errors[-1]["error"]}, ensure_ascii=False) + "\n")
                print(f"[{case_idx}/{len(sample)}] FAILED {iid}: {errors[-1]['error']}", flush=True)
            else:
                print(f"[{case_idx}/{len(sample)}] scored {iid} in {receipts[-1]['elapsed_seconds']:.1f}s", flush=True)

    means = {name: {metric: mean(row[metric] for row in rows_for_method) for metric in rows_for_method[0]} for name, rows_for_method in metrics_by_method.items() if rows_for_method}
    summary = {
        "schema": "wrench.swe-explore.contextledger-pilot.v1",
        "benchmark": "SWE-Explore-Bench",
        "scope": "complete 848-case exact-snapshot run" if args.full_suite else "18-case stratified, exact-snapshot pilot",
        "wrench_component": "ContextLedger.search; component score, not complete agent workflow",
        "official_suite_rows": len(rows),
        "pilot_rows": len(sample),
        "scored_rows": len(receipts),
        "failed_rows": len(errors),
        "sample_seed": None if args.full_suite else SEED,
        "sample_per_source": None if args.full_suite else PER_SOURCE,
        "top_k_regions": TOP_K_REGIONS,
        "wrench_chunk_lines": CHUNK_LINES,
        "outside_methods": "public successful-trajectory read sequences included with SWE-Explore; score references, not newly inferred model completions",
        "mean_metrics_by_system": means,
        "systems_case_counts": {name: len(values) for name, values in metrics_by_method.items()},
        "paired_wrench_minus_outside_trajectory_bootstrap": {
            method: paired_cluster_intervals(metrics_by_case, method, {row["instance_id"]: row["repo"] for row in sample})
            for method in sorted({name for systems in metrics_by_case.values() for name in systems if name != "wrench_contextledger_search"})
        },
        "case_receipts": receipts,
        "errors": errors,
        "wall_seconds": time.perf_counter() - started,
        "input_sha256": {"benchmark": sha256_file(BENCH_FILE), "issue_commit_map": sha256_file(ISSUE_MAP_FILE), "sample_manifest": sha256_file(SAMPLE_FILE)},
        "wrench_source_sha256_at_start": wrench_source_sha256_at_start,
        "wrench_source_git_blob_sha1_at_start": wrench_source_git_blob_at_start,
        "official_code_commit": "5602f031f2d9562d0a805f83402b536e831a5a11",
        "resource_after": resource_sample(),
        "resource_guard": "sequential exact-commit snapshots; 10 percent RAM and VRAM reserve checked before each case; temp snapshot deleted after each case",
        "limitations": [
            "This is a development pilot, not the official 848-case leaderboard result." if not args.full_suite else "This is a full data-split component run, not an official leaderboard submission.",
            "ContextLedger.search is a real Wrench retrieval component, not the complete agent workflow.",
            "Trajectory references are saved reads from released solved runs; they are not fresh model calls.",
            "An independent direct outside-model inference run remains outstanding.",
        ],
    }
    enforce_reserve(summary["resource_after"])
    SUMMARY_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("pilot_rows", "scored_rows", "failed_rows", "mean_metrics_by_system", "systems_case_counts", "wall_seconds")}, ensure_ascii=False, indent=2))
    return 0 if receipts else 2


if __name__ == "__main__":
    raise SystemExit(main())
