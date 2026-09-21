#!/usr/bin/env python3
"""Evaluate a real Hugging Face Wrench checkpoint without the mechanical fast path.

This tool is intentionally development-only. It runs the model's own
generation on a named split, then applies the same independent verifier used by
the serving path. It never reads the sealed final split unless the caller
explicitly supplies that path, and its receipt remains a diagnostic artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForImageTextToText, AutoTokenizer


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness.core import execute_model_output  # noqa: E402
try:
    from tools.calibrate_qwen_router import LoRALinear, _attach_attention_lora  # type: ignore  # noqa: E402
except ModuleNotFoundError:
    from calibrate_qwen_router import LoRALinear, _attach_attention_lora  # type: ignore  # noqa: E402


def _load_adapter(model: Any, adapter_path: Path) -> dict[str, Any]:
    bundle = torch.load(adapter_path, map_location="cpu", weights_only=False)
    if not isinstance(bundle, dict) or bundle.get("schema") != "wrench.qwen-router-adapter.v1":
        raise ValueError(f"unsupported Wrench adapter: {adapter_path}")
    rank = int(bundle.get("lora_rank", 8))
    alpha = float(bundle.get("lora_alpha", 16.0))
    base_head = model.lm_head
    model.lm_head = LoRALinear(base_head, rank, alpha)
    attention_modules: list[str] = []
    if bundle.get("attention_lora"):
        _, attention_modules = _attach_attention_lora(model, rank=rank, alpha=alpha)
    state_dict = bundle.get("state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError(f"adapter state_dict is missing: {adapter_path}")
    missing, unexpected = model.load_state_dict(state_dict, strict=False)
    unexpected = [name for name in unexpected if not name.endswith(".weight_scale")]
    if unexpected:
        raise ValueError(f"adapter has unexpected parameters: {unexpected[:5]}")
    return {
        "path": str(adapter_path.resolve()),
        "rank": rank,
        "alpha": alpha,
        "attention_lora": bool(bundle.get("attention_lora")),
        "attention_modules": attention_modules,
        "missing_count": len(missing),
    }


def _messages(row: dict[str, Any]) -> list[dict[str, str]]:
    messages = row.get("messages")
    if isinstance(messages, list) and messages:
        return messages
    result: list[dict[str, str]] = []
    if isinstance(row.get("system"), str) and row["system"]:
        result.append({"role": "system", "content": row["system"]})
    result.append({"role": "user", "content": str(row.get("prompt", ""))})
    return result


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    rows = [
        json.loads(line)
        for line in args.cases.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if args.max_cases is not None:
        if args.max_cases < 1:
            raise ValueError("--max-cases must be positive")
        rows = rows[: args.max_cases]
    if not rows:
        raise ValueError("cases file is empty")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        local_files_only=True,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        dtype=torch.bfloat16,
        local_files_only=True,
        trust_remote_code=True,
    ).to("cuda" if torch.cuda.is_available() else "cpu")
    adapter_receipt = None
    if args.adapter:
        adapter_receipt = _load_adapter(model, args.adapter)
    model.eval()
    device = next(model.parameters()).device
    results: list[dict[str, Any]] = []
    for row in rows:
        messages = _messages(row)
        prompt = next(
            (item["content"] for item in reversed(messages) if item.get("role") == "user"),
            "",
        )
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        batch = tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False)
        batch = {key: value.to(device) for key, value in batch.items()}
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(
                **batch,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                use_cache=True,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        generated = output[0, batch["input_ids"].shape[-1] :]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        verified = execute_model_output(text, args.allowed_root, request_prompt=prompt)
        expected_status = row.get("expected_status")
        expected_target = row.get("target")
        exact = False
        if isinstance(expected_target, str):
            try:
                exact = json.loads(text) == json.loads(expected_target)
            except json.JSONDecodeError:
                exact = False
        outcome_match = (
            verified.get("status") == expected_status
            and (expected_status != "accepted" or exact)
        )
        results.append(
            {
                "id": row.get("id"),
                "family": row.get("family"),
                "expected_status": expected_status,
                "model_output": text,
                "verified_status": verified.get("status"),
                "fallback_reason": verified.get("fallback_reason"),
                "exact_target_match": exact,
                "outcome_match": outcome_match,
                "latency_ms": elapsed_ms,
                "prompt_tokens": int(batch["input_ids"].shape[-1]),
            }
        )
    accepted = sum(item["verified_status"] == "accepted" for item in results)
    exact = sum(item["exact_target_match"] for item in results)
    matched = sum(item["outcome_match"] for item in results)
    receipt = {
        "schema": "wrench.hf-generation-development-eval.v1",
        "status": "PASS_DEVELOPMENT_DIAGNOSTIC" if matched == len(results) else "DEVELOPMENT_GAPS",
        "model": str(args.model.resolve()),
        "cases": str(args.cases.resolve()),
        "case_count": len(results),
        "max_cases": args.max_cases,
        "verified_accepted": accepted,
        "exact_target_matches": exact,
        "outcome_matches": matched,
        "median_latency_ms": _percentile([item["latency_ms"] for item in results], 50),
        "p95_latency_ms": _percentile([item["latency_ms"] for item in results], 95),
        "device": str(device),
        "adapter": adapter_receipt,
        "quality_claim": False,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt


def _percentile(values: list[float], percentile: int) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile / 100)))
    return round(ordered[index], 3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--allowed-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="development-only prefix limit for overfit and pipeline sanity checks",
    )
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--adapter", type=Path, default=None)
    args = parser.parse_args()
    receipt = evaluate(args)
    print(json.dumps({key: receipt[key] for key in (
        "status", "case_count", "verified_accepted", "exact_target_matches",
        "outcome_matches", "median_latency_ms", "p95_latency_ms", "device",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
