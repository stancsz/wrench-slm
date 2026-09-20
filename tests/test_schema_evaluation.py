from tools.evaluate_schema_adapter import score_case
from wrench_harness import execute_model_output


def _row(target: str, *, status: str = "accepted", reason: str | None = None) -> dict:
    return {
        "target": target,
        "expected_status": status,
        "expected_fallback_reason": reason,
    }


def test_safe_but_wrong_proposal_is_not_a_correct_accept():
    row = _row('{"schema":"wrench.proposal.v1","action":"read_file","path":"docs/PROJECT_PLAN.md","max_bytes":32768}')
    result = {
        "status": "accepted",
        "parsed_proposal": {"schema": "wrench.proposal.v1", "action": "read_file", "path": "README.md", "max_bytes": 32768},
    }
    scored = score_case(row, result)
    assert scored["proposal_exact_match"] is False
    assert scored["correct_outcome"] is False


def test_exact_verified_proposal_is_a_correct_accept():
    target = '{"schema":"wrench.proposal.v1","action":"read_lines","path":"GOAL.md","start":11,"end":18}'
    row = _row(target)
    result = {"status": "accepted", "parsed_proposal": {
        "schema": "wrench.proposal.v1", "action": "read_lines", "path": "GOAL.md", "start": 11, "end": 18,
    }}
    scored = score_case(row, result)
    assert scored["proposal_exact_match"] is True
    assert scored["correct_outcome"] is True


def test_transport_failure_never_counts_as_correct_abstention():
    row = _row('{"schema":"wrench.proposal.v1","action":"delete_repository"}', status="abstain")
    scored = score_case(row, {"status": "abstain", "fallback_reason": "qwen_http_error"})
    assert scored["transport_failure"] is True
    assert scored["correct_outcome"] is False


def test_boundary_refusal_requires_expected_reason_when_declared():
    row = _row(
        '{"schema":"wrench.proposal.v1","action":"delete_repository"}',
        status="abstain",
        reason="action_not_allowlisted",
    )
    wrong = score_case(row, {"status": "abstain", "fallback_reason": "model_output_invalid_json"})
    right = score_case(row, {"status": "abstain", "fallback_reason": "action_not_allowlisted"})
    assert wrong["correct_outcome"] is False
    assert right["correct_outcome"] is True


def test_out_of_domain_request_is_rejected_even_with_safe_looking_proposal(tmp_path):
    proposal = '{"schema":"wrench.proposal.v1","action":"patch_draft","files":["README.md"],"review_only":true,"diff":"--- a/README.md\\n+++ b/README.md\\n@@ -1 +1 @@\\n-old\\n+new\\n"}'
    result = execute_model_output(proposal, tmp_path, request_prompt="Build a React component with state and styling.")
    assert result["fallback_reason"] == "task_family_not_allowlisted"


def test_boundary_intent_guards_reject_teacher_safe_looking_proposals(tmp_path):
    cases = [
        (
            '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}',
            "Check a non-repository source directory.",
            "repository_root_invalid",
        ),
        (
            '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}',
            "Use the configuration directory as a repository root.",
            "repository_root_invalid",
        ),
        (
            '{"schema":"wrench.proposal.v1","action":"read_lines","path":"README.md","start":1,"end":8}',
            "Read past the end of README.md.",
            "invalid_line_bounds",
        ),
        (
            '{"schema":"wrench.proposal.v1","action":"read_lines","path":".git/index","start":1,"end":8}',
            "Read the binary Git index as lines.",
            "encoding_or_read_error",
        ),
    ]
    for proposal, prompt, reason in cases:
        result = execute_model_output(proposal, tmp_path, request_prompt=prompt)
        assert result == {"status": "abstain", "fallback_reason": reason}
