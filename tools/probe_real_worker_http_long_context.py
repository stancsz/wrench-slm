#!/usr/bin/env python3
"""Probe the model-local HTTP endpoint with a monster payload.

This development probe deliberately uses an ambiguous current intent so the
HTTP server cannot satisfy the request through the deterministic mechanical
shortcut. The real Wrench worker must receive the raw payload, compact it
locally, and perform one actual model generation. The result is diagnostic
and does not claim dense-native attention quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from probe_native_handoff_prefill import _build_payload


_ADMISSION_ESTIMATE_SAFETY_MARGIN = 4_096


def run(args: argparse.Namespace) -> dict[str, object]:
    raw_content = _build_payload(
        max(1, args.payload_tokens - _ADMISSION_ESTIMATE_SAFETY_MARGIN)
    )
    raw_prefix, _, _ = raw_content.rpartition("CURRENT INTENT:")
    current_intent = (
        "CURRENT INTENT: Review the supplied repository context and explain the "
        "most likely architectural risk in one bounded JSON response. This is "
        "not a direct file read, search, patch, health check, or shell action."
    )
    content = raw_prefix + current_intent
    request_body = json.dumps(
        {
            "model": args.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Wrench, a bounded developer-tool proposal worker. "
                        "Return exactly one JSON object and never execute tools. "
                        "If the request is outside the allowed mechanical actions, "
                        "return a structured abstain."
                    ),
                },
                {"role": "user", "content": content},
            ],
            "max_tokens": args.max_new_tokens,
            "temperature": 0,
            "stream": False,
            "options": {"num_ctx": 4_000_000},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        args.endpoint,
        data=request_body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(request_body))},
        method="POST",
    )
    started = time.perf_counter()
    http_status: int | None = None
    response_body: dict[str, object] = {}
    error: str | None = None
    try:
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as response:
            http_status = response.status
            response_body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        http_status = getattr(exc, "code", None)
        error = str(exc)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    wrench = response_body.get("wrench") if isinstance(response_body, dict) else None
    wrench = wrench if isinstance(wrench, dict) else {}
    dynamic_prefill = wrench.get("dynamic_prefill")
    dynamic_prefill = dynamic_prefill if isinstance(dynamic_prefill, dict) else {}
    choices = response_body.get("choices") if isinstance(response_body, dict) else None
    assistant_content = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        message = choices[0].get("message")
        if isinstance(message, dict):
            assistant_content = message.get("content")
    model_calls = wrench.get("model_calls")
    staged_tokens = dynamic_prefill.get("model_prefill_token_count")
    raw_tokens = dynamic_prefill.get("raw_token_count")
    status = (
        "PASS_REAL_WORKER_HTTP_4M_INTAKE_AND_GENERATION"
        if http_status == 200
        and model_calls == 1
        and isinstance(raw_tokens, int)
        and raw_tokens >= int(args.payload_tokens * 0.95)
        and isinstance(staged_tokens, int)
        and staged_tokens <= 64_000
        else "REAL_WORKER_HTTP_4M_GAP"
    )
    receipt: dict[str, object] = {
        "schema": "wrench.real-worker-http-long-context-probe.v1",
        "status": status,
        "endpoint": args.endpoint,
        "model": args.model,
        "payload_target_tokens": args.payload_tokens,
        "admission_estimate_safety_margin_tokens": _ADMISSION_ESTIMATE_SAFETY_MARGIN,
        "request_bytes": len(request_body),
        "raw_payload_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "http_status": http_status,
        "elapsed_ms": elapsed_ms,
        "model_calls": model_calls,
        "raw_token_count": raw_tokens,
        "model_prefill_token_count": staged_tokens,
        "context_gate_latency_ms": dynamic_prefill.get("context_gate_latency_ms"),
        "working_context_budget_tokens": dynamic_prefill.get("working_context_budget_tokens"),
        "backend": wrench.get("backend"),
        "assistant_content": assistant_content,
        "error": error,
        "native_attention_claim": False,
        "quality_claim": False,
        "notes": [
            "The request was sent directly to the package-local OpenAI-compatible endpoint.",
            "This proves model-local raw intake, reduction, and real generation, not dense-native attention quality.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in (
        "status", "http_status", "elapsed_ms", "model_calls",
        "raw_token_count", "model_prefill_token_count", "context_gate_latency_ms",
    )}, ensure_ascii=False))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--payload-tokens", type=int, default=4_000_000)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.payload_tokens < 1:
        raise ValueError("payload-tokens must be positive")
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
