import re

import pytest

from wrench_harness import mechanical_route
from wrench_harness import core
from wrench_harness.mechanical import reference_patch_route


def test_mechanical_route_builds_bounded_read_proposals():
    assert mechanical_route("Read README.md without exceeding 4096 bytes.") == {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "README.md",
        "max_bytes": 4096,
    }
    assert mechanical_route("Read lines 3 through 9 in README.md.") == {
        "schema": "wrench.proposal.v1",
        "action": "read_lines",
        "path": "README.md",
        "start": 3,
        "end": 9,
    }


def test_mechanical_route_uses_verifier_bounded_default_for_simple_read():
    assert mechanical_route("Read README.md.") == {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "README.md",
        "max_bytes": 256 * 1024,
    }
    assert mechanical_route("Read the entire README.md.") is None


def test_mechanical_route_handles_literal_health_and_git():
    assert mechanical_route("Find the exact text 'TODO' below src, capped at 5 matches.") == {
        "schema": "wrench.proposal.v1",
        "action": "literal_search",
        "root": "src",
        "literal": "TODO",
        "max_matches": 5,
    }
    assert mechanical_route("Report the read-only Git status for repository root '.'.") == {
        "schema": "wrench.proposal.v1",
        "action": "git_read_status",
        "repo_root": ".",
    }
    assert mechanical_route("Inspect staged and unstaged files read-only.") == {
        "schema": "wrench.proposal.v1",
        "action": "git_read_status",
        "repo_root": ".",
    }
    assert mechanical_route("Check http://localhost:4000/health with a three second timeout.") == {
        "schema": "wrench.proposal.v1",
        "action": "health_read",
        "url": "http://localhost:4000/health",
        "timeout_seconds": 3.0,
        "max_bytes": 65536,
    }


def test_literal_search_accelerator_timeout_does_not_fall_back_to_unbounded_walk(tmp_path, monkeypatch):
    monkeypatch.setattr(
        core,
        "_literal_search_with_rg",
        lambda *args: {"status": "abstain", "fallback_reason": "search_timeout"},
    )

    result = core._literal_search(
        {
            "action": "literal_search",
            "root": ".",
            "literal": "Wrench",
            "max_matches": 5,
        },
        tmp_path,
    )

    assert result == {"status": "abstain", "fallback_reason": "search_timeout"}


def test_mechanical_route_abstains_on_risky_or_ambiguous_requests():
    assert mechanical_route("Delete obsolete project files and permanently clean the repository.") == {
        "status": "abstain",
        "fallback_reason": "task_family_not_allowlisted",
    }
    assert mechanical_route("Please debug this failure across several files.") == {
        "status": "abstain",
        "fallback_reason": "task_family_not_allowlisted",
    }
    assert mechanical_route("Read the relevant thing and decide what to do.") is None
    assert mechanical_route("Draft a review-only change for README.md and do not apply it.") == {
        "status": "abstain",
        "fallback_reason": "patch_content_missing",
    }
    assert mechanical_route("Read a missing file safely.")["fallback_reason"] == "missing_path"
    assert mechanical_route("Use a boolean repository root.")["fallback_reason"] == "repository_root_invalid"


def test_mechanical_route_normalizes_unified_diff_b_path():
    prompt = (
        "Draft a review-only change for README.md and do not apply it.\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    assert mechanical_route(prompt) == {
        "schema": "wrench.proposal.v1",
        "action": "patch_draft",
        "files": ["README.md"],
        "review_only": True,
        "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n",
    }


def test_mechanical_route_builds_a_review_patch_for_one_explicit_replacement(tmp_path):
    target = tmp_path / "README.md"
    target.write_text("before\nkeep\nafter\n", encoding="utf-8")

    proposal = mechanical_route(
        'Replace "before" with "updated" in README.md and leave the file unchanged.',
        allowed_root=tmp_path,
    )

    assert proposal is not None
    assert proposal["action"] == "patch_draft"
    assert proposal["files"] == ["README.md"]
    assert proposal["review_only"] is True
    assert "-before" in proposal["diff"]
    assert "+updated" in proposal["diff"]
    assert target.read_text(encoding="utf-8") == "before\nkeep\nafter\n"


def test_mechanical_route_defers_ambiguous_replacement_to_model(tmp_path):
    target = tmp_path / "README.md"
    target.write_text("before\nbefore\n", encoding="utf-8")

    assert mechanical_route(
        'Replace "before" with "updated" in README.md and leave the file unchanged.',
        allowed_root=tmp_path,
    ) is None


@pytest.mark.parametrize(
    ("instruction", "before", "removed", "added"),
    [
        ('Append "tail" to README.md and leave the file unchanged.', "head\n", "head", "tail"),
        ('Prepend "top" to README.md and leave the file unchanged.', "head\n", "head", "top"),
        ('Insert "middle" after "head" in README.md and leave the file unchanged.', "head\ntail\n", "tail", "middle"),
        ('Remove "obsolete" from README.md and leave the file unchanged.', "keep\nobsolete\n", "obsolete", "keep"),
    ],
)
def test_mechanical_route_builds_bounded_text_patch(tmp_path, instruction, before, removed, added):
    target = tmp_path / "README.md"
    target.write_text(before, encoding="utf-8")

    proposal = mechanical_route(instruction, allowed_root=tmp_path)

    assert proposal is not None
    assert proposal["action"] == "patch_draft"
    assert proposal["files"] == ["README.md"]
    assert proposal["review_only"] is True
    assert removed in proposal["diff"]
    assert added in proposal["diff"]
    assert target.read_text(encoding="utf-8") == before


def test_reference_patch_route_recovers_exact_old_diff():
    prompt = (
        "Historical review artifact:\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-old line\n"
        "+new line\n"
        "CURRENT INTENT: Prepare an unapplied unified diff for README.md for review."
    )

    assert reference_patch_route(prompt) == {
        "schema": "wrench.proposal.v1",
        "action": "patch_draft",
        "files": ["README.md"],
        "review_only": True,
        "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old line\n+new line\n",
    }


def test_reference_patch_route_recovers_explicit_multi_file_diff():
    prompt = (
        "Historical review artifact:\n"
        "--- a/README.md\n"
        "+++ b/README.md\n"
        "@@ -1 +1 @@\n"
        "-old readme\n"
        "+new readme\n"
        "--- a/config/policy.json\n"
        "+++ b/config/policy.json\n"
        "@@ -1 +1 @@\n"
        "-old policy\n"
        "+new policy\n"
        "CURRENT INTENT: prepare an unapplied unified diff for README.md and config/policy.json for review."
    )

    proposal = reference_patch_route(prompt)
    assert proposal is not None
    assert proposal["files"] == ["README.md", "config/policy.json"]
    assert len(re.findall(r"(?m)^@@", proposal["diff"])) == 2
    assert proposal["review_only"] is True
