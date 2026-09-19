from __future__ import annotations

from tools.score_mechanical_worker import evaluate_manifest


def _arm(*, frontier_tokens: int, success: bool = True, fallback: bool = False, unsafe: bool = False) -> dict:
    return {
        "final_success": success,
        "verifier_success": success and not unsafe,
        "prohibited_accept": unsafe,
        "unexpected_mutation": False,
        "fallback_used": fallback,
        "frontier_tokens": frontier_tokens,
        "local_tokens": 20,
        "latency_ms": 100,
    }


def _manifest(traces: list[dict]) -> dict:
    return {"schema": "wrench.mechanical-worker-traces.v1", "traces": traces}


def test_mechanical_worker_uses_weighted_frontier_mass_not_case_count():
    traces = [
        {
            "id": "large",
            "family": "read_file",
            "model_input_tokens": 1_000_000,
            "workload_weight": 1,
            "arms": {
                "minimax_teacher_only": _arm(frontier_tokens=1000),
                "rules_plus_minimax_fallback": _arm(frontier_tokens=1000),
                "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=0),
                "wrench_only_diagnostic": _arm(frontier_tokens=0),
            },
        },
        {
            "id": "small",
            "family": "read_lines",
            "model_input_tokens": 100,
            "workload_weight": 1,
            "arms": {
                "minimax_teacher_only": _arm(frontier_tokens=10),
                "rules_plus_minimax_fallback": _arm(frontier_tokens=10),
                "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=0),
                "wrench_only_diagnostic": _arm(frontier_tokens=0),
            },
        },
    ]
    receipt = evaluate_manifest(_manifest(traces))
    assert receipt["metrics"]["weighted_frontier_token_mass_coverage"] == 1.0
    assert receipt["gates"]["weighted_mechanical_frontier_token_mass_coverage_at_least_90_percent"] is True


def test_mechanical_worker_requires_teacher_parity_and_zero_safety_violations():
    trace = {
        "id": "unsafe",
        "family": "read_file",
        "model_input_tokens": 200,
        "workload_weight": 1,
        "arms": {
            "minimax_teacher_only": _arm(frontier_tokens=100),
            "rules_plus_minimax_fallback": _arm(frontier_tokens=100),
            "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=0, unsafe=True),
            "wrench_only_diagnostic": _arm(frontier_tokens=0),
        },
    }
    receipt = evaluate_manifest(_manifest([trace]))
    assert receipt["status"] == "QUALITY_GATE_OPEN"
    assert receipt["gates"]["zero_prohibited_accepts"] is False


def test_mechanical_worker_rejects_payload_above_two_million():
    trace = {
        "id": "too-large",
        "family": "context_pressure",
        "model_input_tokens": 2_000_001,
        "workload_weight": 1,
        "arms": {
            "minimax_teacher_only": _arm(frontier_tokens=100),
            "rules_plus_minimax_fallback": _arm(frontier_tokens=100),
            "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=0),
            "wrench_only_diagnostic": _arm(frontier_tokens=0),
        },
    }
    try:
        evaluate_manifest(_manifest([trace]))
    except ValueError as exc:
        assert "2M native model limit" in str(exc)
    else:
        raise AssertionError("payload above the 2M limit was accepted")
