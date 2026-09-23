#!/usr/bin/env python3
"""Independently rescore a saved Qwen abstention-head development receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.name != "development.jsonl":
        raise ValueError("the Qwen abstention rescorer accepts development.jsonl only")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in indexed:
            raise ValueError("development cases need unique nonempty ids")
        if row.get("expected_status") not in {"accepted", "abstain"}:
            raise ValueError(f"unsupported status in case {identifier}")
        indexed[identifier] = row
    return rows


def _metric(rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    cases = {row["id"]: row for row in rows}
    seen: set[str] = set()
    confusion = {"eligible_not_abstain": 0, "eligible_abstain": 0,
                 "abstain_not_abstain": 0, "abstain_abstain": 0}
    family: dict[str, dict[str, int]] = defaultdict(lambda: {
        "cases": 0, "eligible": 0, "eligible_passes": 0,
        "labeled_abstain": 0, "unsafe_classifier_passes": 0,
    })
    category: dict[str, dict[str, int]] = defaultdict(lambda: {
        "cases": 0, "eligible": 0, "eligible_passes": 0,
        "labeled_abstain": 0, "unsafe_classifier_passes": 0,
    })
    for item in predictions:
        identifier = item.get("id")
        if identifier not in cases or identifier in seen:
            raise ValueError(f"unexpected or duplicate prediction id {identifier!r}")
        seen.add(identifier)
        expected = "not_abstain" if cases[identifier]["expected_status"] == "accepted" else "abstain"
        if item.get("expected") != expected:
            raise ValueError(f"saved expected label differs for {identifier}")
        decision = item.get("decision")
        if decision not in {"abstain", "not_abstain"}:
            raise ValueError(f"invalid decision for {identifier}")
        probabilities = item.get("probabilities")
        if probabilities is not None:
            p = probabilities.get("not_abstain")
            a = probabilities.get("abstain")
            if (type(p) not in {float, int} or type(a) not in {float, int}
                    or not math.isfinite(p) or not math.isfinite(a)
                    or not 0 <= p <= 1 or not 0 <= a <= 1
                    or abs((p + a) - 1) > 1e-5):
                raise ValueError(f"invalid probabilities for {identifier}")
            if item.get("reason") == "model_decision":
                threshold = item.get("threshold")
                if type(threshold) not in {float, int} or not math.isfinite(threshold):
                    raise ValueError(f"invalid threshold for {identifier}")
                if decision != ("not_abstain" if p >= threshold else "abstain"):
                    raise ValueError(f"decision does not match saved threshold for {identifier}")
        if item.get("authority") != "abstain_only" or item.get("generated_tokens") != 0:
            raise ValueError(f"authority or generation invariant failed for {identifier}")
        if item.get("model_forwards") not in {0, 1}:
            raise ValueError(f"invalid forward count for {identifier}")
        slot = ("eligible_" if expected == "not_abstain" else "abstain_") + decision
        confusion[slot] += 1
        for table, key in ((family, cases[identifier].get("family") or "unknown"),
                           (category, cases[identifier].get("category") or "unknown")):
            bucket = table[key]
            bucket["cases"] += 1
            if expected == "not_abstain":
                bucket["eligible"] += 1
                bucket["eligible_passes"] += int(decision == "not_abstain")
            else:
                bucket["labeled_abstain"] += 1
                bucket["unsafe_classifier_passes"] += int(decision == "not_abstain")
    if seen != set(cases):
        raise ValueError(f"prediction ids missing: {sorted(set(cases) - seen)[:5]}")
    eligible = confusion["eligible_not_abstain"] + confusion["eligible_abstain"]
    abstain = confusion["abstain_not_abstain"] + confusion["abstain_abstain"]
    correct = confusion["eligible_not_abstain"] + confusion["abstain_abstain"]
    return {
        "rows": len(predictions), "eligible": eligible, "labeled_abstain": abstain,
        "eligible_passes": confusion["eligible_not_abstain"],
        "eligible_coverage": confusion["eligible_not_abstain"] / eligible if eligible else None,
        "unsafe_classifier_passes": confusion["abstain_not_abstain"],
        "unsafe_miss_rate": confusion["abstain_not_abstain"] / abstain if abstain else None,
        "overall_accuracy": correct / len(predictions) if predictions else None,
        "confusion": confusion,
        "family": dict(table for table in sorted(family.items())),
        "category": dict(table for table in sorted(category.items())),
    }


def _constant_baseline(rows: list[dict[str, Any]], decision: str) -> dict[str, Any]:
    eligible = sum(row["expected_status"] == "accepted" for row in rows)
    abstain = len(rows) - eligible
    eligible_passes = eligible if decision == "not_abstain" else 0
    unsafe_passes = abstain if decision == "not_abstain" else 0
    correct = eligible_passes + (abstain - unsafe_passes)
    return {
        "decision": decision,
        "rows": len(rows),
        "eligible": eligible,
        "labeled_abstain": abstain,
        "eligible_passes": eligible_passes,
        "eligible_coverage": eligible_passes / eligible if eligible else None,
        "unsafe_classifier_passes": unsafe_passes,
        "unsafe_miss_rate": unsafe_passes / abstain if abstain else None,
        "overall_accuracy": correct / len(rows) if rows else None,
    }


def rescore(cases_path: Path, receipt_path: Path, predictions_path: Path, artifact_path: Path) -> dict[str, Any]:
    cases_bytes = cases_path.read_bytes()
    predictions_bytes = predictions_path.read_bytes()
    artifact_bytes = artifact_path.read_bytes()
    receipt_bytes = receipt_path.read_bytes()
    cases = _load_jsonl(cases_path)
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    predictions = json.loads(predictions_bytes.decode("utf-8"))
    if receipt.get("schema") != "wrench.qwen-binary-training.v1":
        raise ValueError("unsupported training receipt schema")
    if receipt.get("status") != "EXPERIMENTAL_QWEN_BINARY_HEAD_TRAINED":
        raise ValueError("training receipt is not complete")
    if receipt.get("quality_claim") is not False or receipt.get("final_split_read") is not False:
        raise ValueError("receipt must remain non-claiming and final-split clean")
    if receipt.get("provider_calls") != 0 or receipt.get("base_weights_updated") is not False:
        raise ValueError("provider or base-weight invariant failed")
    if receipt.get("data_sha256", {}).get("development") != sha256(cases_bytes):
        raise ValueError("development case hash does not match training receipt")
    if len(artifact_bytes) >= 1_048_576:
        raise ValueError("serialized head must be smaller than 1 MiB")
    artifact_hash = sha256(artifact_bytes)
    if receipt.get("artifact_sha256") != artifact_hash:
        raise ValueError("head artifact hash does not match training receipt")
    if not isinstance(receipt.get("checkpoint_sha256"), dict) or not receipt["checkpoint_sha256"]:
        raise ValueError("checkpoint identity hashes are missing")
    if not isinstance(predictions, list):
        raise ValueError("development predictions must be a list")

    styles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    head_ids: set[str] = set()
    thresholds: set[float] = set()
    for row in predictions:
        style = row.get("prompt_style")
        if style not in {"original", "plain"}:
            raise ValueError("unknown prompt style")
        styles[style].append(row)
        head_ids.add(row.get("head_sha256"))
        thresholds.add(row.get("threshold"))
    if set(styles) != {"original", "plain"}:
        raise ValueError("expected original and plain prompt styles")
    if head_ids != {artifact_hash} or thresholds != {receipt.get("threshold")}:
        raise ValueError("prediction head identity or threshold mismatch")

    scored: dict[str, Any] = {}
    for style in ("original", "plain"):
        scored[style] = _metric(cases, styles[style])
        recorded = receipt.get("development", {}).get(style, {})
        for key in ("rows", "eligible", "eligible_passes", "unsafe_classifier_passes"):
            if scored[style].get(key) != recorded.get(key):
                raise ValueError(f"independent score differs from receipt: {style}.{key}")
    timing = receipt.get("warm_classification_ms", {})
    resources = receipt.get("resource_samples", [])
    baselines = {
        "always_abstain": _constant_baseline(cases, "abstain"),
        "always_not_abstain": _constant_baseline(cases, "not_abstain"),
    }
    return {
        "schema": "wrench.qwen-binary-development-rescore.v1",
        "status": "STRICT_DEVELOPMENT_RESCORE_COMPLETE",
        "quality_claim": False,
        "scope": "development classifier decisions only; no proposal, verifier, or tool execution",
        "final_split_read": False,
        "provider_calls": 0,
        "base_weights_updated": False,
        "case_file_sha256": sha256(cases_bytes),
        "source_receipt_sha256": sha256(receipt_bytes),
        "predictions_sha256": sha256(predictions_bytes),
        "head_artifact_sha256": artifact_hash,
        "head_artifact_bytes": len(artifact_bytes),
        "checkpoint_identity": receipt["checkpoint_sha256"],
        "backbone_parameter_bytes": receipt.get("backbone_parameter_bytes"),
        "backbone_vram_allocated_bytes_after_load": receipt.get("backbone_vram_allocated_bytes_after_load"),
        "head_parameter_bytes": receipt.get("head_raw_bytes"),
        "head_vram_allocated_delta_bytes": receipt.get("head_vram_allocated_delta_bytes"),
        "threshold": receipt.get("threshold"),
        "max_tokens": receipt.get("max_tokens"),
        "warm_classification_ms": timing,
        "development_constant_baselines": baselines,
        "resource_sample_count": len(resources),
        "minimum_free_vram_mib": min((item["vram_free_mib"] for item in resources), default=None),
        "minimum_free_ram_bytes": min((item["ram_free"] for item in resources), default=None),
        "development": scored,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = rescore(args.cases, args.receipt, args.predictions, args.artifact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {style: {key: value for key, value in metrics.items() if key in {
        "rows", "eligible", "labeled_abstain", "eligible_passes", "eligible_coverage",
        "unsafe_classifier_passes", "unsafe_miss_rate", "overall_accuracy", "confusion",
    }} for style, metrics in result["development"].items()}
    print(json.dumps({"status": result["status"], "quality_claim": False,
                      "development": summary,
                      "constant_baselines": result["development_constant_baselines"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
