#!/usr/bin/env python3
"""Measure deterministic review-only patch draft mechanics on synthetic files."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ARTIFACT_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-local-acceptability").resolve()
TMP_ROOT = ARTIFACT_ROOT / "tmp"

from wrench_harness.worker import WrenchWorker


JOB_ID = "LOCAL-PATCH-WHOLE-LINE-SCREEN-20260925-01"
NONCE = "PWL01-91D7"
PROTOCOL_ID = "wrench.local.patch-whole-line.route-verifier.synthetic.v1"
CASES = (
    {
        "id": "remove_middle_line",
        "files": {"app/local.cfg": b"cache=warm\ntrace=verbose\nretry=2\n"},
        "prompt": "Draft a review-only patch: remove the entire line containing `trace=verbose` from app/local.cfg and do not apply it.",
        "target_files": {"app/local.cfg": b"cache=warm\nretry=2\n"},
    },
    {
        "id": "remove_final_line",
        "files": {"runtime/worker.env": b"MODE=safe\nRETRY=3\nTRACE=full\n"},
        "prompt": "Prepare an unapplied review patch: remove the entire line containing `TRACE=full` from runtime/worker.env.",
        "target_files": {"runtime/worker.env": b"MODE=safe\nRETRY=3\n"},
    },
    {
        "id": "remove_first_line",
        "files": {"profile/session.ini": b"obsolete.theme=amber\nlocale=en-CA\n"},
        "prompt": "For review only, remove the entire line containing `obsolete.theme=amber` in profile/session.ini; leave the file unapplied.",
        "target_files": {"profile/session.ini": b"locale=en-CA\n"},
    },
    {
        "id": "duplicate_matching_lines",
        "files": {"app/local.cfg": b"trace=verbose\ncache=warm\ntrace=verbose\n"},
        "prompt": "Draft a review-only patch: remove the entire line containing `trace=verbose` from app/local.cfg and do not apply it.",
        "target_files": None,
        "expected_boundary_reason": "patch_target_not_unique",
    },
    {
        "id": "missing_matching_line",
        "files": {"runtime/worker.env": b"MODE=safe\nRETRY=3\n"},
        "prompt": "Draft a review-only patch: remove the entire line containing `TRACE=none` from runtime/worker.env and do not apply it.",
        "target_files": None,
        "expected_boundary_reason": "patch_target_not_unique",
    },
    {
        "id": "unterminated_matching_line",
        "files": {"profile/session.ini": b"obsolete.theme=amber"},
        "prompt": "For review only, remove the entire line containing `obsolete.theme=amber` in profile/session.ini; leave the file unapplied.",
        "target_files": None,
        "expected_boundary_reason": "patch_source_format_unsupported",
    },
    {
        "id": "crlf_matching_line",
        "files": {"app/local.cfg": b"cache=warm\r\ntrace=verbose\r\n"},
        "prompt": "Draft a review-only patch: remove the entire line containing `trace=verbose` from app/local.cfg and do not apply it.",
        "target_files": None,
        "expected_boundary_reason": "patch_source_format_unsupported",
    },
    {
        "id": "missing_file",
        "files": {},
        "prompt": "Draft a review-only patch: remove the entire line containing `TRACE=full` from the missing file runtime/missing.env and do not apply it.",
        "target_files": None,
        "expected_boundary_reason": "patch_file_invalid",
    },
    {
        "id": "outside_root",
        "files": {},
        "prompt": "Draft a review-only patch: remove the entire line containing `TRACE=full` from ../outside.env outside the repository and do not apply it.",
        "target_files": None,
        "expected_boundary_reason": "path_outside_allowed_root",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_identity(root: Path) -> tuple[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError("fixture_symlink_unexpected")
        if path.is_file():
            body = path.read_bytes()
            rows.append({"entry_type": "file", "path": path.relative_to(root).as_posix(), "bytes": len(body), "sha256": sha256(body)})
        elif path.is_dir():
            rows.append({"entry_type": "directory", "path": path.relative_to(root).as_posix()})
        else:
            raise RuntimeError("fixture_entry_type_unexpected")
    return sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("ascii")), rows


def target_tree_identity(files: dict[str, bytes] | None) -> tuple[str | None, list[dict[str, Any]] | None]:
    if files is None:
        return None, None
    rows = [
        {"path": path, "bytes": len(body), "sha256": sha256(body)}
        for path, body in sorted(files.items())
    ]
    return sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("ascii")), rows


def apply_single_file_unified_diff(original: bytes, relative_path: str, diff: str) -> bytes:
    """Independently apply the frozen screen's single-hunk UTF-8 diff subset."""
    if type(original) is not bytes or type(relative_path) is not str or type(diff) is not str:
        raise ValueError("diff_application_input_type_invalid")
    old_header = f"--- a/{relative_path}\n"
    new_header = f"+++ b/{relative_path}\n"
    lines = diff.splitlines(keepends=True)
    if len(lines) < 4 or lines[0] != old_header or lines[1] != new_header:
        raise ValueError("diff_path_headers_do_not_match_allowed_file")
    if any(line.startswith(("--- ", "+++ ")) for line in lines[2:]):
        raise ValueError("diff_contains_multiple_file_sections")
    match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n", lines[2])
    if match is None:
        raise ValueError("diff_hunk_header_invalid")
    old_start = int(match.group(1))
    old_count = int(match.group(2) or "1")
    new_start = int(match.group(3))
    new_count = int(match.group(4) or "1")
    old_segment: list[str] = []
    new_segment: list[str] = []
    for line in lines[3:]:
        if not line:
            raise ValueError("diff_line_termination_invalid")
        marker, body = line[0], line[1:]
        if marker == " ":
            old_segment.append(body)
            new_segment.append(body)
        elif marker == "-":
            old_segment.append(body)
        elif marker == "+":
            new_segment.append(body)
        else:
            raise ValueError("diff_marker_invalid")
    if len(old_segment) != old_count or len(new_segment) != new_count:
        raise ValueError("diff_hunk_line_count_mismatch")
    original_lines = original.decode("utf-8").splitlines(keepends=True)
    offset = old_start - 1
    if old_start < 1 or original_lines[offset : offset + old_count] != old_segment:
        raise ValueError("diff_old_hunk_does_not_match_source")
    expected_new_start = old_start if old_count else old_start + 1
    if new_start != expected_new_start:
        raise ValueError("diff_new_hunk_location_invalid")
    updated = original_lines[:offset] + new_segment + original_lines[offset + old_count :]
    if len(updated) != len(original_lines) - old_count + new_count:
        raise ValueError("diff_application_line_count_invalid")
    return "".join(updated).encode("utf-8")


