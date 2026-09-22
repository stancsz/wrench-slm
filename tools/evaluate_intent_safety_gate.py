#!/usr/bin/env python3
"""Evaluate an intent-family safety gate over an existing HF generation receipt.

This is a diagnostic A/B tool. The gate can only turn a generated proposal into
an abstention when the frozen sidecar disagrees with its action family. It
cannot create or authorize a proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import torch

from train_intent_router import (
    ABSTAIN,
    FAMILIES,
    IntentHead,
    _embed_rows,
    _read_rows,
)


def _load_sidecar(path: Path) -> tuple[IntentHead, list[str], float, dict[str, Any]]:
    bundle = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(bundle, dict) or bundle.get("schema") != "wrench.intent-router-sidecar.v1":
        raise ValueError(f"unsupported sidecar: {path}")
    labels = bundle.get("labels")
    if labels != [ABSTAIN, *FAMILIES]:
        raise ValueError("sidecar labels do not match the current allowlisted families")
    width = int(bundle.get("embedding_width", 0))
    if width < 1:
        raise ValueError("sidecar embedding width is invalid")
    head = IntentHead(width, len(labels))
    state_dict = bundle.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError("sidecar state_dict is missing")
    head.load_state_dict(state_dict, strict=True)
    threshold = float(bundle.get("confidence_threshold", 1.0))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("sidecar confidence threshold is invalid")
    return head.eval(), labels, threshold, bundle


def evaluate_gate(rows: list[dict[str, Any]], direct_receipt: dict[str, Any], predicted: list[str], confidence: list[float]) -> dict[str, Any]:
    direct_results = direct_receipt.get("results")
    if not isinstance(direct_results, list) or len(direct_results) != len(rows):
        raise ValueError("direct receipt does not align with cases")
    results: list[dict[str, Any]] = []
    for row, direct, family, score in zip(rows, direct_results, predicted, confidence):
        output = str(direct.get("model_output", ""))
        try:
            proposal = json.loads(output)
        except json.JSONDecodeError:
            proposal = None
        action = proposal.get("action") if isinstance(proposal, dict) else None
        gate_passed = family != ABSTAIN and action == family
        gated_status = direct.get("verified_status") if gate_passed else ABSTAIN
        expected_status = row.get("expected_status")
        exact = bool(direct.get("exact_target_match")) if gate_passed else False
        outcome_match = gated_status == expected_status and (expected_status != "accepted" or exact)
        results.append(
            {
                "id": row.get("id"),
                "expected_status": expected_status,
                "direct_verified_status": direct.get("verified_status"),
                "direct_outcome_match": bool(direct.get("outcome_match")),
                "predicted_family": family,
                "confidence": score,
                "generated_action": action,
                "gate_passed": gate_passed,
                "gated_status": gated_status,
                "outcome_match": outcome_match,
            }
        )
    return {
        "case_count": len(results),
        "outcome_matches": sum(int(item["outcome_match"]) for item in results),
        "verified_accepts": sum(int(item["gated_status"] == "accepted") for item in results),
        "prohibited_accepts": sum(
            int(item["expected_status"] != "accepted" and item["gated_status"] == "accepted")
            for item in results
        ),
        "gate_abstentions": sum(int(not item["gate_passed"]) for item in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--direct-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()
    rows = _read_rows(args.cases)
    direct_receipt = json.loads(args.direct_receipt.read_text(encoding="utf-8"))
    head, labels, threshold, sidecar = _load_sidecar(args.sidecar)
    tokenizer = __import__("transformers").AutoTokenizer.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = __import__("transformers").AutoModelForImageTextToText.from_pretrained(
        args.model, dtype=torch.bfloat16, local_files_only=True, trust_remote_code=True
    ).to("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    features, per_row_ms = _embed_rows(
        model,
        tokenizer,
        rows,
        batch_size=args.batch_size,
        device=next(model.parameters()).device,
    )
    with torch.inference_mode():
        probabilities = head(features).softmax(dim=-1)
    confidence_tensor, index_tensor = probabilities.max(dim=-1)
    predicted: list[str] = []
    confidence: list[float] = []
    for index, score in zip(index_tensor.tolist(), confidence_tensor.tolist()):
        predicted.append(labels[index] if score >= threshold else ABSTAIN)
        confidence.append(round(float(score), 6))
    evaluation = evaluate_gate(rows, direct_receipt, predicted, confidence)
    receipt = {
        "schema": "wrench.intent-safety-gate-development.v1",
        "status": "PASS_SHADOW_ONLY" if evaluation["prohibited_accepts"] == 0 else "REJECT_PROHIBITED_ACCEPT",
        "model": str(args.model.resolve()),
        "sidecar": str(args.sidecar.resolve()),
        "cases": str(args.cases.resolve()),
        "direct_receipt": str(args.direct_receipt.resolve()),
        "sidecar_sha256": hashlib.sha256(args.sidecar.read_bytes()).hexdigest(),
        "direct_receipt_sha256": hashlib.sha256(args.direct_receipt.read_bytes()).hexdigest(),
        "device": str(next(model.parameters()).device),
        "embedding_median_ms": round(float(torch.tensor(per_row_ms).median()), 3),
        "embedding_p95_ms": round(float(torch.tensor(per_row_ms).quantile(0.95)), 3),
        "threshold": threshold,
        "evaluation": evaluation,
        "quality_claim": False,
        "production_enabled": False,
        "authority": "gate_can_only_abstain; verifier_remains_authoritative",
        "sidecar_metadata": {
            "schema": sidecar.get("schema"),
            "base_model": sidecar.get("base_model"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "outcome_matches": evaluation["outcome_matches"],
        "verified_accepts": evaluation["verified_accepts"],
        "prohibited_accepts": evaluation["prohibited_accepts"],
        "embedding_p95_ms": receipt["embedding_p95_ms"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
