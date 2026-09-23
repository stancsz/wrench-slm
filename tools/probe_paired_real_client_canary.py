#!/usr/bin/env python3
"""Run a paired direct-baseline versus Wrench-hybrid client canary.

The default baseline is a local deterministic OpenAI-compatible endpoint. A
human-authorized loopback gateway may be substituted for client compatibility
diagnostics, but that remains incomplete until provider accounting is observed.
The hybrid arm uses the real portable OpenCode and DeepSeek Harness launchers
against the current Wrench package's mechanical route.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import http.client
import json
import math
import os
import signal
import shutil
import secrets
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from .canary_answer_check import check_answer
    from .windows_job_process import run_bounded_subprocess as _run_windows_job_subprocess
except ImportError:
    from canary_answer_check import check_answer
    from windows_job_process import run_bounded_subprocess as _run_windows_job_subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
PARENT_CONTRACT_PATH = REPO_ROOT / "COLLABORATION_CONTRACT.json"
PROMPT = "Read README.md and report its first heading."
EXPECTED = "# Wrench SLM"
BASELINE_TEXT = "The first heading is # Wrench SLM."
WORKLOAD_SCHEMA = "wrench.paired-canary-workload.v1"
EXTERNAL_AUTHORIZATION = "approved_real_workflow"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
PAIRED_BASELINE_CLIENTS = ("opencode", "deepseek_harness")
CHILD_CONTRACT_SCHEMA = "wrench.paid-canary-child-contract.v3"
PARENT_CONTRACT_ID = "wrench-slm-productive-value-2026-09-22"
PARENT_ROUTE_ALLOWANCE_SCHEMA = "wrench.paid-canary-route-allowance.v1"
PROVIDER_COST_ACCOUNTING_SCHEMA = "wrench.provider-cost-accounting-binding.v1"
OPENAI_COSTS_ENDPOINT = "https://api.openai.com/v1/organization/costs"
SECONDS_PER_DAY = 24 * 60 * 60


def _text_tail(value: object, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            # Some Windows client launchers still write console text using the
            # active code page. Preserve those answers for the strict oracle
            # instead of losing output during subprocess capture.
            value = value.decode("cp1252", errors="replace")
    return str(value).strip()[-limit:]


def _run_bounded_subprocess(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    if os.name == "nt":
        result = _run_windows_job_subprocess(
            command,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
        )
        result["stdout"] = _text_tail(result["stdout"])
        result["stderr"] = _text_tail(result["stderr"])
        return result

    started = time.perf_counter()
    process_options: dict[str, Any] = {}
    process_options["start_new_session"] = True
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **process_options,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as timeout_error:
        tree_cleanup_complete = _terminate_process_tree(process)
        if tree_cleanup_complete:
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired as cleanup_error:
                tree_cleanup_complete = False
                stdout = cleanup_error.stdout or timeout_error.stdout or b""
                stderr = cleanup_error.stderr or timeout_error.stderr or b""
        else:
            stdout = timeout_error.stdout or b""
            stderr = timeout_error.stderr or b""
        if not tree_cleanup_complete:
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        return {
            "exit_code": None,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "stdout": _text_tail(stdout),
            "stderr": _text_tail(stderr),
            "tree_cleanup_complete": tree_cleanup_complete,
        }
    return {
        "exit_code": process.returncode,
        "timed_out": False,
        "timeout_seconds": timeout_seconds,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "stdout": _text_tail(stdout),
        "stderr": _text_tail(stderr),
        "tree_cleanup_complete": True,
    }


def _terminate_process_tree(process: subprocess.Popen[bytes], grace_seconds: float = 0.5) -> bool:
    """Terminate the POSIX process group owned by this bounded invocation."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return process.poll() is not None
    except OSError:
        return False
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        return False
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        return False
    return process.poll() is not None


def _classify_canary_status(
    *,
    baseline_correct: bool,
    hybrid_correct: bool,
    hybrid_frontier_tokens: int | None,
    hybrid_model_calls: int | None,
    accounting_complete: bool,
) -> str:
    if not hybrid_correct:
        return "FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY"
    if not baseline_correct:
        return "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_COMPARATOR_INVALID"
    if baseline_correct and hybrid_correct and not accounting_complete:
        return "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE"
    if baseline_correct and hybrid_correct:
        # Zero observed model calls or frontier tokens is not net savings.
        # This runner has no complete overhead reconciliation, so it cannot
        # issue the North Star's paired-canary pass yet.
        return "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED"
    return "INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_COMPARATOR_INVALID"


def _baseline_clients_correct(client_results: dict[str, Any]) -> bool:
    """Require every expected direct comparator and no missing client result."""
    return (
        set(client_results) == set(PAIRED_BASELINE_CLIENTS)
        and all(
            isinstance(client_results[name], dict)
            and client_results[name].get("correct") is True
            for name in PAIRED_BASELINE_CLIENTS
        )
    )


def _canary_process_exit_code(status: str) -> int:
    """Return success only for the scoped, fully accounted canary pass."""
    return 0 if status == "PASS_PAIRED_REAL_CLIENT_HYBRID_CANARY" else 1


def _canary_token_accounting(
    *,
    baseline_url_configured: bool,
    baseline_call_count: int,
    captured_frontier_tokens: object,
    hybrid_frontier_tokens: object,
) -> dict[str, int | float | str | None]:
    """Keep local-stub estimates and raw usage separate from net savings."""
    observed_tokens = (
        captured_frontier_tokens
        if baseline_url_configured
        and isinstance(captured_frontier_tokens, int)
        and not isinstance(captured_frontier_tokens, bool)
        and captured_frontier_tokens >= 0
        else None
    )
    stub_estimate = 516 * baseline_call_count if not baseline_url_configured else None
    diagnostic_baseline = observed_tokens if baseline_url_configured else stub_estimate
    raw_rate = None
    if (
        isinstance(diagnostic_baseline, int)
        and diagnostic_baseline > 0
        and isinstance(hybrid_frontier_tokens, int)
        and not isinstance(hybrid_frontier_tokens, bool)
        and hybrid_frontier_tokens >= 0
    ):
        raw_rate = 1.0 - hybrid_frontier_tokens / diagnostic_baseline
    return {
        "baseline_frontier_tokens": observed_tokens,
        "local_stub_synthetic_tokens_estimate": stub_estimate,
        "diagnostic_raw_token_reduction_rate": raw_rate,
        "diagnostic_token_basis": (
            "gateway_response_usage" if observed_tokens is not None
            else "synthetic_local_stub_estimate" if stub_estimate is not None
            else "unavailable"
        ),
        "frontier_token_reduction_rate": None,
        "net_frontier_token_savings_rate": None,
    }


def _compare_client_latencies(
    baseline_clients: dict[str, Any],
    hybrid: dict[str, Any],
    *,
    baseline_correct: bool,
) -> dict[str, Any]:
    """Pair comparable client timings without overstating one-run evidence."""

    observations: dict[str, Any] = {}
    hybrid_answers = hybrid.get("client_answers", {})
    hybrid_elapsed = hybrid.get("client_elapsed_ms", {})
    for client in PAIRED_BASELINE_CLIENTS:
        baseline = baseline_clients.get(client, {})
        baseline_ms = baseline.get("elapsed_ms")
        hybrid_ms = hybrid_elapsed.get(client)
        client_correct = (
            baseline_correct
            and baseline.get("correct") is True
            and isinstance(hybrid_answers.get(client), dict)
            and hybrid_answers[client].get("correct") is True
            and isinstance(baseline_ms, (int, float))
            and not isinstance(baseline_ms, bool)
            and math.isfinite(float(baseline_ms))
            and baseline_ms > 0
            and isinstance(hybrid_ms, (int, float))
            and not isinstance(hybrid_ms, bool)
            and math.isfinite(float(hybrid_ms))
            and hybrid_ms > 0
        )
        observations[client] = {
            "paired_successful_observation": client_correct,
            "baseline_elapsed_ms": baseline_ms if client_correct else None,
            "hybrid_elapsed_ms": hybrid_ms if client_correct else None,
            "latency_reduction_percent": (
                round((1 - float(hybrid_ms) / float(baseline_ms)) * 100, 3)
                if client_correct
                else None
            ),
        }
    return {
        "status": "DIAGNOSTIC_ONLY_INSUFFICIENT_TASK_PAIRS",
        "client_observations": observations,
        "successful_paired_task_count": int(any(
            item["paired_successful_observation"] for item in observations.values()
        )),
        "confidence_interval_95": None,
        "gate_c_claim": False,
        "reason": "one canary case cannot establish a task latency distribution or confidence interval",
    }