def run_case(case: dict[str, Any], work_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"{case['id']}-", dir=work_root) as name:
        fixture_root = Path(name)
        for relpath, body in case["files"].items():
            target = fixture_root.joinpath(*relpath.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        before_hash, before_rows = tree_identity(fixture_root)
        worker = WrenchWorker(tokenizer=None, model=None, allowed_root=fixture_root)
        started = time.perf_counter_ns()
        result = worker.propose([{"role": "user", "content": case["prompt"]}])
        elapsed_ns = time.perf_counter_ns() - started
        after_hash, after_rows = tree_identity(fixture_root)
        positive = case["target_files"] is not None
        expected_target_hash, expected_target_rows = target_tree_identity(case["target_files"])
        observation = result.get("observation") if isinstance(result.get("observation"), dict) else {}
        raw_proposal = result.get("raw_model_output")
        try:
            proposal = json.loads(raw_proposal) if isinstance(raw_proposal, str) else None
        except json.JSONDecodeError:
            proposal = None
        exact_files = sorted(case["target_files"]) if positive else None
        expected_diff = None
        applied_target_match = False
        exact_diff_match = False
        if positive and isinstance(proposal, dict):
            changed = [path for path in exact_files if case["files"].get(path) != case["target_files"].get(path)]
            if len(changed) != 1 or set(case["files"]) != set(case["target_files"]):
                raise ValueError("frozen_positive_must_change_exactly_one_existing_file")
            relative = changed[0]
            expected_diff = "".join(difflib.unified_diff(
                case["files"][relative].decode("utf-8").splitlines(keepends=True),
                case["target_files"][relative].decode("utf-8").splitlines(keepends=True),
                fromfile=f"a/{relative}", tofile=f"b/{relative}", n=3,
            ))
            if expected_diff and not expected_diff.endswith("\n"):
                expected_diff += "\n"
            observed_diff = proposal.get("diff")
            exact_diff_match = (
                proposal.get("files") == [relative]
                and proposal.get("review_only") is True
                and observed_diff == expected_diff
                and observation.get("files") == [str(fixture_root.joinpath(*relative.split("/")))]
                and observation.get("diff") == expected_diff
                and observation.get("review_only") is True
                and observation.get("applied") is False
                and result.get("status") == "accepted"
                and result.get("action") == "patch_draft"
                and result.get("mechanical_fast_path") is True
                and isinstance(result.get("ttc"), dict)
                and result["ttc"].get("profile") == "deep"
                and result["ttc"].get("passed") is True
            )
            try:
                applied = apply_single_file_unified_diff(case["files"][relative], relative, observed_diff)
                applied_target_match = applied == case["target_files"][relative]
            except (ValueError, TypeError):
                applied_target_match = False
        exact_positive = exact_diff_match and applied_target_match
        boundary_abstained = (
            not positive
            and result.get("status") == "abstain"
            and result.get("action") is None
            and result.get("fallback_reason") == case["expected_boundary_reason"]
            and result.get("mechanical_fast_path") is True
        )
        unchanged = before_hash == after_hash and before_rows == after_rows
        return {
            "case_id": case["id"],
            "prompt_sha256": sha256(case["prompt"].encode("utf-8")),
            "fixture_before": {"tree_sha256": before_hash, "files": before_rows},
            "fixture_after": {"tree_sha256": after_hash, "files": after_rows},
            "fixture_unchanged": unchanged,
            "expected_target_tree_sha256": expected_target_hash,
            "expected_target_files": expected_target_rows,
            "status": result.get("status"),
            "action": result.get("action"),
            "fallback_reason": result.get("fallback_reason"),
            "mechanical_fast_path": result.get("mechanical_fast_path"),
            "proposal_sha256": result.get("ttc", {}).get("base_verifier", {}).get("proposal_sha256") if isinstance(result.get("ttc"), dict) else None,
            "expected_files": exact_files,
            "expected_boundary_reason": case.get("expected_boundary_reason"),
            "expected_diff_sha256": sha256(expected_diff.encode("utf-8")) if expected_diff is not None else None,
            "observed_files": proposal.get("files") if isinstance(proposal, dict) else None,
            "observed_diff_sha256": sha256(proposal["diff"].encode("utf-8")) if isinstance(proposal, dict) and isinstance(proposal.get("diff"), str) else None,
            "exact_diff_match": exact_diff_match,
            "independent_diff_application_matches_target": applied_target_match,
            "positive_exact_oracle_match": exact_positive,
            "boundary_correctly_abstained": boundary_abstained,
            "review_only": observation.get("review_only") if result.get("status") == "accepted" else None,
            "applied": observation.get("applied") if result.get("status") == "accepted" else None,
            "ttc_profile": result.get("ttc", {}).get("profile") if isinstance(result.get("ttc"), dict) else None,
            "ttc_passed": result.get("ttc", {}).get("passed") if isinstance(result.get("ttc"), dict) else None,
            "elapsed_ns": elapsed_ns,
        }


def run(output: Path, work_root: Path) -> dict[str, Any]:
    output = output.resolve()
    work_root = work_root.resolve()
    try:
        output.relative_to(ARTIFACT_ROOT)
        work_root.relative_to(TMP_ROOT)
    except ValueError as exc:
        raise ValueError("receipt_and_scratch_must_remain_under_approved_artifact_roots") from exc
    if work_root == TMP_ROOT or work_root.is_symlink():
        raise ValueError("approved_dedicated_work_root_required")
    if not work_root.exists():
        work_root.mkdir(parents=True)
    if not work_root.is_dir():
        raise ValueError("approved_work_root_must_be_directory")
    if any(work_root.iterdir()):
        raise ValueError("work_root_must_be_empty")
    if output.exists():
        raise FileExistsError("refusing_to_overwrite_existing_receipt")
    protocol_path = ROOT / "docs/evals/wrench-local-acceptability/patch-whole-line-screen-01-protocol.md"
    started = time.perf_counter_ns()
    cases = [run_case(case, work_root) for case in CASES]
    positives = [row for row, case in zip(cases, CASES) if case["target_files"] is not None]
    boundaries = [row for row, case in zip(cases, CASES) if case["target_files"] is None]
    all_unchanged = all(row["fixture_unchanged"] for row in cases)
    passed = (
        all(row["positive_exact_oracle_match"] for row in positives)
        and all(row["boundary_correctly_abstained"] for row in boundaries)
        and all_unchanged
    )
    receipt = {
        "schema": "wrench.local-patch-whole-line-screen.v1",
        "job_id": JOB_ID,
        "nonce": NONCE,
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": sha256(protocol_path.read_bytes()),
        "runner_sha256": sha256(Path(__file__).read_bytes()),
        "mechanical_route_sha256": sha256((ROOT / "src/wrench_harness/mechanical.py").read_bytes()),
        "core_verifier_sha256": sha256((ROOT / "src/wrench_harness/core.py").read_bytes()),
        "ttc_verifier_sha256": sha256((ROOT / "src/wrench_harness/ttc.py").read_bytes()),
        "toolbelt_sha256": sha256((ROOT / "src/wrench_harness/toolbelt.py").read_bytes()),
        "worker_sha256": sha256((ROOT / "src/wrench_harness/worker.py").read_bytes()),
        "repo_head": __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),
        "runtime": sys.version,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "provider_calls": 0,
        "client_calls": 0,
        "case_count": len(cases),
        "positive_count": len(positives),
        "positive_exact_oracle_matches": sum(row["positive_exact_oracle_match"] for row in positives),
        "independent_diff_applications_matching_target": sum(row["independent_diff_application_matches_target"] for row in positives),
        "boundary_count": len(boundaries),
        "boundary_abstentions": sum(row["boundary_correctly_abstained"] for row in boundaries),
        "fixture_trees_unchanged": all_unchanged,
        "status": "PASS_OPEN_DEVELOPMENT_MECHANICS_ONLY" if passed else "FAIL",
        "real_task_utility_claim": False,
        "frontier_token_savings_percent": None,
        "elapsed_ns": time.perf_counter_ns() - started,
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists():
        raise FileExistsError("refusing_to_overwrite_existing_temporary_receipt")
    temporary.write_text(json.dumps(receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if output.exists():
        raise FileExistsError("receipt_appeared_during_measurement")
    temporary.replace(output)
    print(json.dumps({key: receipt[key] for key in (
        "status", "case_count", "positive_exact_oracle_matches",
        "independent_diff_applications_matching_target", "boundary_abstentions",
        "fixture_trees_unchanged", "frontier_token_savings_percent",
    )}, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.output, args.work_root)
    return 0 if receipt["status"] == "PASS_OPEN_DEVELOPMENT_MECHANICS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
