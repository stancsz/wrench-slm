"""Summarize class-specific timing from a measured binary hybrid regression.

This reads recorded predictions only. It makes no model or provider call.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty timing group")
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def timing(rows: list[dict]) -> dict:
    values = [row["elapsed_ms"] for row in rows]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0
           for value in values):
        raise ValueError("invalid elapsed time")
    return {"count": len(rows), "p50_ms": quantile(values, .5),
            "p95_ms": quantile(values, .95)}


def summarize(receipt_path: Path, predictions_path: Path) -> dict:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (receipt.get("status") != "CLASSIFIER_SUITE_COMPLETE"
            or receipt.get("preflight_enabled") is not True
            or receipt.get("runtime_errors") != 0
            or receipt.get("cases_sha256") !=
            "26fafa2e008ed3b6ee1fefd11293802f47dcdd35b44a295cece1c2a301433ec1"):
        raise ValueError("wrong or failed measured hybrid receipt")
    rows = [json.loads(line) for line in predictions_path.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    if len(rows) != 5600 or len({row.get("id") for row in rows}) != 5600:
        raise ValueError("prediction count or IDs invalid")
    if Counter(row.get("label") for row in rows) != {"abstain": 5000, "wrench": 600}:
        raise ValueError("prediction labels invalid")
    for row in rows:
        expected = "not_abstain" if row["label"] == "wrench" else "abstain"
        if (row.get("decision") not in {"abstain", "not_abstain"}
                or row.get("correct") is not (row["decision"] == expected)
                or row.get("model_forwards") not in {0, 1}
                or (row["model_forwards"] == 0) != str(row.get("reason", "")).startswith("explicit_")):
            raise ValueError("invalid binary prediction record")
    eligible = [row for row in rows if row["label"] == "wrench"]
    eligible_correct = [row for row in eligible if row["correct"]]
    model = [row for row in rows if row["model_forwards"] == 1]
    preflight = [row for row in rows if row["model_forwards"] == 0]
    if (len(model) != receipt.get("model_forward_count")
            or len(preflight) != receipt.get("preflight_veto_count")
            or sum(row["correct"] for row in rows) != receipt.get("correct")
            or len(eligible) - len(eligible_correct) != receipt.get("false_abstain")
            or sum(row["label"] == "abstain" and not row["correct"] for row in rows)
            != receipt.get("false_wrench")):
        raise ValueError("measured receipt and predictions disagree")
    samples = receipt.get("resource_samples") or []
    if not samples:
        raise ValueError("missing resource samples")
    min_ram = min(sample["ram_free"] / sample["ram_total"] for sample in samples)
    min_vram = min(sample["vram_free_mib"] / sample["vram_total_mib"] for sample in samples)
    if min_ram < .1 or min_vram < .1:
        raise ValueError("host resource reserve breached")
    return {"schema": "wrench.system-one-hybrid-timing-summary.v1",
            "status": "MEASURED_CONSUMED_SUITE_REGRESSION_NOT_RELEASE_EVIDENCE",
            "measured_receipt_sha256": sha256(receipt_path),
            "predictions_sha256": sha256(predictions_path),
            "preflight_source_sha256": receipt["preflight_source_sha256"],
            "evaluator_sha256": receipt["evaluator_sha256"],
            "gpu": receipt["environment"]["gpu"],
            "accuracy": receipt["accuracy"],
            "balanced_accuracy": receipt["balanced_accuracy"],
            "false_wrench": receipt["false_wrench"],
            "false_abstain": receipt["false_abstain"],
            "all_decisions": timing(rows),
            "eligible_decisions": timing(eligible),
            "correct_eligible_decisions": timing(eligible_correct),
            "model_forward_decisions": timing(model),
            "preflight_veto_decisions": timing(preflight),
            "resource_samples": len(samples),
            "minimum_ram_free_fraction": min_ram,
            "minimum_vram_free_fraction": min_vram,
            "diagnostic_target_pass": receipt["diagnostic_target_pass"],
            "production_enabled": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output exists")
    result = summarize(args.receipt, args.predictions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
