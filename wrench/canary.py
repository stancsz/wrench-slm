"""Shadow canary runner that compares local vs. cloud routes without executing."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from .protocol import ROUTER_FALLBACK, exact_match, iter_jsonl, parse_call, target_call


@dataclass
class CanaryResult:
    samples: int
    divergence_rate: float
    local_executed: int
    fallback: int
    avg_local_latency_ms: float
    avg_cloud_latency_ms: float
    cloud_tokens_saved: int
    cloud_tokens_baseline: int


def _local_latency() -> float:
    return 8.0 + 1.0


def _cloud_latency(prompt: str) -> float:
    base = 1100.0
    return base + max(0, len(prompt) // 8)


def _cloud_tokens(prompt: str) -> int:
    return max(60, len(prompt) // 2 + 80)


def run_canary(policy, path: str, limit: Optional[int] = 1000) -> CanaryResult:
    samples = 0
    divergence = 0
    fallback = 0
    local_latencies: List[float] = []
    cloud_latencies: List[float] = []
    cloud_tokens_saved = 0
    cloud_tokens_baseline = 0
    for record in iter_jsonl(path):
        if limit is not None and samples >= limit:
            break
        samples += 1
        prediction = policy.predict(record["prompt"])
        local_latencies.append(_local_latency())
        cloud_tokens_baseline += _cloud_tokens(record["prompt"])
        if prediction.text == ROUTER_FALLBACK:
            fallback += 1
            cloud_latencies.append(_cloud_latency(record["prompt"]))
            continue
        parsed, _ = parse_call(prediction.text)
        if parsed is None or not exact_match(parsed, target_call(record)):
            divergence += 1
            cloud_latencies.append(_cloud_latency(record["prompt"]))
            continue
        local_latencies[-1] = _local_latency()
        cloud_tokens_saved += _cloud_tokens(record["prompt"])
    return CanaryResult(
        samples=samples,
        divergence_rate=(divergence / max(1, samples)),
        local_executed=samples - fallback,
        fallback=fallback,
        avg_local_latency_ms=(sum(local_latencies) / max(1, len(local_latencies))),
        avg_cloud_latency_ms=(sum(cloud_latencies) / max(1, len(cloud_latencies)) if cloud_latencies else 0.0),
        cloud_tokens_saved=cloud_tokens_saved,
        cloud_tokens_baseline=cloud_tokens_baseline,
    )


def write_canary(result: CanaryResult, path: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(asdict(result), handle, ensure_ascii=False, indent=2)
    return str(target)
