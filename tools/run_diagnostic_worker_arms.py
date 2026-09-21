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
import http.server
import json
import os
import statistics
import subprocess
import sys
import threading
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


class _HealthFixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/v1/models"}:
            body = b'{"status":"ok","fixture":true}\n'
            status = 200
        else:
            body = b"not found\n"
            status = 404
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _HealthFixture:
    def __init__(self, enabled: bool, port: int) -> None:
        self.enabled = enabled
        self.port = port
        self.server: http.server.ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if not self.enabled:
            return
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), _HealthFixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        os.environ["WRENCH_TEST_HEALTH_FIXTURE_BASE_URL"] = f"http://127.0.0.1:{self.port}"

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)
        if self.enabled:
            os.environ.pop("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", None)


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


def _wrench_needs_teacher_fallback(result: dict[str, Any]) -> bool:
    """Fallback only when the local/model path, not the mechanical boundary, failed."""

    return result.get("status") != "accepted" and not bool(result.get("mechanical_fast_path", False))


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


def _teacher_from_capture(item: dict[str, Any], row: dict[str, Any], root: str) -> dict[str, Any]:
    """Replay one provider-backed capture without making another API call."""
    usage = item.get("usage") if isinstance(item.get("usage"), dict) else {}
    normalized = item.get("normalized_proposal")
    raw_output = item.get("raw_model_output")
    if isinstance(normalized, dict):
        result = execute_model_output(
            json.dumps(normalized, ensure_ascii=False),
            root,
            request_prompt=row["prompt"],
        )
        result["parsed_proposal"] = normalized
    elif item.get("transport_failure"):
        result = _abstain("teacher_transport_error", str(item.get("error", "captured_transport_failure")))
        result["parsed_proposal"] = None
    else:
        result = _abstain("model_output_invalid_json", "captured_response_was_not_a_complete_proposal")
        result["parsed_proposal"] = None
    result["model"] = item.get("response_model")
    result["usage"] = usage
    result["raw_model_output"] = raw_output if isinstance(raw_output, str) else None
    return {
        "result": result,
        "usage": usage,
        "latency_ms": float(item.get("latency_ms", 0.0) or 0.0),
        "frontier_tokens": _usage_tokens(usage),
        "cost_usd": _cost_usd(usage),
        "provider_requests": 1,
        "raw_output": raw_output if isinstance(raw_output, str) else None,
    }


def _load_teacher_capture(path: Path, cases: list[dict[str, Any]], root: str) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "wrench.mechanical-worker-teacher-traces.v1":
        raise ValueError("teacher capture schema mismatch")
    expected_hash = hashlib.sha256(
        ("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in cases) + "\n").encode("utf-8")
    ).hexdigest()
    # The capture stores the source file hash, so compare against the exact
    # bytes represented by the case rows rather than trusting only case ids.
    source_path = Path(payload.get("input_path", ""))
    if source_path.is_file():
        expected_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if payload.get("input_sha256") != expected_hash:
        raise ValueError("teacher capture input hash does not match requested cases")
    captured = {item.get("id"): item for item in payload.get("results", []) if isinstance(item, dict)}
    missing = [row["id"] for row in cases if row["id"] not in captured]
    if missing:
        raise ValueError(f"teacher capture is missing {len(missing)} requested cases")
    return {row["id"]: _teacher_from_capture(captured[row["id"]], row, root) for row in cases}


def _rule_result(row: dict[str, Any], root: str) -> dict[str, Any] | None:
    proposal = mechanical_route(row["prompt"], allowed_root=root)
    # A deterministic abstention is a routing miss, not a completed rules
    # arm. The named fallback arm must send that request to the identical
    # teacher, otherwise it silently measures "rules only" and understates
    # both provider tokens and fallback safety risk.
    if proposal is None or proposal.get("status") == "abstain":
        return None
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
    mechanical_fast_path: bool = True,
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
    if mechanical_fast_path and fast is not None:
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
        "mechanical_fast_path": mechanical_fast_path,
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
    if args.teacher_traces:
        teacher_by_id = _load_teacher_capture(args.teacher_traces, rows, root)
    else:
        teacher_by_id = {}
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
            mechanical_fast_path=not args.disable_client_mechanical_fast_path,
        )
        wrench_result = wrench_local["result"]
        # The package endpoint owns its mechanical boundary. A deterministic
        # abstention is already a safe terminal result and must not be sent to
        # the frontier teacher. Only a non-mechanical local/model failure is
        # eligible for identical-teacher fallback.
        if not _wrench_needs_teacher_fallback(wrench_result):
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
                        fallback_used=rule_source == "teacher_fallback",
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
        "client_mechanical_fast_path": not args.disable_client_mechanical_fast_path,
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
    parser.add_argument("--teacher-traces", type=Path, default=None, help="replay a provider-backed capture instead of making calls")
    parser.add_argument("--wrench-endpoint", required=True)
    parser.add_argument("--wrench-model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-max-tokens", type=int, default=768)
    parser.add_argument("--teacher-workers", type=int, default=4)
    parser.add_argument("--wrench-max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--health-fixture",
        action="store_true",
        help="serve deterministic responses for allowlisted local health requests",
    )
    parser.add_argument("--health-fixture-port", type=int, default=28907)
    parser.add_argument(
        "--disable-client-mechanical-fast-path",
        action="store_true",
        help="send every Wrench-arm request to the configured HTTP endpoint",
    )
    args = parser.parse_args()
    if not 1 <= args.teacher_workers <= 16:
        raise ValueError("teacher-workers must be between 1 and 16")
    fixture = _HealthFixture(args.health_fixture, args.health_fixture_port)
    fixture.start()
    try:
        manifest, evaluation = run(args)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "trace-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (args.output_dir / "evaluation.json").write_text(json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": evaluation["status"], "trace_count": evaluation["trace_count"]}, ensure_ascii=False))
    finally:
        fixture.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
