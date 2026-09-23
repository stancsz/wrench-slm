from __future__ import annotations

import hashlib
import json

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
    encoded = json.dumps(traces, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema": "wrench.workflow-arm-traces.v1",
        "authorization": "approved_real_workflow",
        "trace_set_sha256": hashlib.sha256(encoded).hexdigest(),
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
    assert receipt["status"] == "INCONCLUSIVE_ACTIVE_GATE_D_UNSCORED"
    assert receipt["historical_10_percent_metric_pass"] is True
    assert receipt["active_gate_d_evaluable"] is False

    near_zero_frontier = evaluate_manifest(_approved_manifest([_trace(str(index), learned_tokens=0) for index in range(20)]))
    assert near_zero_frontier["status"] == "INCONCLUSIVE_ACTIVE_GATE_D_UNSCORED"
    assert near_zero_frontier["active_gate_d_evaluable"] is False

    unsafe = evaluate_manifest(_approved_manifest([_trace("unsafe", mutation=True)]))
    assert unsafe["status"] == "QUALITY_GATE_OPEN"
    assert unsafe["gates"]["zero_unexpected_mutations"] is False


def test_workflow_scoring_blocks_approved_manifest_without_provenance():
    manifest = _approved_manifest([_trace("missing-provenance")])
    manifest.pop("provenance")
    receipt = evaluate_manifest(manifest)
    assert receipt["status"] == "BLOCKED_TRACE_PROVENANCE"
    assert receipt["paired_savings"] == []


def test_workflow_scoring_blocks_trace_hash_mismatch():
    manifest = _approved_manifest([_trace("hash-mismatch")])
    manifest["trace_set_sha256"] = "f" * 64
    receipt = evaluate_manifest(manifest)
    assert receipt["status"] == "BLOCKED_TRACE_PROVENANCE"
    assert receipt["paired_savings"] == []
    assert len(receipt["expected_trace_set_sha256"]) == 64
