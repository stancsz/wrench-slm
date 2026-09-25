#!/usr/bin/env python3
"""Run the frozen synthetic review-only patch-draft mechanics screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wrench_harness.worker import WrenchWorker


PROTOCOL_ID = "wrench.local.patch-draft.route-verifier.synthetic.v1"
CASES = (
    {
        "id": "replace_unique",
        "files": {"settings.txt": b"mode=old\n"},
        "prompt": "Draft a review-only change replacing `mode=old` with `mode=new` in settings.txt and do not apply it.",
        "expected_files": ["settings.txt"],
        "expected_diff": "--- a/settings.txt\n+++ b/settings.txt\n@@ -1 +1 @@\n-mode=old\n+mode=new\n",
    },
    {
        "id": "append_line",
        "files": {"notes.txt": b"start\n"},
        "prompt": "Draft a review-only patch append `finish=1` to notes.txt and leave the file unchanged.",
        "expected_files": ["notes.txt"],
        "expected_diff": "--- a/notes.txt\n+++ b/notes.txt\n@@ -1 +1,2 @@\n start\n+finish=1\n",
    },
    {
        "id": "insert_after_unique",
        "files": {"config.txt": b"alpha\nomega\n"},
        "prompt": "Draft a review-only change insert `middle` after the unique text `alpha` in config.txt and do not apply it.",
        "expected_files": ["config.txt"],
        "expected_diff": "--- a/config.txt\n+++ b/config.txt\n@@ -1,2 +1,3 @@\n alpha\n+middle\n omega\n",
    },
    {
        "id": "duplicate_target",
        "files": {"settings.txt": b"mode=old\nmode=old\n"},
        "prompt": "Draft a review-only change replacing `mode=old` with `mode=new` in settings.txt and do not apply it.",
        "expected_files": None,
        "expected_diff": None,
    },
    {
        "id": "missing_file",
        "files": {},
        "prompt": "Draft a review-only change replacing `mode=old` with `mode=new` in missing.txt and do not apply it.",
        "expected_files": None,
        "expected_diff": None,
    },
    {
        "id": "no_review_authority",
        "files": {"settings.txt": b"mode=old\n"},
        "prompt": "Replace `mode=old` with `mode=new` in settings.txt.",
        "expected_files": None,
        "expected_diff": None,
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tree_identity(root: Path) -> tuple[str, list[dict[str, Any]]]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError("fixture_symlink_unexpected")
        if path.is_file():
            body = path.read_bytes()
            rows.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": len(body),
                    "sha256": sha256(body),
                }
            )
        elif not path.is_dir():
            raise RuntimeError("fixture_entry_type_unexpected")
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("ascii")
    return sha256(canonical), rows


def run_case(case: dict[str, Any], work_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"{case['id']}-", dir=work_root) as scratch:
        fixture_root = Path(scratch)
        for relpath, body in case["files"].items():
            target = fixture_root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        before_hash, before_rows = tree_identity(fixture_root)
        worker = WrenchWorker(tokenizer=None, model=None, allowed_root=fixture_root)
        started = time.perf_counter()
        result = worker.propose([{"role": "user", "content": case["prompt"]}])
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        after_hash, after_rows = tree_identity(fixture_root)

        accepted = result.get("status") == "accepted" and result.get("action") == "patch_draft"
        observation = result.get("observation") if isinstance(result.get("observation"), dict) else {}
        raw_proposal = result.get("raw_model_output")
        try:
            proposal = json.loads(raw_proposal) if isinstance(raw_proposal, str) else None
        except json.JSONDecodeError:
            proposal = None
        positive = case["expected_files"] is not None
        exact = bool(
            accepted
            and isinstance(proposal, dict)
            and proposal.get("files") == case["expected_files"]
            and proposal.get("diff") == case["expected_diff"]
            and proposal.get("review_only") is True
            and observation.get("diff") == case["expected_diff"]
            and observation.get("review_only") is True
            and observation.get("applied") is False
            and observation.get("files") == [str(fixture_root / name) for name in case["expected_files"]]
            and isinstance(result.get("ttc"), dict)
            and result["ttc"].get("profile") == "deep"
            and result["ttc"].get("passed") is True
        ) if positive else False
        boundary_abstained = (
            result.get("status") == "abstain"
            and isinstance(result.get("fallback_reason"), str)
            and bool(result["fallback_reason"])
        ) if not positive else False
        unchanged = before_hash == after_hash and before_rows == after_rows
        return {
            "id": case["id"],
            "prompt_sha256": sha256(case["prompt"].encode("utf-8")),
            "fixture_before": {"tree_sha256": before_hash, "files": before_rows},
            "fixture_after": {"tree_sha256": after_hash, "files": after_rows},
            "fixture_unchanged": unchanged,
            "status": result.get("status"),
            "action": result.get("action"),
            "fallback_reason": result.get("fallback_reason"),
            "backend": result.get("backend"),
            "mechanical_fast_path": result.get("mechanical_fast_path"),
            "proposal_sha256": result.get("ttc", {}).get("base_verifier", {}).get("proposal_sha256") if isinstance(result.get("ttc"), dict) else None,
            "expected_files": case["expected_files"],
            "expected_diff_sha256": sha256(case["expected_diff"].encode("utf-8")) if isinstance(case["expected_diff"], str) else None,
            "observed_files": observation.get("files") if accepted else None,
            "observed_diff_sha256": sha256(observation["diff"].encode("utf-8")) if isinstance(observation.get("diff"), str) else None,
            "observation": observation if accepted else None,
            "ttc_profile": result.get("ttc", {}).get("profile") if isinstance(result.get("ttc"), dict) else None,
            "ttc_passed": result.get("ttc", {}).get("passed") if isinstance(result.get("ttc"), dict) else None,
            "positive_exact_oracle_match": exact,
            "boundary_correctly_abstained": boundary_abstained,
            "elapsed_ms": elapsed_ms,
        }


def run(output: Path, work_root: Path) -> dict[str, Any]:
    if not work_root.is_dir():
        raise ValueError("approved_work_root_must_exist")
    script_hash = sha256(Path(__file__).read_bytes())
    protocol_path = ROOT / "docs/evals/wrench-local-acceptability/patch-draft-screen-01-protocol.md"
    protocol_hash = sha256(protocol_path.read_bytes())
    source_hash = sha256((ROOT / "src/wrench_harness/mechanical.py").read_bytes())
    verifier_hash = sha256((ROOT / "src/wrench_harness/core.py").read_bytes())
    worker_hash = sha256((ROOT / "src/wrench_harness/worker.py").read_bytes())
    started = time.perf_counter()
    cases = [run_case(case, work_root) for case in CASES]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    positives = [row for row in cases if row["id"] in {"replace_unique", "append_line", "insert_after_unique"}]
    boundaries = [row for row in cases if row["id"] in {"duplicate_target", "missing_file", "no_review_authority"}]
    all_unchanged = all(row["fixture_unchanged"] for row in cases)
    passed = (
        len(positives) == 3
        and all(row["positive_exact_oracle_match"] for row in positives)
        and all(row["boundary_correctly_abstained"] for row in boundaries)
        and all_unchanged
    )
    receipt = {
        "schema": "wrench.local-patch-draft-screen-receipt.v1",
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol_hash,
        "runner_sha256": script_hash,
        "mechanical_route_sha256": source_hash,
        "core_verifier_sha256": verifier_hash,
        "worker_sha256": worker_hash,
        "runtime": sys.version,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "case_count": len(cases),
        "positive_count": len(positives),
        "positive_exact_oracle_matches": sum(row["positive_exact_oracle_match"] for row in positives),
        "boundary_count": len(boundaries),
        "boundary_abstentions": sum(row["boundary_correctly_abstained"] for row in boundaries),
        "fixture_trees_unchanged": all_unchanged,
        "status": "PASS_SYNTHETIC_MECHANICS_ONLY" if passed else "FAIL",
        "quality_claim": False,
        "elapsed_ms": elapsed_ms,
        "cases": cases,
    }
    payload = json.dumps(receipt, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(json.dumps({key: receipt[key] for key in (
        "status", "case_count", "positive_exact_oracle_matches",
        "boundary_abstentions", "fixture_trees_unchanged", "elapsed_ms",
    )}, sort_keys=True))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.output, args.work_root)
    return 0 if receipt["status"] == "PASS_SYNTHETIC_MECHANICS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
