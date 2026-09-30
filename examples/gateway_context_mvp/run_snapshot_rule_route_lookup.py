"""Exercise the production-shaped Wrench snapshot rule route on demo lookups.

The route can only read files present in one immutable source snapshot. Small
stdlib parsers answer three synthetic mechanical questions after retrieval.
Unsupported, missing, and stale reads must abstain. No model/provider is used.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from examples.gateway_context_mvp import run_demo as demo
from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.snapshot import bind_source_root, create_snapshot

JOB_ID = os.environ.get("WRENCH_DEMO_JOB_ID", "WRENCH-SNAPSHOT-RULE-LOOKUP-ITER124")
OUTPUT = Path(os.environ.get(
    "WRENCH_DEMO_OUTPUT_PATH",
    r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\snapshot-rule-lookup-iter124.json",
))
APPROVED_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp")
TEMP_ROOT = APPROVED_ROOT / "tmp"
EXPECTED_FIXTURE_SHA256 = "92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1"
CASES = (
    ("retry-policy", "config/service.toml", "3,250"),
    ("session-lifetime", "config/service.toml", "1800,300"),
    ("retry-function", "src/retry.py", "calculate_retry_delay"),
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def answer_from_snapshot(case_id: str, source: str) -> tuple[str, tuple[str, ...]]:
    if case_id in {"retry-policy", "session-lifetime"}:
        config = tomllib.loads(source)
        if case_id == "retry-policy":
            retry = config["retry"]
            if 429 not in retry["retry_statuses"]:
                raise ValueError("requested_status_not_configured_for_retry")
            return f"{retry['max_retries']},{retry['initial_backoff_ms']}", (
                f"retry_statuses = {retry['retry_statuses']}",
                f"max_retries = {retry['max_retries']}",
                f"initial_backoff_ms = {retry['initial_backoff_ms']}",
            )
        auth = config["auth"]
        return f"{auth['session_timeout_seconds']},{auth['refresh_before_expiry_seconds']}", (
            f"session_timeout_seconds = {auth['session_timeout_seconds']}",
            f"refresh_before_expiry_seconds = {auth['refresh_before_expiry_seconds']}",
        )

    if case_id == "retry-function":
        tree = ast.parse(source)
        definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                       and node.name == "calculate_retry_delay"]
        if len(definitions) != 1:
            raise ValueError("function_identity_ambiguous")
        returns = [node for node in ast.walk(definitions[0]) if isinstance(node, ast.Return)]
        if len(returns) != 1 or ast.get_source_segment(source, returns[0]) != (
            "return initial_backoff_ms * (2 ** max(0, attempt))"
        ):
            raise ValueError("function_body_unverified")
        return definitions[0].name, (
            source.splitlines()[definitions[0].lineno - 1],
            ast.get_source_segment(source, returns[0]),
        )
    raise ValueError("unknown_case_id")


def run() -> dict[str, Any]:
    if OUTPUT.exists():
        raise FileExistsError("refusing_to_overwrite_existing_snapshot_route_receipt")
    if APPROVED_ROOT.resolve() not in OUTPUT.resolve().parents:
        raise ValueError("receipt_path_outside_approved_demo_root")
    fixture_bytes = demo._canonical_json(demo.FIXTURE_FILES).encode("utf-8")
    if sha256(fixture_bytes) != EXPECTED_FIXTURE_SHA256:
        raise ValueError("frozen_fixture_identity_mismatch")

    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{JOB_ID.lower()}-", dir=TEMP_ROOT))
    source_root = temp_dir / "repository"
    source_root.mkdir()
    for relative, content in demo.FIXTURE_FILES.items():
        target = source_root.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")

    cases: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    try:
        binding = bind_source_root(source_root)
        snapshot = create_snapshot(binding, sorted(demo.FIXTURE_FILES))
        for case_id, path, expected in CASES:
            route_started = time.perf_counter()
            route = run_e0_rule_route(
                f"Read {path} with a 1024 byte limit.", root_binding=binding, snapshot=snapshot
            )
            route_seconds = time.perf_counter() - route_started
            row: dict[str, Any] = {
                "case_id": case_id,
                "route_status": route.status.value,
                "route": route.route,
                "action": route.action,
                "reason": route.reason,
                "snapshot_sha256": route.snapshot_sha256,
                "exact_read_attempts": route.exact_read_attempts,
                "exact_read_successes": route.exact_read_successes,
                "exact_read_bytes": route.exact_read_bytes,
                "evidence": [
                    {"path": item.path, "status": item.status,
                     "content_sha256": item.content_sha256, "size_bytes": item.size_bytes}
                    for item in route.evidence
                ],
                "route_seconds": round(route_seconds, 8),
                "verified": False,
            }
            if (route.status is RuleRouteStatus.COMPLETED and route.route == "none"
                    and route.action == "read_file" and isinstance(route.observation, dict)
                    and route.observation.get("path") == path
                    and type(route.observation.get("text")) is str):
                answer, required_evidence = answer_from_snapshot(case_id, route.observation["text"])
                visible = all(fragment in route.observation["text"] for fragment in required_evidence)
                row.update(
                    answer=answer,
                    expected=expected,
                    required_evidence=list(required_evidence),
                    required_evidence_visible=visible,
                    verified=answer == expected and visible,
                )
            else:
                row.update(answer=None, expected=expected, required_evidence_visible=False)
            cases.append(row)

        missing = run_e0_rule_route(
            "Read missing.py with a 1024 byte limit.", root_binding=binding, snapshot=snapshot
        )
        negatives.append({
            "case_id": "source_absent_from_snapshot",
            "expected": "abstain",
            "actual": missing.status.value,
            "reason": missing.reason,
            "passed": missing.status is RuleRouteStatus.ABSTAIN,
        })
        unsupported = run_e0_rule_route("Fix the retry bug and update the code.", root_binding=binding, snapshot=snapshot)
        negatives.append({
            "case_id": "unsupported_code_mutation_request",
            "expected": "abstain",
            "actual": unsupported.status.value,
            "reason": unsupported.reason,
            "passed": unsupported.status is RuleRouteStatus.ABSTAIN,
        })

        changed = source_root / "src" / "retry.py"
        changed.write_text(demo.FIXTURE_FILES["src/retry.py"] + "\n# changed after snapshot\n", encoding="utf-8")
        stale = run_e0_rule_route(
            "Read src/retry.py with a 1024 byte limit.", root_binding=binding, snapshot=snapshot
        )
        negatives.append({
            "case_id": "source_changed_after_snapshot",
            "expected": "abstain",
            "actual": stale.status.value,
            "reason": stale.reason,
            "passed": stale.status is RuleRouteStatus.ABSTAIN,
        })

        result = {
            "schema": "wrench.snapshot-bound-rule-lookup.v1",
            "job_id": JOB_ID,
            "status": "complete" if all(row["verified"] for row in cases) and all(row["passed"] for row in negatives) else "failed",
            "claim_scope": "three_synthetic_mechanical_lookups_through_Wrench_snapshot_bound_rule_route_plus_stdlib_parse",
            "tested_revision": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.strip(),
            "working_tree_dirty": bool(subprocess.run(
                ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.strip()),
            "fixture_sha256": sha256(fixture_bytes),
            "source_sha256": {
                "examples/gateway_context_mvp/run_snapshot_rule_route_lookup.py": sha256(Path(__file__).read_bytes()),
                "src/wrench_harness/e0_rule_route.py": sha256((ROOT / "src/wrench_harness/e0_rule_route.py").read_bytes()),
                "src/wrench_harness/mechanical.py": sha256((ROOT / "src/wrench_harness/mechanical.py").read_bytes()),
                "src/wrench_harness/snapshot.py": sha256((ROOT / "src/wrench_harness/snapshot.py").read_bytes()),
            },
            "snapshot_sha256": snapshot.snapshot_sha256,
            "cases": cases,
            "fail_closed_controls": negatives,
            "summary": {
                "case_count": len(cases),
                "verified_successes": sum(bool(row["verified"]) for row in cases),
                "route_read_attempts": sum(row["exact_read_attempts"] for row in cases),
                "route_read_successes": sum(row["exact_read_successes"] for row in cases),
                "source_bytes_read": sum(row["exact_read_bytes"] for row in cases),
                "fail_closed_controls_passed": sum(bool(row["passed"]) for row in negatives),
                "fail_closed_control_count": len(negatives),
                "model_calls": 0,
                "provider_calls": 0,
                "frontier_tokens_saved": None,
            },
            "limitations": [
                "three fixed authored synthetic question shapes, not unseen tasks or open-ended coding",
                "stdlib parsing happens after exact Wrench snapshot retrieval; no model is needed for this narrow slice",
                "does not measure frontier-only matched task outcomes, frontier token savings, all-in cost, or sustained engineering",
            ],
        }
    finally:
        shutil.rmtree(temp_dir)

    payload = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(payload) > 100_000:
        raise RuntimeError("snapshot_route_receipt_byte_limit_exceeded")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
