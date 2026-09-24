#!/usr/bin/env python3
"""Capture proposal-only traces from the local MiniMax-compatible teacher.

The tool never executes a teacher proposal. It records raw output, a minimal
normalized proposal suitable for calibration, usage, and transport evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from generate_wrench_calibration import SYSTEM_EXPLICIT
except ModuleNotFoundError:
    from tools.generate_wrench_calibration import SYSTEM_EXPLICIT

from tools.provider_budget_guard import admit, debit_attempt
from tools.provider_budget_guard import conservative_input_size


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
    """Extract only the schema-bearing object, discarding any reasoning text."""
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
    request_reserve_usd: str,
    maximum_input_tokens: int,
    maximum_input_rate: str,
    maximum_output_rate: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    messages = row.get("messages")
    if not isinstance(messages, list) or not messages:
        messages = [
            {"role": "system", "content": row.get("system") or SYSTEM_EXPLICIT},
            {"role": "user", "content": row["prompt"]},
        ]
    if conservative_input_size(messages) > maximum_input_tokens:
        raise ValueError("synthetic case exceeds child receipt maximum input token ceiling")
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
            "chat_template_kwargs": {"enable_thinking": False},
            "provider": {
                "only": ["minimax"],
                "allow_fallbacks": False,
                "enforce_distillable_text": True,
                "data_collection": "deny",
                "max_price": {
                    "prompt": float(Decimal(maximum_input_rate)),
                    "completion": float(Decimal(maximum_output_rate)),
                },
            },
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
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "normalized_proposal": None,
            "response_model": None,
            "provider_usage_and_cost": {"usage": None, "accounted_cost_usd": request_reserve_usd},
            "response_content_sha256": None,
        }
    if not isinstance(content, str):
        return {
            "normalized_proposal": None,
            "response_model": response_model,
            "provider_usage_and_cost": {
                "usage": usage,
                "accounted_cost_usd": debit_attempt(request_reserve_usd, usage.get("cost") if isinstance(usage, dict) else None),
            },
            "response_content_sha256": None,
        }
    actual_cost = usage.get("cost") if isinstance(usage, dict) else None
    normalized = _normalize(content)
    if response_model != model:
        normalized = None
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        if ((isinstance(prompt_tokens, int) and prompt_tokens > maximum_input_tokens)
                or (isinstance(completion_tokens, int) and completion_tokens > max_tokens)):
            normalized = None
    return {
        "normalized_proposal": normalized,
        "response_model": response_model,
        "provider_usage_and_cost": {"usage": usage, "accounted_cost_usd": debit_attempt(request_reserve_usd, actual_cost)},
        "response_content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def capture(args: argparse.Namespace) -> dict[str, Any]:
    admission = admit(
        args.approval, args.child_receipt, args.cases,
        endpoint=args.endpoint, model=args.model, max_tokens=args.max_tokens,
        workers=args.workers, prior_spend_usd=args.prior_spend_usd,
        prior_charge_status=args.prior_charge_status,
        reconciliation_reference=args.reconciliation_reference,
        remaining_cap_usd=args.remaining_cap_usd,
        output_path=args.output,
    )
    rows = [json.loads(line) for line in args.cases.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError("the approved pilot is exactly one canonical synthetic case")
    if rows[0].get("synthetic") is not True:
        raise ValueError("case must be explicitly marked synthetic before dispatch")
    auth_env = args.auth_env
    if not isinstance(auth_env, str) or not auth_env.strip():
        raise ValueError("--auth-env must name an environment variable")
    api_key = os.environ.get(auth_env, "")
    if not api_key:
        raise ValueError(f"configured auth environment variable is empty: {auth_env}")
    messages = rows[0].get("messages")
    if not isinstance(messages, list) or not messages:
        messages = [
            {"role": "system", "content": rows[0].get("system") or SYSTEM_EXPLICIT},
            {"role": "user", "content": rows[0]["prompt"]},
        ]
    if conservative_input_size(messages) > admission["maximum_input_tokens"]:
        raise ValueError("synthetic case exceeds child receipt maximum input token ceiling")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    claim_path = args.output.with_name(args.output.name + ".claim")
    try:
        claim_fd = os.open(claim_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("this child receipt/output path has already been claimed; retries are prohibited") from exc
    with os.fdopen(claim_fd, "w", encoding="utf-8") as claim:
        claim.write(json.dumps({"approval_sha256": admission["approval_sha256"], "cases_sha256": admission["cases_canonical_sha256"]}))
        claim.flush()
        os.fsync(claim.fileno())
    results = [_request(args.endpoint, args.model, rows[0], args.timeout, args.max_tokens,
                        admission["maximum_request_reserve_usd"], admission["maximum_input_tokens"],
                        admission["maximum_input_rate_usd_per_million_tokens"],
                        admission["maximum_output_rate_usd_per_million_tokens"], api_key or None)]
    payload = results[0]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--child-receipt", type=Path, required=True)
    parser.add_argument("--endpoint", default="https://openrouter.ai/api/v1/chat/completions")
    parser.add_argument("--model", default="minimax/minimax-m3")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--prior-spend-usd", required=True)
    parser.add_argument("--prior-charge-status", required=True)
    parser.add_argument("--reconciliation-reference", required=True)
    parser.add_argument("--remaining-cap-usd", required=True)
    parser.add_argument(
        "--auth-env",
        default="OPENROUTER_API_KEY",
        help="environment variable containing a bearer token; the token is never written to the receipt",
    )
    args = parser.parse_args()
    if args.workers != 1:
        raise ValueError("workers is fixed at 1")
    if args.max_tokens != 128:
        raise ValueError("max_tokens is fixed at 128")
    receipt = capture(args)
    print(json.dumps({"status": "CAPTURED", "requests": 1}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
