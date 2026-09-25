#!/usr/bin/env python3
"""Measure exact no-model read/search execution on the admitted open fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wrench_harness import execute_model_output
from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.mechanical import mechanical_route
from wrench_harness.snapshot import bind_source_root, create_snapshot
from wrench_harness.synthetic_fixture_admission import validate_synthetic_fixture_admission


FIXTURE_DIR = ROOT / "tests" / "fixtures" / "e0_synthetic_matched_tasks_v1"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SIDECAR_PATH = FIXTURE_DIR / "manifest.sha256"
REVIEW_PATH = ROOT / "docs" / "evals" / "wrench-e0-synthetic-matched-tasks" / "review.md"
ARTIFACT_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-local-acceptability")
TEMP_ROOT = ARTIFACT_ROOT / "tmp"
ALLOWED_EXECUTOR_ACTIONS = {"read_file", "literal_search"}
SOURCE_PATHS = (
    ROOT / "src" / "wrench_harness" / "e0_rule_route.py",
    ROOT / "src" / "wrench_harness" / "mechanical.py",
    ROOT / "src" / "wrench_harness" / "snapshot.py",
    ROOT / "src" / "wrench_harness" / "core.py",
    ROOT / "src" / "wrench_harness" / "synthetic_fixture_admission.py",
    ROOT / "tools" / "measure_local_task_acceptability.py",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _normalize_path(value: Any, root: Path) -> Any:
    if not isinstance(value, str):
        return value
    candidate = Path(value)
    if not candidate.is_absolute():
        return value.replace("\\", "/")
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("executor returned a path outside the isolated fixture root") from exc


def _normalize_route_observation(observation: dict[str, Any], root: Path) -> dict[str, Any]:
    normalized = dict(observation)
    if "path" in normalized:
        normalized["path"] = _normalize_path(normalized["path"], root)
    if "root" in normalized:
        normalized["root"] = _normalize_path(normalized["root"], root)
    if "matches" in normalized:
        normalized["matches"] = [
            {**match, "path": _normalize_path(match.get("path"), root)}
            for match in normalized["matches"]
        ]
    return normalized


def _normalize_executor_observation(observation: dict[str, Any], root: Path) -> dict[str, Any]:
    normalized = dict(observation)
    if "path" in normalized:
        normalized["path"] = _normalize_path(normalized["path"], root)
    if "root" in normalized:
        normalized["root"] = _normalize_path(normalized["root"], root)
    if "matches" in normalized:
        normalized["matches"] = [
            {**match, "path": _normalize_path(match.get("path"), root)}
            for match in normalized["matches"]
        ]
    return normalized


def _expected_core_observation(expected: dict[str, Any]) -> dict[str, Any]:
    observation = dict(expected)
    # The independent core executor reports its bounded live-root observation;
    # only fields it actually returns are compared. E0 separately proves the
    # full snapshot-scoped observation, including its explicit scope marker.
    observation.pop("scope", None)
    return observation


def _expected_observation(case: dict[str, Any], *, include_scope: bool) -> dict[str, Any]:
    expected = case["expected_mechanics"]
    observation = dict(expected["observation"])
    if expected.get("action") == "read_file":
        source = next(item for item in case["files"] if item["path"] == observation["path"])
        observation["bytes"] = len(source["content_utf8"].encode("utf-8"))
    if not include_scope:
        observation.pop("scope", None)
    return observation


def _case_source_state(case: dict[str, Any], root: Path) -> dict[str, str]:
    paths = {item["path"]: item["sha256"] for item in case["files"]}
    mutation = case.get("mutate_after_snapshot")
    if mutation is not None:
        paths[mutation["path"]] = mutation["sha256"]
    observed: dict[str, str] = {}
    for relative, expected_hash in paths.items():
        path = root.joinpath(*relative.split("/"))
        if not path.is_file():
            observed[relative] = "missing"
            continue
        actual = _sha256(path.read_bytes())
        observed[relative] = actual
        if actual != expected_hash:
            raise ValueError(f"fixture source identity mismatch for {relative}")
    tree: dict[str, str] = {}
    for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in [*directories, *filenames]:
            path = current_path / name
            if path.is_symlink():
                raise ValueError("symlink appeared in isolated fixture tree")
            relative = path.relative_to(root).as_posix()
            if path.is_file():
                tree[relative] = _sha256(path.read_bytes())
            elif not path.is_dir():
                raise ValueError("non-regular entry appeared in isolated fixture tree")
    if tree != observed:
        raise ValueError("isolated fixture tree differs from its frozen file inventory")
    return observed


def _load_fixture() -> tuple[dict[str, Any], str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sidecar_digest, sidecar_name = SIDECAR_PATH.read_text(encoding="ascii").split()
    if sidecar_name != MANIFEST_PATH.name or _sha256(_canonical_bytes(manifest)) != sidecar_digest:
        raise ValueError("synthetic fixture manifest identity mismatch")
    review = manifest["admission"]["review"]
    if review["receipt_path"] != "docs/evals/wrench-e0-synthetic-matched-tasks/review.md":
        raise ValueError("synthetic fixture review path changed")
    admission = validate_synthetic_fixture_admission(
        manifest,
        manifest_sha256=sidecar_digest,
        requested_usage="open_development_fixture_only",
        review_receipt_path=review["receipt_path"],
        review_receipt_bytes=REVIEW_PATH.read_bytes(),
    )
    if not admission.admitted:
        raise ValueError(f"synthetic fixture admission rejected: {admission.reason}")
    return manifest, sidecar_digest, admission


def measure(output_path: Path) -> dict[str, Any]:
    output_path = output_path.resolve()
    try:
        output_path.relative_to(ARTIFACT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("receipt path must remain below the approved Wrench artifact root") from exc
    if output_path.exists():
        raise FileExistsError("refusing to overwrite an existing local-acceptability receipt")

    manifest, manifest_digest, admission = _load_fixture()
    rows: list[dict[str, Any]] = []
    group_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    started = time.perf_counter()
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="local-exec-accept-", dir=TEMP_ROOT) as scratch_name:
        scratch = Path(scratch_name)
        for pair in manifest["pairs"]:
            group = pair["pair_id"]
            for case in pair["cases"]:
                case_started = time.perf_counter()
                fixture_root = scratch / case["case_id"]
                fixture_root.mkdir()
                for item in case["files"]:
                    content = item["content_utf8"].encode("utf-8")
                    if _sha256(content) != item["sha256"]:
                        raise ValueError(f"fixture source hash mismatch for {case['case_id']}")
                    path = fixture_root.joinpath(*item["path"].split("/"))
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)

                root_binding = bind_source_root(fixture_root)
                snapshot = create_snapshot(root_binding, [item["path"] for item in case["files"]])
                mutation = case.get("mutate_after_snapshot")
                if mutation is not None:
                    changed = fixture_root.joinpath(*mutation["path"].split("/"))
                    changed.write_bytes(mutation["content_utf8"].encode("utf-8"))

                before_state = _case_source_state(case, fixture_root)
                route_started = time.perf_counter()
                routed = run_e0_rule_route(
                    case["prompt"], root_binding=root_binding, snapshot=snapshot
                )
                route_ms = (time.perf_counter() - route_started) * 1000
                expected = case["expected_mechanics"]
                expected_status = expected["status"]
                route_status = routed.status.value
                route_observation = (
                    _normalize_route_observation(routed.observation, fixture_root)
                    if routed.observation is not None
                    else None
                )
                expected_route_observation = _expected_observation(case, include_scope=True) if expected_status == "completed" else None
                route_exact = (
                    route_status == expected_status
                    and routed.action == expected.get("action")
                    and (routed.reason == expected.get("reason") if expected_status == "abstain" else True)
                    and route_observation == expected_route_observation
                )

                executor_called = False
                executor_status: str | None = None
                executor_reason: str | None = None
                executor_exact: bool | None = None
                executor_ms: float | None = None
                if expected_status == "completed":
                    proposal = mechanical_route(case["prompt"], allowed_root=fixture_root)
                    if type(proposal) is not dict or proposal.get("action") not in ALLOWED_EXECUTOR_ACTIONS:
                        raise ValueError(f"unexpected or missing operation proposal for {case['case_id']}")
                    if routed.status is not RuleRouteStatus.COMPLETED or routed.action != proposal.get("action"):
                        raise ValueError(f"route/parser action disagreement for {case['case_id']}")
                    executor_started = time.perf_counter()
                    executed = execute_model_output(
                        json.dumps(proposal, ensure_ascii=False, separators=(",", ":")),
                        fixture_root,
                        request_prompt=case["prompt"],
                    )
                    executor_ms = (time.perf_counter() - executor_started) * 1000
                    executor_called = True
                    executor_status = executed.get("status")
                    executor_reason = executed.get("fallback_reason")
                    observed_executor = executed.get("observation")
                    if isinstance(observed_executor, dict):
                        observed_executor = _normalize_executor_observation(observed_executor, fixture_root)
                    expected_executor = _expected_core_observation(
                        _expected_observation(case, include_scope=False)
                    )
                    executor_exact = (
                        executor_status == "accepted"
                        and executed.get("action") == expected.get("action")
                        and observed_executor == expected_executor
                        and executed.get("model_output_validated") is True
                    )

                after_state = _case_source_state(case, fixture_root)
                mutated = before_state != after_state
                if mutated:
                    raise ValueError(f"executor unexpectedly changed fixture source for {case['case_id']}")
                case_pass = route_exact and (executor_exact is True if executor_called else expected_status == "abstain")
                row = {
                    "case_id": case["case_id"],
                    "group": group,
                    "fixture_group": pair["group"],
                    "expected_status": expected_status,
                    "expected_action": expected.get("action"),
                    "route_status": route_status,
                    "route_action": routed.action,
                    "route_reason": routed.reason,
                    "route_evidence_count": len(routed.evidence),
                    "route_evidence_sha256": sorted(
                        evidence.content_sha256 for evidence in routed.evidence if evidence.content_sha256
                    ),
                    "route_observation_exact": route_exact,
                    "executor_called": executor_called,
                    "executor_status": executor_status,
                    "executor_reason": executor_reason,
                    "executor_observation_exact": executor_exact,
                    "unexpected_mutations": int(mutated),
                    "route_elapsed_ms": round(route_ms, 4),
                    "executor_elapsed_ms": round(executor_ms, 4) if executor_ms is not None else None,
                    "case_elapsed_ms": round((time.perf_counter() - case_started) * 1000, 4),
                    "case_pass": case_pass,
                }
                rows.append(row)
                group_rows[group].append(row)

    group_results = {}
    for group, group_cases in sorted(group_rows.items()):
        accepted = sum(row["expected_status"] == "completed" and row["case_pass"] for row in group_cases)
        abstained = sum(row["expected_status"] == "abstain" and row["case_pass"] for row in group_cases)
        group_results[group] = {
            "cases": len(group_cases),
            "exact_completed_operations": accepted,
            "correct_abstentions": abstained,
            "false_abstentions": sum(
                row["expected_status"] == "completed" and row["route_status"] == "abstain"
                for row in group_cases
            ),
            "unresolved_or_wrong": sum(not row["case_pass"] for row in group_cases),
            "operation_screen_pass": bool(group_cases) and all(row["case_pass"] for row in group_cases),
        }

    head = _git_head()
    return {
        "schema": "wrench.local_deterministic_execution_screen.v1",
        "status": "PASS_FIXTURE_MECHANICS" if rows and all(row["case_pass"] for row in rows) else "FAIL_FIXTURE_MECHANICS",
        "scope": "open_development_synthetic_operation_mechanics_only",
        "repo_head": head,
        "fixture_manifest_sha256": manifest_digest,
        "fixture_review_receipt_sha256": _sha256(REVIEW_PATH.read_bytes()),
        "fixture_usage": admission.usage,
        "source_sha256": {path.relative_to(ROOT).as_posix(): _sha256(path.read_bytes()) for path in SOURCE_PATHS},
        "measurement_runner_sha256": _sha256(Path(__file__).read_bytes()),
        "action_allowlist": sorted(ALLOWED_EXECUTOR_ACTIONS),
        "case_count": len(rows),
        "exact_route_outcomes": sum(row["route_observation_exact"] for row in rows),
        "exact_executor_observations": sum(row["executor_observation_exact"] is True for row in rows),
        "correct_abstentions": sum(row["expected_status"] == "abstain" and row["case_pass"] for row in rows),
        "false_abstentions": sum(row["expected_status"] == "completed" and row["route_status"] == "abstain" for row in rows),
        "unexpected_mutations": sum(row["unexpected_mutations"] for row in rows),
        "runtime_errors": 0,
        "group_results": group_results,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 4),
        "frontier_token_savings_percent": None,
        "frontier_calls": 0,
        "provider_calls": 0,
        "training": False,
        "model_inference": False,
        "quality_claim": False,
        "cases": rows,
        "limitations": [
            "All ten cases are exposed Wrench-authored open-development synthetic mechanics fixtures.",
            "The evaluated user requests are explicit read/search operations, not general coding-agent questions.",
            "The core executor reads the isolated current fixture tree; snapshot freshness is enforced separately by E0.",
            "This result does not establish real-work utility, SLM acceptability, production readiness, or frontier-token savings.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = measure(args.output)
    payload = (json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    args.output.resolve().write_bytes(payload)
    print(json.dumps({
        "status": receipt["status"],
        "case_count": receipt["case_count"],
        "exact_route_outcomes": receipt["exact_route_outcomes"],
        "exact_executor_observations": receipt["exact_executor_observations"],
        "correct_abstentions": receipt["correct_abstentions"],
        "false_abstentions": receipt["false_abstentions"],
        "unexpected_mutations": receipt["unexpected_mutations"],
        "groups": receipt["group_results"],
        "receipt_sha256": _sha256(payload),
        "output": str(args.output.resolve()),
    }, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS_FIXTURE_MECHANICS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
