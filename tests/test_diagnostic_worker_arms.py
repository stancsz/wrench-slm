from __future__ import annotations

from tools.run_diagnostic_worker_arms import _strict_success, _unexpected_mutation, _verifier_success
import tools.run_diagnostic_worker_arms as diagnostic


def _row(expected_status: str = "accepted", reason: str | None = None) -> dict:
    return {
        "expected_status": expected_status,
        "expected_fallback_reason": reason,
        "target": '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}',
    }


def test_diagnostic_success_requires_exact_accepted_proposal():
    row = _row()
    accepted = {
        "status": "accepted",
        "parsed_proposal": {
            "schema": "wrench.proposal.v1",
            "action": "read_file",
            "path": "README.md",
            "max_bytes": 4096,
        },
    }
    wrong = {**accepted, "parsed_proposal": {**accepted["parsed_proposal"], "max_bytes": 8192}}
    assert _strict_success(accepted, row) is True
    assert _strict_success(wrong, row) is False


def test_diagnostic_success_accepts_expected_abstention_and_rejects_mutation():
    row = _row("abstain", "missing_path")
    result = {"status": "abstain", "fallback_reason": "missing_path"}
    assert _strict_success(result, row) is True
    assert _verifier_success(result) is True
    assert _unexpected_mutation({"observation": {"applied": False, "mutated": False}}) is False
    assert _unexpected_mutation({"observation": {"applied": True}}) is True


def test_teacher_hard_deadline_returns_explicit_timeout(monkeypatch):
    def blocked(*args, **kwargs):
        raise diagnostic.subprocess.TimeoutExpired(cmd="teacher", timeout=0.01)

    monkeypatch.setattr(diagnostic.subprocess, "run", blocked)
    row = {"id": "slow", "system": "system", "prompt": "prompt"}
    receipt = diagnostic._call_teacher("http://127.0.0.1:1", "teacher", row, ".", timeout=0.01, max_tokens=1)
    assert receipt["result"]["fallback_reason"] == "teacher_timeout"


def test_wrench_process_wrapper_records_transport_failures():
    row = {"id": "bad", "system": "system", "prompt": "prompt"}
    receipt = diagnostic._local_result("http://127.0.0.1:1", "wrench", row, ".", timeout=0.1, max_tokens=1)
    assert receipt["result"]["fallback_reason"] in {
        "qwen_endpoint_not_allowlisted",
        "qwen_transport_error",
        "wrench_timeout",
    }


def test_rules_arm_routes_explicit_abstention_to_teacher_fallback(tmp_path):
    accepted = {
        "prompt": "Read README.md with a 4096 byte limit.",
    }
    boundary = {
        "prompt": "Read a missing file safely.",
    }
    assert diagnostic._rule_result(accepted, str(tmp_path)) is not None
    assert diagnostic._rule_result(boundary, str(tmp_path)) is None
