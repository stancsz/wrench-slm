#!/usr/bin/env python3
"""Fast output-head-only calibration for a pruned Wrench checkpoint.

The original calibration probe keeps autograd alive through the full 4B
backbone. On a 16 GB GPU that makes even a tiny LoRA probe page heavily. This
variant runs the frozen backbone under ``no_grad`` once per row, caches only
the hidden states that predict target tokens, and trains a LoRA on ``lm_head``
against those cached states. It is still a development experiment, not a
quality or release pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any
import sys

import torch
from torch import nn
from transformers import AutoModelForImageTextToText, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.calibrate_qwen_router import LoRALinear, _example, _read_cases


def _cache_states(model: nn.Module, tokenizer: Any, rows: list[dict[str, Any]], device: str) -> list[tuple[torch.Tensor, torch.Tensor]]:
    cached: list[tuple[torch.Tensor, torch.Tensor]] = []
    model.eval()
    with torch.no_grad():
        for index, row in enumerate(rows):
            full_ids, labels = _example(tokenizer, row)
            prompt_messages = row.get("messages")
            if not isinstance(prompt_messages, list) or not prompt_messages:
                prompt_messages = []
                if isinstance(row.get("system"), str) and row["system"].strip():
                    prompt_messages.append({"role": "system", "content": row["system"]})
                prompt_messages.append({"role": "user", "content": row["prompt"]})
            prompt_text = tokenizer.apply_chat_template(
                prompt_messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            prompt_len = len(tokenizer(prompt_text, add_special_tokens=False).input_ids)
            input_ids = torch.tensor([full_ids], dtype=torch.long, device=device)
            attention_mask = torch.ones_like(input_ids)
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                output_hidden_states=True,
            )
            hidden_states = output.hidden_states[-1]
            target_positions = [pos - 1 for pos, label in enumerate(labels) if label != -100 and pos > 0]
            target_ids = [label for label in labels if label != -100]
            if not target_positions or len(target_positions) != len(target_ids):
                raise ValueError(f"row has no aligned target states: {row.get('id')}")
            row_hidden = hidden_states[0, target_positions].detach().to("cpu")
            row_targets = torch.tensor(target_ids, dtype=torch.long, device="cpu")
            cached.append((row_hidden, row_targets))
            if (index + 1) % 25 == 0:
                print(json.dumps({"cached_rows": index + 1, "total_rows": len(rows)}), flush=True)
    return cached


def calibrate(args: argparse.Namespace) -> dict[str, Any]:
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        local_files_only=True,
    )
    model = AutoModelForImageTextToText.from_pretrained(
        args.model,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=False,
        trust_remote_code=True,
        local_files_only=True,
    ).to(device)
    model.requires_grad_(False)
    rows = _read_cases(args.calibration)
    cached = _cache_states(model, tokenizer, rows, device)
    output_head = model.lm_head
    if not isinstance(output_head, nn.Linear):
        raise TypeError(f"expected a linear lm_head, got {type(output_head).__name__}")
    adapter = LoRALinear(output_head, args.rank, args.alpha)
    model.lm_head = adapter
    adapter.train()
    optimizer = torch.optim.AdamW([adapter.lora_a, adapter.lora_b], lr=args.learning_rate, weight_decay=0.0)
    history: list[float] = []
    order = list(range(len(cached)))
    for step in range(args.steps):
        if step % len(order) == 0:
            random.shuffle(order)
        hidden, targets = cached[order[step % len(order)]]
        hidden = hidden.to(device)
        targets = targets.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = adapter(hidden)
        loss = nn.functional.cross_entropy(logits.float(), targets)
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}: {loss.item()}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_([adapter.lora_a, adapter.lora_b], 1.0)
        optimizer.step()
        history.append(float(loss.detach().cpu()))
        if args.log_every and (step + 1) % args.log_every == 0:
            print(json.dumps({"step": step + 1, "loss": history[-1]}), flush=True)
    with torch.no_grad():
        output_head.weight.add_((adapter.scaling * torch.matmul(adapter.lora_b, adapter.lora_a)).to(output_head.weight.dtype))
    model.lm_head = output_head
    model.eval()
    args.output.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(args.output, safe_serialization=True, max_shard_size="2GB")
    tokenizer.save_pretrained(args.output)
    manifest = {
        "schema": "wrench.qwen-head-only-calibration.v1",
        "status": "EXPERIMENTAL_HEAD_ONLY_CALIBRATED_UNQUANTIZED",
        "source_model": str(args.model.resolve()),
        "calibration_path": str(args.calibration.resolve()),
        "calibration_sha256": hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
        "rows": len(rows),
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "lora_rank": args.rank,
        "lora_alpha": args.alpha,
        "trainable_parameter_count": adapter.lora_a.numel() + adapter.lora_b.numel(),
        "initial_loss": history[0],
        "final_loss": history[-1],
        "device": device,
        "backbone_gradients": False,
        "quality_claim": False,
        "scope": "development-only frozen-backbone output-head calibration",
    }
    (args.output / "wrench-calibration-receipt.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--alpha", type=float, default=32.0)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--log-every", type=int, default=25)
    args = parser.parse_args()
    calibrate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
