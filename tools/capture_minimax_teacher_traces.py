#!/usr/bin/env python3
"""Capture proposal-only traces from the local MiniMax-compatible teacher.

The tool never executes a teacher proposal. It records raw output, a minimal
normalized proposal suitable for calibration, usage, and transport evidence.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from generate_wrench_calibration import SYSTEM_EXPLICIT


ACTION_KEYS: dict[str, tuple[str, ...]] = {
    "read_file": ("path", "max_bytes"),
    "read_lines": ("path", "start", "end"),
    "literal_search": ("root", "literal", "max_matches"),
    "git_read_status": ("repo_root",),
    "health_read": ("url", "timeout_seconds", "max_bytes"),
    "patch_draft": ("files", "review_only", "diff"),
}


def _normalize(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or parsed.get("schema") != "wrench.proposal.v1":
        return None
    action = parsed.get("action")
    if not isinstance(action, str):
        return None
    if action not in ACTION_KEYS:
        return {"schema": "wrench.proposal.v1", "action": action}
    normalized: dict[str, Any] = {"schema": "wrench.proposal.v1", "action": action}
    for key in ACTION_KEYS[action]:
        if key in parsed:
            normalized[key] = parsed[key]
    return normalized


def _request(endpoint: str, model: str, row: dict[str, Any], timeout: float, max_tokens: int) -> dict[str, Any]:
    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        messages = [
            {"role": "system", "content": row.get("system") or SYSTEM_EXPLICIT},
            {"role": "user", "content": row["prompt"]},
        ]
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"id": row["id"], "transport_failure": True, "error": type(exc).__name__}
    choices = payload.get("choices") if isinstance(payload, dict) else None
    message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return {"id": row["id"], "transport_failure": False, "response_invalid": True, "payload": payload}
    return {
        "id": row["id"],
        "family": row.get("family"),
        "prompt": row.get("prompt"),
        "system": row.get("system") or SYSTEM_EXPLICIT,
        "target": row.get("target"),
        "expected_status": row.get("expected_status"),
        "expected_fallback_reason": row.get("expected_fallback_reason"),
        "raw_model_output": content,
        "normalized_proposal": _normalize(content),
        "response_model": payload.get("model"),
        "finish_reason": choices[0].get("finish_reason") if isinstance(choices[0], dict) else None,
        "usage": payload.get("usage"),
        "provider": payload.get("provider"),
        "transport_failure": False,
        "response_invalid": False,
    }


def capture(args: argparse.Namespace) -> dict[str, Any]:
    rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise ValueError("no cases to capture")
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_request, args.endpoint, args.model, row, args.timeout, args.max_tokens) for row in rows]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: str(item["id"]))
    payload = {
        "schema": "wrench.mechanical-worker-teacher-traces.v1",
        "status": "CAPTURED_TEACHER_PROPOSAL_ONLY",
        "teacher": {
            "endpoint": args.endpoint,
            "model": args.model,
            "label": "MiniMax M3",
            "identity_status": "endpoint_model_id_recorded_owner_label_not_independently_verified",
            "max_tokens": args.max_tokens,
        },
        "input_path": str(args.cases.resolve()),
        "input_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "request_count": len(results),
        "transport_failures": sum(bool(item.get("transport_failure")) for item in results),
        "invalid_responses": sum(bool(item.get("response_invalid")) for item in results),
        "results": results,
        "quality_claim": False,
        "execution_performed": False,
        "scope": "teacher proposal capture for calibration; no model-quality or workflow-value claim",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:4000/v1/chat/completions")
    parser.add_argument("--model", default="minimax")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        raise ValueError("workers must be between 1 and 16")
    if not 128 <= args.max_tokens <= 8192:
        raise ValueError("max_tokens must be between 128 and 8192")
    receipt = capture(args)
    print(json.dumps({"status": receipt["status"], "requests": receipt["request_count"], "transport_failures": receipt["transport_failures"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
