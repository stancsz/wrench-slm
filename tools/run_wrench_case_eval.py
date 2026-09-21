#!/usr/bin/env python3
"""Run a full JSONL proposal evaluation against a local Wrench endpoint.

This is a diagnostic runner for the historical 220-case fixture. It preserves
model output and verifier receipts, but it never treats the fixture as the
matched MiniMax workflow evaluation.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import statistics
import threading
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness import execute_local_qwen
try:
    from tools.evaluation_provenance import canonical_jsonl_sha256, raw_sha256
except ModuleNotFoundError:
    from evaluation_provenance import canonical_jsonl_sha256, raw_sha256


class _HealthFixtureHandler(http.server.BaseHTTPRequestHandler):
    """Small local fixture for the two allowlisted health paths."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/health", "/v1/models"}:
            payload = b'{"status":"ok","fixture":true}\n'
            status = 200
        else:
            payload = b"not found\n"
            status = 404
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

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

    def stop(self) -> None:
        if self.server is None:
            return
        self.server.shutdown()
        self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)


def _proposal_from_result(result: dict[str, Any]) -> dict[str, Any] | None:
    proposal = result.get("parsed_proposal")
    return proposal if isinstance(proposal, dict) else None


def _cost_accounting_from_result(result: dict[str, Any]) -> dict[str, Any] | None:
    endpoint_receipt = result.get("endpoint_receipt")
    if not isinstance(endpoint_receipt, dict):
        return None
    accounting = endpoint_receipt.get("cost_accounting")
    return accounting if isinstance(accounting, dict) else None


def _exact_match(result: dict[str, Any], target: dict[str, Any]) -> bool:
    proposal = _proposal_from_result(result)
    if proposal is None:
        return False
    return proposal == target


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return round(ordered[index], 3)


