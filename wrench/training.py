"""LoRA SFT and GRPO training loops for the local execution SLM."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch
from torch.utils.data import DataLoader

from .dataset import JsonlDataset, build_training_prompt
from .protocol import ROUTER_FALLBACK
from .reward import compute_reward


@dataclass
class TrainingMetrics:
    steps: int
    loss_start: float
    loss_end: float
    duration_s: float
    examples_seen: int


def build_lora_model(base_model, peft_config):
    from peft import get_peft_model
    model = get_peft_model(base_model, peft_config)
    model.print_trainable_parameters()
    return model


def sft_train(
    model,
    tokenizer,
    train_path: str,
    *,
    val_path: Optional[str] = None,
    micro_batch_size: int = 1,
    grad_accum_steps: int = 16,
    learning_rate: float = 1e-4,
    max_steps: int = 500,
    log_every: int = 25,
    seed: int = 42,
) -> TrainingMetrics:
    """LoRA SFT over masked prompts with deterministic data order."""
    torch.manual_seed(seed)
    dataset = JsonlDataset(train_path, tokenizer)
    dataloader = DataLoader(dataset, batch_size=None, num_workers=0)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=learning_rate)
    model.train()

    iterator = iter(dataloader)
    loss_start = loss_end = 0.0
    examples = 0
    started = time.perf_counter()
    losses: List[float] = []
    for step in range(max_steps):
        optimizer.zero_grad(set_to_none=True)
        accumulated = 0.0
        for micro in range(grad_accum_steps):
            try:
                batch = next(iterator)
            except StopIteration:
                iterator = iter(dataloader)
                batch = next(iterator)
            batch = {k: v.to(model.device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / grad_accum_steps
            loss.backward()
            accumulated += float(loss.detach())
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        optimizer.step()
        examples += grad_accum_steps
        losses.append(accumulated)
        if step == 0:
            loss_start = accumulated
        if (step + 1) % log_every == 0 or step == max_steps - 1:
            recent = sum(losses[-log_every:]) / max(1, len(losses[-log_every:]))
            print(f"[sft] step {step + 1:>4}/{max_steps} loss={recent:.4f}")

    loss_end = accumulated
    duration = time.perf_counter() - started
    return TrainingMetrics(max_steps, loss_start, loss_end, duration, examples)


def _advantage(rewards: List[float]) -> List[float]:
    if not rewards:
        return []
    mean = sum(rewards) / len(rewards)
    variance = sum((r - mean) ** 2 for r in rewards) / len(rewards)
    std = math.sqrt(variance) + 1e-6
    return [(r - mean) / std for r in rewards]


def grpo_step(
    model,
    tokenizer,
    sample_records: List[dict],
    *,
    group_size: int = 4,
    max_new_tokens: int = 96,
    learning_rate: float = 1e-5,
) -> dict:
    """Single GRPO step with deterministic Python-runtime rewards."""
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=learning_rate)
    optimizer.zero_grad(set_to_none=True)
    rewards: List[float] = []
    advantages: List[float] = []
    log_probs: List[torch.Tensor] = []
    for record in sample_records:
        prompt = build_training_prompt(record)
        prompt_ids = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **prompt_ids,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.9,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
            )
        completion = tokenizer.decode(generated[0][prompt_ids["input_ids"].shape[-1]:], skip_special_tokens=True)
        completion = completion.strip().splitlines()[0] if completion.strip() else ROUTER_FALLBACK
        breakdown = compute_reward(record["prompt"], completion, record)
        rewards.append(breakdown.total)
        if breakdown.total <= 0.0:
            advantages.append(0.0)
            continue
        full = torch.cat([prompt_ids["input_ids"], generated[0][prompt_ids["input_ids"].shape[-1]:].unsqueeze(0)], dim=-1)
        outputs = model(full, labels=full)
        log_probs.append(outputs.loss)
        advantages.append(breakdown.total)

    if not log_probs:
        return {"loss": 0.0, "reward_mean": sum(rewards) / max(1, len(rewards)), "samples": len(sample_records)}

    normalized = _advantage(advantages)
    loss = -sum(normalized[i] * log_probs[i] for i in range(len(log_probs))) / max(1, len(log_probs))
    loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
    optimizer.step()
    return {"loss": float(loss.detach()), "reward_mean": sum(rewards) / max(1, len(rewards)), "samples": len(sample_records)}


def grpo_train(
    model,
    tokenizer,
    train_path: str,
    *,
    steps: int = 500,
    group_size: int = 4,
    log_every: int = 25,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    from .dataset import iter_jsonl
    records: List[dict] = []
    for record in iter_jsonl(train_path):
        records.append(record)
        if len(records) >= steps * group_size:
            break

    history = []
    started = time.perf_counter()
    for step in range(steps):
        batch = records[step * group_size:(step + 1) * group_size]
        if not batch:
            break
        metrics = grpo_step(model, tokenizer, batch, group_size=group_size)
        history.append(metrics)
        if (step + 1) % log_every == 0 or step == steps - 1:
            recent = history[-log_every:]
            avg = sum(h["reward_mean"] for h in recent) / max(1, len(recent))
            print(f"[grpo] step {step + 1:>4}/{steps} reward_mean={avg:.4f}")
    return {
        "steps": len(history),
        "duration_s": time.perf_counter() - started,
        "final_reward_mean": (history[-1]["reward_mean"] if history else 0.0),
    }


def save_lora(model, output_dir: str) -> str:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(path)
    return str(path)


def save_metrics(metrics: dict, output_dir: str, name: str = "training_metrics.json") -> str:
    path = Path(output_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, ensure_ascii=False, indent=2)
    return str(path)
