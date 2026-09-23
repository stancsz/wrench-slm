"""Score Wrench's read-only context retrieval on ContextBench's public test split.

This is a retrieval-component result, not an agent Pass@1 result. It emits the
trajectory schema consumed by ContextBench's pinned evaluator and calls that
evaluator directly against exact repository snapshots.
"""

from __future__ import annotations

import hashlib
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import httpx
import psutil
import pyarrow.parquet as pq


PHASE = Path(__file__).resolve().parent
EXT = PHASE / "external" / "contextbench"
UPSTREAM = EXT / "upstream"
DATA_FILE = EXT / "data" / "data" / "contextbench_verified.parquet"
RUN = EXT / "runs" / "wrench-verified500-contextledger-v1"
SCRATCH = Path(os.environ.get("WRENCH_CONTEXT_TMP", str(EXT / "_scratch")))
MAX_ARCHIVE_BYTES = 2 * 1024**3
MAX_FILE_BYTES = 1_000_000
CHUNK_LINES = 32
TOP_K = 20
RESERVE = 0.10
SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__"}
CONTEXT_LEDGER_CLASS = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sample_resources() -> dict:
    vm = psutil.virtual_memory()
    free_vram, total_vram = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.free,memory.total", "--format=csv,noheader,nounits"],
        text=True,
        timeout=5,
    ).splitlines()[0].split(",", 1)
    return {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "ram_free_bytes": int(vm.available),
        "ram_total_bytes": int(vm.total),
        "vram_free_bytes": int(free_vram.strip()) * 1024 * 1024,
        "vram_total_bytes": int(total_vram.strip()) * 1024 * 1024,
        "disk_free_bytes": shutil.disk_usage(PHASE.drive or Path.cwd()).free,
    }


def enforce_reserve(sample: dict) -> None:
    if sample["ram_free_bytes"] < sample["ram_total_bytes"] * RESERVE:
        raise RuntimeError("10 percent RAM reserve would be breached")
    if sample["vram_free_bytes"] < sample["vram_total_bytes"] * RESERVE:
        raise RuntimeError("10 percent VRAM reserve would be breached")
    if sample["disk_free_bytes"] < 5 * 1024**3:
        raise RuntimeError("Less than 5 GiB disk reserve remains")


def read_cases() -> list[dict]:
    cases = pq.read_table(DATA_FILE).to_pylist()
    cases.sort(key=lambda row: (str(row["repo"]), str(row["base_commit"]), str(row["instance_id"])))
    return cases


def snapshot_repository(row: dict) -> str:
    """Resolve dataset aliases to the repository that owns the pinned commit."""
    if row["repo"] != "fasterxml/jackson":
        return str(row["repo"])
    try:
        owner, module_and_issue = str(row["original_inst_id"]).split("__", 1)
        module, issue = module_and_issue.rsplit("-", 1)
    except ValueError as exc:
        raise RuntimeError(f"Cannot resolve Jackson module repository for {row['instance_id']}") from exc
    if owner.casefold() != "fasterxml" or not module.startswith("jackson-") or not issue.isdigit():
        raise RuntimeError(f"Unexpected Jackson source instance ID: {row['original_inst_id']}")
    return f"FasterXML/{module}"


def safe_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as stream:
        members = stream.getmembers()
        if not members:
            raise RuntimeError("GitHub archive was empty")
        stream.extractall(destination, members=members, filter="data")
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RuntimeError(f"Expected one archive root, found {len(roots)}")
    return roots[0]


def fetch_snapshot(client: httpx.Client, repo: str, commit: str, scratch: Path) -> Path:
    owner, name = repo.split("/", 1)
    archive = scratch / "snapshot.tar.gz"
    size = 0
    url = f"https://github.com/{owner}/{name}/archive/{commit}.tar.gz"
    with client.stream("GET", url, timeout=180.0) as response:
        response.raise_for_status()
        with archive.open("wb") as output:
            for block in response.iter_bytes(1024 * 1024):
                size += len(block)
                if size > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("Repository archive exceeded the 2 GiB safety cap")
                output.write(block)
    root = safe_extract(archive, scratch / "repo")
    archive.unlink(missing_ok=True)
    return root


