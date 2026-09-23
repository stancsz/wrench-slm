#!/usr/bin/env python3
"""Evaluate a real Hugging Face Wrench checkpoint without the mechanical fast path.

This tool is intentionally development-only. It runs the model's own
generation on a named split, then applies the same independent verifier used by
the serving path. It never reads the sealed final split unless the caller
explicitly supplies that path, and its receipt remains a diagnostic artifact.
"""

from __future__ import annotations

import argparse
import hashlib
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
    from tools.score_hf_wrench_receipt import score_result  # type: ignore  # noqa: E402
except ModuleNotFoundError:
    from score_hf_wrench_receipt import score_result  # type: ignore  # noqa: E402
try:
    from tools.calibrate_qwen_router import LoRALinear, _attach_attention_lora  # type: ignore  # noqa: E402
except ModuleNotFoundError:
    from calibrate_qwen_router import LoRALinear, _attach_attention_lora  # type: ignore  # noqa: E402


def _guided_json_prefix_fn(tokenizer: Any) -> Any:
    """Build an optional development-only JSON schema decoder."""

    try:
        import transformers
        import transformers.tokenization_utils as tokenization_utils

        # lm-format-enforcer 0.11.x imports this symbol from the pre-5.x
        # module location, while Transformers 5.16 exports it at package root.
        if not hasattr(tokenization_utils, "PreTrainedTokenizerBase"):
            tokenization_utils.PreTrainedTokenizerBase = transformers.PreTrainedTokenizerBase
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.transformers import (
            build_transformers_prefix_allowed_tokens_fn,
        )
    except ImportError as exc:
        raise RuntimeError(
            "--guided-json-schema requires lm-format-enforcer in the evaluation environment"
        ) from exc

    schema = {
        "type": "object",
        "properties": {
            "schema": {"type": "string", "enum": ["wrench.proposal.v1"]},
            "action": {
                "type": "string",
                "enum": [
                    "read_file",
                    "read_lines",
                    "literal_search",
                    "git_read_status",
                    "health_read",
                    "patch_draft",
                ],
            },
            "path": {"type": "string", "maxLength": 512},
            "max_bytes": {"type": "integer", "minimum": 1, "maximum": 1048576},
            "start": {"type": "integer", "minimum": 1},
            "end": {"type": "integer", "minimum": 1},
            "root": {"type": "string", "maxLength": 256},
            "literal": {"type": "string", "maxLength": 512},
            "max_matches": {"type": "integer", "minimum": 1, "maximum": 1000},
            "repo_root": {"type": "string", "maxLength": 256},
            "url": {"type": "string", "maxLength": 2048},
            "timeout_seconds": {"type": "number", "minimum": 0.1, "maximum": 30},
            "files": {"type": "array", "maxItems": 16, "items": {"type": "string", "maxLength": 512}},
            "review_only": {"type": "boolean"},
            "diff": {"type": "string", "maxLength": 20000},
        },
        "required": ["schema", "action"],
        "additionalProperties": False,
    }
    return build_transformers_prefix_allowed_tokens_fn(
        tokenizer,
        JsonSchemaParser(schema),
    )


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
    guided_json_prefix_fn = _guided_json_prefix_fn(tokenizer) if args.guided_json_schema else None
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
                **({"prefix_allowed_tokens_fn": guided_json_prefix_fn} if guided_json_prefix_fn else {}),
            )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        generated = output[0, batch["input_ids"].shape[-1] :]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        verified = execute_model_output(text, args.allowed_root, request_prompt=prompt)
        expected_status = row.get("expected_status")
        scoring = score_result(
            row,
            text,
            verified.get("status"),
            verified.get("fallback_reason"),
        )
        results.append(
            {
                "id": row.get("id"),
                "family": row.get("family"),
                "expected_status": expected_status,
                "expected_fallback_reason": row.get("expected_fallback_reason"),
                "model_output": text,
                "verified_status": verified.get("status"),
                "fallback_reason": verified.get("fallback_reason"),
                **scoring,
                "latency_ms": elapsed_ms,
                "prompt_tokens": int(batch["input_ids"].shape[-1]),
            }
        )
    accepted = sum(item["verified_status"] == "accepted" for item in results)
    exact = sum(item["exact_target_match"] for item in results)
    matched = sum(item["outcome_match"] for item in results)
    eligible = [item for item in results if item["expected_status"] == "accepted"]
    expected_abstains = [item for item in results if item["expected_status"] == "abstain"]
    receipt = {
        "schema": "wrench.hf-generation-development-eval.v1",
        "status": "PASS_DEVELOPMENT_DIAGNOSTIC" if matched == len(results) else "DEVELOPMENT_GAPS",
        "model": str(args.model.resolve()),
        "cases": str(args.cases.resolve()),
        "cases_bytes_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest().upper(),
        "case_count": len(results),
        "max_cases": args.max_cases,
        "max_new_tokens": args.max_new_tokens,
        "do_sample": False,
        "verified_accepted": accepted,
        "exact_target_matches": exact,
        "outcome_matches": matched,
        "eligible_case_count": len(eligible),
        "eligible_exact_accepts": sum(item["outcome_match"] for item in eligible),
        "expected_abstain_count": len(expected_abstains),
        "exact_abstention_matches": sum(item["outcome_match"] for item in expected_abstains),
        "prohibited_accepts": sum(
            item["expected_status"] == "abstain" and item["verified_status"] == "accepted"
            for item in results
        ),
        "invalid_json_outputs": sum(not item["model_json_valid"] for item in results),
        "median_latency_ms": _percentile([item["latency_ms"] for item in results], 50),
        "p95_latency_ms": _percentile([item["latency_ms"] for item in results], 95),
        "device": str(device),
        "adapter": adapter_receipt,
        "guided_json_schema": args.guided_json_schema,
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
    parser.add_argument(
        "--guided-json-schema",
        action="store_true",
        help="development-only LM Format Enforcer constraint for JSON syntax",
    )
    args = parser.parse_args()
    receipt = evaluate(args)
    print(json.dumps({key: receipt[key] for key in (
        "status", "case_count", "verified_accepted", "exact_target_matches",
        "outcome_matches", "eligible_exact_accepts", "exact_abstention_matches",
        "prohibited_accepts", "invalid_json_outputs", "median_latency_ms",
        "p95_latency_ms", "device",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
