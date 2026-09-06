"""Held-out evaluation harness that produces Gate A / Gate B receipts."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional

from .fsm import fsm_validate
from .protocol import ROUTER_FALLBACK, exact_match, iter_jsonl, parse_call, target_call
from .policy import ProductionDataBaseline


@dataclass
class EvalRecord:
    id: str
    prompt: str
    target_tool: str
    prediction: str
    schema_valid: bool
    arg_exact: bool
    fallback: bool


@dataclass
class EvalSummary:
    total: int
    schema_valid: int
    arg_exact: int
    fallback: int
    schema_valid_rate: float
    arg_exact_rate: float
    fallback_rate: float
    duration_s: float
    failure_samples: List[dict]


def _evaluate_with_policy(policy, records: Iterable[dict], limit: Optional[int]) -> EvalSummary:
    samples: List[EvalRecord] = []
    failures: List[dict] = []
    started = time.perf_counter()
    total = 0
    for record in records:
        if limit is not None and total >= limit:
            break
        total += 1
        prediction = policy.predict(record["prompt"])
        parsed, valid = parse_call(prediction.text)
        schema_valid = bool(valid.valid) and fsm_validate(prediction.text)
        fallback = prediction.text == ROUTER_FALLBACK
        arg_exact = parsed is not None and exact_match(parsed, target_call(record))
        samples.append(EvalRecord(
            id=record.get("id", str(total)),
            prompt=record["prompt"],
            target_tool=record["tool"],
            prediction=prediction.text,
            schema_valid=schema_valid,
            arg_exact=arg_exact,
            fallback=fallback,
        ))
        if not schema_valid and len(failures) < 8:
            failures.append({
                "id": record.get("id"),
                "tool": record["tool"],
                "platform": record.get("platform"),
                "error": valid.error or "fsm rejection",
                "args_preview": str(record.get("args"))[:160],
            })

    schema_total = sum(1 for s in samples if s.schema_valid)
    arg_total = sum(1 for s in samples if s.arg_exact)
    fallback_total = sum(1 for s in samples if s.fallback)
    duration = time.perf_counter() - started
    return EvalSummary(
        total=len(samples),
        schema_valid=schema_total,
        arg_exact=arg_total,
        fallback=fallback_total,
        schema_valid_rate=(schema_total / max(1, len(samples))),
        arg_exact_rate=(arg_total / max(1, len(samples))),
        fallback_rate=(fallback_total / max(1, len(samples))),
        duration_s=duration,
        failure_samples=failures,
    )


def evaluate_baseline(path: str, limit: Optional[int] = None) -> EvalSummary:
    summary = _evaluate_with_policy(ProductionDataBaseline(), iter_jsonl(path), limit)
    return summary


def write_summary(summary: EvalSummary, path: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(summary)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return str(target)
