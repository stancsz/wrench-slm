"""Streaming JSONL dataset with deterministic prompt formatting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, Iterator

import torch
from torch.utils.data import IterableDataset

from .protocol import canonical_json, iter_jsonl


SYSTEM_PROMPT = (
    "You are Wrench, a local edge SLM that returns a single JSON tool call "
    "exactly matching {\"tool\": <name>, \"args\": {<object>}}. No prose, no "
    "Markdown fences. Reply only with the JSON object."
)


def build_training_prompt(record: dict) -> str:
    return f"{SYSTEM_PROMPT}\n\nUser: {record['prompt']}\nAssistant:"


def format_completion(record: dict) -> str:
    return canonical_json({"tool": record["tool"], "args": record.get("args", {})})


class JsonlDataset(IterableDataset):
    """Iterable dataset that lazily streams JSONL to keep memory bounded."""

    def __init__(self, path: str | Path, tokenizer, max_length: int = 1024) -> None:
        self.path = Path(path)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __iter__(self) -> Iterator[torch.Tensor]:
        for record in iter_jsonl(self.path):
            prompt = build_training_prompt(record)
            completion = format_completion(record)
            full_text = f"{prompt} {completion}{self.tokenizer.eos_token}"
            token_ids = self.tokenizer(full_text, truncation=True, max_length=self.max_length)["input_ids"]
            prompt_ids = self.tokenizer(prompt, truncation=True, max_length=self.max_length)["input_ids"]
            labels = list(token_ids)
            for index in range(min(len(prompt_ids), len(labels))):
                labels[index] = -100
            yield {
                "input_ids": torch.tensor(token_ids, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long),
            }


def split_iter(paths: Iterable[str], transform: Callable[[dict], dict] | None = None) -> Iterator[dict]:
    for path in paths:
        for record in iter_jsonl(path):
            yield transform(record) if transform else record


def write_jsonl(records: Iterable[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
