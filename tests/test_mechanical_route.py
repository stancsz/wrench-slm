from wrench_harness import mechanical_route


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
    assert mechanical_route("Draft a review-only change for README.md and do not apply it.") is None
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
