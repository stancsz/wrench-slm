"""Convert an authorized trace export into deterministic, content-safe scenarios.

The input is an operator-approved JSONL export. The output contains only the
fields needed by the trusted scenario audit. This script never calls a
provider and never labels a row production unless the input does so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*[^\s,;]+", re.IGNORECASE), "[REDACTED_SECRET]"),
    (re.compile(r"\b(?:sk|rk)-[A-Za-z0-9_-]{12,}\b"), "[REDACTED_KEY]"),
)
FORBIDDEN_KEYS = {"answer", "expected_answer", "fixture", "gold", "task_kind"}


def redact(value: Any, replacements: list[str]) -> Any:
    if isinstance(value, str):
        result = value
        for pattern, replacement in SECRET_PATTERNS:
            result, count = pattern.subn(replacement, result)
            replacements.extend([replacement] * count)
        return result
    if isinstance(value, list):
        return [redact(item, replacements) for item in value]
    if isinstance(value, dict):
        return {str(key): redact(item, replacements) for key, item in value.items()}
    return value


def keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from keys(item)


def convert_row(row: dict[str, Any], source_hash: str, line_number: int) -> dict[str, Any]:
    if any(key.lower() in FORBIDDEN_KEYS for key in keys(row)):
        raise ValueError(f"line {line_number}: evaluator-only field present")
    prompt = row.get("prompt")
    context = row.get("context", {})
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"line {line_number}: prompt must be non-empty text")
    if not isinstance(context, dict):
        raise ValueError(f"line {line_number}: context must be an object")
    source_class = row.get("source_class")
    if source_class not in {"observed_production_replay", "synthetic", "adversarial"}:
        raise ValueError(f"line {line_number}: source_class must be explicitly classified")
    replay_eligible = row.get("replay_eligible")
    if not isinstance(replay_eligible, bool):
        raise ValueError(f"line {line_number}: replay_eligible must be explicitly set to true or false")
    replacements: list[str] = []
    clean_prompt = redact(prompt, replacements)
    clean_context = redact(context, replacements)
    identifier = str(row.get("request_id") or row.get("id") or f"line-{line_number}")
    digest = hashlib.sha256(f"{source_hash}:{identifier}:{line_number}".encode()).hexdigest()[:24]
    return {
        "id": str(row.get("id") or f"trace-{digest}"),
        "source_class": source_class,
        "source_ref_sha256": source_hash,
        "redaction": {"status": "complete", "method": "deterministic-pattern-v1", "replacement_count": len(replacements)},
        "prompt": clean_prompt,
        "context": clean_context,
        "replay_eligible": replay_eligible,
    }


def convert(input_path: Path, output_path: Path) -> dict[str, int]:
    source_bytes = input_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {"input_rows": 0, "output_rows": 0, "rejected_rows": 0}
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output_path.parent, delete=False) as target:
            temporary_path = target.name
            for line_number, raw_line in enumerate(source_bytes.splitlines(), 1):
                    line = raw_line.decode("utf-8", errors="strict")
                    if not line.strip():
                        continue
                    counts["input_rows"] += 1
                    try:
                        row = json.loads(line)
                        converted = convert_row(row, source_hash, line_number)
                    except (json.JSONDecodeError, ValueError, TypeError) as exc:
                        counts["rejected_rows"] += 1
                        raise ValueError(str(exc)) from exc
                    target.write(json.dumps(converted, ensure_ascii=False) + "\n")
                    counts["output_rows"] += 1
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass
    return counts


def validate_authorization(receipt_path: Path, source_hash: str) -> None:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("authorized") is not True:
        raise ValueError("authorization receipt must set authorized=true")
    if receipt.get("source_sha256") != source_hash:
        raise ValueError("authorization receipt source_sha256 does not match input")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--authorization-receipt", required=True, type=Path)
    args = parser.parse_args()
    validate_authorization(args.authorization_receipt, hashlib.sha256(args.input.read_bytes()).hexdigest())
    print(json.dumps(convert(args.input, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
