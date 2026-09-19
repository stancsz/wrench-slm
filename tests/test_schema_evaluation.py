from tools.evaluate_schema_adapter import score_case


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
