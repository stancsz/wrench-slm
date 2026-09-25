"""Run a frozen, provider-free E0 read_lines route/executor mechanics screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Direct `python tools/...` execution does not add `src/` to sys.path.
REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from wrench_harness.core import execute_model_output
from wrench_harness.e0_rule_route import run_e0_rule_route
from wrench_harness.mechanical import mechanical_route
from wrench_harness.snapshot import bind_source_root, create_snapshot


JOB_ID = "LOCAL-READLINES-ACCEPT-20260925-03"
NONCE = "RL03-E1F6"
SCHEMA = "wrench.local-read-lines-screen.v1"
CASES = (
    {
        "case_id": "line-a",
        "pair_id": "line-range-fact",
        "prompt": "Read lines 2-3 of src/cache.py.",
        "files": {"src/cache.py": "def is_expired(entry):\n    return entry.expires_at <= 0\n# trailing line\n"},
        "expected_status": "completed",
        "expected_action": "read_lines",
        "expected_lines": ["    return entry.expires_at <= 0", "# trailing line"],
    },
    {
        "case_id": "line-b",
        "pair_id": "line-range-fact",
        "prompt": "Read lines 2-3 of src/cache.py.",
        "files": {"src/cache.py": "def needs_refresh(entry):\n    return entry.expires_at <= 0\n# trailing line\n"},
        "expected_status": "completed",
        "expected_action": "read_lines",
        "expected_lines": ["    return entry.expires_at <= 0", "# trailing line"],
    },
    {
        "case_id": "line-missing",
        "pair_id": "line-availability",
        "prompt": "Read lines 2-3 of src/missing.py.",
        "files": {"src/cache.py": "one\ntwo\nthree\n"},
        "expected_status": "abstain",
        "expected_action": "read_lines",
        "expected_reason": "source_not_in_snapshot",
    },
    {
        "case_id": "line-stale",
        "pair_id": "line-availability",
        "prompt": "Read lines 2-3 of src/cache.py.",
        "files": {"src/cache.py": "one\ntwo\nthree\n"},
        "mutate_after_snapshot": {"src/cache.py": "one\nchanged\nthree\n"},
        "expected_status": "abstain",
        "expected_action": "read_lines",
        "expected_reason": "snapshot_read_changed",
    },
    {
        "case_id": "line-out-of-range",
        "pair_id": "line-bounds",
        "prompt": "Read lines 9-10 of src/cache.py.",
        "files": {"src/cache.py": "one\ntwo\nthree\n"},
        "expected_status": "abstain",
        "expected_action": "read_lines",
        "expected_reason": "line_end_out_of_range",
    },
    {
        "case_id": "line-ambiguous",
        "pair_id": "line-specificity",
        "prompt": "Read lines 2-3 of the relevant file.",
        "files": {"src/cache.py": "one\ntwo\nthree\n"},
        "expected_status": "abstain",
        "expected_action": None,
        "expected_reason": "ambiguous_or_unsupported_request",
    },
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_identity(root: Path) -> tuple[str, int, int]:
    rows: list[list[object]] = []
    total_bytes = 0
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        if path.is_symlink() or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise RuntimeError("fixture_tree_link_or_reparse_point")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            size = path.stat().st_size
            total_bytes += size
            rows.append([relative, size, _sha256(path)])
    encoded = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest(), len(rows), total_bytes


def _write_tree(root: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        target = root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))


def _snapshot(root: Path):
    binding = bind_source_root(root)
    paths = tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))
    return binding, create_snapshot(binding, paths)


def _run_case(base: Path, case: dict[str, object]) -> dict[str, object]:
    case_root = base / str(case["case_id"])
    case_root.mkdir()
    files = case["files"]
    assert isinstance(files, dict)
    _write_tree(case_root, files)
    binding, snapshot = _snapshot(case_root)
    mutation = case.get("mutate_after_snapshot")
    if isinstance(mutation, dict):
        _write_tree(case_root, mutation)

    prompt = str(case["prompt"])
    proposal = mechanical_route(prompt)
    before_sha, before_count, before_bytes = _tree_identity(case_root)
    route_start = time.perf_counter_ns()
    route = run_e0_rule_route(prompt, root_binding=binding, snapshot=snapshot)
    route_ns = time.perf_counter_ns() - route_start

    actual_status = route.status.value
    actual_reason = route.reason
    route_exact = (
        actual_status == case["expected_status"]
        and route.action == case["expected_action"]
    )
    if actual_status == "completed":
        route_exact = route_exact and route.action == case["expected_action"]
        route_exact = route_exact and route.observation == {
            "path": proposal["path"],
            "start": proposal["start"],
            "end": proposal["end"],
            "lines": case["expected_lines"],
        }
    else:
        route_exact = route_exact and route.reason == case.get("expected_reason")

    executor_exact: bool | None = None
    executor_ns: int | None = None
    executor_result: dict[str, object] | None = None
    if actual_status == "completed":
        if not isinstance(proposal, dict) or proposal.get("action") != "read_lines":
            raise RuntimeError("completed_route_has_no_read_lines_prompt_proposal")
        exec_start = time.perf_counter_ns()
        executor_result = execute_model_output(json.dumps(proposal), str(case_root), request_prompt=prompt)
        executor_ns = time.perf_counter_ns() - exec_start
        observation = executor_result.get("observation")
        if isinstance(observation, dict):
            observed_path = Path(str(observation.get("path", "")))
            try:
                observation = {**observation, "path": observed_path.relative_to(case_root).as_posix()}
            except ValueError:
                observation = {**observation, "path": "outside_root"}
        executor_exact = (
            executor_result.get("status") == "accepted"
            and executor_result.get("action") == "read_lines"
            and observation == {
                "path": proposal["path"],
                "start": proposal["start"],
                "end": proposal["end"],
                "lines": case["expected_lines"],
            }
        )

    after_sha, after_count, after_bytes = _tree_identity(case_root)
    unchanged = (before_sha, before_count, before_bytes) == (after_sha, after_count, after_bytes)
    return {
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "expected_status": case["expected_status"],
        "expected_action": case["expected_action"],
        "expected_reason": case.get("expected_reason"),
        "route_status": actual_status,
        "route_action": route.action,
        "route_reason": actual_reason,
        "route_exact": route_exact,
        "executor_called": executor_result is not None,
        "executor_status": executor_result.get("status") if executor_result else None,
        "executor_exact": executor_exact,
        "tree_unchanged_during_operation": unchanged,
        "tree_sha256_before": before_sha,
        "tree_sha256_after": after_sha,
        "tree_file_count": before_count,
        "tree_bytes": before_bytes,
        "route_ns": route_ns,
        "executor_ns": executor_ns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("refusing_to_overwrite_existing_receipt")
    if len(CASES) != 6:
        raise SystemExit("frozen_case_count_changed")
    started = time.perf_counter_ns()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="read-lines-01-", dir=output.parent) as scratch_name:
        scratch = Path(scratch_name)
        cases = [_run_case(scratch, case) for case in CASES]
    completed = sum(case["route_status"] == "completed" for case in cases)
    abstained = sum(case["route_status"] == "abstain" for case in cases)
    executor_called = sum(case["executor_called"] is True for case in cases)
    false_abstentions = sum(case["expected_status"] == "completed" and case["route_status"] == "abstain" for case in cases)
    unresolved = sum(case["route_exact"] is not True or case["executor_exact"] is False for case in cases)
    mutations = sum(case["tree_unchanged_during_operation"] is not True for case in cases)
    report: dict[str, object] = {
        "schema": SCHEMA,
        "job_id": JOB_ID,
        "nonce": NONCE,
        "status": "complete",
        "claim_scope": "open_development_fixture_operation_mechanics_only",
        "repo_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "runner_sha256": _sha256(Path(__file__).resolve()),
        "fixture_sha256": hashlib.sha256(json.dumps(CASES, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest(),
        "case_count": len(cases),
        "route_exact_count": sum(case["route_exact"] is True for case in cases),
        "completed_routes": completed,
        "abstentions": abstained,
        "correct_abstentions": sum(case["expected_status"] == "abstain" and case["route_exact"] is True for case in cases),
        "executor_calls": executor_called,
        "executor_exact_count": sum(case["executor_exact"] is True for case in cases),
        "false_abstentions": false_abstentions,
        "unresolved": unresolved,
        "unexpected_mutations": mutations,
        "unsafe_dispatches": 0,
        "runtime_errors": 0,
        "elapsed_ns": time.perf_counter_ns() - started,
        "cases": cases,
        "frontier_token_savings_percent": None,
        "frontier_usage_pairs": 0,
        "note": "This is not semantic task completion, local SLM quality, real-work utility, or a frontier savings result.",
    }
    serialized = json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(serialized + "\n", encoding="utf-8")
    os.replace(temporary, output)
    print(json.dumps({key: report[key] for key in ("status", "case_count", "route_exact_count", "executor_calls", "executor_exact_count", "correct_abstentions", "false_abstentions", "unresolved", "unexpected_mutations", "runner_sha256")}, sort_keys=True))
    return 0 if unresolved == 0 and mutations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
