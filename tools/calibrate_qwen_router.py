#!/usr/bin/env python3
"""Small, explicit SFT probe for a structurally pruned Qwen checkpoint.

This is intentionally a development calibration tool. It freezes the dense
backbone, trains the pruned router rows plus a low-rank output-head adapter on
JSONL cases carrying an explicit target, merges the adapter, and writes a
normal HF checkpoint outside the repository. It is not a final training or
release pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import torch
from torch import nn
from transformers import AutoModelForImageTextToText, AutoTokenizer


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, rank: int, alpha: float) -> None:
        super().__init__()
        self.base = base
        self.rank = rank
        self.scaling = alpha / rank
        self.lora_a = nn.Parameter(torch.zeros(rank, base.in_features, dtype=base.weight.dtype, device=base.weight.device))
        self.lora_b = nn.Parameter(torch.zeros(base.out_features, rank, dtype=base.weight.dtype, device=base.weight.device))
        nn.init.normal_(self.lora_a, std=0.02)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        base = self.base(hidden_states)
        delta = torch.matmul(torch.matmul(hidden_states, self.lora_a.t()), self.lora_b.t())
        return base + self.scaling * delta

    def merge(self) -> nn.Linear:
        with torch.no_grad():
            self.base.weight.add_(self.scaling * torch.matmul(self.lora_b, self.lora_a).to(self.base.weight.dtype))
        return self.base


def _read_cases(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or any(not isinstance(row.get("target"), str) or not row["target"] for row in rows):
        raise ValueError("every calibration row needs a non-empty target string")
    return rows


def _example(tokenizer: Any, row: dict[str, Any]) -> tuple[list[int], list[int]]:
    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        messages = []
        if isinstance(row.get("system"), str) and row["system"].strip():
            messages.append({"role": "system", "content": row["system"]})
        messages.append({"role": "user", "content": row["prompt"]})
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    target_text = row["target"] + (tokenizer.eos_token or "")
    prompt_ids = tokenizer(prompt_text, add_special_tokens=False).input_ids
    full_ids = tokenizer(prompt_text + target_text, add_special_tokens=False).input_ids
    if len(full_ids) <= len(prompt_ids):
        raise ValueError(f"target tokenization was empty for {row.get('id')}")
    return full_ids, [-100] * len(prompt_ids) + full_ids[len(prompt_ids) :]


def _pad(batch: list[tuple[list[int], list[int]]], pad_id: int, device: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    length = max(len(item[0]) for item in batch)
    ids, labels, mask = [], [], []
    for input_ids, target_labels in batch:
        pad = length - len(input_ids)
        ids.append(input_ids + [pad_id] * pad)
        labels.append(target_labels + [-100] * pad)
        mask.append([1] * len(input_ids) + [0] * pad)
    return (
        torch.tensor(ids, dtype=torch.long, device=device),
        torch.tensor(labels, dtype=torch.long, device=device),
        torch.tensor(mask, dtype=torch.long, device=device),
    )


def calibrate(args: argparse.Namespace) -> dict[str, Any]:
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, low_cpu_mem_usage=False).to(device)
    model.config.use_cache = False
    model.train()
    model.requires_grad_(False)

    trainable: list[nn.Parameter] = []
    router_count = 0
    for name, parameter in model.named_parameters():
        if ".mlp.gate.weight" in name or ".mlp.shared_expert_gate.weight" in name:
            parameter.requires_grad_(True)
            trainable.append(parameter)
            router_count += parameter.numel()

    output_head = model.lm_head
    if not isinstance(output_head, nn.Linear):
        raise TypeError(f"expected a linear lm_head, got {type(output_head).__name__}")
    model.lm_head = LoRALinear(output_head, args.rank, args.alpha)
    trainable.extend([model.lm_head.lora_a, model.lm_head.lora_b])
    optimizer = torch.optim.AdamW(trainable, lr=args.learning_rate, weight_decay=0.0)
    rows = _read_cases(args.calibration)
    encoded = [_example(tokenizer, row) for row in rows]
    order = list(range(len(rows)))
    history: list[float] = []
    for step in range(args.steps):
        if step % len(order) == 0:
            random.shuffle(order)
        batch = [encoded[order[step % len(order)]]]
        input_ids, labels, attention_mask = _pad(batch, tokenizer.pad_token_id or tokenizer.eos_token_id, device)
        optimizer.zero_grad(set_to_none=True)
        output = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels, use_cache=False)
        loss = output.loss
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step}: {loss.item()}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()
        history.append(float(loss.detach().cpu()))
        if args.log_every and (step + 1) % args.log_every == 0:
            print(json.dumps({"step": step + 1, "loss": history[-1]}))

    model.lm_head = model.lm_head.merge()
    model.config.use_cache = True
    model.eval()
    args.output.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(args.output, safe_serialization=True, max_shard_size="2GB")
    tokenizer.save_pretrained(args.output)
    manifest = {
        "schema": "wrench.qwen-router-calibration.v1",
        "status": "EXPERIMENTAL_CALIBRATED_UNQUANTIZED",
        "source_model": str(args.model.resolve()),
        "calibration_path": str(args.calibration.resolve()),
        "calibration_sha256": hashlib.sha256(args.calibration.read_bytes()).hexdigest(),
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "lora_rank": args.rank,
        "lora_alpha": args.alpha,
        "trainable_router_parameters": router_count,
        "final_loss": history[-1],
        "initial_loss": history[0],
        "device": device,
        "quality_claim": False,
        "scope": "development-only calibration probe; not final quality evidence",
    }
    (args.output / "wrench-calibration-receipt.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=5e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=float, default=16.0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--log-every", type=int, default=10)
    args = parser.parse_args()
    calibrate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
