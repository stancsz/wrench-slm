"""Regression checks for the observed experiment and accounting drift."""
from copy import deepcopy
import pytest

from tools import check_token30_objective as guard


@pytest.fixture
def objective():
    return guard.load_object(guard.REPO / guard.OBJECTIVE_PATH)[0]


@pytest.fixture
def plan(objective):
    return {
        "schema": guard.PLAN_SCHEMA, "objective_id": guard.OBJECTIVE_ID,
        "objective_sha256": "a" * 64, "primary_metric": objective["primary_metric"],
        "task_family": "multi-module regression diagnosis",
        "tasks": [{"id": "stable-task-1", "source_sha256": "b" * 64,
                   "requirements_sha256": "c" * 64, "oracle_sha256": "d" * 64}],
        "arms": {
            "baseline": {"workflow": "frontier_only"},
            "candidate": {"workflow": "qwen_assisted", "local_model": deepcopy(objective["current_local_model"]),
                          "local_work": "preparation", "local_output_consumption": "context_handoff",
                          "adapter_identity": "none"}},
        "accounting": {**{key: objective[key] for key in
                         ("frontier_accounting", "local_token_weight", "unknown_usage", "budget_scope", "retain_tighter_campaign_caps")},
                       "per_task_cap_usd": "1.00", "durable_ledger_ref": "existing-stable-task-ledger"},
        "quality": {key: True for key in
                    ("same_frozen_tasks_and_oracle", "require_successful_baseline_and_candidate", "retain_failed_tasks")},
        "identities": {key: "e" * 64 for key in
                       ("runner_sha256", "prompts_sha256", "frontier_route_sha256", "prices_sha256", "local_runtime_sha256")},
        "limits": {"max_frontier_calls": 6, "max_local_calls": 6, "wall_seconds": 1200, "storage_reserve_bytes": 10_000_000}}


def test_real_entrypoints_align(objective):
    guard.validate_objective(objective)
    guard.check_documentation(guard.REPO, objective)


def test_consumed_local_plan_aligns(plan, objective):
    guard.validate_plan(plan, objective, "a" * 64)


@pytest.mark.parametrize("field,value", [("workflow", "frontier_only"),
    ("local_output_consumption", "discarded"), ("local_model", None), ("local_work", "unused_sidecar")])
def test_no_useful_qwen_candidate_is_rejected(plan, objective, field, value):
    plan["arms"]["candidate"][field] = value
    with pytest.raises(ValueError):
        guard.validate_plan(plan, objective, "a" * 64)


@pytest.mark.parametrize("field,value", [("local_token_weight", 1),
    ("frontier_accounting", "initial_prompt_only"), ("per_task_cap_usd", "1.01"),
    ("budget_scope", "new_run_directory"), ("unknown_usage", "assume_zero"),
    ("retain_tighter_campaign_caps", False)])
def test_metric_or_budget_substitution_is_rejected(plan, objective, field, value):
    plan["accounting"][field] = value
    with pytest.raises(ValueError):
        guard.validate_plan(plan, objective, "a" * 64)


def test_dropping_failed_tasks_is_rejected(plan, objective):
    plan["quality"]["retain_failed_tasks"] = False
    with pytest.raises(ValueError):
        guard.validate_plan(plan, objective, "a" * 64)


def test_mismatched_objective_bytes_are_rejected(plan, objective):
    with pytest.raises(ValueError, match="current objective bytes"):
        guard.validate_plan(plan, objective, "f" * 64)


def test_unfrozen_or_repeated_task_is_rejected(plan, objective):
    plan["tasks"].append(deepcopy(plan["tasks"][0]))
    with pytest.raises(ValueError, match="duplicate stable"):
        guard.validate_plan(plan, objective, "a" * 64)
    plan["tasks"].pop()
    del plan["tasks"][0]["oracle_sha256"]
    with pytest.raises(ValueError, match="oracle_sha256"):
        guard.validate_plan(plan, objective, "a" * 64)


@pytest.mark.parametrize("cap", [True, "NaN", "Infinity", "0", "-1"])
def test_invalid_caps_cannot_bypass_spend_limit(plan, objective, cap):
    plan["accounting"]["per_task_cap_usd"] = cap
    with pytest.raises(ValueError):
        guard.validate_plan(plan, objective, "a" * 64)


def test_changed_target_is_explicit_drift(objective):
    objective["target_reduction"] = 0.03
    with pytest.raises(ValueError, match="target_reduction"):
        guard.validate_objective(objective)


def test_legacy_zero_qwen_plan_cannot_qualify(objective):
    legacy = {"schema": "wrench.token30.frontier-pilot.v1", "local_model_calls": 0,
              "max_calls": 6, "token_gate": "every pair saves >=30%"}
    with pytest.raises(ValueError, match="not a qualifying"):
        guard.validate_plan(legacy, objective, "a" * 64)


def test_duplicate_json_keys_fail_closed(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"local_token_weight": 1, "local_token_weight": 0}')
    with pytest.raises(ValueError, match="duplicate JSON key"):
        guard.load_object(path)
