"""Profile production usage fields without exporting request content or calling a provider."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


TOKEN_FIELDS = {
    "prompt_tokens": ("prompt_tokens", "input_tokens_estimate"),
    "completion_tokens": ("completion_tokens", "output_tokens_estimate"),
}


def read_events(source: Path) -> Iterable[dict[str, Any]]:
    paths = [source] if source.is_file() else sorted(source.rglob("*.jsonl"))
    for path in paths:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(value, dict):
                        yield value
        except OSError:
            continue


def first_number(event: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        value = event.get(name)
        if isinstance(value, int) and value >= 0:
            return value
    return None


def profile(events: Iterable[dict[str, Any]], price_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    total = 0
    complete_usage = 0
    cached_complete = 0
    prompt_total = 0
    completion_total = 0
    cached_total = 0
    durations: list[float] = []
    models: Counter[str] = Counter()
    routes: Counter[str] = Counter()
    usage_sources: Counter[str] = Counter()
    daily: defaultdict[str, dict[str, int]] = defaultdict(lambda: {"events": 0, "complete_usage": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0})
    estimated_cost = 0.0
    cost_rows = 0
    for event in events:
        total += 1
        model = str(event.get("served_model") or event.get("model") or "unknown")
        route = str(event.get("route") or event.get("tier") or "unknown")
        models[model] += 1
        routes[route] += 1
        if event.get("usage_source") is not None:
            usage_sources[str(event["usage_source"])] += 1
        prompt = first_number(event, TOKEN_FIELDS["prompt_tokens"])
        completion = first_number(event, TOKEN_FIELDS["completion_tokens"])
        cached = event.get("cached_tokens")
        if isinstance(cached, int) and cached >= 0:
            cached_complete += 1
            cached_total += cached
        duration = event.get("duration") or event.get("latency_s")
        if isinstance(duration, (int, float)) and duration >= 0:
            durations.append(float(duration))
        day = str(event.get("ts") or event.get("iso") or "unknown")[:10]
        daily[day]["events"] += 1
        if prompt is None or completion is None:
            continue
        complete_usage += 1
        prompt_total += prompt
        completion_total += completion
        daily[day]["complete_usage"] += 1
        daily[day]["prompt_tokens"] += prompt
        daily[day]["completion_tokens"] += completion
        daily[day]["cached_tokens"] += cached if isinstance(cached, int) and cached >= 0 else 0
        if price_ledger and model == price_ledger.get("model"):
            cached_for_cost = cached if isinstance(cached, int) and 0 <= cached <= prompt else 0
            input_price = price_ledger["input_price_per_million"]
            if cached_for_cost and "cached_input_price_per_million" in price_ledger:
                input_cost = ((prompt - cached_for_cost) * input_price + cached_for_cost * price_ledger["cached_input_price_per_million"])
            else:
                input_cost = prompt * input_price
            estimated_cost += (input_cost + completion * price_ledger["output_price_per_million"]) / 1_000_000
            cost_rows += 1
    coverage = lambda value: value / total if total else 0.0
    duration_outliers = sum(value > 3600 for value in durations)
    duration_unit_status = (
        "UNVERIFIED"
        if not durations
        else "MIXED_OR_OUTLIER"
        if duration_outliers
        else "UNVERIFIED_SECONDS"
    )
    result = {
        "schema": "production-usage-profile-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "events": total,
        "complete_usage_events": complete_usage,
        "usage_coverage": coverage(complete_usage),
        "cached_token_field_events": cached_complete,
        "cached_token_field_coverage": coverage(cached_complete),
        "prompt_tokens_total": prompt_total,
        "completion_tokens_total": completion_total,
        "cached_tokens_total": cached_total,
        "models": dict(models),
        "routes": dict(routes),
        "usage_sources": dict(usage_sources),
        "duration_count": len(durations),
        "duration_mean": statistics.fmean(durations) if durations and not duration_outliers else None,
        "duration_p50": statistics.median(durations) if durations else None,
        "duration_p95": statistics.quantiles(durations, n=20, method="inclusive")[18] if len(durations) >= 2 else (durations[0] if durations else None),
        "duration_max": max(durations) if durations else None,
        "duration_outlier_count_over_3600": duration_outliers,
        "duration_unit_status": duration_unit_status,
        "daily": dict(sorted(daily.items())),
        "cost_status": "CALCULATED" if price_ledger and cost_rows else "PRICE_LEDGER_REQUIRED",
        "cost_rows": cost_rows,
        "estimated_cost_usd": estimated_cost if cost_rows else None,
        "scope": "Metadata-only usage profile; no request content and no production-value claim",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--price-ledger", type=Path)
    args = parser.parse_args()
    ledger = None
    if args.price_ledger:
        ledger = json.loads(args.price_ledger.read_text(encoding="utf-8"))
    result = profile(read_events(args.source), ledger)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("events", "complete_usage_events", "usage_coverage", "cost_status", "estimated_cost_usd")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
