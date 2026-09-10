"""Streaming JSONL dataset with deterministic prompt formatting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, Iterator

import torch
from torch.utils.data import IterableDataset

from .protocol import ROUTER_FALLBACK, canonical_json, iter_jsonl


SYSTEM_PROMPT = (
    "You are Wrench, a local edge SLM that returns a single JSON tool call "
    "exactly matching {\"tool\": <name>, \"args\": {<object>}}. No prose, no "
    "Markdown fences. If the request cannot be resolved from the available "
    "context and tools, reply ROUTER_FALLBACK."
)


def build_training_prompt(record: dict, tokenizer=None) -> str:
    user = record['prompt']
    if record.get('context') is not None:
        user += '\nAvailable context: ' + json.dumps(record['context'], ensure_ascii=False, sort_keys=True)
    if tokenizer is not None and getattr(tokenizer, 'chat_template', None):
        return tokenizer.apply_chat_template(
            [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': user}],
            tokenize=False, add_generation_prompt=True,
        )
    return f"{SYSTEM_PROMPT}\n\nUser: {user}\nAssistant:"


def format_completion(record: dict) -> str:
    if record['tool'] == 'fallback':
        return ROUTER_FALLBACK
    return canonical_json({"tool": record["tool"], "args": record.get("args", {})})


class JsonlDataset(IterableDataset):
    """Iterable dataset that lazily streams JSONL to keep memory bounded."""

    def __init__(self, path: str | Path, tokenizer, max_length: int = 1024) -> None:
        self.path = Path(path)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __iter__(self) -> Iterator[torch.Tensor]:
        for record in iter_jsonl(self.path):
            prompt = build_training_prompt(record, self.tokenizer)
            completion = format_completion(record)
            prompt_ids = self.tokenizer(prompt, add_special_tokens=False)['input_ids']
            if self.tokenizer.eos_token_id is None:
                raise ValueError('Training requires an EOS token')
            completion_ids = self.tokenizer(completion, add_special_tokens=False)['input_ids'] + [self.tokenizer.eos_token_id]
            token_ids = prompt_ids + completion_ids
            if len(token_ids) > self.max_length:
                raise ValueError(
                    f"Record {record.get('id', '<unknown>')} needs {len(token_ids)} tokens; "
                    f"max_length={self.max_length}. Curate or bucket it; truncation is forbidden."
                )
            labels = [-100] * len(prompt_ids) + completion_ids
            yield {
                "input_ids": torch.tensor(token_ids, dtype=torch.long),
                "labels": torch.tensor(labels, dtype=torch.long),
            }


def collate_sft(batch: list[dict], pad_token_id: int) -> dict:
    """Right-pad completions; masked padding never contributes to loss."""
    width = max(len(item['input_ids']) for item in batch)
    ids = torch.full((len(batch), width), pad_token_id, dtype=torch.long)
    labels = torch.full_like(ids, -100)
    attention = torch.zeros_like(ids)
    for index, item in enumerate(batch):
        length = len(item['input_ids'])
        ids[index, :length] = item['input_ids']
        labels[index, :length] = item['labels']
        attention[index, :length] = 1
    return {'input_ids': ids, 'labels': labels, 'attention_mask': attention}


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