def _validate_external_baseline_guard(
    baseline_url: str,
    *,
    workload_authorization: str,
    allow_external_baseline: bool,
    api_key: str,
) -> None:
    parsed = urlparse(baseline_url)
    is_loopback = parsed.hostname in LOOPBACK_HOSTS
    if is_loopback:
        return
    if parsed.scheme.lower() != "https":
        raise RuntimeError("external baseline requires an https URL")
    if not allow_external_baseline:
        raise RuntimeError("external baseline requires --allow-external-baseline and human authorization")
    if workload_authorization != EXTERNAL_AUTHORIZATION:
        raise RuntimeError(f"external baseline requires workload authorization {EXTERNAL_AUTHORIZATION!r}")
    if not api_key:
        raise RuntimeError("missing baseline API key environment variable")


def _validate_parent_monetary_budget(parent_contract: object) -> float:
    if not isinstance(parent_contract, dict) or parent_contract.get("contract_id") != PARENT_CONTRACT_ID:
        raise RuntimeError("current parent Q4 contract identity invalid")
    collaboration = parent_contract.get("collaboration")
    bounds = collaboration.get("bounds") if isinstance(collaboration, dict) else None
    budget = bounds.get("monetary_budget") if isinstance(bounds, dict) else None
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not math.isfinite(budget) or budget < 0:
        raise RuntimeError("current parent Q4 monetary_budget invalid")
    return float(budget)


def _validate_parent_route_allowance(
    parent_contract: object,
    *,
    endpoint: str,
    gateway_model_alias: str,
    expected_provider_model: str,
) -> None:
    if not isinstance(parent_contract, dict):
        raise RuntimeError("current parent Q4 route allowance invalid")
    collaboration = parent_contract.get("collaboration")
    bounds = collaboration.get("bounds") if isinstance(collaboration, dict) else None
    allowance = bounds.get("paid_canary_route_allowance") if isinstance(bounds, dict) else None
    if not isinstance(allowance, dict):
        raise RuntimeError("current parent Q4 paid_canary_route_allowance missing or invalid")
    if (
        allowance.get("schema") != PARENT_ROUTE_ALLOWANCE_SCHEMA
        or allowance.get("decision") != "human.approve_commit"
        or allowance.get("status") != "APPROVED"
        or not isinstance(allowance.get("approved_by"), str)
        or not allowance["approved_by"].strip()
        or not isinstance(allowance.get("approval_reference"), str)
        or not allowance["approval_reference"].strip()
    ):
        raise RuntimeError("current parent Q4 paid_canary_route_allowance missing or invalid")
    routes = allowance.get("routes")
    if not isinstance(routes, list) or not routes:
        raise RuntimeError("current parent Q4 paid_canary_route_allowance missing or invalid")
    for route in routes:
        if not isinstance(route, dict) or any(
            not isinstance(route.get(field), str)
            or not route[field].strip()
            or route[field] != route[field].strip()
            for field in ("endpoint", "gateway_model_alias", "expected_provider_model")
        ):
            raise RuntimeError("current parent Q4 paid_canary_route_allowance missing or invalid")
    requested_route = {
        "endpoint": endpoint.rstrip("/"),
        "gateway_model_alias": gateway_model_alias,
        "expected_provider_model": expected_provider_model,
    }
    if not any(
        {
            "endpoint": route["endpoint"].rstrip("/"),
            "gateway_model_alias": route["gateway_model_alias"],
            "expected_provider_model": route["expected_provider_model"],
        }
        == requested_route
        for route in routes
    ):
        raise RuntimeError("child route is not authorized by parent Q4 route allowance")


def _read_current_parent_contract() -> tuple[dict[str, Any], str, float]:
    try:
        contract_bytes = PARENT_CONTRACT_PATH.read_bytes()
        contract = json.loads(contract_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("current parent Q4 contract unavailable or invalid") from exc
    if not isinstance(contract, dict):
        raise RuntimeError("current parent Q4 contract unavailable or invalid")
    budget = _validate_parent_monetary_budget(contract)
    return contract, hashlib.sha256(contract_bytes).hexdigest(), budget


def _validate_paid_baseline_child_contract(
    contract: object,
    *,
    parent_contract: object,
    parent_contract_sha256: str,
    baseline_url: str,
    baseline_model: str,
    workload_sha256: str,
    workload_authorization: str,
) -> dict[str, Any]:
    """Require an exact human child decision even for paid loopback gateways.

    The cap reference is a human-reviewed external control, not a cap enforced
    by this process. Never infer approval from a loopback hostname alone.
    """
    if workload_authorization != EXTERNAL_AUTHORIZATION:
        raise RuntimeError("configured baseline requires approved workload authorization")
    parent_budget = _validate_parent_monetary_budget(parent_contract)
    if (
        not isinstance(parent_contract_sha256, str)
        or len(parent_contract_sha256) != 64
        or any(character not in "0123456789abcdef" for character in parent_contract_sha256)
    ):
        raise RuntimeError("current parent Q4 contract hash invalid")
    if not isinstance(contract, dict):
        raise RuntimeError("approved child contract required for configured baseline")
    if contract.get("template") is True:
        raise RuntimeError("child contract template cannot authorize configured baseline")
    required = {
        "schema": CHILD_CONTRACT_SCHEMA,
        "parent_contract_id": PARENT_CONTRACT_ID,
        "parent_contract_sha256": parent_contract_sha256,
        "decision": "human.approve_commit",
        "status": "APPROVED",
        "workload_sha256": workload_sha256,
        "endpoint": baseline_url.rstrip("/"),
        "model": baseline_model,
        "repetitions": 1,
        "spend_cap_kind": "provider_hard_cap",
    }
    for field, expected in required.items():
        if contract.get(field) != expected or (field == "repetitions" and isinstance(contract.get(field), bool)):
            raise RuntimeError(f"child contract {field} mismatch")
    for field in (
        "approved_by",
        "approval_reference",
        "spend_cap_reference",
        "expected_provider_model",
    ):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            raise RuntimeError(f"child contract {field} missing")
    cap = contract.get("max_spend_usd")
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap <= 0:
        raise RuntimeError("child contract max_spend_usd invalid")
    if parent_budget <= 0:
        raise RuntimeError("parent monetary_budget is zero; configured baseline is blocked")
    if cap > parent_budget:
        raise RuntimeError("child contract max_spend_usd exceeds parent monetary_budget")
    _validate_parent_route_allowance(
        parent_contract,
        endpoint=contract["endpoint"],
        gateway_model_alias=contract["model"],
        expected_provider_model=contract["expected_provider_model"],
    )
    cost_accounting = contract.get("cost_accounting")
    if not isinstance(cost_accounting, dict) or cost_accounting.get("schema") != PROVIDER_COST_ACCOUNTING_SCHEMA:
        raise RuntimeError("child contract cost_accounting binding missing or invalid")
    accounting_mode = cost_accounting.get("mode")
    if accounting_mode == "provider_request_rows":
        if (
            not isinstance(cost_accounting.get("provider"), str)
            or not cost_accounting["provider"].strip()
            or not isinstance(cost_accounting.get("export_endpoint"), str)
            or not cost_accounting["export_endpoint"].startswith("https://")
            or not isinstance(cost_accounting.get("export_path_reference"), str)
            or not cost_accounting["export_path_reference"].strip()
        ):
            raise RuntimeError("child contract request-level cost export binding invalid")
    elif accounting_mode == "openai_organization_costs_daily_aggregate":
        if cost_accounting.get("provider") != "openai" or cost_accounting.get("export_endpoint") != OPENAI_COSTS_ENDPOINT:
            raise RuntimeError("child contract OpenAI Costs endpoint binding invalid")
        for field in ("project_id", "api_key_id", "isolation_evidence_reference", "spend_headroom_evidence_reference"):
            if not isinstance(cost_accounting.get(field), str) or not cost_accounting[field].strip():
                raise RuntimeError(f"child contract aggregate {field} missing")
        for field in ("dedicated_project", "exclusive_api_key", "exclusive_for_entire_interval"):
            if cost_accounting.get(field) is not True:
                raise RuntimeError(f"child contract aggregate {field} not approved")
        start = cost_accounting.get("bucket_start_time")
        end = cost_accounting.get("bucket_end_time")
        if (
            isinstance(start, bool)
            or not isinstance(start, int)
            or isinstance(end, bool)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or start % SECONDS_PER_DAY
            or end % SECONDS_PER_DAY
            or end - start > 2 * SECONDS_PER_DAY
        ):
            raise RuntimeError("child contract aggregate billing interval invalid")
        spend_before = cost_accounting.get("current_project_spend_usd")
        project_limit = cost_accounting.get("project_hard_limit_usd")
        overshoot_reserve = cost_accounting.get("hard_limit_overshoot_reserve_usd")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            for value in (spend_before, project_limit, overshoot_reserve)
        ):
            raise RuntimeError("child contract aggregate spend headroom invalid")
        if project_limit <= spend_before or overshoot_reserve <= 0:
            raise RuntimeError("child contract aggregate spend headroom exhausted")
        if project_limit - spend_before + overshoot_reserve > cap:
            raise RuntimeError("child contract aggregate hard limit lacks approved spend headroom")
    if any(field in contract for field in ("api_key", "secret", "access_token")):
        raise RuntimeError("child contract must not contain credentials")
    return contract


