#!/usr/bin/env python3
"""Score matched cloud, rules, and learned workflow arms.

This tool only scores an already captured trace manifest. It never calls a
model, executes a proposal, or mutates a repository. Real-workflow scoring is
blocked unless the manifest carries the explicit authorization value required
by the Wrench goal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any


ARMS = ("cloud_only", "rules_plus_identical_fallback", "learned_plus_identical_fallback")
AUTHORIZATION = "approved_real_workflow"
PROVENANCE_FIELDS = ("capture_id", "captured_at", "reviewer", "source_scope")


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction)))
    return ordered[index]


def _as_nonnegative_number(value: Any, field: str, trace_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{trace_id}: {field} must be a non-negative number")
    return float(value)


def _validate_trace(trace: Any) -> None:
    if not isinstance(trace, dict) or not isinstance(trace.get("id"), str) or not trace["id"]:
        raise ValueError("each trace needs a non-empty id")
    arms = trace.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ARMS):
        raise ValueError(f"{trace['id']}: trace must contain exactly the three configured arms")
    for arm in ARMS:
        result = arms[arm]
        if not isinstance(result, dict):
            raise ValueError(f"{trace['id']}/{arm}: arm result must be an object")
        for field in ("final_success", "prohibited_accept", "unexpected_mutation"):
            if not isinstance(result.get(field), bool):
                raise ValueError(f"{trace['id']}/{arm}: {field} must be boolean")
        _as_nonnegative_number(result.get("stronger_model_tokens"), "stronger_model_tokens", f"{trace['id']}/{arm}")
        _as_nonnegative_number(result.get("latency_ms"), "latency_ms", f"{trace['id']}/{arm}")


def _trace_set_digest(traces: list[dict[str, Any]]) -> str:
    encoded = json.dumps(traces, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bootstrap_interval(values: list[float], seed: int = 17, samples: int = 2000) -> dict[str, float | None]:
    if not values:
        return {"low": None, "high": None}
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(samples):
        draw = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(draw) / len(draw))
    return {"low": _percentile(means, 0.025), "high": _percentile(means, 0.975)}


def _arm_metrics(traces: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    results = [trace["arms"][arm] for trace in traces]
    tokens = [float(result["stronger_model_tokens"]) for result in results]
    latency = [float(result["latency_ms"]) for result in results]
    return {
        "cases": len(results),
        "final_success_rate": sum(result["final_success"] for result in results) / len(results),
        "prohibited_accepts": sum(result["prohibited_accept"] for result in results),
        "unexpected_mutations": sum(result["unexpected_mutation"] for result in results),
        "mean_stronger_model_tokens": sum(tokens) / len(tokens),
        "p95_latency_ms_nearest_rank": _percentile(latency, 0.95),
    }


def _paired_savings(traces: list[dict[str, Any]], comparator: str) -> dict[str, Any]:
    differences: list[float] = []
    rates: list[float] = []
    for trace in traces:
        learned = float(trace["arms"]["learned_plus_identical_fallback"]["stronger_model_tokens"])
        baseline = float(trace["arms"][comparator]["stronger_model_tokens"])
        differences.append(baseline - learned)
        rates.append((baseline - learned) / baseline if baseline > 0 else 0.0)
    mean_difference = sum(differences) / len(differences)
    mean_baseline = sum(float(trace["arms"][comparator]["stronger_model_tokens"]) for trace in traces) / len(traces)
    return {
        "comparator": comparator,
        "mean_token_savings": mean_difference,
        "mean_token_savings_rate": mean_difference / mean_baseline if mean_baseline > 0 else None,
        "paired_rate_bootstrap_95ci": _bootstrap_interval(rates),
    }


def evaluate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest.get("schema") != "wrench.workflow-arm-traces.v1":
        raise ValueError("workflow trace schema mismatch")
    traces = manifest.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ValueError("workflow trace manifest must contain at least one trace")
    seen: set[str] = set()
    for trace in traces:
        _validate_trace(trace)
        if trace["id"] in seen:
            raise ValueError(f"duplicate trace id: {trace['id']}")
        seen.add(trace["id"])
    base = {
        "schema": "wrench.workflow-arm-evaluation.v1",
        "trace_schema": manifest["schema"],
        "trace_authorization": manifest.get("authorization"),
        "trace_count": len(traces),
        "trace_set_sha256": manifest.get("trace_set_sha256"),
        "arms": {arm: _arm_metrics(traces, arm) for arm in ARMS},
        "quality_claim": False,
        "production_enablement": False,
    }
    if manifest.get("authorization") != AUTHORIZATION:
        return {
            **base,
            "status": "BLOCKED_TRACE_AUTHORIZATION",
            "paired_savings": [],
            "reason": f"authorization must equal {AUTHORIZATION!r}; no release conclusion is permitted",
        }
    trace_hash = manifest.get("trace_set_sha256")
    provenance = manifest.get("provenance")
    if not isinstance(trace_hash, str) or re.fullmatch(r"[0-9a-f]{64}", trace_hash) is None:
        return {
            **base,
            "status": "BLOCKED_TRACE_PROVENANCE",
            "paired_savings": [],
            "reason": "approved real workflow manifests require a 64-character trace_set_sha256",
        }
    expected_trace_hash = _trace_set_digest(traces)
    if trace_hash != expected_trace_hash:
        return {
            **base,
            "status": "BLOCKED_TRACE_PROVENANCE",
            "paired_savings": [],
            "reason": "trace_set_sha256 does not match the canonical trace contents",
            "expected_trace_set_sha256": expected_trace_hash,
        }
    if not isinstance(provenance, dict) or any(
        not isinstance(provenance.get(field), str) or not provenance[field].strip()
        for field in PROVENANCE_FIELDS
    ):
        return {
            **base,
            "status": "BLOCKED_TRACE_PROVENANCE",
            "paired_savings": [],
            "reason": f"approved real workflow manifests require provenance fields: {', '.join(PROVENANCE_FIELDS)}",
        }
    comparisons = [_paired_savings(traces, arm) for arm in ("cloud_only", "rules_plus_identical_fallback")]
    learned = base["arms"]["learned_plus_identical_fallback"]
    success_regression = any(
        learned["final_success_rate"] < base["arms"][arm]["final_success_rate"]
        for arm in ("cloud_only", "rules_plus_identical_fallback")
    )
    no_safety_violations = learned["prohibited_accepts"] == 0 and learned["unexpected_mutations"] == 0
    savings_gate = all(
        item["mean_token_savings_rate"] is not None
        and item["mean_token_savings_rate"] >= 0.10
        and item["paired_rate_bootstrap_95ci"]["low"] is not None
        and item["paired_rate_bootstrap_95ci"]["low"] > 0
        for item in comparisons
    )
    return {
        **base,
        "status": "PASS_WORKFLOW_ARM_METRICS" if savings_gate and not success_regression and no_safety_violations else "QUALITY_GATE_OPEN",
        "paired_savings": comparisons,
        "gates": {
            "savings_at_least_10_percent_with_ci_above_zero": savings_gate,
            "no_final_success_regression": not success_regression,
            "zero_prohibited_accepts": learned["prohibited_accepts"] == 0,
            "zero_unexpected_mutations": learned["unexpected_mutations"] == 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    receipt = evaluate_manifest(manifest)
    receipt["input_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": receipt["status"], "trace_count": receipt["trace_count"]}))
    return 0 if receipt["status"] in {"PASS_WORKFLOW_ARM_METRICS", "BLOCKED_TRACE_AUTHORIZATION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
