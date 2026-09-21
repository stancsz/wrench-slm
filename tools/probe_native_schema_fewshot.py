#!/usr/bin/env python3
"""Diagnostic native-upstream probe for schema few-shot behavior.

This intentionally bypasses the Wrench mechanical route and sends a bounded
payload to the package's native OpenAI-compatible endpoint. It is diagnostic
only and does not claim model quality or release readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from probe_native_handoff_prefill import _build_payload


def run(args: argparse.Namespace) -> dict[str, object]:
    raw = _build_payload(max(1, args.payload_tokens - 4096))
    prefix, _, _ = raw.rpartition("CURRENT INTENT:")
    intent = (
        "CURRENT INTENT: Review the supplied repository context and explain the "
        "most likely architectural risk in one bounded JSON response. This is "
        "not a direct file read, search, patch, health check, or shell action."
    )
    content = prefix + intent
    system = (
        "You are Wrench, a narrow developer-tool proposal generator. Output "
        "exactly one valid JSON object and nothing else. Always include schema "
        "wrench.proposal.v1. For requests outside the allowed mechanical actions, "
        "return an abstain object."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Prepare a bounded read of README.md with a 4096 byte ceiling."},
        {"role": "assistant", "content": '{"schema":"wrench.proposal.v1","action":"read_file","path":"README.md","max_bytes":4096}'},
        {"role": "user", "content": content},
    ]
    body = json.dumps(
        {
            "model": args.model,
            "messages": messages,
            "max_tokens": args.max_new_tokens,
            "temperature": 0,
            "stream": False,
            "options": {"num_ctx": args.payload_tokens},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        args.endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    started = time.perf_counter()
    http_status: int | None = None
    response: dict[str, object] = {}
    error: str | None = None
    try:
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as result:
            http_status = result.status
            response = json.loads(result.read().decode("utf-8"))
    except Exception as exc:
        http_status = getattr(exc, "code", None)
        error = str(exc)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    content_out = None
    choices = response.get("choices") if isinstance(response, dict) else None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict):
            content_out = message.get("content")
    parsed = None
    if isinstance(content_out, str):
        try:
            candidate = json.loads(content_out)
            if isinstance(candidate, dict):
                parsed = candidate
        except json.JSONDecodeError:
            pass
    receipt = {
        "schema": "wrench.native-schema-fewshot-probe.v1",
        "status": "PASS_NATIVE_SCHEMA_FEWSHOT_FORMAT" if isinstance(parsed, dict) else "NATIVE_SCHEMA_FEWSHOT_GAP",
        "endpoint": args.endpoint,
        "model": args.model,
        "payload_target_tokens": args.payload_tokens,
        "http_status": http_status,
        "elapsed_ms": elapsed_ms,
        "raw_payload_chars": len(content),
        "raw_payload_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "few_shot": True,
        "model_output": content_out,
        "parsed_output": parsed,
        "error": error,
        "quality_claim": False,
        "notes": [
            "Native upstream only; the Wrench mechanical route is bypassed.",
            "A valid JSON object proves formatting only, not semantic correctness or safety.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "http_status", "elapsed_ms", "parsed_output", "error")}, ensure_ascii=False))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--payload-tokens", type=int, default=65536)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
