from __future__ import annotations

import io
import json

import pytest

from tools.run_diagnostic_worker_arms import (
    _strict_success,
    _unexpected_mutation,
    _verifier_success,
    _wrench_needs_teacher_fallback,
)
import tools.run_diagnostic_worker_arms as diagnostic
import tools.run_local_wrench_call as local_call
import tools.run_teacher_call as teacher_call


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
    assert receipt["frontier_tokens"] is None
    assert receipt["cost_usd"] is None


def test_missing_or_invalid_provider_tokens_and_cost_stay_unknown():
    assert diagnostic._usage_tokens({"total_tokens": 12}) == 12
    assert diagnostic._usage_tokens({}) is None
    assert diagnostic._usage_tokens({"total_tokens": True}) is None
    assert diagnostic._usage_tokens({"total_tokens": 12.5}) is None
    assert diagnostic._cost_usd({"cost": 0.004}) == 0.004
    assert diagnostic._cost_usd({"cost_details": {"upstream_inference_cost": 0.006}}) == 0.006
    assert diagnostic._cost_usd({}) is None
    assert diagnostic._cost_usd({"cost": True}) is None
    assert diagnostic._cost_usd({"cost": float("nan")}) is None


def test_arm_record_requires_explicit_cost_and_preserves_unknown_provider_cost():
    with pytest.raises(TypeError, match="cost_usd"):
        diagnostic._arm_record({}, {}, latency_ms=0, frontier_tokens=1, source="teacher")

    receipt = diagnostic._arm_record(
        {},
        {},
        latency_ms=0,
        frontier_tokens=1,
        cost_usd=None,
        provider_requests=1,
        source="teacher",
    )
    assert receipt["provider_requests"] == 1
    assert receipt["cost_usd"] is None


def test_teacher_capture_requires_complete_usage_and_actual_response_model():
    assert diagnostic._complete_usage_record({"prompt_tokens": 8, "completion_tokens": 3, "total_tokens": 11}) is True
    assert diagnostic._complete_usage_record({"prompt_tokens": 8, "completion_tokens": 3, "total_tokens": 12}) is False
    assert diagnostic._complete_usage_record({"prompt_tokens": 8, "completion_tokens": 3}) is False
    assert diagnostic._captured_response_model({"one": {"result": {"model": "openrouter/minimax/minimax-m3"}}}) == "openrouter/minimax/minimax-m3"
    with pytest.raises(ValueError, match="mixed or missing"):
        diagnostic._captured_response_model(
            {
                "one": {"result": {"model": "provider/model-a"}},
                "two": {"result": {"model": "provider/model-b"}},
            }
        )


def test_live_teacher_path_fails_before_reading_cases_or_making_requests(tmp_path):
    args = diagnostic.argparse.Namespace(
        cases=tmp_path / "missing-cases.jsonl",
        limit=None,
        root=tmp_path,
        teacher_traces=None,
    )
    with pytest.raises(RuntimeError, match="live_teacher_calls_disabled"):
        diagnostic.run(args)


def test_diagnostic_wrench_arm_rejects_subroute_4000_before_reading_cases(tmp_path):
    args = diagnostic.argparse.Namespace(
        cases=tmp_path / "missing-cases.jsonl",
        limit=None,
        root=tmp_path,
        teacher_traces=tmp_path / "capture.json",
        wrench_endpoint="http://127.0.0.1:4000/v1/chat/completions",
    )
    with pytest.raises(RuntimeError, match="diagnostic_wrench_calls_to_subroute_4000_disabled"):
        diagnostic.run(args)


def test_teacher_child_rejects_even_a_fully_formed_live_request(monkeypatch, capsys):
    request = {
        "endpoint": "http://127.0.0.1:4000/v1/chat/completions",
        "model": "openrouter",
        "messages": [{"role": "user", "content": "request must not be sent"}],
        "timeout": 2,
        "max_tokens": 1,
    }
    monkeypatch.setattr(teacher_call.sys, "stdin", io.StringIO(json.dumps(request)))

    assert teacher_call.main() == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {"ok": False, "error": teacher_call.LIVE_CALLS_DISABLED}


def test_local_wrench_child_rejects_subroute_4000_before_model_execution(monkeypatch):
    request = {
        "endpoint": "http://127.0.0.1:4000/v1/chat/completions",
        "model": "openrouter",
        "messages": [{"role": "user", "content": "request must not be sent"}],
        "root": ".",
        "timeout": 2,
        "max_tokens": 1,
    }
    monkeypatch.setattr(local_call.sys, "stdin", io.StringIO(json.dumps(request)))
    monkeypatch.setattr(local_call, "execute_local_qwen", lambda *args, **kwargs: pytest.fail("model call started"))

    with pytest.raises(RuntimeError, match="SubRoute :4000 is not a local Wrench model endpoint"):
        local_call.main()


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


def test_mechanical_abstention_is_terminal_and_does_not_pay_teacher_tokens():
    assert _wrench_needs_teacher_fallback({"status": "abstain", "mechanical_fast_path": True}) is False
    assert _wrench_needs_teacher_fallback({"status": "abstain", "mechanical_fast_path": False}) is True
    assert _wrench_needs_teacher_fallback({"status": "accepted", "mechanical_fast_path": False}) is False
