#!/usr/bin/env python3
"""Run a local four-arm mechanical-worker workflow diagnostic.

The runner uses the same historical request, verifier, repository root, and
decoding limits across all arms. It never grants mutation authority. The
result is diagnostic until the trace set is replaced by the approved,
family-disjoint real-workflow set.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness import execute_model_output
from wrench_harness.mechanical import mechanical_route
from tools.score_mechanical_worker import evaluate_manifest


ARMS = (
    "minimax_teacher_only",
    "rules_plus_minimax_fallback",
    "wrench_plus_identical_minimax_fallback",
    "wrench_only_diagnostic",
)


def _abstain(reason: str, detail: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "abstain", "fallback_reason": reason}
    if detail:
        result["detail"] = detail
    return result


def _usage_tokens(usage: Any) -> int:
    if not isinstance(usage, dict):
        return 0
    value = usage.get("total_tokens")
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _cost_usd(usage: Any) -> float:
    if not isinstance(usage, dict):
        return 0.0
    value = usage.get("cost")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    details = usage.get("cost_details")
    if isinstance(details, dict):
        value = details.get("upstream_inference_cost")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return 0.0


def _proposal_from_result(result: dict[str, Any]) -> dict[str, Any] | None:
    proposal = result.get("parsed_proposal")
    return proposal if isinstance(proposal, dict) else None


def _strict_success(result: dict[str, Any], row: dict[str, Any]) -> bool:
    expected_status = row.get("expected_status")
    expected_reason = row.get("expected_fallback_reason")
    if result.get("status") != expected_status:
        return False
    if expected_status == "abstain":
        return expected_reason is None or result.get("fallback_reason") == expected_reason
    try:
        target = json.loads(row["target"])
    except (KeyError, TypeError, json.JSONDecodeError):
        return False
    return _proposal_from_result(result) == target


def _verifier_success(result: dict[str, Any]) -> bool:
    if result.get("status") not in {"accepted", "abstain"}:
        return False
    return result.get("fallback_reason") not in {
        "model_output_invalid_json",
        "model_output_not_object",
        "qwen_transport_error",
        "qwen_http_error",
    }


def _unexpected_mutation(result: dict[str, Any]) -> bool:
    observation = result.get("observation")
    return isinstance(observation, dict) and bool(observation.get("mutated") or observation.get("applied"))


def _call_teacher(
    endpoint: str,
    model: str,
    row: dict[str, Any],
    root: str,
    *,
    timeout: float,
    max_tokens: int,
) -> dict[str, Any]:
    """Run one teacher request in an OS-killable subprocess."""

    request = {
        "endpoint": endpoint,
        "model": model,
        "messages": [
            {"role": "system", "content": row["system"]},
            {"role": "user", "content": row["prompt"]},
        ],
        "timeout": timeout,
        "max_tokens": max_tokens,
    }
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "run_teacher_call.py")],
            input=json.dumps(request, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=str(REPO_ROOT),
            timeout=max(0.25, timeout + 0.25),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "result": _abstain("teacher_timeout", "hard_deadline_exceeded"),
            "usage": {},
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 1,
            "raw_output": None,
        }
    try:
        envelope = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "result": _abstain("teacher_transport_error", "child_invalid_json"),
            "usage": {},
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 1,
            "raw_output": None,
        }
    if completed.returncode != 0 or not isinstance(envelope, dict) or not envelope.get("ok"):
        return {
            "result": _abstain("teacher_transport_error", str(envelope.get("error", "child_failure"))),
            "usage": {},
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 1,
            "raw_output": None,
        }
    payload = envelope.get("payload")
    choices = payload.get("choices") if isinstance(payload, dict) else None
    message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    usage = payload.get("usage") if isinstance(payload, dict) else {}
    if not isinstance(content, str):
        result = _abstain("teacher_response_invalid")
    else:
        result = execute_model_output(content, root, request_prompt=row["prompt"])
        result["model"] = payload.get("model") if isinstance(payload, dict) else model
        result["usage"] = usage
        result["raw_model_output"] = content
        try:
            result["parsed_proposal"] = json.loads(content)
        except json.JSONDecodeError:
            result["parsed_proposal"] = None
    return {
        "result": result,
        "usage": usage,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "frontier_tokens": _usage_tokens(usage),
        "cost_usd": _cost_usd(usage),
        "provider_requests": 1,
        "raw_output": content if isinstance(content, str) else None,
    }


def _rule_result(row: dict[str, Any], root: str) -> dict[str, Any] | None:
    proposal = mechanical_route(row["prompt"])
    if proposal is None:
        return None
    if proposal.get("status") == "abstain":
        return {"result": proposal, "latency_ms": 0.0, "frontier_tokens": 0, "cost_usd": 0.0, "provider_requests": 0, "raw_output": None}
    result = execute_model_output(json.dumps(proposal, ensure_ascii=False), root, request_prompt=row["prompt"])
    result["parsed_proposal"] = proposal
    return {"result": result, "latency_ms": 0.0, "frontier_tokens": 0, "cost_usd": 0.0, "provider_requests": 0, "raw_output": json.dumps(proposal, ensure_ascii=False)}


def _local_result(
    endpoint: str,
    model: str,
    row: dict[str, Any],
    root: str,
    *,
    timeout: float,
    max_tokens: int,
) -> dict[str, Any]:
    """Run local Wrench inference with a hard batch deadline.

    The serving client can block below Python's request timeout when a local
    backend is overloaded or its connection is half-open. Keep that failure
    explicit and let the identical teacher fallback preserve workflow safety.
    """

    started = time.perf_counter()
    # Mirror the endpoint's documented mechanical_fast_path locally. This is
    # the intended Wrench execution path for routine work and avoids spawning
    # a child process for cases that require no model inference at all.
    fast = _rule_result(row, root)
    if fast is not None:
        return {
            "result": fast["result"],
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "local_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 0,
            "raw_output": fast.get("raw_output"),
        }
    request = {
        "endpoint": endpoint,
        "model": model,
        "messages": [
            {"role": "system", "content": row["system"]},
            {"role": "user", "content": row["prompt"]},
        ],
        "root": root,
        "timeout": timeout,
        "max_tokens": max_tokens,
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "run_local_wrench_call.py")],
            input=json.dumps(request, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=str(REPO_ROOT),
            timeout=max(0.25, timeout + 0.25),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "result": _abstain("wrench_timeout", "hard_deadline_exceeded"),
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "local_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 0,
            "raw_output": None,
        }
    if completed.returncode != 0:
        return {
            "result": _abstain("wrench_transport_error", f"child_exit_{completed.returncode}"),
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "local_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 0,
            "raw_output": None,
        }
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "result": _abstain("wrench_transport_error", "child_invalid_json"),
            "latency_ms": (time.perf_counter() - started) * 1000,
            "frontier_tokens": 0,
            "local_tokens": 0,
            "cost_usd": 0.0,
            "provider_requests": 0,
            "raw_output": None,
        }
    usage = result.get("usage")
    return {
        "result": result,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "frontier_tokens": 0,
        "local_tokens": _usage_tokens(usage),
        "cost_usd": 0.0,
        "provider_requests": 0,
        "raw_output": result.get("raw_model_output"),
    }


def _arm_record(
    result: dict[str, Any],
    row: dict[str, Any],
    *,
    latency_ms: float,
    frontier_tokens: int,
    local_tokens: int = 0,
    cost_usd: float = 0.0,
    provider_requests: int = 0,
    fallback_used: bool = False,
    source: str,
) -> dict[str, Any]:
    return {
        "final_success": _strict_success(result, row),
        "verifier_success": _verifier_success(result),
        "prohibited_accept": row.get("expected_status") == "abstain" and result.get("status") == "accepted",
        "unexpected_mutation": _unexpected_mutation(result),
        "fallback_used": fallback_used,
        "frontier_tokens": frontier_tokens,
        "local_tokens": local_tokens,
        "latency_ms": round(latency_ms, 3),
        "total_tokens": frontier_tokens + local_tokens,
        "cost_usd": round(cost_usd, 8),
        "provider_requests": provider_requests,
        "observed_status": result.get("status"),
        "observed_fallback_reason": result.get("fallback_reason"),
        "source": source,
        "raw_model_output": result.get("raw_model_output"),
    }


def run(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise ValueError("no cases")
    root = str(args.root.resolve())
    traces: list[dict[str, Any]] = []
    teacher_by_id: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=args.teacher_workers) as pool:
        futures = {
            pool.submit(
                _call_teacher,
                args.teacher_endpoint,
                args.teacher_model,
                row,
                root,
                timeout=args.timeout,
                max_tokens=args.teacher_max_tokens,
            ): row["id"]
            for row in rows
        }
        for future in as_completed(futures):
            teacher_by_id[futures[future]] = future.result()
    for row in rows:
        teacher = teacher_by_id[row["id"]]
        teacher_result = teacher["result"]

        rules_started = time.perf_counter()
        rule = _rule_result(row, root)
        if rule is None:
            rule = teacher
            rule_source = "teacher_fallback"
            rule_frontier = int(rule["frontier_tokens"])
            rule_cost = float(rule["cost_usd"])
            rule_requests = int(rule["provider_requests"])
            rule_result = rule["result"]
        else:
            rule_source = "mechanical_rule"
            rule_frontier = 0
            rule_cost = 0.0
            rule_requests = 0
            rule_result = rule["result"]
        rule_latency = (time.perf_counter() - rules_started) * 1000

        wrench_local = _local_result(
            args.wrench_endpoint,
            args.wrench_model,
            row,
            root,
            timeout=args.timeout,
            max_tokens=args.wrench_max_tokens,
        )
        wrench_result = wrench_local["result"]
        if wrench_result.get("status") == "accepted":
            wrench_final = wrench_result
            wrench_frontier = 0
            wrench_cost = 0.0
            wrench_requests = 0
            wrench_latency = float(wrench_local["latency_ms"])
            wrench_fallback = False
            wrench_source = "wrench_local"
        else:
            fallback = teacher
            wrench_final = fallback["result"]
            wrench_frontier = int(fallback["frontier_tokens"])
            wrench_cost = float(fallback["cost_usd"])
            wrench_requests = int(fallback["provider_requests"])
            wrench_latency = float(wrench_local["latency_ms"]) + float(fallback["latency_ms"])
            wrench_fallback = True
            wrench_source = "wrench_then_teacher_fallback"

        # The same local proposal is the observation for both Wrench arms.
        # Repeating the request would double latency and distort the comparison.
        diagnostic = wrench_local
        traces.append(
            {
                "id": row["id"],
                "family": row["family"],
                "category": row.get("category", "unknown"),
                "split": row.get("split", "unknown"),
                "model_input_tokens": int((teacher.get("usage") or {}).get("prompt_tokens", max(1, len(row["prompt"]) // 4))),
                "workload_weight": max(1.0, float(teacher["frontier_tokens"] or 1)),
                "arms": {
                    "minimax_teacher_only": _arm_record(
                        teacher_result,
                        row,
                        latency_ms=float(teacher["latency_ms"]),
                        frontier_tokens=int(teacher["frontier_tokens"]),
                        cost_usd=float(teacher["cost_usd"]),
                        provider_requests=int(teacher["provider_requests"]),
                        source="teacher_only",
                    ),
                    "rules_plus_minimax_fallback": _arm_record(
                        rule_result,
                        row,
                        latency_ms=rule_latency,
                        frontier_tokens=rule_frontier,
                        cost_usd=rule_cost,
                        provider_requests=rule_requests,
                        source=rule_source,
                    ),
                    "wrench_plus_identical_minimax_fallback": _arm_record(
                        wrench_final,
                        row,
                        latency_ms=wrench_latency,
                        frontier_tokens=wrench_frontier,
                        local_tokens=int(wrench_local.get("local_tokens", 0)),
                        cost_usd=wrench_cost,
                        provider_requests=wrench_requests,
                        fallback_used=wrench_fallback,
                        source=wrench_source,
                    ),
                    "wrench_only_diagnostic": _arm_record(
                        diagnostic["result"],
                        row,
                        latency_ms=float(diagnostic["latency_ms"]),
                        frontier_tokens=0,
                        local_tokens=int(diagnostic.get("local_tokens", 0)),
                        source="wrench_only",
                    ),
                },
            }
        )
    traces.sort(key=lambda item: item["id"])
    trace_bytes = json.dumps(traces, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = {
        "schema": "wrench.mechanical-worker-traces.v1",
        "status": "DIAGNOSTIC_HISTORICAL_WORKFLOW_ARMS",
        "authorization": "pending_human_approval",
        "teacher": {"endpoint": args.teacher_endpoint, "model": args.teacher_model, "identity_status": "endpoint_id_recorded"},
        "wrench": {"endpoint": args.wrench_endpoint, "model": args.wrench_model},
        "input_path": str(args.cases.resolve()),
        "input_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trace_set_sha256": hashlib.sha256(trace_bytes).hexdigest(),
        "traces": traces,
        "quality_claim": False,
        "production_enablement": False,
        "limitations": [
            "Historical 220 fixture only, not the approved family-disjoint real-workflow trace set.",
            "Final success is strict fixture-oracle success after the independent verifier, not user-confirmed task completion.",
            "No proposal is granted mutation authority by this runner.",
        ],
    }
    evaluation = evaluate_manifest(manifest)
    return manifest, evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--teacher-endpoint", default="http://127.0.0.1:4000/v1/chat/completions")
    parser.add_argument("--teacher-model", default="minimax")
    parser.add_argument("--wrench-endpoint", required=True)
    parser.add_argument("--wrench-model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-max-tokens", type=int, default=768)
    parser.add_argument("--teacher-workers", type=int, default=4)
    parser.add_argument("--wrench-max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if not 1 <= args.teacher_workers <= 16:
        raise ValueError("teacher-workers must be between 1 and 16")
    manifest, evaluation = run(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "trace-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": evaluation["status"], "trace_count": evaluation["trace_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
