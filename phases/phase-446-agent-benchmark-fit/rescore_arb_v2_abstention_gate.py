"""Rescore a completed ARB V2 Wrench gate prediction file with official split labels."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_arb_v2_abstention_gate import (
    DATA,
    evaluate,
    load_cases,
    sha256_file,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--suffix", default="final")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    run_path = run_dir / "run.json"
    predictions_path = run_dir / "predictions.jsonl"
    if not run_path.is_file() or not predictions_path.is_file():
        parser.error("run.json and predictions.jsonl must exist in the run directory")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    cases = load_cases(DATA)
    by_id = {case["id"]: case for case in cases}
    limits_path = run_dir / "input-limit-audit" / "input-limits.jsonl"
    if not limits_path.is_file():
        raise ValueError("exact Wrench tokenizer input-limit audit is required")
    limits_rows = [json.loads(line) for line in limits_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    limits_by_id = {str(row["id"]): row for row in limits_rows}
    if len(limits_by_id) != len(limits_rows) or set(limits_by_id) != set(by_id):
        raise ValueError("input-limit audit IDs do not exactly match the pinned dataset")
    if len(by_id) != len(cases):
        raise ValueError("duplicate IDs in pinned ARB V2 data")
    raw_rows = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen: set[str] = set()
    rescored: list[dict[str, Any]] = []
    for row in raw_rows:
        row_id = str(row.get("id"))
        if row_id in seen:
            raise ValueError(f"duplicate prediction ID: {row_id}")
        seen.add(row_id)
        case = by_id.get(row_id)
        if case is None:
            raise ValueError(f"prediction ID absent from pinned data: {row_id}")
        limit = limits_by_id[row_id]
        if (row.get("reason") == "input_too_long") != (limit["limit_reason"] != "within_limits"):
            raise ValueError(f"recorded input-limit decision differs from tokenizer audit for {row_id}")
        if row.get("decision") not in {"abstain", "not_abstain"}:
            raise ValueError(f"invalid decision for prediction ID {row_id}")
        rescored.append({
            "id": row_id,
            "repo": case["repo"],
            "group": case["group"],
            "expected": case["expected"],
            "decision": row["decision"],
            "reason": row.get("reason"),
            "probabilities": row.get("probabilities"),
            "input_tokens": row.get("input_tokens"),
            "input_chars": limit["input_chars"],
            "input_tokens": limit["input_tokens"],
            "limit_reason": limit["limit_reason"],
            "latency_ms": row["latency_ms"],
        })
    if seen != set(by_id):
        raise ValueError(f"prediction ID coverage mismatch: {len(seen)} of {len(by_id)}")
    if run.get("data_sha256") != sha256_file(DATA):
        raise ValueError("run data hash does not match the pinned ARB V2 sample file")
    if not args.suffix.replace("-", "").isalnum():
        parser.error("--suffix may contain only letters, digits, and hyphens")
    output_predictions = run_dir / f"full-limit-rescored-{args.suffix}-predictions.jsonl"
    with output_predictions.open("x", encoding="utf-8") as stream:
        for row in rescored:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    source_run_hash = sha256_file(run_path)
    controls: dict[str, Any] = {}
    for name, decision_fn in (
        ("always_abstain", lambda row: ("abstain", "control_baseline")),
        ("always_continue", lambda row: ("not_abstain", "control_baseline")),
        (
            "input_limits_then_continue",
            lambda row: ("abstain", "input_too_long") if row["limit_reason"] != "within_limits" else ("not_abstain", "control_baseline"),
        ),
    ):
        control_rows = []
        for row in rescored:
            decision, reason = decision_fn(row)
            control_rows.append({**row, "decision": decision, "reason": reason})
        control_metrics = evaluate(control_rows)
        for field in ("mean_latency_ms", "p50_latency_ms", "p95_latency_ms"):
            control_metrics.pop(field, None)
        controls[name] = control_metrics
    summary = {
        "schema": "wrench.arb-v2-binary-gate-rescored.v1",
        "status": "COMPLETE_RESCORING",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_status": run.get("status"),
        "source_run_error": run.get("error"),
        "source_run_sha256": source_run_hash,
        "source_predictions_sha256": sha256_file(predictions_path),
        "rescored_predictions_file": output_predictions.name,
        "rescored_predictions_sha256": sha256_file(output_predictions),
        "data_sha256": sha256_file(DATA),
        "input_limit_audit_sha256": sha256_file(limits_path),
        "scoring_note": (
            "All 427 inference predictions completed. The initial post-inference scorer used selective_source, "
            "which labels all 82 no-gold rows identically. This rescore maps natural vs counterfactual using "
            "the official metadata.organic field, validates exact one-to-one ID coverage, and does not alter predictions."
        ),
        "input_limit_policy": {
            "max_chars": 8192,
            "max_tokens": 512,
            "tokenizer": "same Wrench Qwen checkpoint and exact chat-template rendering",
            "cases_over_limit": sum(row["limit_reason"] != "within_limits" for row in rescored),
            "character_limit_cases": sum(row["limit_reason"] == "input_too_long_chars" for row in rescored),
            "token_limit_cases": sum(row["limit_reason"] == "input_too_long_tokens" for row in rescored),
        },
        "inference_run": {
            "device": run.get("device"),
            "torch_version": run.get("torch_version"),
            "transformers_version": run.get("transformers_version"),
            "checkpoint_sha256": run.get("checkpoint_sha256"),
            "head_sha256": run.get("head_sha256"),
            "head_threshold": run.get("head_threshold"),
            "prompt_adapter": run.get("prompt_adapter"),
            "provider_calls": run.get("provider_calls"),
            "tool_execution": run.get("tool_execution"),
            "training_or_tuning": run.get("training_or_tuning"),
            "resources": run.get("resources"),
            "warmup_latency_ms": run.get("warmup_latency_ms"),
        },
        "metrics": evaluate(rescored),
        "control_baselines": controls,
    }
    target = run_dir / f"full-limit-rescored-{args.suffix}-summary.json"
    write_json(target, summary)
    print(json.dumps({"status": summary["status"], "metrics": summary["metrics"], "summary": str(target)}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
