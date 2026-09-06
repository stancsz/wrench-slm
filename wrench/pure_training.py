"""Pure-Blood training engine for NanoWrench from scratch.

Runs natively on PyTorch with zero external framework dependencies.
Features:
- Full pretraining and continuous incremental training
- Prompt masking (loss only on structured tool call completion)
- Mixed precision (BF16 / FP16 / FP32)
- Gradient accumulation and norm clipping
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch
from torch.utils.data import DataLoader, Dataset

from .model import NanoWrench
from .tokenizer import WrenchTokenizer

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_LOG_FILE = LOG_DIR / "training.log"

class FlushFileHandler(logging.FileHandler):
    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


train_logger = logging.getLogger("wrench.training")
train_logger.setLevel(logging.INFO)
if not train_logger.handlers:
    _file_h = FlushFileHandler(str(TRAIN_LOG_FILE), encoding="utf-8")
    _file_h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    _stream_h = logging.StreamHandler()
    _stream_h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    train_logger.addHandler(_file_h)
    train_logger.addHandler(_stream_h)



@dataclass
class PureTrainMetrics:
    steps: int
    loss_start: float
    loss_end: float
    duration_s: float
    examples_seen: int


class PureJsonlDataset(Dataset):
    def __init__(self, path: str, tokenizer: WrenchTokenizer, max_len: int = 512) -> None:
        self.samples = []
        self.tokenizer = tokenizer
        self.max_len = max_len

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    prompt = data.get("prompt", "")
                    target = data.get("canonical_call")
                    if not target:
                        target = json.dumps({"tool": data.get("tool"), "args": data.get("args", {})}, ensure_ascii=False)
                    self.samples.append((prompt, target))
                except Exception:
                    continue

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        prompt, target = self.samples[idx]
        p_ids = self.tokenizer.encode(f"Prompt: {prompt}\nCall: ", add_special_tokens=False)
        t_ids = self.tokenizer.encode(target, add_special_tokens=False) + [self.tokenizer.eos_token_id]

        input_ids = [self.tokenizer.bos_token_id] + p_ids + t_ids
        # Mask prompt from loss
        labels = [-100] * (1 + len(p_ids)) + t_ids

        if len(input_ids) > self.max_len:
            input_ids = input_ids[: self.max_len]
            labels = labels[: self.max_len]

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def collate_fn(batch: List[dict], pad_id: int = 256) -> dict:
    max_len = max(len(item["input_ids"]) for item in batch)
    bsz = len(batch)

    input_ids = torch.full((bsz, max_len), pad_id, dtype=torch.long)
    labels = torch.full((bsz, max_len), -100, dtype=torch.long)

    for i, item in enumerate(batch):
        seq_len = len(item["input_ids"])
        input_ids[i, :seq_len] = item["input_ids"]
        labels[i, :seq_len] = item["labels"]

    return {"input_ids": input_ids, "labels": labels}


def train_nano_wrench(
    model: NanoWrench,
    tokenizer: WrenchTokenizer,
    train_path: str,
    *,
    batch_size: int = 8,
    grad_accum_steps: int = 4,
    learning_rate: float = 3e-4,
    max_steps: int = 200,
    log_every: int = 5,
    device: Optional[str] = None,
) -> PureTrainMetrics:
    """Train NanoWrench natively on GPU/CPU from scratch."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    model = model.to(device)
    model.train()

    dataset = PureJsonlDataset(train_path, tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_fn(b, pad_id=tokenizer.pad_token_id),
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))

    iterator = iter(loader)
    loss_start = loss_end = 0.0
    examples = 0
    started = time.perf_counter()
    losses: List[float] = []

    for step in range(max_steps):
        optimizer.zero_grad(set_to_none=True)
        accum_loss = 0.0

        for _ in range(grad_accum_steps):
            try:
                batch = next(iterator)
            except StopIteration:
                iterator = iter(loader)
                batch = next(iterator)

            inp = batch["input_ids"].to(device)
            lbl = batch["labels"].to(device)

            with torch.amp.autocast("cuda", enabled=(device == "cuda"), dtype=torch.bfloat16):
                _, loss = model(inp, labels=lbl)
                loss = loss / grad_accum_steps

            scaler.scale(loss).backward()
            accum_loss += float(loss.detach().item() * grad_accum_steps)
            examples += inp.shape[0]

        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()

        losses.append(accum_loss)
        if step == 0:
            loss_start = accum_loss
        if (step + 1) % log_every == 0 or step == max_steps - 1:
            recent = sum(losses[-log_every:]) / max(1, len(losses[-log_every:]))
            train_logger.info(f"[pure-train] step {step + 1:>4}/{max_steps} loss={recent:.4f} examples_seen={examples}")

    loss_end = accum_loss
    duration = time.perf_counter() - started
    return PureTrainMetrics(max_steps, loss_start, loss_end, duration, examples)


def save_pure_model(model: NanoWrench, path: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"config": model.config, "state_dict": model.state_dict()}, str(target))
    return str(target)


def load_pure_model(path: str, device: str = "cpu") -> NanoWrench:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model = NanoWrench(checkpoint["config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device)
    model.eval()
    return model
