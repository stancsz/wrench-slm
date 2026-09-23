"""Apply Wrench's fixed 8192-character abstention limit to matched Ollama results."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_arb_v2_abstention_gate import DATA, evaluate, load_cases, sha256_file, write_json
from run_arb_v2_ollama_gate import paired_comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--wrench-predictions", type=Path, required=True)
    parser.add_argument("--wrench-input-limits", type=Path, required=True)
    parser.add_argument("--suffix", default="final")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    run_path = run_dir / "run.json"
    predictions_path = run_dir / "predictions.jsonl"
    wrench_path = args.wrench_predictions.resolve()
    limits_path = args.wrench_input_limits.resolve()
    if not run_path.is_file() or not predictions_path.is_file() or not wrench_path.is_file() or not limits_path.is_file():
        parser.error("outside run, predictions, and Wrench predictions must exist")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    cases = load_cases(DATA)
    by_id = {case["id"]: case for case in cases}
    limit_rows = [json.loads(line) for line in limits_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    limits = {str(row["id"]): row for row in limit_rows}
    if len(limits) != len(limit_rows) or set(limits) != set(by_id):
        raise ValueError("exact Wrench tokenizer input-limit audit does not match ARB V2 IDs")
    raw = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_pred: dict[str, dict[str, Any]] = {}
    rescored: list[dict[str, Any]] = []
    for row in raw:
        row_id = str(row["id"])
        if row_id in by_pred or row_id not in by_id:
            raise ValueError(f"duplicate or unknown outside prediction ID: {row_id}")
        by_pred[row_id] = row
    if set(by_pred) != set(by_id):
        raise ValueError(f"outside predictions cover {len(by_pred)} of {len(by_id)} IDs")
    for case in cases:
        row = by_pred[case["id"]]
        if row.get("expected") != case["expected"]:
            raise ValueError(f"gold label mismatch for {case['id']}")
        limit = limits[case["id"]]
        over_limit = limit["limit_reason"] != "within_limits"
        rescored.append({
            **row,
            "input_chars": limit["input_chars"],
            "input_tokens": limit["input_tokens"],
            "limit_reason": limit["limit_reason"],
            "raw_model_decision": row["decision"],
            "decision": "abstain" if over_limit else row["decision"],
            "reason": "input_too_long" if over_limit else row.get("reason"),
        })
    if not args.suffix.replace("-", "").isalnum():
        parser.error("--suffix may contain only letters, digits, and hyphens")
    target_predictions = run_dir / f"full-limit-rescored-{args.suffix}-predictions.jsonl"
    with target_predictions.open("x", encoding="utf-8") as stream:
        for row in rescored:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    summary = {
        "schema": "wrench.arb-v2-outside-gate-cap-aware-rescore.v1",
        "status": "COMPLETE_RESCORING",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_status": run.get("status"),
        "source_run_sha256": sha256_file(run_path),
        "source_predictions_sha256": sha256_file(predictions_path),
        "data_sha256": sha256_file(DATA),
        "rescored_predictions_file": target_predictions.name,
        "rescored_predictions_sha256": sha256_file(target_predictions),
        "shared_input_limit": {
            "max_chars": 8192,
            "max_tokens": 512,
            "policy": "force abstain when the Wrench model tokenizer audit marks a prompt over its frozen character or token limit",
            "limit_audit_sha256": sha256_file(limits_path),
            "cases_over_limit": sum(row["limit_reason"] != "within_limits" for row in rescored),
            "character_limit_cases": sum(row["limit_reason"] == "input_too_long_chars" for row in rescored),
            "token_limit_cases": sum(row["limit_reason"] == "input_too_long_tokens" for row in rescored),
            "outside_inference_was_run_on_over_limit_cases": True,
            "over_limit_outputs_ignored": True,
        },
        "metrics": evaluate(rescored),
        "paired_wrench_comparison": paired_comparison(rescored, wrench_path, cases),
        "protocol_note": "Raw Ollama outputs are retained. This view overrides decisions on inputs Wrench cannot score and keeps their original output in raw_model_decision; only under-limit model decisions are compared as learned-gate behavior.",
    }
    target = run_dir / f"full-limit-rescored-{args.suffix}-summary.json"
    write_json(target, summary)
    print(json.dumps({"status": summary["status"], "metrics": summary["metrics"], "paired_wrench_comparison": summary["paired_wrench_comparison"], "summary": str(target)}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
