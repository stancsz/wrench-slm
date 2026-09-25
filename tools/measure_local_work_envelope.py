"""Measure the current deterministic proposal router on non-final local cases.

This is a route-only diagnostic. It does not execute proposed reads, patches,
Git operations, health requests, or verifier checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "wrench-expanded-v2" / "cases.jsonl"
EXCLUDED_SPLITS = {"final"}
INCLUDED_SPLITS = {"calibration", "development"}

sys.path.insert(0, str(ROOT / "src"))
from wrench_harness.mechanical import mechanical_route  # noqa: E402


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_nonfinal(path: Path) -> tuple[list[dict[str, Any]], dict[str, int], str]:
    selected: list[dict[str, Any]] = []
    split_counts: dict[str, int] = defaultdict(int)
    seen_ids: set[str] = set()
    selected_canonical: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            split = row.get("split")
            if split not in INCLUDED_SPLITS | EXCLUDED_SPLITS:
                raise ValueError(f"unexpected split at line {line_number}")
            split_counts[split] += 1
            if split in EXCLUDED_SPLITS:
                continue
            if type(row.get("id")) is not str or row["id"] in seen_ids:
                raise ValueError(f"invalid or duplicate case ID at line {line_number}")
            seen_ids.add(row["id"])
            if row.get("category") not in {"eligible", "boundary", "out_of_domain"}:
                raise ValueError(f"unexpected category at line {line_number}")
            if row.get("expected_status") not in {"accepted", "abstain"}:
                raise ValueError(f"unexpected expected status at line {line_number}")
            selected.append(row)
            selected_canonical.append(_canonical_json(row))
    if not selected:
        raise ValueError("no non-final cases selected")
    selected_sha256 = _sha256(("\n".join(selected_canonical) + "\n").encode("utf-8"))
    return selected, dict(sorted(split_counts.items())), selected_sha256


def _score_candidate(row: dict[str, Any], candidate: dict[str, Any] | None) -> dict[str, Any]:
    expected_status = row["expected_status"]
    if expected_status == "accepted":
        try:
            target = json.loads(row["target"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid target for {row['id']}") from exc
        exact = candidate == target
        return {
            "outcome": "exact_proposal" if exact else "proposal_mismatch" if candidate is not None else "false_abstention",
            "pass": exact,
        }

    if candidate is None:
        return {"outcome": "safe_route_miss_escalation", "pass": True}
    if candidate.get("status") == "abstain":
        expected_reason = row.get("expected_fallback_reason")
        reason_matches = expected_reason is None or candidate.get("fallback_reason") == expected_reason
        return {
            "outcome": "correct_abstention" if reason_matches else "abstention_reason_mismatch",
            "pass": reason_matches,
        }
    return {"outcome": "unsafe_proposal_on_abstain_case", "pass": False}


def measure(cases_path: Path, allowed_root: Path) -> dict[str, Any]:
    rows, split_counts, selected_hash = _load_nonfinal(cases_path)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    results: list[dict[str, Any]] = []
    total_start = time.perf_counter()
    for row in rows:
        started = time.perf_counter()
        candidate = mechanical_route(row.get("prompt", ""), allowed_root=allowed_root)
        elapsed_ms = (time.perf_counter() - started) * 1000
        scored = _score_candidate(row, candidate)
        result = {
            "family": row["family"],
            "category": row["category"],
            "expected_status": row["expected_status"],
            "outcome": scored["outcome"],
            "pass": scored["pass"],
            "elapsed_ms": round(elapsed_ms, 4),
        }
        results.append(result)
        by_family[row["family"]].append(result)
        by_category[row["category"]].append(result)
    total_elapsed_ms = (time.perf_counter() - total_start) * 1000

    def summarize(groups: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        for name in sorted(groups):
            group = groups[name]
            counts: dict[str, int] = defaultdict(int)
            for row in group:
                counts[row["outcome"]] += 1
            eligible = [row for row in group if row["expected_status"] == "accepted"]
            boundary = [row for row in group if row["expected_status"] == "abstain"]
            unsafe = counts["unsafe_proposal_on_abstain_case"]
            false_abstentions = counts["false_abstention"]
            proposal_mismatches = counts["proposal_mismatch"]
            summary[name] = {
                "cases": len(group),
                "passed": sum(row["pass"] for row in group),
                "eligible_cases": len(eligible),
                "exact_eligible_proposals": sum(row["outcome"] == "exact_proposal" for row in eligible),
                "abstain_cases": len(boundary),
                "correct_abstentions": counts["correct_abstention"],
                "safe_route_miss_escalations": counts["safe_route_miss_escalation"],
                "false_abstentions": false_abstentions,
                "proposal_mismatches": proposal_mismatches,
                "unsafe_proposals_on_abstain_cases": unsafe,
                "reason_mismatches": counts["abstention_reason_mismatch"],
                "case_pass_rate": round(sum(row["pass"] for row in group) / len(group), 6),
                "proposal_screen_acceptable": bool(eligible)
                and sum(row["outcome"] == "exact_proposal" for row in eligible) == len(eligible)
                and unsafe == 0,
                "outcomes": dict(sorted(counts.items())),
            }
        return summary

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    source_bytes = (ROOT / "src" / "wrench_harness" / "mechanical.py").read_bytes()
    return {
        "schema": "wrench.local-work-envelope.v1",
        "status": "DIAGNOSTIC_LOCAL_DETERMINISTIC_PROPOSAL_ONLY",
        "repo_head": head,
        "source_path": "src/wrench_harness/mechanical.py",
        "source_sha256": _sha256(source_bytes),
        "cases_path": str(cases_path.resolve()),
        "included_splits": sorted(INCLUDED_SPLITS),
        "excluded_splits": sorted(EXCLUDED_SPLITS),
        "split_counts_seen": split_counts,
        "selected_case_count": len(rows),
        "selected_cases_sha256": selected_hash,
        "decision_rule": {
            "accepted_case": "candidate must exactly equal the frozen proposal JSON",
            "abstain_case": "explicit expected abstention or safe route miss/escalation; any proposal is unsafe",
            "family_screen": "all eligible proposals exact and zero proposals on abstain cases",
        },
        "family_results": summarize(by_family),
        "category_results": summarize(by_category),
        "case_passes": sum(row["pass"] for row in results),
        "case_failures": len(results) - sum(row["pass"] for row in results),
        "unsafe_proposals": sum(row["outcome"] == "unsafe_proposal_on_abstain_case" for row in results),
        "median_case_elapsed_ms": round(sorted(row["elapsed_ms"] for row in results)[len(results) // 2], 4),
        "total_route_elapsed_ms": round(total_elapsed_ms, 4),
        "actions_executed": 0,
        "verifier_runs": 0,
        "model_calls": 0,
        "provider_calls": 0,
        "quality_claim": False,
        "frontier_savings_percent": None,
        "limitations": [
            "Wrench-authored synthetic prompts and targets measure route mechanics only.",
            "Calibration and development cases are exposed; results are not held-out utility evidence.",
            "A proposal pass does not prove action execution, source observation, independent verification, or task completion.",
            "Patch cases are review-only drafts; the route does not apply code changes.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = measure(args.cases, args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "selected_case_count": receipt["selected_case_count"],
        "case_passes": receipt["case_passes"],
        "case_failures": receipt["case_failures"],
        "unsafe_proposals": receipt["unsafe_proposals"],
        "family_results": receipt["family_results"],
        "receipt_sha256": _sha256(payload.encode("utf-8")),
        "output": str(args.output.resolve()),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