def _effective_baseline_api_key(baseline_url: str, api_key: str) -> str:
    """Give no-auth loopback gateways a non-secret provider placeholder."""

    if api_key:
        return api_key
    if urlparse(baseline_url).hostname in LOOPBACK_HOSTS:
        return "local-gateway"
    return ""


def _probe_loopback_spend_logs(baseline_url: str) -> dict[str, Any]:
    """Probe LiteLLM's read-only spend surface without sending a model call."""

    parsed = urlparse(baseline_url)
    if parsed.hostname not in LOOPBACK_HOSTS:
        return {"status": "not_attempted", "reason": "non_loopback_endpoint"}
    endpoint = f"{parsed.scheme}://{parsed.netloc}/spend/logs"
    request = urllib.request.Request(endpoint, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, list):
            row_count = len(payload)
        elif isinstance(payload, dict):
            rows = payload.get("data") or payload.get("logs") or []
            row_count = len(rows) if isinstance(rows, list) else None
        else:
            row_count = None
        return {
            "status": "observed",
            "endpoint": endpoint,
            "http_status": 200,
            "row_count": row_count,
            "request_correlation_observed": False,
        }
    except urllib.error.HTTPError as exc:
        return {
            "status": "http_error",
            "endpoint": endpoint,
            "http_status": exc.code,
            "request_correlation_observed": False,
        }
    except (OSError, ValueError) as exc:
        return {
            "status": "probe_error",
            "endpoint": endpoint,
            "error_type": type(exc).__name__,
            "request_correlation_observed": False,
        }


def _usage_from_response(body: bytes, content_type: str) -> dict[str, Any] | None:
    """Extract provider-reported usage from JSON or an SSE response body."""

    candidates: list[dict[str, Any]] = []
    if "text/event-stream" in content_type.lower():
        for line in body.decode("utf-8", errors="replace").splitlines():
            if not line.startswith("data: ") or line[6:] == "[DONE]":
                continue
            try:
                payload = json.loads(line[6:])
            except ValueError:
                continue
            if isinstance(payload, dict):
                candidates.append(payload)
    else:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            payload = None
        if isinstance(payload, dict):
            candidates.append(payload)
    for payload in reversed(candidates):
        usage = payload.get("usage")
        if isinstance(usage, dict):
            numeric = {}
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = usage.get(key)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    numeric = {}
                    break
                numeric[key] = value
            if (
                len(numeric) == 3
                and numeric["prompt_tokens"] + numeric["completion_tokens"]
                == numeric["total_tokens"]
            ):
                return numeric
    return None


def _read_trace_jsonl(path: Path) -> tuple[list[dict[str, Any]], bool]:
    """Read trace objects while making malformed or non-object rows fail closed."""
    if not path.is_file():
        return [], False
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], False
    rows: list[dict[str, Any]] = []
    well_formed = True
    for line in content.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (TypeError, ValueError):
            well_formed = False
            continue
        if not isinstance(row, dict):
            well_formed = False
            continue
        rows.append(row)
    return rows, well_formed and bool(rows)


def _trace_identity_accounting(rows: list[dict[str, Any]]) -> tuple[bool, bool]:
    """Require unique nonblank request IDs and a valid attempt identity per row."""
    request_ids = [row.get("request_id") for row in rows]
    request_ids_unique = (
        bool(rows)
        and all(isinstance(value, str) and value.strip() for value in request_ids)
        and len(set(request_ids)) == len(request_ids)
    )
    attempts = [(row.get("client_workflow_id"), row.get("client_attempt")) for row in rows]
    attempts_wellformed = all(
        isinstance(workflow_id, str)
        and bool(workflow_id.strip())
        and isinstance(attempt_number, int)
        and not isinstance(attempt_number, bool)
        and attempt_number > 0
        for workflow_id, attempt_number in attempts
    )
    attempts_unique = (
        bool(rows)
        and attempts_wellformed
        and len(set(attempts)) == len(attempts)
    )
    return request_ids_unique, attempts_unique


def _trace_token_accounting_complete(
    rows: list[dict[str, Any]], *, trace_jsonl_well_formed: bool
) -> bool:
    """Validate row identity and arithmetic before aggregating trace tokens."""
    request_ids_unique, attempts_unique = _trace_identity_accounting(rows)
    return bool(rows) and trace_jsonl_well_formed and request_ids_unique and attempts_unique and all(
        isinstance(cost := row.get("cost_accounting"), dict)
        and cost.get("schema") == "wrench.cost-accounting-receipt.v1"
        and cost.get("token_usage_complete") is True
        and all(
            isinstance(cost.get(field), int)
            and not isinstance(cost.get(field), bool)
            and cost[field] >= 0
            for field in (
                "frontier_tokens",
                "local_model_tokens",
                "total_workflow_tokens",
                "repair_passes",
                "local_model_calls",
                "frontier_model_calls",
            )
        )
        and isinstance(row.get("client_workflow_id"), str)
        and bool(row["client_workflow_id"].strip())
        and isinstance(row.get("client_attempt"), int)
        and not isinstance(row.get("client_attempt"), bool)
        and row["client_attempt"] > 0
        and isinstance(row.get("model_calls"), int)
        and not isinstance(row.get("model_calls"), bool)
        and row["model_calls"] == cost["local_model_calls"] + cost["frontier_model_calls"]
        and cost["total_workflow_tokens"] == cost["local_model_tokens"] + cost["frontier_tokens"]
        for row in rows
    )