def _wait_for_ready(endpoint: str, model: str, timeout_seconds: float) -> dict[str, Any]:
    """Wait for a real buffered mechanical completion, not /v1/models alone."""

    if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("startup timeout must be positive")
    body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": "Read README.md with a 4096 byte limit."}],
            "temperature": 0,
            "max_tokens": 1,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    attempts = 0
    last_error = "not_started"
    deadline = started + float(timeout_seconds)
    while time.perf_counter() < deadline:
        attempts += 1
        try:
            with urllib.request.urlopen(request, timeout=min(2.0, max(0.1, deadline - time.perf_counter()))) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if response.status == 200 and isinstance(payload, dict) and isinstance(payload.get("choices"), list):
                return {
                    "status": "READY_MECHANICAL_COMPLETION",
                    "attempts": attempts,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                    "last_error": None,
                }
            last_error = "readiness_response_invalid"
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = type(exc).__name__
        time.sleep(0.25)
    raise RuntimeError(
        f"endpoint did not pass a buffered mechanical readiness probe within {timeout_seconds}s; "
        f"attempts={attempts} last_error={last_error}"
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 220 and not args.allow_noncanonical_count:
        raise ValueError(f"expected the canonical 220-case fixture, got {len(rows)} rows")
    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    health_fixture = _HealthFixture(args.health_fixture, args.health_fixture_port)
    health_fixture.start()
    if args.health_fixture:
        os.environ["WRENCH_TEST_HEALTH_FIXTURE_BASE_URL"] = f"http://127.0.0.1:{args.health_fixture_port}"
    try:
        readiness = _wait_for_ready(args.endpoint, args.model, args.startup_timeout)
        for row in rows:
            target = json.loads(row["target"])
            started = time.perf_counter()
            model_result = execute_local_qwen(
                args.endpoint,
                args.model,
                [
                    {"role": "system", "content": row["system"]},
                    {"role": "user", "content": row["prompt"]},
                ],
                str(args.root.resolve()),
                max_tokens=args.max_tokens,
                timeout_seconds=args.timeout,
                capture_trace=True,
                mechanical_fast_path=not args.disable_mechanical_fast_path,
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            latencies.append(elapsed_ms)
            observed_status = model_result.get("status")
            expected_status = row["expected_status"]
            expected_reason = row.get("expected_fallback_reason")
            reason_match = expected_reason is None or model_result.get("fallback_reason") == expected_reason
            exact = observed_status == "accepted" and _exact_match(model_result, target)
            outcome_match = observed_status == expected_status and reason_match
            prohibited = expected_status == "abstain" and observed_status == "accepted"
            results.append(
                {
                    "id": row["id"],
                    "family": row["family"],
                    "category": row["category"],
                    "split": row["split"],
                    "expected_status": expected_status,
                    "expected_fallback_reason": expected_reason,
                    "observed_status": observed_status,
                    "observed_fallback_reason": model_result.get("fallback_reason"),
                    "outcome_match": outcome_match,
                    "exact_proposal_match": exact,
                    "prohibited_accept": prohibited,
                    "latency_ms": elapsed_ms,
                    "model": model_result.get("model"),
                    "usage": model_result.get("usage"),
                    "backend": model_result.get("backend"),
                    "model_calls": model_result.get("model_calls"),
                    "endpoint_elapsed_ms": model_result.get("elapsed_ms"),
                    "mechanical_fast_path": model_result.get("mechanical_fast_path", False),
                    "raw_model_output": model_result.get("raw_model_output"),
                    "parsed_proposal": model_result.get("parsed_proposal"),
                    "multi_pass_verifier": model_result.get("multi_pass_verifier"),
                    "cost_accounting": _cost_accounting_from_result(model_result),
                }
            )
    finally:
        health_fixture.stop()
        if args.health_fixture:
            os.environ.pop("WRENCH_TEST_HEALTH_FIXTURE_BASE_URL", None)
    accounting_rows = [
        item["cost_accounting"]
        for item in results
        if isinstance(item.get("cost_accounting"), dict)
    ]
    eligible = [item for item in results if item["category"] == "eligible"]
    receipt = {
        "schema": "wrench.historical-220-model-evaluation.v1",
        "status": "DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY",
        "endpoint": args.endpoint,
        "model": args.model,
        "cases_path": str(args.cases.resolve()),
        "cases_sha256": canonical_jsonl_sha256(args.cases),
        "cases_bytes_sha256": raw_sha256(args.cases),
        "request_count": len(results),
        "canonical_case_count": len(rows) == 220,
        "mechanical_fast_path_enabled": not args.disable_mechanical_fast_path,
        "health_fixture_enabled": args.health_fixture,
        "readiness": readiness,
        "max_tokens": args.max_tokens,
        "timeout_seconds": args.timeout,
        "summary": {
            "outcome_matches": sum(item["outcome_match"] for item in results),
            "exact_proposal_matches": sum(item["exact_proposal_match"] for item in results),
            "eligible_case_count": len(eligible),
            "eligible_exact_accepts": sum(item["exact_proposal_match"] for item in eligible),
            "prohibited_accepts": sum(item["prohibited_accept"] for item in results),
            "transport_or_runtime_abstentions": sum(
                item["observed_fallback_reason"] in {"qwen_transport_error", "qwen_http_error"}
                for item in results
            ),
            "mechanical_fast_path_requests": sum(item["mechanical_fast_path"] for item in results),
            "model_calls": sum(
                item["model_calls"]
                for item in results
                if isinstance(item.get("model_calls"), int)
            ),
            "median_latency_ms": _percentile(latencies, 0.5),
            "p95_latency_ms": _percentile(latencies, 0.95),
            "mean_latency_ms": round(statistics.mean(latencies), 3) if latencies else None,
            "cost_accounting": {
                "receipt_count": len(accounting_rows),
                "total_raw_input_tokens": sum(
                    int(item.get("raw_input_tokens", 0)) for item in accounting_rows
                ),
                "total_model_prompt_tokens": sum(
                    int(item.get("model_prompt_tokens", 0)) for item in accounting_rows
                ),
                "total_model_completion_tokens": sum(
                    int(item.get("model_completion_tokens", 0)) for item in accounting_rows
                ),
                "total_local_model_tokens": sum(
                    int(item.get("local_model_tokens", 0)) for item in accounting_rows
                ),
                "total_input_tokens_not_sent_to_model": sum(
                    int(item.get("input_tokens_not_sent_to_model", 0)) for item in accounting_rows
                ),
                "total_repair_passes": sum(
                    int(item.get("repair_passes", 0)) for item in accounting_rows
                ),
                "total_local_elapsed_ms": round(
                    sum(float(item.get("total_local_elapsed_ms", 0.0)) for item in accounting_rows),
                    3,
                ),
                "usd_cost": None,
                "usd_cost_status": "not_priced_local_runtime",
            },
        },
        "quality_claim": False,
        "limitations": [
            "The canonical 220 fixture is historical regression input, not the approved matched MiniMax workflow trace set.",
            "This receipt does not prove weighted frontier-token coverage, teacher parity, or production readiness.",
            "No proposal is executed with mutation authority; the verifier is the only local execution boundary.",
        ],
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--startup-timeout", type=float, default=60)
    parser.add_argument("--disable-mechanical-fast-path", action="store_true")
    parser.add_argument(
        "--allow-noncanonical-count",
        action="store_true",
        help="run a named held-out split without weakening the default 220-case contract",
    )
    parser.add_argument(
        "--health-fixture",
        action="store_true",
        help="serve deterministic responses on the allowlisted local health endpoints",
    )
    parser.add_argument(
        "--health-fixture-port",
        type=int,
        default=28907,
        help="loopback port for the deterministic health fixture",
    )
    args = parser.parse_args()
    if not 1 <= args.max_tokens <= 512:
        raise ValueError("max_tokens must be between 1 and 512")
    receipt = run(args)
    print(json.dumps({"status": receipt["status"], **receipt["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
