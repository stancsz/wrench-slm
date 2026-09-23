"""Count explicit source locators in an authorized capture without exporting text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(
    r"C:\Users\stanc\github\lean-router\logs\wrench-capture\wrench-authorized-capture.jsonl"
)
DEFAULT_OUTPUT = Path(
    r"D:\wrench-slm-data\quarantine\phase-447-capture-review-2026-09-23\locator-prevalence-v2.json"
)
DEFAULT_SOURCE_SHA256 = "3c6e1e549a57d8b02ff20f5dcc27d061766050fa862d542808d9b381387420fe"
DATA_ROOT = Path(r"D:\wrench-slm-data").resolve()

PATTERNS = {
    "line_mentions": re.compile(r"\blines?\s+#?\d+(?:\s*[-:]\s*\d+)?\b", re.IGNORECASE),
    "path_colon_line": re.compile(
        r"(?:^|[\s(\"'`])(?:[\w./\\-]+\.(?:py|ts|tsx|js|jsx|go|rs|java|md|json|yaml|yml|toml|sh|ps1|c|cpp|h|cs)):\d+\b",
        re.IGNORECASE,
    ),
    "line_anchors": re.compile(r"#L\d+(?:-L\d+)?\b", re.IGNORECASE),
}


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)


def _within_data_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(DATA_ROOT)
    except ValueError:
        return False
    return True


def audit(source: Path, output: Path, expected_sha256: str) -> dict[str, Any]:
    source = source.resolve(strict=True)
    output = output.resolve(strict=False)
    if not source.is_file():
        raise ValueError("source_not_file")
    if not _within_data_root(output):
        raise ValueError("output_must_be_under_D_wrench_slm_data")
    if output.exists():
        raise ValueError("output_already_exists")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected_sha256_invalid")

    digest = hashlib.sha256()
    prompt_counts = {name: 0 for name in PATTERNS}
    context_counts = {name: 0 for name in PATTERNS}
    prompt_locator_records = 0
    context_locator_records = 0
    both_locator_records = 0
    records = 0
    parse_failures = 0
    with source.open("rb") as stream:
        for raw_line in stream:
            digest.update(raw_line)
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                parse_failures += 1
                continue
            if not isinstance(row, dict):
                parse_failures += 1
                continue
            records += 1
            prompt_text = "\n".join(_strings(row.get("prompt")))
            context_text = "\n".join(_strings(row.get("context")))
            prompt_matches = False
            context_matches = False
            for name, pattern in PATTERNS.items():
                if pattern.search(prompt_text):
                    prompt_counts[name] += 1
                    prompt_matches = True
                if pattern.search(context_text):
                    context_counts[name] += 1
                    context_matches = True
            if prompt_matches:
                prompt_locator_records += 1
            if context_matches:
                context_locator_records += 1
            if prompt_matches and context_matches:
                both_locator_records += 1

    actual_sha256 = digest.hexdigest()
    if actual_sha256.casefold() != expected_sha256.casefold():
        raise ValueError("source_sha256_mismatch")
    report = {
        "schema": "wrench.capture-locator-prevalence.v2",
        "source_path": str(source),
        "source_sha256": actual_sha256,
        "source_sha256_expected": expected_sha256.casefold(),
        "records": records,
        "parse_failures": parse_failures,
        "prompt_field_record_counts_by_pattern": prompt_counts,
        "context_field_record_counts_by_pattern": context_counts,
        "prompt_field_records_with_any_locator_pattern": prompt_locator_records,
        "context_field_records_with_any_locator_pattern": context_locator_records,
        "records_with_locator_patterns_in_both_fields": both_locator_records,
        "text_values_emitted": False,
        "text_values_persisted": False,
        "interpretation": (
            "Separate prompt/context field pattern prevalence only. A prompt "
            "field may contain serialized history rather than only the latest "
            "user request. Matches are not proof of an eligible, current, or "
            "verifier-supported read_lines task."
        ),
        "audit_tool_path": str(Path(__file__).resolve()),
        "audit_tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-sha256", default=DEFAULT_SOURCE_SHA256)
    args = parser.parse_args()
    try:
        report = audit(args.source, args.output, args.expected_sha256)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
