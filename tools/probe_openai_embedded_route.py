#!/usr/bin/env python3
"""Send a raw monster payload to an already-running OpenAI-compatible endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path


UNIT = "old reference status observed record=000000; inert lookup only.\n"
PAYLOAD_ESTIMATE_SAFETY_MARGIN = 300


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--target-tokens", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    unit_tokens = max(1, UNIT.count(" ") + UNIT.count("\n"))
    # The server also counts the live-intent suffix and samples very large
    # payloads. Leave a small deterministic margin so a nominal 4M probe does
    # not accidentally cross the hard input limit by a few hundred estimated
    # tokens while building the fixture.
    generation_target_tokens = max(
        1,
        args.target_tokens - PAYLOAD_ESTIMATE_SAFETY_MARGIN
        if args.target_tokens >= 1_000_000
        else args.target_tokens,
    )
    repetitions = max(1, (generation_target_tokens + unit_tokens - 1) // unit_tokens)
    content = UNIT * repetitions + (
        "\nCURRENT INTENT: Read src/wrench_harness/worker.py with a 65536 byte limit."
    )
    payload = json.dumps(
        {
            "model": args.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 1,
            "temperature": 0,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        args.endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            http_status = response.status
            body = json.loads(response.read().decode("utf-8"))
        error = None
    except Exception as exc:
        http_status = getattr(exc, "code", None)
        body = {}
        error = str(exc)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    choices = body.get("choices", []) if isinstance(body, dict) else []
    message = choices[0].get("message", {}) if choices and isinstance(choices[0], dict) else {}
    content_out = message.get("content", "") if isinstance(message, dict) else ""
    wrench = body.get("wrench", {}) if isinstance(body, dict) else {}
    usage = body.get("usage", {}) if isinstance(body, dict) else {}
    status = (
        "PASS_OPENAI_EMBEDDED_ROUTE_4M"
        if http_status == 200
        and isinstance(content_out, str)
        and '"action":"read_file"' in content_out
        and isinstance(wrench, dict)
        and wrench.get("model_calls") == 0
        else "FAIL_OPENAI_EMBEDDED_ROUTE_4M"
    )
    receipt = {
        "schema": "wrench.openai-embedded-route-4m-probe.v1",
        "status": status,
        "endpoint": args.endpoint,
        "model": args.model,
        "requested_tokens": args.target_tokens,
        "generation_target_tokens": generation_target_tokens,
        "payload_estimate_safety_margin_tokens": (
            PAYLOAD_ESTIMATE_SAFETY_MARGIN if args.target_tokens >= 1_000_000 else 0
        ),
        "raw_payload_chars": len(content),
        "request_bytes": len(payload),
        "payload_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "http_status": http_status,
        "elapsed_ms": elapsed_ms,
        "usage": usage,
        "wrench": wrench,
        "assistant_content": content_out,
        "error": error,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "http_status": http_status, "elapsed_ms": elapsed_ms}))
    return 0 if status == "PASS_OPENAI_EMBEDDED_ROUTE_4M" else 1


if __name__ == "__main__":
    raise SystemExit(main())
