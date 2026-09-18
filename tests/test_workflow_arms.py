from __future__ import annotations

from tools.evaluate_workflow_arms import evaluate_manifest


def _trace(identifier: str, learned_tokens: int = 70, *, mutation: bool = False) -> dict:
    result = {
        "final_success": True,
        "prohibited_accept": False,
        "unexpected_mutation": mutation,
        "stronger_model_tokens": 100,
        "latency_ms": 1000,
    }
    learned = {**result, "stronger_model_tokens": learned_tokens, "latency_ms": 500}
    rules = {**result, "stronger_model_tokens": 90, "latency_ms": 700}
    return {"id": identifier, "family": "read_file", "arms": {"cloud_only": result, "rules_plus_identical_fallback": rules, "learned_plus_identical_fallback": learned}}


def _approved_manifest(traces: list[dict]) -> dict:
    return {
        "schema": "wrench.workflow-arm-traces.v1",
        "authorization": "approved_real_workflow",
        "trace_set_sha256": "0" * 64,
        "provenance": {
            "capture_id": "capture-test",
            "captured_at": "2026-09-18T00:00:00Z",
            "reviewer": "test-reviewer",
            "source_scope": "test-only fixture",
        },
        "traces": traces,
    }


def test_workflow_scoring_blocks_unapproved_trace_manifest():
    receipt = evaluate_manifest({"schema": "wrench.workflow-arm-traces.v1", "authorization": "pending_human_approval", "traces": [_trace("one")]})
    assert receipt["status"] == "BLOCKED_TRACE_AUTHORIZATION"
    assert receipt["paired_savings"] == []


def test_workflow_scoring_requires_paired_safety_and_savings_gates():
    receipt = evaluate_manifest(_approved_manifest([_trace(str(index)) for index in range(20)]))
    assert receipt["status"] == "PASS_WORKFLOW_ARM_METRICS"
    assert receipt["gates"]["savings_at_least_10_percent_with_ci_above_zero"] is True

    unsafe = evaluate_manifest(_approved_manifest([_trace("unsafe", mutation=True)]))
    assert unsafe["status"] == "QUALITY_GATE_OPEN"
    assert unsafe["gates"]["zero_unexpected_mutations"] is False


def test_workflow_scoring_blocks_approved_manifest_without_provenance():
    manifest = _approved_manifest([_trace("missing-provenance")])
    manifest.pop("provenance")
    receipt = evaluate_manifest(manifest)
    assert receipt["status"] == "BLOCKED_TRACE_PROVENANCE"
    assert receipt["paired_savings"] == []
