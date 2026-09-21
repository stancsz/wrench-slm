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
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    from generate_wrench_calibration import SYSTEM_EXPLICIT
except ModuleNotFoundError:
    from tools.generate_wrench_calibration import SYSTEM_EXPLICIT


ACTION_KEYS: dict[str, tuple[str, ...]] = {
    "read_file": ("path", "max_bytes"),
    "read_lines": ("path", "start", "end"),
    "literal_search": ("root", "literal", "max_matches"),
    "git_read_status": ("repo_root",),
    "health_read": ("url", "timeout_seconds", "max_bytes"),
    "patch_draft": ("files", "review_only", "diff"),
}


def _parse_streaming_response(response: Any) -> tuple[str, str | None, str | None, dict[str, Any] | None]:
    """Aggregate an OpenAI chat-completions SSE response into one message."""

    content_parts: list[str] = []
    response_model: str | None = None
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    for raw_line in response:
        line = raw_line.decode("utf-8", "replace") if isinstance(raw_line, bytes) else str(raw_line)
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        chunk = json.loads(data)
        if not isinstance(chunk, dict):
            continue
        if isinstance(chunk.get("model"), str):
            response_model = chunk["model"]
        if isinstance(chunk.get("usage"), dict):
            usage = chunk["usage"]
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            continue
        choice = choices[0]
        if isinstance(choice.get("finish_reason"), str):
            finish_reason = choice["finish_reason"]
        delta = choice.get("delta")
        if isinstance(delta, dict) and isinstance(delta.get("content"), str):
            content_parts.append(delta["content"])
    return "".join(content_parts), response_model, finish_reason, usage


def _parse_json_object(content: str) -> dict[str, Any] | None:
    """Extract the first schema-bearing JSON object from a model response.

    MiniMax may return private reasoning in a ``<think>`` block before the
    final JSON object even when thinking is disabled in the request. Keep the
    raw response for provenance, but normalize only the structured object.
    This parser deliberately accepts no prose as a proposal and requires the
    Wrench schema discriminator below.
    """
    cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            parsed, _ = decoder.raw_decode(cleaned[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("schema") == "wrench.proposal.v1":
            return parsed
    return None


def _normalize(content: str) -> dict[str, Any] | None:
    parsed = _parse_json_object(content)
    if parsed is None:
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


def _request(
    endpoint: str,
    model: str,
    row: dict[str, Any],
    timeout: float,
    max_tokens: int,
    api_key: str | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()

    def with_latency(result: dict[str, Any]) -> dict[str, Any]:
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
        return result

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
            "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content, response_model, finish_reason, usage = _parse_streaming_response(response)
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return with_latency({"id": row["id"], "transport_failure": True, "error": type(exc).__name__})
    if not isinstance(content, str):
        return with_latency({"id": row["id"], "transport_failure": False, "response_invalid": True})
    return with_latency({
        "id": row["id"],
        "family": row.get("family"),
        "prompt": row.get("prompt"),
        "system": row.get("system") or SYSTEM_EXPLICIT,
        "target": row.get("target"),
        "expected_status": row.get("expected_status"),
        "expected_fallback_reason": row.get("expected_fallback_reason"),
        "raw_model_output": content,
        "normalized_proposal": _normalize(content),
        "response_model": response_model,
        "finish_reason": finish_reason,
        "usage": usage,
        "provider": None,
        "transport_failure": False,
        "response_invalid": False,
    })


def capture(args: argparse.Namespace) -> dict[str, Any]:
    rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise ValueError("no cases to capture")
    api_key = os.environ.get(args.auth_env, "") if args.auth_env else ""
    if args.auth_env and not api_key:
        raise ValueError(f"configured auth environment variable is empty: {args.auth_env}")
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(_request, args.endpoint, args.model, row, args.timeout, args.max_tokens, api_key or None)
            for row in rows
        ]
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
            "auth_env": args.auth_env,
            "auth_configured": bool(api_key),
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
    parser.add_argument(
        "--auth-env",
        default=None,
        help="environment variable containing a bearer token; the token is never written to the receipt",
    )
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
