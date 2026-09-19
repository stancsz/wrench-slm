#!/usr/bin/env python3
"""Score a provisional tier receipt through the independent Wrench verifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_model_output


def _adapt_generic_tool(value: object) -> object:
    """Map common generic tool-call envelopes into Wrench proposal JSON.

    This is only for an explicitly requested teacher-baseline comparison. The
    Wrench runtime itself remains strict and does not silently accept this
    dialect.
    """

    if not isinstance(value, dict) or not isinstance(value.get("action"), str):
        return value
    action = value["action"]
    params = value.get("params") or value.get("parameters") or {}
    if not isinstance(params, dict):
        params = {}
    proposal: dict[str, object] = {"schema": "wrench.proposal.v1", "action": action}
    if action == "read_file":
        proposal.update({"path": params.get("path"), "max_bytes": params.get("max_bytes", 65536)})
    elif action == "read_lines":
        proposal.update({
            "path": params.get("path", params.get("file", params.get("file_path"))),
            "start": params.get("start", params.get("start_line")),
            "end": params.get("end", params.get("end_line")),
        })
    elif action == "literal_search":
        proposal.update({
            "root": params.get("root", params.get("search_root", ".")),
            "literal": params.get("literal", params.get("text")),
            "max_matches": params.get("max_matches", params.get("match_limit", 100)),
        })
        if "mode" in params:
            proposal["mode"] = params["mode"]
    elif action == "git_read_status":
        proposal["repo_root"] = params.get("repo_root", params.get("repo", "."))
    elif action == "health_read":
        proposal.update({
            "url": params.get("url"),
            "timeout_seconds": params.get("timeout_seconds", params.get("timeout", 3)),
            "max_bytes": params.get("max_bytes", 65536),
        })
    elif action == "patch_draft":
        proposal.update({
            "files": params.get("files", []),
            "review_only": params.get("review_only", True),
            "diff": params.get("diff", ""),
        })
    return proposal


def score(receipt_path: Path, cases_path: Path, root: Path, output: Path, adapter: str | None = None) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    cases = {row["id"]: row for row in (json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip())}
    results = []
    for observed in receipt.get("requests", []):
        case = cases.get(observed["id"])
        if case is None:
            continue
        raw_content = observed.get("response_content", "")
        try:
            raw_proposal = json.loads(raw_content)
        except (TypeError, json.JSONDecodeError):
            raw_proposal = None
        adapted_proposal = _adapt_generic_tool(raw_proposal) if adapter == "generic-tool" else raw_proposal
        adapted_content = json.dumps(adapted_proposal, separators=(",", ":")) if adapted_proposal is not None else raw_content
        parsed = execute_model_output(adapted_content, str(root.resolve()), request_prompt=case.get("prompt"))
        try:
            observed_proposal = adapted_proposal
        except (TypeError, json.JSONDecodeError):
            observed_proposal = None
        try:
            expected_proposal = json.loads(case["target"])
        except (KeyError, TypeError, json.JSONDecodeError):
            expected_proposal = None
        expected_status = case["expected_status"]
        expected_reason = case.get("expected_fallback_reason")
        status_match = parsed.get("status") == expected_status
        reason_match = expected_reason is None or parsed.get("fallback_reason") == expected_reason
        proposal_match = observed_proposal == expected_proposal
        results.append(
            {
                "id": observed["id"],
                "family": case["family"],
                "expected_status": expected_status,
                "expected_fallback_reason": expected_reason,
                "observed_status": parsed.get("status"),
                "observed_fallback_reason": parsed.get("fallback_reason"),
                "status_match": status_match,
                "reason_match": reason_match,
                "proposal_match": proposal_match,
                "usage": observed.get("usage"),
                "wall_seconds": observed.get("wall_seconds"),
            }
        )
    exact = sum(item["status_match"] and item["reason_match"] for item in results)
    proposal_exact = sum(item["proposal_match"] for item in results)
    result = {
        "schema": "wrench.provisional-tier-development-score.v1",
        "status": "PASS_PROVISIONAL_VERIFIER_SCORE" if exact == len(results) else "OBSERVED_PROVISIONAL_MISMATCHES",
        "receipt": str(receipt_path.resolve()),
        "cases": str(cases_path.resolve()),
        "case_count": len(results),
        "exact_matches": exact,
        "proposal_exact_matches": proposal_exact,
        "results": results,
        "scope": "development-only synthetic templates; portfolio pending human approval; not final quality evidence",
        "adapter": adapter,
        "quality_claim": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapter", choices=("generic-tool",), default=None)
    args = parser.parse_args()
    result = score(args.receipt.resolve(), args.cases.resolve(), args.root.resolve(), args.output.resolve(), args.adapter)
    print(json.dumps({"status": result["status"], "case_count": result["case_count"], "exact_matches": result["exact_matches"], "proposal_exact_matches": result["proposal_exact_matches"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
