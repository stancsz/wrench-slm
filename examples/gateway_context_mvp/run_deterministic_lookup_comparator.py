"""Evaluate bounded deterministic lookups on the frozen gateway demo fixture.

This hand-written parser comparison is limited to three known TOML/Python
questions. It has no model, provider, shell, filesystem mutation, or retrieval
authority beyond the in-memory synthetic fixture.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from examples.gateway_context_mvp import run_demo as demo

JOB_ID = os.environ.get("WRENCH_DEMO_JOB_ID", "WRENCH-DETERMINISTIC-GUARD-ITER123")
OUTPUT = Path(os.environ.get(
    "WRENCH_DEMO_OUTPUT_PATH",
    r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\deterministic-guard-iter123.json",
))
APPROVED_ROOT = Path(r"C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp")
EXPECTED_FIXTURE_SHA256 = "92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1"
CASES = (
    ("retry-policy", "3,250"),
    ("session-lifetime", "1800,300"),
    ("retry-function", "calculate_retry_delay"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture_identity(files: dict[str, str]) -> str:
    return sha256(demo._canonical_json(files).encode("utf-8"))


def retry_policy_lookup(raw: str) -> tuple[str, tuple[str, ...]] | None:
    try:
        config = tomllib.loads(raw)
        retry = config["retry"]
        statuses = retry["retry_statuses"]
        retries = retry["max_retries"]
        delay = retry["initial_backoff_ms"]
        if type(statuses) is not list or type(retries) is not int or type(delay) is not int or 429 not in statuses:
            return None
        return f"{retries},{delay}", (
            f"retry_statuses = {statuses}",
            f"max_retries = {retries}",
            f"initial_backoff_ms = {delay}",
        )
    except (tomllib.TOMLDecodeError, KeyError, TypeError, ValueError):
        return None


def function_lookup(source: str, name: str) -> tuple[str, tuple[str, ...]] | None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(functions) != 1:
        return None
    selected = functions[0]
    returns = [node for node in ast.walk(selected) if isinstance(node, ast.Return)]
    if len(returns) != 1:
        return None
    return_source = ast.get_source_segment(source, returns[0])
    if return_source != "return initial_backoff_ms * (2 ** max(0, attempt))":
        return None
    source_lines = source.splitlines()
    signature = source_lines[selected.lineno - 1]
    return selected.name, (signature, return_source)


def answer_case(case_id: str, files: dict[str, str]) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    if fixture_identity(files) != EXPECTED_FIXTURE_SHA256:
        raise ValueError("stale_or_unapproved_fixture_identity")
    if case_id == "retry-policy":
        path = "config/service.toml"
        parsed = retry_policy_lookup(files[path])
        if parsed is None:
            raise ValueError("ambiguous_or_invalid_retry_configuration")
        answer, evidence = parsed
        return answer, (path,), evidence
    if case_id == "session-lifetime":
        path = "config/service.toml"
        config = tomllib.loads(files[path])
        auth = config["auth"]
        return f"{auth['session_timeout_seconds']},{auth['refresh_before_expiry_seconds']}", (path,), (
            f"session_timeout_seconds = {auth['session_timeout_seconds']}",
            f"refresh_before_expiry_seconds = {auth['refresh_before_expiry_seconds']}",
        )
    if case_id == "retry-function":
        path = "src/retry.py"
        parsed = function_lookup(files[path], "calculate_retry_delay")
        if parsed is None:
            raise ValueError("ambiguous_or_unverified_function_source")
        answer, evidence = parsed
        return answer, (path,), evidence
    raise ValueError("unknown_case_id")


def run() -> dict[str, Any]:
    if OUTPUT.exists():
        raise FileExistsError("refusing_to_overwrite_existing_deterministic_receipt")
    if APPROVED_ROOT.resolve() not in OUTPUT.resolve().parents:
        raise ValueError("receipt_path_outside_approved_demo_root")

    if fixture_identity(demo.FIXTURE_FILES) != EXPECTED_FIXTURE_SHA256:
        raise ValueError("frozen_fixture_identity_mismatch")

    results: list[dict[str, Any]] = []
    for case_id, expected in CASES:
        started = time.perf_counter()
        answer, paths, evidence = answer_case(case_id, demo.FIXTURE_FILES)
        elapsed = time.perf_counter() - started
        source_bytes = sum(len(demo.FIXTURE_FILES[path].encode("utf-8")) for path in paths)
        visible = all(line in demo.FIXTURE_FILES[path] for line in evidence for path in paths)
        results.append({
            "case_id": case_id,
            "source_paths": list(paths),
            "source_bytes_examined": source_bytes,
            "evidence_lines": list(evidence),
            "evidence_visible": visible,
            "answer": answer,
            "expected": expected,
            "verifier_passed": answer == expected and visible,
            "elapsed_seconds": round(elapsed, 8),
            "language_model_calls": 0,
            "provider_calls": 0,
            "model_tokens": 0,
            "answer_utf8_bytes": len(answer.encode("utf-8")),
        })

    malformed_toml = demo.FIXTURE_FILES["config/service.toml"].replace(
        "max_retries = 3", "max_retries = 3\nmax_retries = 7", 1
    )
    missing_field_toml = demo.FIXTURE_FILES["config/service.toml"].replace("max_retries = 3\n", "", 1)
    duplicate_function = demo.FIXTURE_FILES["src/retry.py"] + (
        "\ndef calculate_retry_delay(attempt: int) -> int:\n    return 0\n"
    )
    stale_files = dict(demo.FIXTURE_FILES)
    stale_files["config/service.toml"] = stale_files["config/service.toml"].replace(
        "max_retries = 3", "max_retries = 4", 1
    )
    negative_checks = (
        ("duplicate_toml_key", retry_policy_lookup(malformed_toml) is None),
        ("missing_required_toml_key", retry_policy_lookup(missing_field_toml) is None),
        ("duplicate_python_symbol", function_lookup(duplicate_function, "calculate_retry_delay") is None),
        ("stale_fixture_hash", fixture_identity(stale_files) != EXPECTED_FIXTURE_SHA256),
    )
    negative_results = [
        {"case_id": case_id, "expected_behavior": "abstain_or_reject", "observed_behavior_passed": passed}
        for case_id, passed in negative_checks
    ]

    fixture_bytes = demo._canonical_json(demo.FIXTURE_FILES).encode("utf-8")
    result = {
        "schema": "wrench.deterministic-lookup-comparator.v2",
        "job_id": JOB_ID,
        "status": "complete" if all(item["verifier_passed"] for item in results) and all(item["observed_behavior_passed"] for item in negative_results) else "failed",
        "claim_scope": "three_authored_synthetic_TOML_and_Python_lookups_with_fail_closed_mutation_controls",
        "tested_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "working_tree_dirty": bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()),
        "fixture_sha256": sha256(fixture_bytes),
        "local_model_comparator_receipt": {
            "job_id": "WRENCH-DEMO-BUDGET-SWEEP-ITER121",
            "receipt_sha256": "db7ec618e9c5612fc1df747768089a8f1ffa0a5fbbf61f77a30dbc7e2cd338aa",
            "context_budget": 64,
            "verified_successes": 3,
            "local_model_tokens": {"input": 1392, "output": 25},
        },
        "cases": results,
        "fail_closed_controls": negative_results,
        "summary": {
            "case_count": len(results),
            "verified_successes": sum(item["verifier_passed"] for item in results),
            "fail_closed_controls_passed": sum(item["observed_behavior_passed"] for item in negative_results),
            "fail_closed_control_count": len(negative_results),
            "source_bytes_examined_total": sum(item["source_bytes_examined"] for item in results),
            "deterministic_model_tokens": 0,
            "target_frontier_tokens_saved": None,
            "provider_spend_usd": 0,
            "total_seconds": round(sum(item["elapsed_seconds"] for item in results), 8),
        },
        "limitations": [
            "tasks, source fixture, query families, and expected answers are synthetic and predeclared",
            "fail-closed controls cover only malformed or changed forms included in this receipt",
            "direct parsed answers are a narrow mechanical baseline, not open-ended coding capacity",
            "zero model tokens by construction do not establish frontier-token savings or all-in cost savings",
            "does not measure uncompressed-model success retention, Wrench LoRA value, or all-day reliability",
        ],
    }
    payload = (json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(payload) > 50_000:
        raise RuntimeError("deterministic_receipt_byte_limit_exceeded")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
