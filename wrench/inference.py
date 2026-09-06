"""Local inference wrapper around an HF causal LM with the FSM mask applied."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import torch

from .dataset import build_training_prompt
from .fsm import JsonToolCallFSM
from .policy import Prediction, load_json_prediction
from .protocol import ROUTER_FALLBACK
from .reward import compute_reward
from .tokenizer_fsm import TokenizerGrammar


@dataclass
class InferenceStats:
    samples: int
    total_latency_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    peak_vram_mb: float


class FsmLogitsProcessor:
    """Hugging Face logits processor that masks tokens outside the FSM state."""

    def __init__(self, grammar: TokenizerGrammar) -> None:
        self.grammar = grammar

    def __call__(self, input_ids: torch.Tensor, scores: torch.Tensor) -> torch.Tensor:
        fsm = JsonToolCallFSM()
        decoded_so_far = self._decode(input_ids)
        for char in decoded_so_far:
            fsm.accept(char)
        if fsm.complete or fsm.error:
            return scores
        legal_ids = self.grammar.allowed_token_ids(fsm.state)
        if not legal_ids:
            return scores
        mask = torch.full_like(scores, float("-inf"))
        mask[legal_ids] = 0.0
        return scores + mask

    def _decode(self, input_ids: torch.Tensor) -> str:
        if input_ids.dim() == 2:
            input_ids = input_ids[0]
        return self.grammar.tokenizer.decode(input_ids.tolist(), skip_special_tokens=True)


class LocalExecutor:
    """Wrap a causal LM with FSM-constrained decoding for tool calls."""

    def __init__(self, model, tokenizer, device: str = "cuda") -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.grammar = TokenizerGrammar(tokenizer)
        self.processor = FsmLogitsProcessor(self.grammar)
        self._torch = torch

    def predict(self, prompt: str, max_new_tokens: int = 128, temperature: float = 0.0) -> Prediction:
        prompt_text = build_training_prompt({"prompt": prompt})
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)
        do_sample = temperature > 0.0
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature if do_sample else 1.0,
                logits_processor=[self.processor],
                pad_token_id=self.tokenizer.eos_token_id,
            )
        decoded = self.tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return load_json_prediction(decoded.strip().splitlines()[0] if decoded.strip() else ROUTER_FALLBACK)

    def score(self, record: dict) -> tuple[Prediction, float]:
        prediction = self.predict(record["prompt"])
        reward = compute_reward(record["prompt"], prediction.text, record)
        return prediction, reward.total


def benchmark(executor: LocalExecutor, prompts: List[str], *, max_new_tokens: int = 64) -> InferenceStats:
    latencies: List[float] = []
    torch = executor._torch
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    for prompt in prompts:
        begin = time.perf_counter()
        executor.predict(prompt, max_new_tokens=max_new_tokens)
        latencies.append((time.perf_counter() - begin) * 1000.0)
    total_ms = (time.perf_counter() - started) * 1000.0
    sorted_lat = sorted(latencies)

    def pct(p: float) -> float:
        if not sorted_lat:
            return 0.0
        index = max(0, min(len(sorted_lat) - 1, int(round((p / 100.0) * (len(sorted_lat) - 1)))))
        return sorted_lat[index]

    peak_vram_mb = 0.0
    if torch.cuda.is_available():
        peak_vram_mb = torch.cuda.max_memory_allocated() / (1024.0 ** 2)
    return InferenceStats(
        samples=len(prompts),
        total_latency_ms=total_ms,
        p50_ms=pct(50),
        p95_ms=pct(95),
        p99_ms=pct(99),
        peak_vram_mb=peak_vram_mb,
    )


def ensure_model_path(model_id_or_path: str, cache_dir: Optional[str] = None) -> str:
    """Resolve a HF hub id to a local cache path; pass local paths through."""
    if Path(model_id_or_path).exists():
        return model_id_or_path
    from huggingface_hub import snapshot_download
    return snapshot_download(repo_id=model_id_or_path, cache_dir=cache_dir)
