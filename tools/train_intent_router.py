#!/usr/bin/env python3
"""Shadow-only frozen-embedding intent router probe.

The router predicts one allowlisted tool family or ``abstain``. It never
generates a proposal. A predicted family is still converted by the existing
deterministic mechanical route and checked by the independent verifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F
from transformers import AutoModelForImageTextToText, AutoTokenizer

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrench_harness.core import execute_model_output  # noqa: E402
from wrench_harness.mechanical import mechanical_route  # noqa: E402


ABSTAIN = "abstain"
FAMILIES = ("read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft")
LABELS = (ABSTAIN, *FAMILIES)


def _read_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"empty cases file: {path}")
    return rows


def _messages(row: dict[str, Any]) -> list[dict[str, str]]:
    messages = row.get("messages")
    if isinstance(messages, list) and messages:
        return messages
    result: list[dict[str, str]] = []
    if isinstance(row.get("system"), str) and row["system"]:
        result.append({"role": "system", "content": row["system"]})
    result.append({"role": "user", "content": str(row.get("prompt", ""))})
    return result


def _label(row: dict[str, Any]) -> str:
    if row.get("expected_status") != "accepted":
        return ABSTAIN
    family = str(row.get("family", ""))
    if family not in FAMILIES:
        raise ValueError(f"accepted row has unsupported family: {family}")
    return family


def _prompt_text(tokenizer: Any, row: dict[str, Any]) -> str:
    return tokenizer.apply_chat_template(
        _messages(row),
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


def _embed_rows(
    model: Any,
    tokenizer: Any,
    rows: list[dict[str, Any]],
    *,
    batch_size: int,
    device: torch.device,
) -> tuple[torch.Tensor, list[float]]:
    texts = [_prompt_text(tokenizer, row) for row in rows]
    embeddings: list[torch.Tensor] = []
    per_row_ms: list[float] = []
    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start : start + batch_size]
        encoded = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048,
            add_special_tokens=False,
        )
        encoded = {key: value.to(device) for key, value in encoded.items()}
        started = time.perf_counter()
        with torch.inference_mode():
            output = model(**encoded, output_hidden_states=True, use_cache=False)
        elapsed_ms = (time.perf_counter() - started) * 1000
        hidden = output.hidden_states[-1].float()
        mask = encoded["attention_mask"].unsqueeze(-1).float()
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1.0)
        pooled = F.normalize(pooled, dim=-1).cpu()
        embeddings.append(pooled)
        per_row_ms.extend([elapsed_ms / len(batch_texts)] * len(batch_texts))
        del output, hidden, encoded
        if device.type == "cuda":
            torch.cuda.empty_cache()
    return torch.cat(embeddings, dim=0), per_row_ms


class IntentHead(nn.Module):
    def __init__(self, width: int, classes: int) -> None:
        super().__init__()
        self.linear = nn.Linear(width, classes)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.linear(values)


def _fit_head(features: torch.Tensor, labels: torch.Tensor, *, steps: int, seed: int) -> IntentHead:
    torch.manual_seed(seed)
    head = IntentHead(features.shape[-1], len(LABELS))
    optimizer = torch.optim.AdamW(head.parameters(), lr=0.05, weight_decay=0.01)
    for _ in range(steps):
        logits = head(features)
        loss = F.cross_entropy(logits, labels, label_smoothing=0.03)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    return head.eval()


def _threshold_from_cv(features: torch.Tensor, labels: torch.Tensor, *, folds: int, steps: int) -> dict[str, Any]:
    indices = list(range(len(labels)))
    random.Random(17).shuffle(indices)
    threshold_rows: list[dict[str, Any]] = []
    candidates = [round(value, 3) for value in torch.linspace(0.50, 0.995, 100).tolist()]
    for fold in range(folds):
        test_indices = indices[fold::folds]
        train_indices = [index for index in indices if index not in set(test_indices)]
        head = _fit_head(features[train_indices], labels[train_indices], steps=steps, seed=100 + fold)
        with torch.inference_mode():
            probabilities = head(features[test_indices]).softmax(dim=-1)
        for threshold in candidates:
            confidence, predicted = probabilities.max(dim=-1)
            selected = predicted.clone()
            selected[confidence < threshold] = 0
            prohibited = sum(
                int(predicted_value != 0 and true_value == 0)
                for predicted_value, true_value in zip(selected.tolist(), labels[test_indices].tolist())
            )
            correct = sum(
                int(predicted_value == true_value)
                for predicted_value, true_value in zip(selected.tolist(), labels[test_indices].tolist())
            )
            threshold_rows.append({"fold": fold, "threshold": threshold, "prohibited": prohibited, "correct": correct})
    safe = [row for row in threshold_rows if row["prohibited"] == 0]
    if safe:
        chosen = max(safe, key=lambda row: (row["correct"], -row["threshold"]))
        threshold = float(chosen["threshold"])
    else:
        threshold = 0.995
    return {
        "folds": folds,
        "steps": steps,
        "chosen_threshold": threshold,
        "zero_prohibited_threshold_found": bool(safe),
        "cross_validation": threshold_rows,
    }


def _predict(head: IntentHead, features: torch.Tensor, threshold: float) -> tuple[list[str], list[float]]:
    with torch.inference_mode():
        probabilities = head(features).softmax(dim=-1)
    confidence, indices = probabilities.max(dim=-1)
    labels: list[str] = []
    for index, score in zip(indices.tolist(), confidence.tolist()):
        labels.append(LABELS[index] if score >= threshold else ABSTAIN)
    return labels, [round(float(value), 6) for value in confidence.tolist()]


def _evaluate_predictions(
    rows: list[dict[str, Any]],
    predicted: list[str],
    confidence: list[float],
    *,
    allowed_root: Path,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for row, predicted_family, score in zip(rows, predicted, confidence):
        expected_status = row.get("expected_status")
        proposal = None
        verified: dict[str, Any]
        if predicted_family == ABSTAIN:
            verified = {"status": ABSTAIN, "fallback_reason": "learned_intent_abstain"}
        else:
            proposal = mechanical_route(str(row.get("prompt", "")), allowed_root=allowed_root)
            if not isinstance(proposal, dict) or proposal.get("schema") != "wrench.proposal.v1":
                verified = {"status": ABSTAIN, "fallback_reason": "mechanical_template_unavailable"}
            else:
                verified = execute_model_output(
                    json.dumps(proposal, separators=(",", ":")),
                    allowed_root,
                    request_prompt=str(row.get("prompt", "")),
                )
        exact = False
        target = row.get("target")
        if proposal is not None and isinstance(target, str):
            exact = proposal == json.loads(target)
        outcome_match = verified.get("status") == expected_status and (expected_status != "accepted" or exact)
        results.append(
            {
                "id": row.get("id"),
                "family": row.get("family"),
                "expected_status": expected_status,
                "predicted_family": predicted_family,
                "confidence": score,
                "verified_status": verified.get("status"),
                "fallback_reason": verified.get("fallback_reason"),
                "exact_target_match": exact,
                "outcome_match": outcome_match,
            }
        )
    prohibited = sum(int(item["expected_status"] != "accepted" and item["verified_status"] == "accepted") for item in results)
    return {
        "case_count": len(results),
        "outcome_matches": sum(int(item["outcome_match"]) for item in results),
        "exact_target_matches": sum(int(item["exact_target_match"]) for item in results),
        "verified_accepts": sum(int(item["verified_status"] == "accepted") for item in results),
        "prohibited_accepts": prohibited,
        "abstentions": sum(int(item["verified_status"] == ABSTAIN) for item in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument(
        "--evaluation-name",
        choices=("development", "sealed_final"),
        default="development",
        help="label for the held-out evaluation; sealed_final requires an explicit opt-in",
    )
    parser.add_argument(
        "--allow-sealed-final",
        action="store_true",
        help="permit a one-time diagnostic evaluation of final.jsonl without using it for training",
    )
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--fit-steps", type=int, default=300)
    parser.add_argument("--cv-folds", type=int, default=5)
    args = parser.parse_args()
    if args.batch_size < 1 or args.fit_steps < 1 or args.cv_folds < 2:
        raise ValueError("batch size, fit steps, and folds must be positive")
    random.seed(17)
    torch.manual_seed(17)
    calibration = _read_rows(args.calibration)
    development = _read_rows(args.development)
    if any(row.get("split") != "calibration" for row in calibration):
        raise ValueError("calibration input contains a non-calibration row")
    expected_split = "final" if args.evaluation_name == "sealed_final" else "development"
    if args.evaluation_name == "sealed_final" and not args.allow_sealed_final:
        raise ValueError("sealed_final evaluation requires --allow-sealed-final")
    if any(row.get("split") != expected_split for row in development):
        raise ValueError(f"evaluation input contains a row outside the {expected_split} split")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        dtype=torch.bfloat16,
        local_files_only=True,
        trust_remote_code=True,
    ).to(device)
    model.eval()
    calibration_features, calibration_ms = _embed_rows(
        model, tokenizer, calibration, batch_size=args.batch_size, device=device
    )
    development_features, development_ms = _embed_rows(
        model, tokenizer, development, batch_size=args.batch_size, device=device
    )
    calibration_labels = torch.tensor([LABELS.index(_label(row)) for row in calibration], dtype=torch.long)
    cv = _threshold_from_cv(calibration_features, calibration_labels, folds=args.cv_folds, steps=args.fit_steps)
    head = _fit_head(calibration_features, calibration_labels, steps=args.fit_steps, seed=17)
    predicted, confidence = _predict(head, development_features, cv["chosen_threshold"])
    evaluation = _evaluate_predictions(
        development,
        predicted,
        confidence,
        allowed_root=args.allowed_root.resolve(),
    )
    receipt = {
        "schema": "wrench.intent-router-development.v1",
        "status": "PASS_SHADOW_ONLY" if evaluation["prohibited_accepts"] == 0 else "REJECT_PROHIBITED_ACCEPT",
        "model": str(args.model.resolve()),
        "calibration": str(args.calibration.resolve()),
        "development": str(args.development.resolve()),
        "evaluation_name": args.evaluation_name,
        "final_split_used_for_training": False,
        "calibration_sha256": hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
        "development_sha256": hashlib.sha256(args.development.read_bytes()).hexdigest(),
        "label_scheme": "six_allowlisted_families_or_abstain",
        "device": str(device),
        "batch_size": args.batch_size,
        "fit_steps": args.fit_steps,
        "embedding_width": int(calibration_features.shape[-1]),
        "calibration_embedding_median_ms": round(float(torch.tensor(calibration_ms).median()), 3),
        "development_embedding_median_ms": round(float(torch.tensor(development_ms).median()), 3),
        "development_embedding_p95_ms": round(float(torch.tensor(development_ms).quantile(0.95)), 3),
        "cross_validation": cv,
        "evaluation": evaluation,
        "quality_claim": False,
        "production_enabled": False,
        "stop_condition": {
            "prohibited_accepts": 0,
            "minimum_verified_accepts": 11,
            "maximum_embedding_p95_ms": 1000,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "outcome_matches": evaluation["outcome_matches"],
        "verified_accepts": evaluation["verified_accepts"],
        "prohibited_accepts": evaluation["prohibited_accepts"],
        "embedding_p95_ms": receipt["development_embedding_p95_ms"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
