#!/usr/bin/env python3
"""Probe the public package through the normal Hugging Face tokenizer API."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from transformers import AutoTokenizer


def _payload(target_tokens: int) -> str:
    marker = "old reference symbol=run_worker path=src/wrench_harness/worker.py line=218\n"
    filler = "stale lookup telemetry record status observed unrelated historical reference-only data; "
    current = (
        'CURRENT INTENT: inspect the source for symbol "run_worker" and return '
        "one bounded proposal for the active task."
    )
    needed = max(1, target_tokens - marker.count(" ") - current.count(" ") - 64)
    old = marker + filler * ((needed + filler.count(" ") - 1) // filler.count(" "))
    return old + current


def probe(model_dir: Path, target_tokens: int) -> dict[str, object]:
    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(
        model_dir,
        trust_remote_code=True,
        local_files_only=True,
    )
    tokenizer_load_ms = round((time.perf_counter() - started) * 1000, 3)
    payload = _payload(target_tokens)
    staged_started = time.perf_counter()
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": payload}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    staged_ms = round((time.perf_counter() - staged_started) * 1000, 3)
    receipt = getattr(tokenizer, "last_wrench_prefill_receipt", None)
    if not isinstance(receipt, dict):
        raise RuntimeError("the Wrench tokenizer did not expose a prefill receipt")
    target_preserved = "src/wrench_harness/worker.py" in rendered and "CURRENT INTENT" in rendered
    result = {
        "schema": "wrench.standard-hf-tokenizer-prefill-probe.v1",
        "status": (
            "PASS_STANDARD_HF_4M_STAGING"
            if receipt.get("split_current_message") is True
            and int(receipt.get("model_prefill_token_count", target_tokens + 1)) <= 64_000
            and target_preserved
            else "FAIL"
        ),
        "model_dir": str(model_dir.resolve()),
        "requested_payload_tokens": target_tokens,
        "raw_payload_chars": len(payload),
        "tokenizer_load_ms": tokenizer_load_ms,
        "staged_ms": staged_ms,
        "rendered_chars": len(rendered),
        "target_reference_preserved": target_preserved,
        "model_calls": 0,
        "receipt": receipt,
        "quality_claim": False,
        "limitations": [
            "This proves the standard package tokenizer stages a 4M estimated-token payload.",
            "It does not prove dense native 4M attention quality or MiniMax parity.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--payload-tokens", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.model_dir, args.payload_tokens)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "staged_ms", "model_calls")}, ensure_ascii=False))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
