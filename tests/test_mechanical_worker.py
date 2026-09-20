from __future__ import annotations

from tools.score_mechanical_worker import evaluate_manifest
from wrench_harness import execute_model_output
from wrench_harness.core import json_result
from wrench_harness.mechanical import mechanical_route


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


def test_mechanical_worker_scopes_coverage_to_eligible_traces_but_keeps_safety_global():
    eligible = {
        "id": "eligible",
        "family": "read_file",
        "category": "eligible",
        "model_input_tokens": 100,
        "workload_weight": 1,
        "arms": {
            "minimax_teacher_only": _arm(frontier_tokens=1000),
            "rules_plus_minimax_fallback": _arm(frontier_tokens=1000),
            "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=0),
            "wrench_only_diagnostic": _arm(frontier_tokens=0),
        },
    }
    boundary = {
        "id": "boundary",
        "family": "read_file",
        "category": "boundary",
        "model_input_tokens": 100,
        "workload_weight": 1,
        "arms": {
            "minimax_teacher_only": _arm(frontier_tokens=10),
            "rules_plus_minimax_fallback": _arm(frontier_tokens=10),
            "wrench_plus_identical_minimax_fallback": _arm(frontier_tokens=10, unsafe=True),
            "wrench_only_diagnostic": _arm(frontier_tokens=0),
        },
    }
    receipt = evaluate_manifest(_manifest([eligible, boundary]))
    assert receipt["mechanical_scope"] == "eligible_category"
    assert receipt["mechanical_trace_count"] == 1
    assert receipt["metrics"]["weighted_frontier_token_mass_coverage"] == 1.0
    assert receipt["gates"]["zero_prohibited_accepts"] is False


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


def test_prompt_semantic_boundary_guards_fail_closed():
    proposal = '{"schema":"wrench.proposal.v1","action":"literal_search","root":".","literal":"x","max_matches":10}'
    assert execute_model_output(proposal, ".", request_prompt="Search for an empty literal.") == {
        "status": "abstain",
        "fallback_reason": "invalid_literal",
    }
    assert execute_model_output(proposal, ".", request_prompt="Search a missing root.") == {
        "status": "abstain",
        "fallback_reason": "missing_search_root",
    }
    assert execute_model_output(proposal, ".", request_prompt="Search with a null root.") == {
        "status": "abstain",
        "fallback_reason": "search_root_outside_allowed_root",
    }
    assert execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}',
        ".",
        request_prompt="Check a non-repository source directory.",
    ) == {"status": "abstain", "fallback_reason": "repository_root_invalid"}
    assert execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"git_read_status","repo_root":"."}',
        ".",
        request_prompt="Read the binary Git index as text.",
    ) == {"status": "abstain", "fallback_reason": "encoding_or_read_error"}
    assert execute_model_output(
        '{"schema":"wrench.proposal.v1","action":"patch_draft","files":["README.md"],"review_only":true,"diff":"--- a/README.md\\n+++ b/README.md\\n-old\\n+new\\n"}',
        ".",
        request_prompt="Draft a patch without a hunk marker.",
    ) == {"status": "abstain", "fallback_reason": "patch_not_unified_diff"}


def test_mechanical_health_route_uses_bounded_defaults_without_model_call():
    proposal = mechanical_route(
        "Read the local health endpoint at http://127.0.0.1:4000/v1/models with a bounded timeout."
    )
    assert proposal == {
        "schema": "wrench.proposal.v1",
        "action": "health_read",
        "url": "http://127.0.0.1:4000/v1/models",
        "timeout_seconds": 3.0,
        "max_bytes": 64 * 1024,
    }


def test_mechanical_health_route_leaves_external_endpoint_to_verifier():
    proposal = mechanical_route("Read an external health endpoint at http://example.com/health.")
    assert proposal == {
        "status": "abstain",
        "fallback_reason": "health_endpoint_not_allowlisted",
    }


def test_mechanical_route_handles_explicit_invalid_boundaries_without_model_guessing():
    cases = {
        "Read README.md with a limit above the verifier maximum.": "invalid_byte_limit",
        "Read the binary Git index as lines.": "encoding_or_read_error",
        "Read lines past the end of README.md.": "invalid_line_bounds",
        "Read a missing line-range file.": "missing_path",
        "Read the tests directory as lines.": "missing_path",
        "Search with a boolean match limit.": "invalid_match_limit",
        "Check Git status in a missing directory.": "repository_root_invalid",
        "Check a non-repository source directory.": "repository_root_invalid",
        "Read a health URL with a fragment.": "health_endpoint_not_allowlisted",
        "Draft a patch without the new-file marker.": "patch_not_unified_diff",
        "Draft a patch for a missing file.": "patch_file_invalid",
        "Apply a patch immediately.": "patch_draft_requires_review_only",
        "Read the parent directory README.": "path_outside_allowed_root",
        "Read a line range outside the repository.": "path_outside_allowed_root",
    }
    for prompt, reason in cases.items():
        assert mechanical_route(prompt) == {"status": "abstain", "fallback_reason": reason}
