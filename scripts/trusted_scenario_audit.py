"""Validate trusted scenario data and calculate provider cost from a price ledger.

The input is an operator-approved, already-redacted JSONL export. This tool
does not read raw production logs, call a provider, or infer production traffic
from authored fixtures. It produces a frozen manifest and an audit receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_CLASSES = {
    "observed_production_replay",
    "synthetic",
    "adversarial",
}
FORBIDDEN_KEYS = {
    "answer",
    "expected_answer",
    "fixture",
    "gold",
    "task_kind",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s,;]{8,}", re.IGNORECASE),
    re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{12,}\b"),
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def validate_row(row: Any, line_number: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(row, dict):
        return [f"line {line_number}: row must be an object"]
    required = {"id", "source_class", "source_ref_sha256", "redaction", "prompt", "context"}
    missing = sorted(required - set(row))
    if missing:
        errors.append(f"line {line_number}: missing required fields: {', '.join(missing)}")
    if not isinstance(row.get("id"), str) or not row.get("id"):
        errors.append(f"line {line_number}: id must be non-empty")
    source_class = row.get("source_class")
    if source_class not in SOURCE_CLASSES:
        errors.append(f"line {line_number}: invalid source_class {source_class!r}")
    source_hash = row.get("source_ref_sha256")
    if not isinstance(source_hash, str) or not SHA256_RE.fullmatch(source_hash):
        errors.append(f"line {line_number}: source_ref_sha256 must be a lowercase SHA-256")
    redaction = row.get("redaction")
    if not isinstance(redaction, dict) or redaction.get("status") != "complete":
        errors.append(f"line {line_number}: redaction.status must be complete")
    if not isinstance(row.get("prompt"), str) or not isinstance(row.get("context"), dict):
        errors.append(f"line {line_number}: prompt must be text and context must be an object")
    if not isinstance(row.get("replay_eligible"), bool):
        errors.append(f"line {line_number}: replay_eligible must be explicitly boolean")
    forbidden = sorted({key for key in _walk_keys(row) if key.lower() in FORBIDDEN_KEYS})
    if forbidden:
        errors.append(f"line {line_number}: private evaluator fields are forbidden: {', '.join(forbidden)}")
    for text in _walk_strings(row):
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            errors.append(f"line {line_number}: possible secret detected after redaction")
            break
    return errors


def validate_ledger(ledger: Any) -> list[str]:
    if not isinstance(ledger, dict):
        return ["price ledger must be an object"]
    required = {
        "version",
        "provider",
        "model",
        "currency",
        "effective_from",
        "source",
        "input_price_per_million",
        "output_price_per_million",
    }
    errors = [f"price ledger missing required fields: {', '.join(sorted(required - set(ledger)))}"] if required - set(ledger) else []
    if ledger.get("currency") != "USD":
        errors.append("price ledger currency must be USD")
    if not isinstance(ledger.get("source"), str) or not ledger.get("source"):
        errors.append("price ledger source must be recorded")
    for field in ("input_price_per_million", "output_price_per_million", "cached_input_price_per_million"):
        if field in ledger and (not isinstance(ledger[field], (int, float)) or ledger[field] < 0):
            errors.append(f"price ledger {field} must be a non-negative number")
    return errors


def calculate_cost(usage: dict[str, Any], ledger: dict[str, Any]) -> float:
    required = ("prompt_tokens", "completion_tokens")
    if any(not isinstance(usage.get(key), int) or usage[key] < 0 for key in required):
        raise ValueError("usage requires non-negative integer prompt_tokens and completion_tokens")
    cached = usage.get("cached_tokens", 0)
    if not isinstance(cached, int) or cached < 0 or cached > usage["prompt_tokens"]:
        raise ValueError("cached_tokens must be between zero and prompt_tokens")
    input_price = ledger["input_price_per_million"]
    if cached and "cached_input_price_per_million" in ledger:
        input_cost = (usage["prompt_tokens"] - cached) * input_price + cached * ledger["cached_input_price_per_million"]
    else:
        input_cost = usage["prompt_tokens"] * input_price
    return (input_cost + usage["completion_tokens"] * ledger["output_price_per_million"]) / 1_000_000


def build_schedule(rows: list[dict[str, Any]], sample_size: int | None, seed: int) -> list[dict[str, Any]]:
    eligible = [row for row in rows if row.get("replay_eligible") is True]
    if sample_size is not None and sample_size > len(eligible):
        raise ValueError(f"sample_size {sample_size} exceeds replay-eligible rows {len(eligible)}")
    rng = random.Random(seed)
    by_class: dict[str, list[dict[str, Any]]] = {}
    for row in eligible:
        by_class.setdefault(row["source_class"], []).append(row)
    for values in by_class.values():
        rng.shuffle(values)
    selected: list[dict[str, Any]] = []
    classes = sorted(by_class)
    while classes and (sample_size is None or len(selected) < sample_size):
        next_classes = []
        for source_class in classes:
            values = by_class[source_class]
            if values and (sample_size is None or len(selected) < sample_size):
                row = values.pop()
                selected.append({
                    "id": row["id"],
                    "source_class": row["source_class"],
                    "source_ref_sha256": row["source_ref_sha256"],
                })
            if values:
                next_classes.append(source_class)
        classes = next_classes
    return selected


def audit(
    input_path: Path,
    ledger_path: Path,
    output: Path,
    allow_no_production: bool = False,
    sample_size: int | None = None,
    seed: int = 20260910,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        errors.extend(validate_row(row, line_number))
        if isinstance(row, dict):
            rows.append(row)
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"price ledger cannot be read: {exc}")
        ledger = {}
    errors.extend(validate_ledger(ledger))
    ids = [row.get("id") for row in rows]
    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    if duplicate_ids:
        errors.append(f"duplicate scenario ids: {', '.join(duplicate_ids)}")
    production_rows = sum(row.get("source_class") == "observed_production_replay" for row in rows)
    if not production_rows and not allow_no_production:
        errors.append("no observed_production_replay rows; production-value claims are not permitted")
    classes = Counter(row.get("source_class") for row in rows)
    schedule: list[dict[str, Any]] = []
    if not errors:
        try:
            schedule = build_schedule(rows, sample_size, seed)
        except ValueError as exc:
            errors.append(str(exc))
    status = "SCHEMA_VALID_NO_PRODUCTION" if not production_rows and not errors else "PASS" if not errors else "REJECTED"
    manifest = {
        "manifest_version": "trusted-scenarios-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_sha256": digest(input_path),
        "price_ledger_sha256": digest(ledger_path) if ledger_path.exists() else None,
        "rows": len(rows),
        "source_class_counts": dict(sorted(classes.items(), key=lambda item: str(item[0]))),
        "production_rows": production_rows,
        "production_claim_allowed": bool(production_rows and not errors),
        "replay_eligible_rows": sum(row.get("replay_eligible") is True for row in rows),
        "replay_schedule_seed": seed,
        "replay_schedule_rows": len(schedule),
        "price_ledger": ledger,
        "errors": errors,
        "scope": "Validated redacted scenario metadata; not a production-performance claim",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    schedule_path = output / "replay-schedule.json"
    schedule_path.write_text(json.dumps(schedule, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest["replay_schedule_sha256"] = digest(schedule_path)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (output / "audit.json").write_text(json.dumps({"errors": errors, "status": manifest["status"]}, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Already-redacted scenario JSONL")
    parser.add_argument("--price-ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, help="Optional deterministic replay sample size")
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument("--allow-no-production", action="store_true", help="Validate schema without making a production claim")
    args = parser.parse_args()
    result = audit(args.input, args.price_ledger, args.output, args.allow_no_production, args.sample_size, args.seed)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] in {"PASS", "SCHEMA_VALID_NO_PRODUCTION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
