#!/usr/bin/env python3
"""Audit local JSONL training inputs without copying them into Git."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(item) for item in value)
    return ""


def audit_file(path: Path) -> dict[str, Any]:
    top_keys: Counter[str] = Counter()
    keyword_hits: Counter[str] = Counter()
    parse_errors = 0
    line_count = 0
    max_line_bytes = 0
    keyword_groups = {
        "tool_execution": ("tool_call", "functioncall", "function_call", "tool response", "terminal"),
        "repository_work": ("pytest", "git status", "grep", "view_file", "repository", "patch"),
        "web_or_research": ("web search", "visit", "news headlines", "wikipedia"),
        "finance_or_crypto": ("bitcoin", "btc/usdt", "trading", "candlesticks", "resistance"),
    }
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line_count += 1
            max_line_bytes = max(max_line_bytes, len(raw.encode("utf-8")))
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if not isinstance(row, dict):
                parse_errors += 1
                continue
            top_keys.update(row.keys())
            text = flatten_text(row).lower()
            for group, terms in keyword_groups.items():
                if any(term in text for term in terms):
                    keyword_hits[group] += 1
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "lines": line_count,
        "parse_errors": parse_errors,
        "max_line_bytes": max_line_bytes,
        "top_level_key_counts": dict(sorted(top_keys.items())),
        "keyword_group_hits": dict(sorted(keyword_hits.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.dataset_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"no JSONL files found under {args.dataset_dir}")
    result = {
        "schema": "wrench.dataset-audit.v1",
        "dataset_dir": str(args.dataset_dir.resolve()),
        "files": [audit_file(path) for path in files],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "files": len(files), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