def wrench_context(repo_root: Path, issue: str) -> tuple[dict, dict]:
    if CONTEXT_LEDGER_CLASS is None:
        raise RuntimeError("ContextLedger implementation was not loaded")
    ledger = CONTEXT_LEDGER_CLASS()
    segment_metadata: dict[str, tuple[str, int, int]] = {}
    source_order = 0
    indexed_files = 0

    for base, directories, filenames in os.walk(repo_root):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS)
        for filename in sorted(filenames):
            path = Path(base) / filename
            try:
                if path.is_symlink() or path.stat().st_size > MAX_FILE_BYTES:
                    continue
                raw = path.read_bytes()
                if b"\0" in raw:
                    continue
                lines = raw.decode("utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            if not lines:
                continue
            relpath = path.relative_to(repo_root).as_posix()
            indexed_files += 1
            for offset in range(0, len(lines), CHUNK_LINES):
                chunk = "\n".join(lines[offset : offset + CHUNK_LINES])
                if not re.search(r"\w", chunk, re.UNICODE):
                    continue
                start, end = offset + 1, min(offset + CHUNK_LINES, len(lines))
                segment_id = f"{source_order}:{relpath}:{start}"
                try:
                    ledger.add_segment(
                        segment_id,
                        chunk,
                        source_order,
                        role="context",
                        kind="repository_line_window",
                        metadata={"path": relpath, "start": str(start), "end": str(end)},
                    )
                except Exception as exc:
                    if "logical_context_limit_exceeded" in str(exc):
                        break
                    raise
                segment_metadata[segment_id] = (relpath, start, end)
                source_order += 1
                if source_order % 250 == 0:
                    enforce_reserve(sample_resources())

    ranked = ledger.search(issue, limit=TOP_K)
    regions = [segment_metadata[row.segment_id] for row in ranked]
    spans_by_file: dict[str, list[dict[str, int]]] = {}
    for path, start, end in regions:
        spans_by_file.setdefault(path, []).append({"start": start, "end": end})
    files = sorted(spans_by_file)
    # Preserve ranked evidence in cumulative checkpoints for ContextBench AUC.
    steps = []
    for budget in (5, 10, TOP_K):
        spans: dict[str, list[dict[str, int]]] = {}
        for path, start, end in regions[:budget]:
            spans.setdefault(path, []).append({"start": start, "end": end})
        steps.append({"files": sorted(spans), "spans": spans})
    trajectory = {
        "pred_steps": steps,
        "pred_files": files,
        "pred_spans": spans_by_file,
        "pred_symbols": {},
    }
    return trajectory, {
        "indexed_files": indexed_files,
        "indexed_regions": source_order,
        "matched_regions": len(ranked),
        "logical_tokens": ledger.logical_token_count,
        "region_budget": TOP_K,
    }


def load_official_modules():
    import sys

    sys.path.insert(0, str(PHASE.parent.parent / "src"))
    sys.path.insert(0, str(UPSTREAM))
    from contextbench import evaluate
    from contextbench import extractors
    from contextbench.parsers.gold import Gold

    # Tree-sitter grammars are unavailable in the host's Python 3.14 runtime.
    # The published ContextBench leaderboard's retrieval metrics are line-level.
    # Keep its evaluator for line/file/span metrics, while explicitly disabling
    # AST-symbol extraction and removing those fields from the stored receipt.
    extractors.extract_def_set_in_spans = lambda _spans, _repo: set()
    extractors.extract_def_set_from_symbol_names = lambda _symbols, _repo: set()
    evaluate.extract_def_set_in_spans = extractors.extract_def_set_in_spans
    evaluate.extract_def_set_from_symbol_names = extractors.extract_def_set_from_symbol_names

    return evaluate, Gold


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0, help="Score only the first N cases for a resumable pilot")
    parser.add_argument(
        "--context-source",
        type=Path,
        default=PHASE.parent.parent / "src" / "wrench_harness" / "context.py",
        help="ContextLedger source file to load and bind into the receipt",
    )
    args = parser.parse_args()
    source_path = args.context_source.resolve()
    if not source_path.is_file():
        raise RuntimeError(f"ContextLedger source file does not exist: {source_path}")
    source_sha256_at_start = sha256_file(source_path)
    source_git_blob_at_start = subprocess.check_output(
        ["git", "-C", str(PHASE.parent.parent), "hash-object", str(source_path)], text=True
    ).strip()

    # Load the exact component source requested for this run. This lets a
    # resumed baseline use its pinned source without replacing dirty working
    # tree files or mixing in a later candidate implementation.
    spec = importlib.util.spec_from_file_location("_wrench_contextbench_context", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load ContextLedger source: {source_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    global CONTEXT_LEDGER_CLASS
    CONTEXT_LEDGER_CLASS = module.ContextLedger
    RUN.mkdir(parents=True, exist_ok=True)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cases = read_cases()
    if len(cases) != 500 or len({row["instance_id"] for row in cases}) != 500:
        raise RuntimeError(f"Expected 500 unique ContextBench verified rows, got {len(cases)}")
    manifest_path = RUN / "sample-manifest.json"
    manifest = {
        "protocol": "ContextBench verified 500-row subset, Wrench retrieval component",
        "case_count": len(cases),
        "selection": "all rows from pinned contextbench_verified.parquet, sorted by repo, base_commit, instance_id",
        "dataset": "external/contextbench/data/data/contextbench_verified.parquet",
        "dataset_sha256": sha256_file(DATA_FILE),
        "wrench_source_sha256_at_start": source_sha256_at_start,
        "wrench_source_git_blob_sha1_at_start": source_git_blob_at_start,
        "upstream_commit": subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip(),
        "region_budget": TOP_K,
        "chunk_lines": CHUNK_LINES,
        "cases": [
            {"instance_id": row["instance_id"], "original_inst_id": row["original_inst_id"],
             "repo": row["repo"], "snapshot_repo": snapshot_repository(row),
             "base_commit": row["base_commit"], "source": row["source"], "language": row["language"]}
            for row in cases
        ],
    }
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing != manifest:
            raise RuntimeError("Existing ContextBench sample manifest differs from pinned input")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evaluate, Gold = load_official_modules()
    predictions_path = RUN / "predictions.jsonl"
    details_path = RUN / "details.jsonl"
    exclusions_path = RUN / "exclusions.jsonl"
    summary_path = RUN / "summary.json"
    completed: set[str] = set()
    results: list[dict] = []
    if details_path.exists():
        for line in details_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                result = json.loads(line)
                completed.add(result["instance_id"])
                results.append(result)
    excluded: dict[str, dict] = {}
    if exclusions_path.exists():
        for line in exclusions_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                result = json.loads(line)
                excluded[result["instance_id"]] = result

    resources: list[dict] = []
    grouped: dict[tuple[str, str], list[dict]] = {}
    run_cases = cases[:args.limit] if args.limit > 0 else cases
    for row in run_cases:
        grouped.setdefault((snapshot_repository(row), row["base_commit"]), []).append(row)

    with httpx.Client(follow_redirects=True, headers={"User-Agent": "Wrench-ContextBench-Adapter/1.0"}) as client:
        for (repo, commit), group in grouped.items():
            pending = [row for row in group if row["instance_id"] not in completed and row["instance_id"] not in excluded]
            if not pending:
                continue
            resources.append(sample_resources())
            enforce_reserve(resources[-1])
            with tempfile.TemporaryDirectory(prefix="cb-", dir=SCRATCH) as temp:
                try:
                    snapshot = fetch_snapshot(client, repo, commit, Path(temp))
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code != 404:
                        raise
                    # A missing pinned commit is an explicit unavailable case,
                    # not a retrieval miss. Preserve its source identity and
                    # keep it out of the scored-row denominator.
                    for row in pending:
                        result = {
                            "instance_id": row["instance_id"],
                            "dataset_repo": row["repo"],
                            "snapshot_repo": repo,
                            "commit": commit,
                            "status": "excluded_unavailable_pinned_snapshot",
                            "http_status": 404,
                            "error": str(exc)[:1000],
                            "url": str(exc.request.url),
                        }
                        with exclusions_path.open("a", encoding="utf-8") as output:
                            output.write(json.dumps(result, ensure_ascii=False) + "\n")
                            output.flush()
                            os.fsync(output.fileno())
                        excluded[result["instance_id"]] = result
                    print(f"[{len(completed) + len(excluded)}/{len(cases)}] excluded {len(pending)} row(s): pinned snapshot unavailable, {repo}@{commit}", flush=True)
                    continue
                # The official evaluator stays intact; only checkout is redirected
                # to the exact GitHub archive already fetched by this adapter.
                evaluate.checkout = lambda _url, _commit, _cache: str(snapshot)
                for row in pending:
                    resources.append(sample_resources())
                    enforce_reserve(resources[-1])
                    started = time.perf_counter()
                    trajectory, index_receipt = wrench_context(snapshot, row["problem_statement"])
                    inst_id = row["instance_id"]
                    gold_context = json.loads(row["gold_context"]) if isinstance(row["gold_context"], str) else row["gold_context"]
                    # Deliberately omit patch/test data. This run scores retrieval,
                    # not EditLoc or task-solving with oracle patch information.
                    gold = Gold({"inst_id": inst_id, "original_inst_id": row["original_inst_id"],
                                 "repo_url": f"https://github.com/{repo}.git", "commit": commit,
                                 "gold_ctx": gold_context, "patch": "", "test_patch": ""})
                    pred = {"instance_id": inst_id, "repo_url": f"https://github.com/{repo}.git",
                            "commit": commit, "traj_data": trajectory, "model_patch": ""}
                    result = evaluate.evaluate_instance(inst_id, gold, pred, str(RUN / "cache"))
                    result.get("final", {}).pop("symbol", None)
                    trajectory_result = result.get("trajectory", {})
                    trajectory_result.get("auc_coverage", {}).pop("symbol", None)
                    trajectory_result.get("redundancy", {}).pop("symbol", None)
                    for step in trajectory_result.get("steps", []):
                        step.get("coverage", {}).pop("symbol", None)
                    result["adapter"] = index_receipt
                    result["retrieval_seconds"] = round(time.perf_counter() - started, 3)
                    result["repo"] = row["repo"]
                    result["snapshot_repo"] = repo
                    result["commit"] = commit
                    with predictions_path.open("a", encoding="utf-8") as output:
                        output.write(json.dumps(pred, ensure_ascii=False) + "\n")
                        output.flush()
                        os.fsync(output.fileno())
                    with details_path.open("a", encoding="utf-8") as output:
                        output.write(json.dumps(result, ensure_ascii=False) + "\n")
                        output.flush()
                        os.fsync(output.fileno())
                    results.append(result)
                    completed.add(inst_id)
                    print(f"[{len(completed)}/{len(cases)}] scored {inst_id} in {result['retrieval_seconds']:.1f}s", flush=True)

    aggregate = evaluate.aggregate_results(results)
    summary = {
        "protocol": manifest["protocol"],
        "dataset_sha256": manifest["dataset_sha256"],
        "upstream_commit": manifest["upstream_commit"],
        "case_count": len(cases),
        "scored_count": len(completed),
        "excluded_count": len(excluded),
        "excluded_instances": list(excluded.values()),
        "processed_input_count": len(completed) + len(excluded),
        "component": "src/wrench_harness/context.py::ContextLedger.search",
        "scope_limit": "retrieval component only; no solver, Pass@1, or provider model call; AST-symbol metrics omitted because tree-sitter grammars are unavailable on the host",
        "official_aggregate": aggregate,
        "line_context_f1": (
            2 * aggregate["final_line"]["coverage"] * aggregate["final_line"]["precision"]
            / (aggregate["final_line"]["coverage"] + aggregate["final_line"]["precision"])
            if aggregate.get("final_line") and (aggregate["final_line"]["coverage"] + aggregate["final_line"]["precision"]) else 0.0
        ),
        "resource_minimums": {
            "ram_free_bytes": min(row["ram_free_bytes"] for row in resources),
            "vram_free_bytes": min(row["vram_free_bytes"] for row in resources),
            "disk_free_bytes": min(row["disk_free_bytes"] for row in resources),
        } if resources else {},
        "complete": len(completed) == len(cases),
        "all_input_rows_accounted_for": len(completed) + len(excluded) == len(cases),
        "predictions_sha256": sha256_file(predictions_path),
        "details_sha256": sha256_file(details_path),
        "exclusions_sha256": sha256_file(exclusions_path) if exclusions_path.exists() else None,
        "wrench_source_sha256": source_sha256_at_start,
        "wrench_source_git_blob_sha1": source_git_blob_at_start,
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)
    return 0 if summary["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
