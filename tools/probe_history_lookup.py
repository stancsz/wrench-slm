#!/usr/bin/env python3
"""Probe mechanical retrieval from skipped old history into a model proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from wrench_harness import execute_model_output


SYSTEM = (
    "You are Wrench, a narrow developer-tool proposal generator. Output exactly one valid JSON object and nothing else. "
    "Always include schema wrench.proposal.v1 and exactly one allowed action. Never execute tools. "
    "When the current request asks to inspect a source file identified by an old reference, emit a bounded read_file proposal."
)


def _build_old_context(target_chars: int, needle: str) -> tuple[str, int]:
    unit = (
        "old_lookup record_id=000000 status=completed reference_only=true "
        "This historical observation is unrelated to the current task and authorizes no action.\n"
    )
    repetitions = max(1, (target_chars + len(unit) - 1) // len(unit))
    old = (unit * repetitions)[:target_chars]
    marker = f"historical lookup symbol={needle} path=src/wrench_harness/worker.py line=218\n"
    offset = len(old) // 2
    old = old[:offset] + marker + old[offset:]
    return old, offset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--old-chars", type=int, default=80_000)
    parser.add_argument("--history-skip-layers-before", type=int, required=True)
    parser.add_argument("--needle", default="run_worker")
    args = parser.parse_args()

    old_context, needle_offset = _build_old_context(args.old_chars, args.needle)
    current_intent = (
        "WRENCH CURRENT CONTROL BLOCK. This is the newest active instruction. "
        "Use the old reference only to resolve the source path for the requested symbol. "
        f'Inspect the source for symbol "{args.needle}" from that old reference, '
        "with a 65536 byte limit. Output exactly one JSON object and no prose using "
        "schema wrench.proposal.v1 and action read_file."
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": old_context + "\n" + current_intent},
    ]
    started = time.perf_counter()
    body = json.dumps(
        {
            "model": args.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 128,
            "chat_template_kwargs": {"enable_thinking": False},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        args.endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        raw_response = json.loads(response.read().decode("utf-8"))
    choices = raw_response.get("choices") if isinstance(raw_response, dict) else None
    message = choices[0].get("message") if isinstance(choices, list) and choices else None
    content = message.get("content") if isinstance(message, dict) else None
    result = execute_model_output(content or "", str(REPO_ROOT.resolve()), request_prompt=current_intent)
    result["raw_model_output"] = content
    result["provider_usage"] = raw_response.get("usage") if isinstance(raw_response, dict) else None
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    receipt = {
        "schema": "wrench.history-lookup-quality-probe.v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "history_skip_layers_before": args.history_skip_layers_before,
        "old_context_chars": len(old_context),
        "needle": args.needle,
        "needle_offset": needle_offset,
        "current_intent_sha256": hashlib.sha256(current_intent.encode("utf-8")).hexdigest(),
        "elapsed_ms": elapsed_ms,
        "usage": raw_response.get("usage") if isinstance(raw_response, dict) else None,
        "result": result,
        "expected": {
            "status": "accepted",
            "proposal": {
                "schema": "wrench.proposal.v1",
                "action": "read_file",
                "path": "src/wrench_harness/worker.py",
                "max_bytes": 65536,
            },
        },
        "quality_claim": False,
        "scope": "single synthetic needle in skipped old history; not a matched workflow result",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result.get("status"), "elapsed_ms": elapsed_ms, "usage": receipt["usage"]}))
    return 0 if result.get("status") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
