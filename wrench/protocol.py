"""Canonical Wrench tool-call protocol and dataset helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable


REQUIRED_KEYS = {"tool", "args"}
ROUTER_FALLBACK = "ROUTER_FALLBACK"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    error: str = ""


def validate_call(value: Any) -> ValidationResult:
    if not isinstance(value, dict):
        return ValidationResult(False, "call must be an object")
    if set(value) != REQUIRED_KEYS:
        return ValidationResult(False, "call must contain exactly tool and args")
    if not isinstance(value["tool"], str) or not value["tool"].strip():
        return ValidationResult(False, "tool must be a non-empty string")
    if not isinstance(value["args"], dict):
        return ValidationResult(False, "args must be an object")
    return ValidationResult(True)


def parse_call(text: str) -> tuple[dict[str, Any] | None, ValidationResult]:
    if not isinstance(text, str) or not text.strip():
        return None, ValidationResult(False, "response is empty")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, ValidationResult(False, f"invalid JSON: {exc.msg}")
    result = validate_call(value)
    return value if result.valid else None, result


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def target_call(record: dict[str, Any]) -> dict[str, Any]:
    return {"tool": record["tool"], "args": record.get("args", {})}


def exact_match(prediction: dict[str, Any] | None, target: dict[str, Any]) -> bool:
    return prediction is not None and canonical_json(prediction) == canonical_json(target)


def prediction_matches_target(prediction: str, record: dict[str, Any]) -> bool:
    """Strict pilot scoring: all arguments matter; fallback is a distinct action."""
    if record['tool'] == 'fallback':
        return prediction == ROUTER_FALLBACK
    parsed, valid = parse_call(prediction)
    return valid.valid and exact_match(parsed, target_call(record))


def iter_jsonl(path: str) -> Iterable[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
