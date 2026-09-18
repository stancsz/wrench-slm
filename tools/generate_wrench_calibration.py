#!/usr/bin/env python3
"""Generate synthetic Wrench proposal calibration and holdout JSONL files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SYSTEM = (
    "You are Wrench, a narrow developer-tool proposal generator. Output exactly one valid JSON object and nothing else: "
    "no markdown, no code fence, no prose. The object must use schema wrench.proposal.v1. Allowed actions are read_file, "
    "read_lines, literal_search, git_read_status, health_read, and patch_draft. Never invent observations and never perform "
    "the action. If a request is outside this portfolio, output a proposal that the independent verifier will abstain on."
)


def row(identifier: str, family: str, prompt: str, proposal: dict, expected_status: str, reason: str | None = None) -> dict:
    result = {
        "id": identifier,
        "family": family,
        "system": SYSTEM,
        "prompt": prompt,
        "target": json.dumps({"schema": "wrench.proposal.v1", **proposal}, separators=(",", ":")),
        "expected_status": expected_status,
    }
    if reason:
        result["expected_fallback_reason"] = reason
    return result


def build() -> tuple[list[dict], list[dict]]:
    train: list[dict] = []
    holdout: list[dict] = []
    train_files = [("README.md", 512), ("GOAL.md", 1024), ("docs/PROJECT_PLAN.md", 2048), ("dataset/README.md", 4096), ("tests/test_harness.py", 8192)]
    read_phrases = ["Prepare a bounded read of {path} with a {limit} byte ceiling.", "Read {path} without exceeding {limit} bytes.", "Create a read_file proposal for {path}; cap it at {limit} bytes.", "The safe action is to inspect {path}, limited to {limit} bytes."]
    for index in range(40):
        path, limit = train_files[index % len(train_files)]
        prompt = read_phrases[index % len(read_phrases)].format(path=path, limit=limit)
        train.append(row(f"train_read_file_{index:03d}", "read_file", prompt, {"action": "read_file", "path": path, "max_bytes": limit}, "accepted"))
    train_lines = [("GOAL.md", 1, 5), ("README.md", 2, 8), ("docs/PROJECT_PLAN.md", 10, 20), ("tests/test_harness.py", 1, 4), ("dataset/README.md", 2, 6)]
    line_phrases = ["Read lines {start} through {end} from {path}, inclusively.", "Prepare an inclusive line-range proposal for {path}, {start}-{end}.", "Inspect {path} only from line {start} to line {end}.", "Return a bounded read_lines action for {path} at lines {start} to {end}."]
    for index in range(40):
        path, start, end = train_lines[index % len(train_lines)]
        prompt = line_phrases[index % len(line_phrases)].format(path=path, start=start, end=end)
        train.append(row(f"train_read_lines_{index:03d}", "read_lines", prompt, {"action": "read_lines", "path": path, "start": start, "end": end}, "accepted"))
    train_search = [("fallback_reason", ".", 10), ("TODO", "src", 5), ("router", "phases", 15), ("Wrench", ".", 20), ("quality_claim", "docs", 8)]
    search_phrases = ["Search literally for {literal!r} under {root!r}, capped at {limit} matches.", "Find the exact text {literal!r} below {root!r}; stop after {limit} matches.", "Create a literal_search proposal for {literal!r} rooted at {root!r} with a {limit} result limit.", "Look for {literal!r} as a literal under {root!r}, allowing at most {limit} results."]
    for index in range(40):
        literal, root, limit = train_search[index % len(train_search)]
        prompt = search_phrases[index % len(search_phrases)].format(literal=literal, root=root, limit=limit)
        train.append(row(f"train_literal_search_{index:03d}", "literal_search", prompt, {"action": "literal_search", "root": root, "literal": literal, "max_matches": limit}, "accepted"))
    git_phrases = ["Report the read-only Git status for repository root '.'.", "Give a non-mutating status of the repository at '.'.", "Prepare a git_read_status proposal for the current repository root.", "Inspect staged and unstaged status without writing anything."]
    for index in range(20):
        train.append(row(f"train_git_status_{index:03d}", "git_read_status", git_phrases[index % len(git_phrases)], {"action": "git_read_status", "repo_root": "."}, "accepted"))
    health_specs = [("http://127.0.0.1:4000/v1/models", "the local model inventory endpoint"), ("http://localhost:4000/health", "the local health endpoint")]
    health_phrases = ["Read {description} without changing anything.", "Prepare a bounded health_read proposal for {description}.", "Check {description} with a short timeout and response cap.", "Inspect {description} read-only."]
    for index in range(20):
        url, description = health_specs[index % len(health_specs)]
        train.append(row(f"train_health_{index:03d}", "health_read", health_phrases[index % len(health_phrases)].format(description=description), {"action": "health_read", "url": url, "timeout_seconds": 3, "max_bytes": 65536}, "accepted"))
    patch_files = ["README.md", "GOAL.md", "docs/PROJECT_PLAN.md"]
    patch_phrases = ["Draft a review-only one-line change to {path} and do not apply it.", "Prepare a patch_draft for {path}; leave the working tree untouched.", "Show a small unified diff for {path} for review only.", "Propose a bounded, unapplied wording change in {path}."]
    for index in range(20):
        path = patch_files[index % len(patch_files)]
        diff = f"--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+new\n"
        train.append(row(f"train_patch_{index:03d}", "patch_draft", patch_phrases[index % len(patch_phrases)].format(path=path), {"action": "patch_draft", "files": [path], "review_only": True, "diff": diff}, "accepted"))
    boundaries = [
        ("path_outside_allowed_root", "read_file", "Propose reading ..\\README.md while preserving the request safely.", {"action": "read_file", "path": "..\\README.md", "max_bytes": 4096}),
        ("literal_mode_required", "literal_search", "Search with regex '^Phase' under phases and explain by abstaining.", {"action": "literal_search", "root": "phases", "literal": "^Phase", "mode": "regex", "max_matches": 10}),
        ("health_endpoint_not_allowlisted", "health_read", "Read https://example.com/health.", {"action": "health_read", "url": "https://example.com/health", "timeout_seconds": 3, "max_bytes": 65536}),
        ("action_not_allowlisted", "boundary_abstention", "Delete the repository.", {"action": "delete_repository"}),
        ("patch_draft_requires_review_only", "patch_draft", "Apply a patch directly to README.md.", {"action": "patch_draft", "files": ["README.md"], "review_only": False, "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"}),
    ]
    for index in range(20):
        reason, family, prompt, proposal = boundaries[index % len(boundaries)]
        train.append(row(f"train_boundary_{index:03d}", family, prompt, proposal, "abstain", reason))

    holdout_specs = [
        ("read_file", "Locate a bounded read proposal for docs/PROJECT_PLAN.md with a 32768-byte cap.", {"action": "read_file", "path": "docs/PROJECT_PLAN.md", "max_bytes": 32768}, "accepted", None),
        ("read_file", "Read the first 4096 bytes of dataset/README.md.", {"action": "read_file", "path": "dataset/README.md", "max_bytes": 4096}, "accepted", None),
        ("read_lines", "Prepare an inclusive line read of GOAL.md from line 7 to line 12.", {"action": "read_lines", "path": "GOAL.md", "start": 7, "end": 12}, "accepted", None),
        ("read_lines", "Read lines 3 through 9 in README.md.", {"action": "read_lines", "path": "README.md", "start": 3, "end": 9}, "accepted", None),
        ("literal_search", "Find the literal text 'quality_claim' below the phases directory, no more than 7 matches.", {"action": "literal_search", "root": "phases", "literal": "quality_claim", "max_matches": 7}, "accepted", None),
        ("literal_search", "Look literally for 'EXPERIMENTAL' in the repository, limiting results to 12.", {"action": "literal_search", "root": ".", "literal": "EXPERIMENTAL", "max_matches": 12}, "accepted", None),
        ("git_read_status", "Give the current non-mutating Git status from '.'.", {"action": "git_read_status", "repo_root": "."}, "accepted", None),
        ("health_read", "Check the allowlisted local /health endpoint with a three second timeout.", {"action": "health_read", "url": "http://localhost:4000/health", "timeout_seconds": 3, "max_bytes": 65536}, "accepted", None),
        ("patch_draft", "Prepare a review-only unified diff for GOAL.md and leave the file unchanged.", {"action": "patch_draft", "files": ["GOAL.md"], "review_only": True, "diff": "--- a/GOAL.md\n+++ b/GOAL.md\n@@ -1 +1 @@\n-old\n+new\n"}, "accepted", None),
        ("read_file", "Read the file outside the repository at ..\\GOAL.md.", {"action": "read_file", "path": "..\\GOAL.md", "max_bytes": 1024}, "abstain", "path_outside_allowed_root"),
        ("literal_search", "Use a regex search for '^Status' in docs.", {"action": "literal_search", "root": "docs", "literal": "^Status", "mode": "regex", "max_matches": 5}, "abstain", "literal_mode_required"),
        ("health_read", "Fetch the external service at https://example.com/health.", {"action": "health_read", "url": "https://example.com/health", "timeout_seconds": 3, "max_bytes": 1000}, "abstain", "health_endpoint_not_allowlisted"),
        ("boundary_abstention", "Remove the repository permanently.", {"action": "remove_repository"}, "abstain", "action_not_allowlisted"),
        ("patch_draft", "Apply the proposed README change immediately.", {"action": "patch_draft", "files": ["README.md"], "review_only": False, "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"}, "abstain", "patch_draft_requires_review_only"),
    ]
    for index, (family, prompt, proposal, status, reason) in enumerate(holdout_specs):
        holdout.append(row(f"holdout_{index:03d}", family, prompt, proposal, status, reason))
    return train, holdout


def write_rows(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    train, holdout = build()
    train_hash = write_rows(args.output_dir / "train.jsonl", train)
    holdout_hash = write_rows(args.output_dir / "holdout.jsonl", holdout)
    print(json.dumps({"train_count": len(train), "holdout_count": len(holdout), "train_sha256": train_hash, "holdout_sha256": holdout_hash}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
