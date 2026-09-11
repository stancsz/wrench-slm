"""Perform a read-only inventory of candidate production log sources.

This command records metadata only. It never copies log content, derives
replay rows, or authorizes production-value claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMPLETED_TOOL_RE = re.compile(r"Completed:\s+(?P<tool>[^\s(]+)\s+\(")


def file_digest(path: Path) -> tuple[str | None, str | None]:
    try:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest(), None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def inspect_file(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": path.name,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": None,
        "hash_error": None,
        "lines": 0,
        "nonempty_lines": 0,
        "completed_tool_records": 0,
        "event_json_records": 0,
        "invalid_json_records": 0,
        "tool_distribution": {},
        "event_field_counts": {},
    }
    result["sha256"], result["hash_error"] = file_digest(path)
    tools: Counter[str] = Counter()
    event_fields: Counter[str] = Counter()
    is_tool_log = path.name.startswith("tool_calls.log")
    is_event_log = path.suffix == ".jsonl" and path.parent.name == "events"
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                result["lines"] = line_number
                if not line.strip():
                    continue
                result["nonempty_lines"] += 1
                if is_tool_log:
                    match = COMPLETED_TOOL_RE.search(line)
                    if match:
                        result["completed_tool_records"] += 1
                        tools[match.group("tool")] += 1
                elif is_event_log:
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError:
                        result["invalid_json_records"] += 1
                    else:
                        if isinstance(value, dict):
                            result["event_json_records"] += 1
                            event_fields.update(str(key) for key in value)
                        else:
                            result["invalid_json_records"] += 1
    except OSError as exc:
        result["read_error"] = f"{type(exc).__name__}: {exc}"
    result["tool_distribution"] = dict(tools)
    result["event_field_counts"] = dict(event_fields)
    return result


def inspect_sqlite(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "sha256": None, "tables": [], "read_error": None}
    result["sha256"], hash_error = file_digest(path)
    if hash_error:
        result["read_error"] = hash_error
        return result
    connection = None
    try:
        connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
        for (table,) in connection.execute("select name from sqlite_master where type='table' order by name"):
            columns = [row[1] for row in connection.execute(f'pragma table_info("{table.replace(chr(34), chr(34) * 2)}")')]
            count = connection.execute(f'select count(*) from "{table.replace(chr(34), chr(34) * 2)}"').fetchone()[0]
            result["tables"].append({"name": table, "columns": columns, "rows": count})
    except (sqlite3.Error, OSError) as exc:
        result["read_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if connection is not None:
            connection.close()
    return result


def discover(source: Path, output: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise ValueError(f"source directory does not exist: {source}")
    files = sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and (path.name.startswith("tool_calls.log") or (path.suffix == ".jsonl" and path.parent.name == "events"))
    )
    records = [inspect_file(path) for path in files]
    sqlite_files = sorted(path for path in source.rglob("*.sqlite3") if path.is_file())
    sqlite_records = [inspect_sqlite(path) for path in sqlite_files]
    tool_counts: Counter[str] = Counter()
    event_fields: Counter[str] = Counter()
    completed = 0
    event_records = 0
    for record in records:
        completed += record["completed_tool_records"]
        event_records += record["event_json_records"]
        tool_counts.update(record["tool_distribution"])
        event_fields.update(record["event_field_counts"])
    locked = [record for record in records if record.get("hash_error") or record.get("read_error")]
    replay_capabilities = {
        "has_prompt_field": event_fields.get("prompt", 0) > 0,
        "has_context_field": event_fields.get("context", 0) > 0,
        "has_tool_field": event_fields.get("tool", 0) > 0,
        "has_request_id": event_fields.get("req_id", 0) > 0,
        "has_prompt_tokens": event_fields.get("prompt_tokens", 0) > 0,
        "has_completion_tokens": event_fields.get("completion_tokens", 0) > 0,
        "has_prompt_token_estimate": event_fields.get("input_tokens_estimate", 0) > 0,
        "has_completion_token_estimate": event_fields.get("output_tokens_estimate", 0) > 0,
        "has_cached_tokens": event_fields.get("cached_tokens", 0) > 0,
        "has_duration": event_fields.get("duration", 0) > 0,
    }
    replay_ready = replay_capabilities["has_prompt_field"] and replay_capabilities["has_tool_field"] and not locked
    receipt = {
        "schema": "production-source-discovery-v1",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source.resolve()),
        "read_only": True,
        "raw_content_written": False,
        "production_authorization_required": True,
        "status": "SOURCE_DISCOVERED_WITH_READ_ERRORS" if locked else "SOURCE_DISCOVERED",
        "replay_ready": replay_ready,
        "replay_capabilities": replay_capabilities,
        "files_scanned": len(records),
        "completed_tool_records": completed,
        "event_json_records": event_records,
        "tool_distribution": dict(tool_counts),
        "event_field_counts": dict(event_fields),
        "cost_field_coverage": {
            key: event_fields.get(key, 0)
            for key in ("prompt_tokens", "completion_tokens", "input_tokens_estimate", "output_tokens_estimate", "cached_tokens", "served_model", "duration", "usage_source", "route", "request_bytes")
        },
        "files_with_read_errors": len(locked),
        "files": records,
        "sqlite_files": sqlite_records,
        "next_step": "operator-approved redaction into trusted scenario JSONL; do not replay raw logs",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "source-discovery.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = discover(args.source, args.output)
    print(json.dumps({key: receipt[key] for key in ("status", "files_scanned", "completed_tool_records", "event_json_records", "files_with_read_errors")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
