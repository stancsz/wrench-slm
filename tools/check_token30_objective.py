"""Read-only objective and proposed-plan guard. Never dispatches or scores a run.

Import validate_plan in the new paired runner before dispatch. A valid plan
does not establish actual Qwen consumption, complete usage or task quality.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
OBJECTIVE_PATH = Path("docs/goal/wrench-token30/objective.json")
OBJECTIVE_ID = "wrench-token30-qwen-assisted-v1"
PLAN_SCHEMA = "wrench.token30.qwen-assisted-plan.v1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_object(path: Path) -> tuple[dict, str]:
    with path.open("rb") as stream:
        raw = stream.read(1_048_577)
    require(len(raw) <= 1_048_576, "JSON exceeds 1 MiB")
    data = json.loads(raw, object_pairs_hook=strict_object)
    require(type(data) is dict, "JSON root must be an object")
    return data, hashlib.sha256(raw).hexdigest()


def usd(value) -> Decimal:
    require(type(value) in (str, int, float), "USD cap must be numeric")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid USD cap") from exc
    require(number.is_finite() and number > 0, "USD cap must be finite and positive")
    return number


def is_hash(value, length: int = 64) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value) is not None


def validate_objective(objective: dict) -> None:
    expected = {
        "schema": "wrench.token30.objective.v1",
        "objective_id": OBJECTIVE_ID,
        "primary_metric": "frontier_input_plus_output_full_workflow",
        "target_reduction": 0.30,
        "baseline_workflow": "frontier_only",
        "candidate_workflow": "qwen_assisted",
        "require_consumed_local_output": True,
        "local_token_weight": 0,
        "same_frozen_tasks_and_oracle": True,
        "require_successful_baseline_and_candidate": True,
        "retain_failed_tasks": True,
        "frontier_accounting": "all_calls_all_attempts_including_verification_recovery_and_escalation",
        "unknown_usage": "retain_hold_and_stop",
        "budget_scope": "stable_task_id_across_all_arms_diagnostics_and_reruns",
        "retain_tighter_campaign_caps": True,
        "artifact_limit_bytes_exclusive": 50_000_000_000,
        "minimum_free_ram_fraction": 0.10,
        "minimum_free_vram_fraction": 0.10,
        "goal": "docs/goal/wrench-token30/GOAL.md",
    }
    for key, value in expected.items():
        require(type(objective.get(key)) is type(value) and objective[key] == value,
                f"objective drift: {key}")
    require(usd(objective.get("per_task_cap_usd")) == Decimal("1.00"), "objective cap changed")
    model = objective.get("current_local_model")
    require(type(model) is dict and type(model.get("id")) is str
            and model["id"].startswith("Qwen/") and is_hash(model.get("revision"), 40),
            "pin the current Qwen model and revision")


def check_documentation(repo: Path, objective: dict) -> None:
    paths = ["AGENTS.md", "GOAL.md", "README.md", "docs/goal/README.md",
             "docs/goal/wrench-gateway-model-research/GOAL.md",
             "docs/archive/2026-10-08-clean-slate/LEARNINGS.md",
             "site/README.md"]
    for name in paths:
        require("wrench-token30/GOAL.md" in (repo / name).read_text(encoding="utf-8"),
                f"missing active-goal pointer: {name}")
    gateway = (repo / "docs/goal/wrench-gateway-model-research/GOAL.md").read_text(encoding="utf-8")
    require("Status: parked" in gateway, "old gateway goal must stay parked")
    contract, _ = load_object(repo / "COLLABORATION_CONTRACT.json")
    collaboration = contract.get("collaboration", {})
    require(collaboration.get("objective_id") == OBJECTIVE_ID, "authority points at another objective")
    require(collaboration.get("goal") == objective["goal"], "authority points at another goal")
    bounds = collaboration.get("bounds", {})
    require(usd(bounds.get("frontier_per_task_cap_usd")) == Decimal("1.00"), "authority cap drift")
    require(type(bounds.get("local_token_weight")) is int and bounds["local_token_weight"] == 0,
            "authority must exclude local tokens")
    require(bounds.get("monetary_budget_scope") == objective["budget_scope"], "authority budget scope drift")


def validate_plan(plan: dict, objective: dict, objective_sha256: str) -> None:
    validate_objective(objective)
    require(plan.get("schema") == PLAN_SCHEMA, "not a qualifying Qwen-assisted plan")
    require(plan.get("objective_id") == OBJECTIVE_ID, "plan objective mismatch")
    require(is_hash(objective_sha256) and plan.get("objective_sha256") == objective_sha256,
            "plan must pin the current objective bytes")
    require(plan.get("primary_metric") == objective["primary_metric"], "proxy metric rejected")
    require(type(plan.get("task_family")) is str and bool(plan["task_family"].strip()), "task family missing")
    tasks = plan.get("tasks")
    require(type(tasks) is list and bool(tasks), "freeze a nonempty shared task cohort")
    ids = set()
    for task in tasks:
        require(type(task) is dict and type(task.get("id")) is str and bool(task["id"].strip()), "task ID missing")
        require(task["id"] not in ids, "duplicate stable task ID")
        ids.add(task["id"])
        for key in ("source_sha256", "requirements_sha256", "oracle_sha256"):
            require(is_hash(task.get(key)), f"missing frozen task identity: {key}")
    arms = plan.get("arms")
    require(type(arms) is dict and set(arms) == {"baseline", "candidate"}, "freeze the two required arms")
    baseline, candidate = arms["baseline"], arms["candidate"]
    require(type(baseline) is dict and baseline.get("workflow") == "frontier_only", "baseline must be frontier-only")
    require(type(candidate) is dict and candidate.get("workflow") == "qwen_assisted", "candidate must use Qwen")
    require(candidate.get("local_model") == objective["current_local_model"], "local model identity mismatch")
    require(candidate.get("local_work") in ("preparation", "reasoning", "verified_task_work"), "useful Qwen work missing")
    require(candidate.get("local_output_consumption") in
            ("context_handoff", "verified_partial_work", "verified_completion"), "discarded local output cannot qualify")
    require(type(candidate.get("adapter_identity")) is str and bool(candidate["adapter_identity"].strip()),
            "freeze adapter identity, including none")
    accounting = plan.get("accounting")
    require(type(accounting) is dict, "frontier accounting missing")
    for key in ("frontier_accounting", "local_token_weight", "unknown_usage", "budget_scope", "retain_tighter_campaign_caps"):
        require(type(accounting.get(key)) is type(objective[key]) and accounting[key] == objective[key],
                f"accounting drift: {key}")
    require(usd(accounting.get("per_task_cap_usd")) <= usd(objective["per_task_cap_usd"]), "task cap exceeds $1")
    require(type(accounting.get("durable_ledger_ref")) is str and bool(accounting["durable_ledger_ref"].strip()),
            "reuse cumulative spend accounting, not a fresh budget")
    quality = plan.get("quality")
    require(type(quality) is dict, "quality policy missing")
    for key in ("same_frozen_tasks_and_oracle", "require_successful_baseline_and_candidate", "retain_failed_tasks"):
        require(quality.get(key) is True, f"quality gate missing: {key}")
    identities = plan.get("identities")
    require(type(identities) is dict, "run identities missing")
    for key in ("runner_sha256", "prompts_sha256", "frontier_route_sha256", "prices_sha256", "local_runtime_sha256"):
        require(is_hash(identities.get(key)), f"freeze run identity: {key}")
    limits = plan.get("limits")
    require(type(limits) is dict, "bounded job limits missing")
    for key in ("max_frontier_calls", "max_local_calls", "wall_seconds", "storage_reserve_bytes"):
        require(type(limits.get(key)) is int and limits[key] > 0, f"bound the job: {key}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="proposed plan JSON; never executes it")
    args = parser.parse_args(argv)
    try:
        objective, identity = load_object(REPO / OBJECTIVE_PATH)
        validate_objective(objective)
        check_documentation(REPO, objective)
        if args.manifest:
            plan, _ = load_object(args.manifest)
            validate_plan(plan, objective, identity)
        print(json.dumps({"status": "ALIGNED_PLAN_NOT_EXECUTION_PROOF" if args.manifest else "ALIGNED_DOCUMENTATION",
                          "objective_id": OBJECTIVE_ID, "objective_sha256": identity,
                          "dispatch": False, "target_achieved": False}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "OBJECTIVE_DRIFT", "reason": str(exc), "dispatch": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