def _iter_text_values(value: Any):
    """Yield request text transiently for exact purpose matching only."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_text_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_text_values(item)


def _classify_request_purpose(
    payload: dict[str, Any],
    *,
    task_marker: str | None = None,
    task_prompt: str | None = None,
    task_prompt_hmac_key: bytes | None = None,
) -> tuple[str, str | None, str]:
    """Classify source-confirmed title requests and opt-in task-marker matches."""
    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) > 32:
        return "unknown", None, "request_shape_out_of_scope"
    if any(not isinstance(message, dict) for message in messages):
        return "unknown", None, "request_shape_out_of_scope"
    tools = payload.get("tools")
    if "tools" in payload and not isinstance(tools, list):
        return "unknown", None, "request_shape_out_of_scope"

    text_values = list(_iter_text_values(messages))
    markers = (
        ("opencode_session_title_v1", "Generate a title for this conversation"),
        (
            "dsh_session_title_v1",
            "Generate the session title from this JSON array of human messages:",
        ),
    )
    title_shape = (
        len(messages) <= 3
        and all(message.get("role") in {"system", "user"} for message in messages)
        and not (isinstance(tools, list) and tools)
    )
    for marker_id, marker in markers:
        if any(text_value.lstrip().startswith(marker) for text_value in text_values):
            if title_shape:
                return "session_title_auxiliary", marker_id, "exact_source_confirmed_prefix"
            return "unknown", None, "request_shape_out_of_scope"
    if task_marker:
        marker_present = any(task_marker in text_value for text_value in text_values)
        roles = {
            message.get("role")
            for message in messages
            if isinstance(message.get("role"), str)
        }
        has_tool_result = "tool" in roles or "function" in roles
        has_tool_definitions = isinstance(tools, list) and bool(tools)
        marker_id = f"task_marker_sha256:{hashlib.sha256(task_marker.encode('utf-8')).hexdigest()}"
        if marker_present and (has_tool_result or has_tool_definitions):
            return "primary_task_workflow", marker_id, "opt_in_task_marker_and_task_state"
    if task_prompt:
        if not isinstance(task_prompt_hmac_key, bytes) or len(task_prompt_hmac_key) < 16:
            return "unknown", None, "task_prompt_hmac_key_missing_or_weak"
        user_text_values = [
            text_value
            for message in messages
            if message.get("role") == "user"
            for text_value in _iter_text_values(message.get("content"))
        ]
        prompt_present = any(task_prompt in text_value for text_value in user_text_values)
        roles = {
            message.get("role")
            for message in messages
            if isinstance(message.get("role"), str)
        }
        has_tool_result = "tool" in roles or "function" in roles
        has_tool_definitions = isinstance(tools, list) and bool(tools)
        prompt_id = hmac.new(
            task_prompt_hmac_key,
            task_prompt.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if prompt_present and (has_tool_result or has_tool_definitions):
            return "primary_task_workflow", f"task_prompt_hmac_sha256:{prompt_id}", "known_workload_prompt_hmac_and_task_state"
    return "unknown", None, "no_exact_source_confirmed_prefix"


def _client_for_timestamp(
    timestamp_unix_ms: int | float | None,
    client_windows: dict[str, dict[str, Any]],
) -> tuple[str | None, str]:
    if not isinstance(timestamp_unix_ms, (int, float)) or isinstance(timestamp_unix_ms, bool):
        return None, "request_timestamp_missing"
    matches = []
    for client_name, window in client_windows.items():
        if not isinstance(window, dict):
            continue
        started = window.get("started_at_unix_ms")
        finished = window.get("finished_at_unix_ms")
        if (
            isinstance(started, (int, float))
            and isinstance(finished, (int, float))
            and not isinstance(started, bool)
            and not isinstance(finished, bool)
            and started <= timestamp_unix_ms <= finished
        ):
            matches.append(client_name)
    if len(matches) == 1:
        return matches[0], "unique_subprocess_window"
    if len(matches) > 1:
        return None, "overlapping_subprocess_windows"
    return None, "no_matching_subprocess_window"


class _LoopbackAccountingProxy:
    """Forward one loopback OpenAI-compatible baseline and capture receipts."""

    def __init__(
        self,
        upstream_url: str,
        *,
        task_marker: str | None = None,
        task_prompt: str | None = None,
    ) -> None:
        parsed = urlparse(upstream_url)
        if parsed.hostname not in LOOPBACK_HOSTS:
            raise ValueError("accounting_proxy_requires_loopback_upstream")
        if task_marker is not None and task_prompt is not None:
            raise ValueError("task_marker_and_task_prompt_are_mutually_exclusive")
        self._parsed = parsed
        self._task_marker = task_marker
        self._task_prompt = task_prompt
        self._task_prompt_hmac_key = secrets.token_bytes(32) if task_prompt else None
        self._task_prompt_hmac = (
            hmac.new(
                self._task_prompt_hmac_key,
                task_prompt.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if task_prompt and self._task_prompt_hmac_key is not None
            else None
        )
        self._task_marker_sha256 = (
            hashlib.sha256(task_marker.encode("utf-8")).hexdigest()
            if task_marker else None
        )
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._idle = threading.Condition(self._lock)
        self._inflight = 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                owner._forward(self)

            def do_POST(self) -> None:  # noqa: N802
                owner._forward(self)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}{self._parsed.path.rstrip('/') or ''}"

    def start(self) -> None:
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _send_downstream_response(
        self,
        handler: BaseHTTPRequestHandler,
        *,
        status: int,
        headers: list[tuple[str, str]],
        body: bytes,
    ) -> None:
        handler.send_response(status)
        for key, value in headers:
            if key.lower() not in {"connection", "content-length", "transfer-encoding", "content-encoding"}:
                handler.send_header(key, value)
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        handler.wfile.flush()

    def _forward(self, handler: BaseHTTPRequestHandler) -> None:
        started = time.perf_counter()
        request_started_at_unix_ns = time.time_ns()
        request_started_at_unix_ms = request_started_at_unix_ns // 1_000_000
        length = int(handler.headers.get("Content-Length", "0"))
        request_body = handler.rfile.read(length) if length else b""
        request_payload: dict[str, Any] = {}
        try:
            parsed_request = json.loads(request_body.decode("utf-8")) if request_body else {}
            if isinstance(parsed_request, dict):
                request_payload = parsed_request
        except (UnicodeDecodeError, ValueError):
            pass
        headers = {
            key: value
            for key, value in handler.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "accept-encoding"}
        }
        headers["Accept-Encoding"] = "identity"
        target_host = self._parsed.hostname or "127.0.0.1"
        target_port = self._parsed.port or (443 if self._parsed.scheme == "https" else 80)
        connection_type = http.client.HTTPSConnection if self._parsed.scheme == "https" else http.client.HTTPConnection
        connection = connection_type(target_host, target_port, timeout=180)
        messages = request_payload.get("messages")
        purpose, purpose_marker_id, purpose_reason = _classify_request_purpose(
            request_payload,
            task_marker=self._task_marker,
            task_prompt=self._task_prompt,
            task_prompt_hmac_key=self._task_prompt_hmac_key,
        )
        transient_text_values = list(_iter_text_values(messages)) if isinstance(messages, list) else []
        task_marker_matched = bool(self._task_marker) and any(
            self._task_marker in text_value for text_value in transient_text_values
        )
        event: dict[str, Any] = {
            "request_started_at_unix_ns": request_started_at_unix_ns,
            "request_started_at_unix_ms": request_started_at_unix_ms,
            "model": request_payload.get("model"),
            "stream": bool(request_payload.get("stream")),
            "purpose": purpose,
            "purpose_marker_id": purpose_marker_id,
            "purpose_classification_reason": purpose_reason,
            "task_marker_matched": task_marker_matched,
            "purpose_classifier_version": "source-title-task-marker-known-prompt-hmac-v3",
            "request_shape": {
                "message_count": len(messages) if isinstance(messages, list) else None,
                "message_roles": [
                    message.get("role")
                    for message in messages
                    if isinstance(message, dict) and isinstance(message.get("role"), str)
                ] if isinstance(messages, list) else [],
                "tool_definition_count": len(request_payload.get("tools", []))
                if isinstance(request_payload.get("tools"), list) else None,
                "tool_result_present": any(
                    isinstance(message, dict) and message.get("role") == "tool"
                    for message in messages
                ) if isinstance(messages, list) else False,
            },
            "status": None,
            "elapsed_ms": None,
            "request_id": None,
            "usage": None,
            "cost_usd": None,
            "downstream_write_status": "not_attempted",
        }
        with self._idle:
            self._inflight += 1
        try:
            connection.request(handler.command, handler.path, body=request_body, headers=headers)
            response = connection.getresponse()
            body = response.read()
            response_headers = {key.lower(): value for key, value in response.getheaders()}
            content_type = response_headers.get("content-type", "")
            usage = _usage_from_response(body, content_type)
            request_id = (
                response_headers.get("x-litellm-call-id")
                or response_headers.get("x-request-id")
                or response_headers.get("x-litellm-trace-id")
            )
            if not request_id and content_type.startswith("application/json"):
                try:
                    response_payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, ValueError):
                    response_payload = {}
                request_id = response_payload.get("id") if isinstance(response_payload, dict) else None
            cost_text = response_headers.get("x-litellm-response-cost") or response_headers.get("x-litellm-cost")
            try:
                parsed_cost = float(cost_text) if cost_text is not None else None
                cost_usd = (
                    parsed_cost
                    if parsed_cost is not None and math.isfinite(parsed_cost) and parsed_cost >= 0
                    else None
                )
            except (TypeError, ValueError):
                cost_usd = None
            event.update({
                "status": response.status,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "response_completed_at_unix_ms": time.time_ns() // 1_000_000,
                "request_id": request_id,
                "usage": usage,
                "cost_usd": cost_usd,
            })
            try:
                self._send_downstream_response(
                    handler,
                    status=response.status,
                    headers=response.getheaders(),
                    body=body,
                )
            except OSError as exc:
                event["downstream_write_status"] = "interrupted"
                event["downstream_write_error_type"] = type(exc).__name__
            else:
                event["downstream_write_status"] = "server_write_completed"
        except (OSError, http.client.HTTPException) as exc:
            if event.get("status") is not None:
                event["downstream_write_status"] = "interrupted"
                event["downstream_write_error_type"] = type(exc).__name__
            else:
                event.update({"status": "proxy_error", "error_type": type(exc).__name__})
                try:
                    handler.send_error(502, "accounting proxy upstream failure")
                    handler.wfile.flush()
                except OSError as downstream_exc:
                    event["downstream_write_status"] = "interrupted"
                    event["downstream_write_error_type"] = type(downstream_exc).__name__
                else:
                    event["downstream_write_status"] = "server_write_completed"
        finally:
            with self._idle:
                self._events.append(event)
                self._inflight -= 1
                self._idle.notify_all()
            connection.close()

    def snapshot(self, client_results: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        with self._idle:
            snapshot_complete = self._idle.wait_for(lambda: self._inflight == 0, timeout=2.0)
            events = [dict(event) for event in self._events]
        events.sort(key=lambda event: event.get("request_started_at_unix_ns", 0))
        for request_index, event in enumerate(events, start=1):
            event["request_index"] = request_index
        for event in events:
            client_name, attribution_reason = _client_for_timestamp(
                event.get("request_started_at_unix_ms"), client_results or {}
            )
            event["client_attribution"] = client_name
            event["client_attribution_reason"] = attribution_reason
        usage_complete = bool(events) and all(isinstance(event.get("usage"), dict) and event.get("usage", {}).get("total_tokens") is not None for event in events)
        request_ids = [event.get("request_id") for event in events]
        request_ids_complete = (
            bool(events)
            and all(isinstance(value, str) and value.strip() for value in request_ids)
            and len(set(request_ids)) == len(request_ids)
        )
        costs_complete = bool(events) and all(
            isinstance(event.get("cost_usd"), (int, float))
            and not isinstance(event.get("cost_usd"), bool)
            and math.isfinite(float(event["cost_usd"]))
            and event["cost_usd"] >= 0
            for event in events
        )
        client_attribution_complete = bool(events) and all(bool(event.get("client_attribution")) for event in events)
        purpose_attribution_complete = bool(events) and all(event.get("purpose") != "unknown" for event in events)
        delivery_status_complete = bool(events) and all(
            event.get("downstream_write_status") in {"server_write_completed", "interrupted"}
            for event in events
        )
        task_marker_counts = {
            client_name: sum(
                event.get("client_attribution") == client_name
                and event.get("purpose") == "primary_task_workflow"
                and event.get("purpose_marker_id") == f"task_marker_sha256:{self._task_marker_sha256}"
                for event in events
            )
            for client_name in ("opencode", "deepseek_harness")
        }
        task_marker_validation = {
            "enabled": self._task_marker is not None,
            "marker_sha256": self._task_marker_sha256,
            "expected_non_title_matches_per_client": 2,
            "non_title_matches_per_client": task_marker_counts,
            "exact_two_matches_per_client": bool(self._task_marker)
            and all(count == 2 for count in task_marker_counts.values()),
        }
        prompt_task_events: dict[str, list[dict[str, Any]]] = {
            client_name: [
                event for event in events
                if event.get("client_attribution") == client_name
                and event.get("purpose") == "primary_task_workflow"
                and event.get("purpose_marker_id") == f"task_prompt_hmac_sha256:{self._task_prompt_hmac}"
            ]
            for client_name in ("opencode", "deepseek_harness")
        }
        prompt_task_states: dict[str, list[str]] = {}
        for client_name, client_events in prompt_task_events.items():
            states = []
            for event in client_events:
                shape = event.get("request_shape", {})
                if shape.get("tool_result_present") is True:
                    states.append("final_tool_result")
                elif isinstance(shape.get("tool_definition_count"), int) and shape["tool_definition_count"] > 0:
                    states.append("proposal_tool_definitions")
                else:
                    states.append("unknown_task_state")
            prompt_task_states[client_name] = states
        exact_two_prompt_task_states = bool(self._task_prompt) and all(
            states == ["proposal_tool_definitions", "final_tool_result"]
            for states in prompt_task_states.values()
        )
        task_prompt_validation = {
            "enabled": self._task_prompt is not None,
            "fingerprint_scheme": "per_run_hmac_sha256",
            "prompt_hmac_sha256": self._task_prompt_hmac,
            "expected_states_per_client": ["proposal_tool_definitions", "final_tool_result"],
            "observed_task_match_count_per_client": {
                client_name: len(client_events)
                for client_name, client_events in prompt_task_events.items()
            },
            "observed_state_order_per_client": prompt_task_states,
            "exact_ordered_two_state_protocol_per_client": exact_two_prompt_task_states,
        }
        route_attribution_complete = bool(self._parsed.geturl()) and bool(events) and all(bool(event.get("model")) for event in events)
        frontier_tokens = sum(int(event["usage"]["total_tokens"]) for event in events) if usage_complete else None
        cost_usd = round(sum(float(event["cost_usd"]) for event in events), 12) if costs_complete else None
        return {
            "status": "captured",
            "snapshot_complete": snapshot_complete,
            "endpoint": self._parsed.geturl(),
            "proxy_base_url": self.base_url,
            "calls": events,
            "call_count": len(events),
            "request_ids_complete": request_ids_complete,
            "usage_complete": usage_complete,
            "costs_complete": costs_complete,
            "client_attribution_complete": client_attribution_complete,
            "purpose_attribution_complete": purpose_attribution_complete,
            "delivery_status_complete": delivery_status_complete,
            "task_marker_validation": task_marker_validation,
            "task_prompt_validation": task_prompt_validation,
            "route_attribution_complete": route_attribution_complete,
            "frontier_tokens": frontier_tokens,
            "cost_usd": cost_usd,
            "accounting_complete": (
                request_ids_complete
                and snapshot_complete
                and usage_complete
                and costs_complete
                and client_attribution_complete
                and purpose_attribution_complete
                and delivery_status_complete
                and (self._task_prompt is None or exact_two_prompt_task_states)
                and route_attribution_complete
            ),
        }


def _json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _default_workload() -> dict[str, Any]:
    return {
        "schema": WORKLOAD_SCHEMA,
        "workload_id": "local-single-readme-heading-v1",
        "authorization": "local_stub_only",
        "cases": [
            {
                "case_id": "readme-heading-001",
                "prompt": PROMPT,
                "expected_observation": EXPECTED,
            }
        ],
    }


def _workload_hash(workload: dict[str, Any]) -> str:
    encoded = json.dumps(workload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_workload(path: Path | None) -> dict[str, Any]:
    """Load one bounded canary case with a stable audit identity."""

    workload = _default_workload() if path is None else json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(workload, dict) or workload.get("schema") != WORKLOAD_SCHEMA:
        raise ValueError("workload_schema_invalid")
    workload_id = workload.get("workload_id")
    cases = workload.get("cases")
    if not isinstance(workload_id, str) or not workload_id.strip():
        raise ValueError("workload_id_invalid")
    if not isinstance(cases, list) or len(cases) != 1:
        raise ValueError("workload_must_contain_exactly_one_case")
    case = cases[0]
    if not isinstance(case, dict):
        raise ValueError("workload_case_invalid")
    for field in ("case_id", "prompt", "expected_observation"):
        if not isinstance(case.get(field), str) or not case[field].strip():
            raise ValueError(f"workload_{field}_invalid")
    if "authorization" not in workload:
        workload["authorization"] = "unspecified"
    workload["workload_sha256"] = _workload_hash({key: value for key, value in workload.items() if key != "workload_sha256"})
    return workload


def _baseline_server(
    model: str = "baseline-local",
    *,
    force_non_stream: bool = False,
    two_state_read_tool: bool = False,
    task_marker: str | None = None,
    task_prompt: str | None = None,
) -> tuple[ThreadingHTTPServer, list[dict[str, Any]]]:
    if task_marker is not None and task_prompt is not None:
        raise ValueError("task_marker_and_task_prompt_are_mutually_exclusive")
    calls: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.rstrip("/") == "/v1/models":
                _json_response(self, {"object": "list", "data": [{"id": "baseline-local"}]})
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            calls.append(payload)
            usage = {"prompt_tokens": 480, "completion_tokens": 36, "total_tokens": 516}
            messages = payload.get("messages", [])
            marker_seen = bool(task_marker) and any(
                task_marker in text_value for text_value in _iter_text_values(messages)
            )
            prompt_seen = bool(task_prompt) and any(
                task_prompt in text_value
                for message in messages
                if isinstance(message, dict) and message.get("role") == "user"
                for text_value in _iter_text_values(message.get("content"))
            )
            has_tool_result = any(
                isinstance(message, dict) and message.get("role") in {"tool", "function"}
                for message in messages
            )
            safe_tool_call = None
            if two_state_read_tool and (marker_seen or prompt_seen) and not has_tool_result:
                for advertised in payload.get("tools", []):
                    function = advertised.get("function", {}) if isinstance(advertised, dict) else {}
                    name = function.get("name") if isinstance(function, dict) else None
                    if name != "read":
                        continue
                    parameters = function.get("parameters", {})
                    properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}
                    required = parameters.get("required", []) if isinstance(parameters, dict) else []
                    path_argument = next(
                        (key for key in ("filePath", "file_path") if key in properties),
                        None,
                    )
                    if path_argument is None or any(key != path_argument for key in required):
                        continue
                    arguments: dict[str, Any] = {path_argument: "README.md"}
                    for key, value in (("offset", 0), ("limit", 12)):
                        if key in properties:
                            arguments[key] = value
                    safe_tool_call = {
                        "id": "call-local-readme-heading",
                        "type": "function",
                        "function": {
                            "name": "read",
                            "arguments": json.dumps(arguments, separators=(",", ":")),
                        },
                    }
                    break
            if payload.get("stream") and not force_non_stream:
                chunks = [
                    {
                        "id": "baseline-local-stream",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
                    },
                ]
                if safe_tool_call is not None:
                    chunks.extend([
                        {
                            "id": "baseline-local-stream",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [{
                                "index": 0,
                                "delta": {"tool_calls": [{"index": 0, **safe_tool_call}]},
                                "finish_reason": None,
                            }],
                        },
                        {
                            "id": "baseline-local-stream",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
                            "usage": usage,
                        },
                    ])
                else:
                    chunks.extend([
                        {
                        "id": "baseline-local-stream",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": BASELINE_TEXT}, "finish_reason": None}],
                        },
                        {
                            "id": "baseline-local-stream",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                            "usage": usage,
                        },
                    ])
                body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
                encoded = body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            _json_response(
                self,
                {
                    "id": "baseline-local-response",
                    "object": "chat.completion",
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": (
                            {"role": "assistant", "content": None, "tool_calls": [safe_tool_call]}
                            if safe_tool_call is not None
                            else {"role": "assistant", "content": BASELINE_TEXT}
                        ),
                        "finish_reason": "tool_calls" if safe_tool_call is not None else "stop",
                    }],
                    "usage": usage,
                },
            )

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    return server, calls


def _run_direct_clients(
    output_dir: Path,
    *,
    base_url: str,
    model: str,
    api_key: str,
    prompt: str,
    expected: str,
    opencode_executable: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = output_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "README.md", workspace / "README.md")
    config = {
        "$schema": "https://opencode.ai/config.json",
        "provider": {
            "baseline": {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Canary baseline",
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model: {"name": "Canary baseline", "limit": {"context": 4000000, "output": 256}}},
            }
        },
        "model": f"baseline/{model}",
    }
    (workspace / "opencode.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    patch = f"""- id: llm-deepseek\n  config:\n    deepseek:\n      apiKeyEnv: DEEPSEEK_API_KEY\n      baseURL: {base_url}\n      models:\n        - id: {model}\n          name: Canary baseline\n          contextWindow: 4000000\n          maxTokens: 256\n      defaultModel:\n        id: {model}\n    apiKeyEnv: DEEPSEEK_API_KEY\n    baseURL: {base_url}\n    models:\n      - id: {model}\n        name: Canary baseline\n        contextWindow: 4000000\n        maxTokens: 256\n    defaultModel:\n      id: {model}\n- id: agent-default-model\n  config:\n    provider: deepseek-official\n    model: {model}\n"""
    patch_path = workspace / "dsh-baseline.patch.yml"
    patch_path.write_text(patch, encoding="utf-8")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    opencode = shutil.which(opencode_executable) if opencode_executable else (shutil.which("opencode.cmd") or shutil.which("opencode"))
    dsh = shutil.which("dsh.cmd") or shutil.which("dsh")
    if not powershell or not opencode or not dsh:
        raise RuntimeError("portable client executables are unavailable")

    env = dict(os.environ)
    env["DEEPSEEK_API_KEY"] = api_key
    env["HOME"] = str(output_dir / "home")
    env["USERPROFILE"] = env["HOME"]
    for name in ("config", "cache", "data", "state", "runtime"):
        (output_dir / "home" / name).mkdir(parents=True, exist_ok=True)
    env["XDG_CONFIG_HOME"] = str(output_dir / "home" / "config")
    env["XDG_CACHE_HOME"] = str(output_dir / "home" / "cache")
    env["XDG_DATA_HOME"] = str(output_dir / "home" / "data")
    env["XDG_STATE_HOME"] = str(output_dir / "home" / "state")
    env["XDG_RUNTIME_DIR"] = str(output_dir / "home" / "runtime")

    results: dict[str, Any] = {}
    for name, command in (("opencode", [opencode, "run", "--pure", "--print-logs", "--format", "json", "-m", f"baseline/{model}", prompt]), ("deepseek_harness", [dsh, "--profile", "headless", "--patch", str(patch_path), prompt])):
        started_at_unix_ms = time.time_ns() // 1_000_000
        result = _run_bounded_subprocess(command, cwd=workspace, env=env, timeout_seconds=120)
        finished_at_unix_ms = time.time_ns() // 1_000_000
        answer_check = check_answer(result["stdout"], expected, exit_code=result["exit_code"], timed_out=result["timed_out"])
        results[name] = {
            "started_at_unix_ms": started_at_unix_ms,
            "finished_at_unix_ms": finished_at_unix_ms,
            "executable": command[0],
            "exit_code": result["exit_code"],
            "correct": answer_check["correct"],
            "answer_check": answer_check,
            "timed_out": result["timed_out"],
            "timeout_seconds": result["timeout_seconds"],
            "elapsed_ms": result["elapsed_ms"],
            "tree_cleanup_complete": result.get("tree_cleanup_complete", True),
            "stdout_tail": result["stdout"],
            "stderr_tail": result["stderr"],
        }
    return results


def _run_hybrid(package_dir: Path, output_dir: Path, port: int, *, prompt: str, expected: str, opencode_executable: str | None = None) -> dict[str, Any]:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise RuntimeError("powershell.exe is required")
    smoke = REPO_ROOT / "tools" / "smoke_portable_clients.ps1"
    result = _run_bounded_subprocess(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(smoke),
            "-PackageDir",
            str(package_dir),
            "-AllowedRoot",
            str(REPO_ROOT),
            "-OutputDir",
            str(output_dir),
            "-Port",
            str(port),
            "-ClaudePort",
            str(port + 1),
            "-ClaudeProxyPort",
            str(port + 2),
            "-Prompt",
            prompt,
            *(["-OpenCodeExecutable", opencode_executable] if opencode_executable else []),
        ],
        cwd=REPO_ROOT,
        env=dict(os.environ),
        timeout_seconds=180,
    )
    receipt_path = output_dir / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig")) if receipt_path.is_file() else {}
    client_answers = {}
    client_elapsed_ms = {}
    for client, filename in (("opencode", "opencode.stdout.txt"), ("deepseek_harness", "dsh.stdout.txt"), ("claude_code", "claude.stdout.txt")):
        output_path = output_dir / filename
        output_text = output_path.read_text(encoding="utf-8-sig") if output_path.is_file() else ""
        client_answers[client] = check_answer(
            output_text,
            expected,
            exit_code=receipt.get("clients", {}).get(client, {}).get("exit_code"),
            timed_out=result["timed_out"],
        )
        elapsed = receipt.get("clients", {}).get(client, {}).get("elapsed_ms")
        client_elapsed_ms[client] = elapsed if isinstance(elapsed, (int, float)) else None
    trace_path = output_dir / "wrench-client.trace.jsonl"
    rows, trace_jsonl_well_formed = _read_trace_jsonl(trace_path)
    cost_rows = [row.get("cost_accounting") for row in rows]
    trace_ids_unique, workflow_attempts_unique = _trace_identity_accounting(rows)
    token_accounting_complete = _trace_token_accounting_complete(
        rows, trace_jsonl_well_formed=trace_jsonl_well_formed
    )
    frontier_tokens = (
        sum(cost["frontier_tokens"] for cost in cost_rows)
        if token_accounting_complete
        else None
    )
    local_model_tokens = (
        sum(cost["local_model_tokens"] for cost in cost_rows)
        if token_accounting_complete
        else None
    )
    local_input_tokens = (
        sum(row["raw_input_tokens_estimate"] for row in rows)
        if trace_jsonl_well_formed
        and rows
        and all(
            isinstance(row.get("raw_input_tokens_estimate"), int)
            and not isinstance(row.get("raw_input_tokens_estimate"), bool)
            and row["raw_input_tokens_estimate"] >= 0
            for row in rows
        )
        else None
    )
    repair_passes = (
        sum(cost["repair_passes"] for cost in cost_rows)
        if token_accounting_complete
        else None
    )
    frontier_calls = (
        sum(cost["frontier_model_calls"] for cost in cost_rows)
        if token_accounting_complete
        else None
    )
    observed_model_calls = (
        sum(row["model_calls"] for row in rows)
        if rows
        and all(
            isinstance(row.get("model_calls"), int)
            and not isinstance(row.get("model_calls"), bool)
            and row["model_calls"] >= 0
            for row in rows
        )
        else None
    )
    abstentions = sum(row.get("status") == "abstain" for row in rows)
    final_answer_rows = sum(bool(row.get("final_answer")) for row in rows)
    local_elapsed = [float(row["elapsed_ms"]) for row in rows if isinstance(row.get("elapsed_ms"), (int, float))]
    return {
        "exit_code": result["exit_code"],
        "receipt_status": receipt.get("status"),
        "correct": not result["timed_out"] and result["exit_code"] == 0 and receipt.get("status") == "PASSED" and all(client_answers[name]["correct"] for name in ("opencode", "deepseek_harness", "claude_code")),
        "client_answers": client_answers,
        "client_elapsed_ms": client_elapsed_ms,
        "timed_out": result["timed_out"],
        "timeout_seconds": result["timeout_seconds"],
        "elapsed_ms": result["elapsed_ms"],
        "tree_cleanup_complete": result.get("tree_cleanup_complete", True),
        "frontier_tokens": frontier_tokens,
        "model_calls": observed_model_calls,
        "trace_rows": len(rows),
        "trace_latency_ms": local_elapsed,
        "accounting": {
            "frontier_tokens": frontier_tokens,
            "local_tokens": local_model_tokens,
            "local_input_tokens_estimate": local_input_tokens,
            "local_model_tokens": local_model_tokens,
            "cost_usd": None,
            "cost_status": "not_priced_local_runtime",
            "retries": repair_passes,
            "corrections": None,
            "final_answer_rows": final_answer_rows,
            "abstentions": abstentions,
            "fallback_calls": frontier_calls,
            "trace_request_ids_unique": trace_ids_unique,
            "workflow_attempts_unique": workflow_attempts_unique,
            "trace_jsonl_well_formed": trace_jsonl_well_formed,
            "token_accounting_complete": token_accounting_complete,
            "accounting_complete": False,
        },
        "receipt": receipt,
        "stdout_tail": result["stdout"],
        "stderr_tail": result["stderr"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=29120)
    parser.add_argument("--baseline-url", help="Configured OpenAI-compatible /v1 endpoint; requires an approved paid-canary child contract even on loopback")
    parser.add_argument("--baseline-model", default="baseline-local")
    parser.add_argument("--baseline-api-key-env", default="WRENCH_CANARY_BASELINE_API_KEY")
    parser.add_argument("--child-contract", type=Path, help="Human-approved, exact-workload paid-canary child contract for any configured baseline")
    parser.add_argument("--allow-external-baseline", action="store_true")
    parser.add_argument("--local-baseline-non-stream", action="store_true")
    parser.add_argument("--capture-gateway-accounting", action="store_true", help="Capture loopback baseline response usage and cost headers through a local forwarding proxy")
    parser.add_argument("--opencode-executable", help="Explicit OpenCode executable used by both arms; preserves the global install")
    parser.add_argument("--workload", type=Path, help="hash-bound JSON workload manifest with exactly one case")
    args = parser.parse_args()
    if args.opencode_executable:
        resolved_opencode = shutil.which(args.opencode_executable)
        if not resolved_opencode:
            parser.error("--opencode-executable must resolve to an installed executable")
        args.opencode_executable = str(Path(resolved_opencode).resolve())
    package_dir = args.package_dir.resolve()
    output = args.output.resolve()
    workload = load_workload(args.workload.resolve() if args.workload else None)
    child_contract_hash = None
    child_contract = None
    parent_contract_hash = None
    parent_monetary_budget = None
    if args.baseline_url:
        if args.child_contract is None:
            raise RuntimeError("approved child contract required for configured baseline")
        if not args.capture_gateway_accounting:
            raise RuntimeError("configured baseline requires --capture-gateway-accounting")
        parent_contract, parent_contract_hash, parent_monetary_budget = _read_current_parent_contract()
        contract_bytes = args.child_contract.resolve().read_bytes()
        child_contract = _validate_paid_baseline_child_contract(
            json.loads(contract_bytes.decode("utf-8")),
            parent_contract=parent_contract,
            parent_contract_sha256=parent_contract_hash,
            baseline_url=args.baseline_url,
            baseline_model=args.baseline_model,
            workload_sha256=workload["workload_sha256"],
            workload_authorization=workload["authorization"],
        )
        child_contract_hash = hashlib.sha256(contract_bytes).hexdigest()
    elif args.child_contract is not None:
        raise RuntimeError("child contract supplied without a configured baseline")
    output.parent.mkdir(parents=True, exist_ok=True)
    case = workload["cases"][0]
    prompt = case["prompt"]
    expected = case["expected_observation"]
    with tempfile.TemporaryDirectory(prefix="wrench-paired-canary-") as temp:
        temp_root = Path(temp)
        baseline_server = None
        baseline_calls: list[dict[str, Any]] = []
        accounting_proxy: _LoopbackAccountingProxy | None = None
        baseline_clients: dict[str, dict[str, Any]] = {}
        gateway_accounting_capture: dict[str, Any] = {"status": "not_attempted", "reason": "capture_disabled"}
        baseline_model = args.baseline_model
        baseline_api_key = "baseline-local"
        if args.baseline_url:
            baseline_url = args.baseline_url.rstrip("/")
            baseline_api_key = _effective_baseline_api_key(
                baseline_url,
                os.environ.get(args.baseline_api_key_env, ""),
            )
            _validate_external_baseline_guard(
                baseline_url,
                workload_authorization=workload["authorization"],
                allow_external_baseline=args.allow_external_baseline,
                api_key=baseline_api_key,
            )
        else:
            baseline_server, baseline_calls = _baseline_server(
                baseline_model,
                force_non_stream=args.local_baseline_non_stream,
            )
            baseline_url = f"http://127.0.0.1:{baseline_server.server_port}/v1"
        client_baseline_url = baseline_url
        if args.capture_gateway_accounting:
            accounting_proxy = _LoopbackAccountingProxy(
                baseline_url,
                task_prompt=prompt,
            )
            accounting_proxy.start()
            client_baseline_url = accounting_proxy.base_url
        try:
            thread = None
            if baseline_server is not None:
                thread = threading.Thread(target=baseline_server.serve_forever, daemon=True)
                thread.start()
            gateway_accounting_before = (
                _probe_loopback_spend_logs(baseline_url)
                if args.baseline_url
                else {"status": "not_attempted", "reason": "local_stub"}
            )
            baseline_started = time.perf_counter()
            baseline_clients = _run_direct_clients(
                temp_root / "baseline",
                base_url=client_baseline_url,
                model=baseline_model,
                api_key=baseline_api_key,
                prompt=prompt,
                expected=expected,
                opencode_executable=args.opencode_executable,
            )
            baseline_elapsed = round((time.perf_counter() - baseline_started) * 1000, 3)
        finally:
            if accounting_proxy is not None:
                gateway_accounting_capture = accounting_proxy.snapshot(baseline_clients)
                accounting_proxy.stop()
            if baseline_server is not None:
                baseline_server.shutdown()
                baseline_server.server_close()
                if thread is not None:
                    thread.join(timeout=5)
        hybrid = _run_hybrid(package_dir, temp_root / "hybrid", args.port, prompt=prompt, expected=expected, opencode_executable=args.opencode_executable)
        gateway_accounting_after = (
            _probe_loopback_spend_logs(baseline_url)
            if args.baseline_url
            else {"status": "not_attempted", "reason": "local_stub"}
        )
        hybrid_persist = output.parent / (output.stem + "-hybrid")
        if hybrid.get("receipt"):
            hybrid_persist.mkdir(parents=True, exist_ok=True)
            receipt_source = temp_root / "hybrid"
            for source in receipt_source.iterdir():
                if source.is_file():
                    shutil.copy2(source, hybrid_persist / source.name)
        token_accounting = _canary_token_accounting(
            baseline_url_configured=bool(args.baseline_url),
            baseline_call_count=len(baseline_calls),
            captured_frontier_tokens=gateway_accounting_capture.get("frontier_tokens"),
            hybrid_frontier_tokens=hybrid.get("frontier_tokens"),
        )
        baseline_frontier_tokens = token_accounting["baseline_frontier_tokens"]
        baseline_correct = _baseline_clients_correct(baseline_clients)
        hybrid_correct = bool(hybrid.get("correct"))
        latency_comparison = _compare_client_latencies(
            baseline_clients,
            hybrid,
            baseline_correct=baseline_correct,
        )
        baseline_accounting_complete = bool(gateway_accounting_capture.get("accounting_complete"))
        accounting_complete = (
            baseline_accounting_complete
            and bool(hybrid.get("accounting", {}).get("accounting_complete"))
        )
        status = _classify_canary_status(
            baseline_correct=baseline_correct,
            hybrid_correct=hybrid_correct,
            hybrid_frontier_tokens=hybrid.get("frontier_tokens"),
            hybrid_model_calls=hybrid.get("model_calls"),
            accounting_complete=accounting_complete,
        )
        baseline_accounting = {
            "frontier_tokens": baseline_frontier_tokens,
            "local_stub_synthetic_tokens_estimate": token_accounting["local_stub_synthetic_tokens_estimate"],
            "local_tokens": 0,
            "cost_usd": gateway_accounting_capture.get("cost_usd"),
            "retries": None,
            "corrections": None,
            "abstentions": None,
            "fallback_calls": None,
            "cost_status": (
                "not_priced_local_stub"
                if not args.baseline_url
                else ("observed_gateway_response" if gateway_accounting_capture.get("costs_complete") else "not_observed")
            ),
            "accounting_complete": baseline_accounting_complete,
        }
        receipt = {
            "schema": "wrench.paired-real-client-hybrid-canary.v1",
            "status": status,
            "baseline_authorization": (
                {
                    "child_contract_sha256": child_contract_hash,
                    "parent_contract_sha256": parent_contract_hash,
                    "parent_monetary_budget_usd": parent_monetary_budget,
                    "max_spend_usd": child_contract["max_spend_usd"],
                    "spend_cap_kind": child_contract["spend_cap_kind"],
                    "cap_source_review_required": True,
                }
                if child_contract is not None
                else {"kind": "built_in_deterministic_stub", "provider_spend_authorized": False}
            ),
            "prompt": prompt,
            "expected_observation": expected,
            "workload_id": workload["workload_id"],
            "workload_case_id": case["case_id"],
            "workload_sha256": workload["workload_sha256"],
            "workload_authorization": workload["authorization"],
            "baseline": {
                "kind": "local_deterministic_openai_compatible_baseline" if not args.baseline_url else "configured_openai_compatible_baseline",
                "endpoint_configured": bool(args.baseline_url),
                "model": baseline_model,
                "transport": "non_stream" if args.local_baseline_non_stream and not args.baseline_url else "stream_or_provider_defined",
                "elapsed_ms": baseline_elapsed,
                "upstream_calls": len(baseline_calls) if not args.baseline_url else None,
                "frontier_tokens": baseline_frontier_tokens,
                "clients": baseline_clients,
                "accounting": baseline_accounting,
            },
            "gateway_accounting_probe": {
                "before": gateway_accounting_before,
                "after": gateway_accounting_after,
                "usable_for_paired_accounting": False,
                "reason": "probe_has_no_request_correlation",
            },
            "gateway_accounting_capture": gateway_accounting_capture,
            "hybrid": hybrid,
            "latency_comparison": latency_comparison,
            "frontier_token_reduction_rate": token_accounting["frontier_token_reduction_rate"],
            "net_frontier_token_savings_rate": token_accounting["net_frontier_token_savings_rate"],
            "diagnostic_raw_token_reduction_rate": token_accounting["diagnostic_raw_token_reduction_rate"],
            "diagnostic_token_basis": token_accounting["diagnostic_token_basis"],
            "quality_claim": False,
            "partial_evidence": True,
            "north_star_complete": False,
            "notes": [
                "Both arms use the same mechanical prompt and real OpenCode and DeepSeek Harness clients.",
                (
                    "The baseline is a configured loopback gateway without observed provider accounting, "
                    "so this is client compatibility evidence, not MiniMax parity or paid-provider quality evidence."
                    if args.baseline_url
                    else "The baseline is deterministic and local, so this is a protocol/cost canary, not MiniMax parity or paid-provider quality evidence."
                ),
                "The hybrid arm also runs Claude Code through the existing portable smoke harness; the paired baseline comparison is scoped to OpenCode and DeepSeek Harness.",
            ],
        }
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "baseline_frontier_tokens": baseline_frontier_tokens, "hybrid_frontier_tokens": hybrid.get("frontier_tokens"), "hybrid_elapsed_ms": hybrid.get("elapsed_ms")}, ensure_ascii=False))
    return _canary_process_exit_code(status)


if __name__ == "__main__":
    raise SystemExit(main())
