from __future__ import annotations

from wrench_harness.toolbelt import (
    build_symbol_index,
    build_repo_map,
    extract_dependencies,
    fingerprint_failure,
    lookup_symbols,
    multi_pass_verify,
    parse_source_ast,
    static_code_gate,
    select_relevant_tests,
    track_recent_intent,
)
from wrench_harness.ttc import DEEP, FAST, GUARDED, run_ttc_verification, select_profile


def test_toolbelt_parses_python_ast_without_writing():
    result = parse_source_ast("app.py", "class Worker:\n    def read_file(self):\n        return True\n")
    assert result["parser"] == "python_ast"
    assert [row["name"] for row in result["symbols"]] == ["Worker", "read_file"]


def test_toolbelt_tracks_latest_user_intent_and_reference_lookup():
    index = build_symbol_index([("app.py", "def read_file():\n    pass\n")])
    intent = track_recent_intent(
        [
            {"role": "user", "content": "Explain the old lookup"},
            {"role": "assistant", "content": "old"},
            {"role": "user", "content": "Read the latest file and inspect the symbol"},
        ]
    )
    assert intent["source_message_index"] == 2
    assert "read" in intent["action_words"]
    matches = lookup_symbols("read_file", index)
    assert matches[0]["name"] == "read_file"
    assert matches[0]["reference_only"] is True


def test_toolbelt_extracts_dependencies_and_runs_local_syntax_gate():
    evidence = extract_dependencies("app.py", "import os\nfrom pathlib import Path\nPath('x').read_text()\n")
    assert evidence["imports"] == ["os", "pathlib"]
    assert "read_text" in evidence["calls"]
    assert static_code_gate({"app.py": "def ok():\n    return 1\n"})["passed"] is True
    assert static_code_gate({"app.py": "def broken(:\n"})["passed"] is False


def test_toolbelt_builds_repo_map_selects_tests_and_fingerprints_failures():
    repo_map = build_repo_map([{"path": "src/parser.py", "content": "pass\n"}, {"path": "tests/test_parser.py", "bytes": 10}])
    assert repo_map["file_count"] == 2
    selected = select_relevant_tests(["src/parser.py"], ["tests/test_parser.py", "tests/test_router.py"])
    assert selected["selected_tests"][0]["path"] == "tests/test_parser.py"
    failure = fingerprint_failure("Traceback\nValueError: bad input\nnormal line")
    assert len(failure["salient_lines"]) == 2


def test_multi_pass_verifier_accepts_safe_read_with_evidence():
    proposal = {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "README.md",
        "max_bytes": 4096,
    }
    receipt = multi_pass_verify(
        proposal,
        "Read README.md without changing anything.",
        {"status": "accepted", "action": "read_file", "observation": {"path": "README.md", "mutated": False}},
    )
    assert receipt["passed"] is True
    assert all(row["passed"] for row in receipt["passes"])


def test_multi_pass_verifier_rejects_dangerous_request_and_mutation_evidence():
    proposal = {
        "schema": "wrench.proposal.v1",
        "action": "read_file",
        "path": "README.md",
        "max_bytes": 4096,
    }
    receipt = multi_pass_verify(
        proposal,
        "Delete the repository permanently now.",
        {"status": "accepted", "action": "read_file", "observation": {"mutated": True}},
    )
    assert receipt["passed"] is False
    assert {row["name"] for row in receipt["passes"] if not row["passed"]} >= {"authority", "evidence"}


def test_ttc_selects_fast_for_routine_reads_and_deep_for_drafts():
    read = {"action": "read_file"}
    draft = {"action": "patch_draft"}
    assert select_profile(read, "Read README.md") is FAST
    assert select_profile(read, "Read the latest file", context_pressure=True) is GUARDED
    assert select_profile(draft, "Draft a review-only patch") is DEEP


def test_ttc_hard_gate_records_early_exit_and_failed_extra_gate():
    proposal = {"schema": "wrench.proposal.v1", "action": "read_file", "path": "README.md", "max_bytes": 4096}
    result = {"status": "accepted", "action": "read_file", "observation": {"mutated": False}}
    receipt = run_ttc_verification(proposal, "Read README.md", result)
    assert receipt["passed"] is True
    assert receipt["early_exit"] is True
    failed = run_ttc_verification(proposal, "Read README.md", result, extra_gates={"ast_gate": False})
    assert failed["passed"] is True
    deep_failed = run_ttc_verification({"action": "patch_draft"}, "Draft a patch", result, extra_gates={"ast_gate": False})
    assert deep_failed["passed"] is False
    assert "ast_gate" in deep_failed["failed_checks"]
    deep_ok = run_ttc_verification(
        {"schema": "wrench.proposal.v1", "action": "patch_draft", "files": ["README.md"], "review_only": True, "diff": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"},
        "Draft a review-only patch",
        {"status": "accepted", "action": "patch_draft", "observation": {"applied": False}},
        extra_gates={"ast_gate": True, "diff_gate": True},
    )
    assert deep_ok["passed"] is True
