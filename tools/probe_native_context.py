#!/usr/bin/env python3
"""Probe native model-visible context through an OpenAI-compatible endpoint.

This tool deliberately does not import the Wrench gateway or ContextLedger.
It sends the generated or file-backed prompt directly to the model endpoint and
records the provider-reported prompt token count. It never executes proposals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROMPT_UNIT = (
    "Mechanical worker context record. This is inert reference data. "
    "record_id=000000; status=observed; no tool execution is authorized.\n"
)


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any], float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            elapsed = (time.perf_counter() - started) * 1000
            return response.status, json.loads(raw.decode("utf-8")), elapsed
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        elapsed = (time.perf_counter() - started) * 1000
        try:
            detail = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            detail = {"error": raw.decode("utf-8", errors="replace")}
        return exc.code, detail, elapsed


def _build_prompt(
    path: Path | None,
    target_tokens: int,
    tokenizer_path: Path | None,
    prompt_salt: str | None = None,
) -> tuple[str, str, int | None]:
    prefix = f"probe_salt={prompt_salt}\n" if prompt_salt else ""
    if path is not None:
        return prefix + path.read_text(encoding="utf-8"), "prompt_file", None
    if target_tokens <= 0:
        raise ValueError("--target-tokens must be positive when --prompt-file is absent")
    if tokenizer_path is not None:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            local_files_only=True,
            trust_remote_code=True,
        )
        unit_tokens = len(tokenizer(PROMPT_UNIT, add_special_tokens=False).input_ids)
        content_target = max(1, target_tokens - 128)
        repetitions = max(1, (content_target + unit_tokens - 1) // unit_tokens)
        prompt = prefix + PROMPT_UNIT * repetitions
        # Do not tokenize the complete generated payload here. Some local
        # tokenizers take superlinear time on multi-million-token strings, which
        # would make the probe measure prompt construction instead of serving.
        # The endpoint's usage.prompt_tokens remains the authoritative count.
        estimated = unit_tokens * repetitions
        return prompt, "local_tokenizer_unit_estimate", estimated
    repetitions = max(1, (target_tokens * 5 + len(PROMPT_UNIT) - 1) // len(PROMPT_UNIT))
    return prefix + PROMPT_UNIT * repetitions, "character_estimate", None


def _usage(response: dict[str, Any]) -> dict[str, Any]:
    usage = response.get("usage")
    return usage if isinstance(usage, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/v1/chat/completions")
    parser.add_argument("--model", required=True)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--tokenizer", type=Path, help="Local tokenizer used to build a near-exact target prompt")
    parser.add_argument("--target-tokens", type=int, default=65536)
    parser.add_argument("--max-model-len", type=int, default=2_000_000)
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument(
        "--prompt-salt",
        help="Prepend a unique marker so radix-prefix cache cannot hide prefill work in A/B probes",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prompt, build_method, estimated_content_tokens = _build_prompt(
        args.prompt_file, args.target_tokens, args.tokenizer, args.prompt_salt
    )
    prompt_bytes = prompt.encode("utf-8")
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return one bounded JSON object with schema "
                    "wrench.proposal.v1. Do not execute tools."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": args.max_tokens,
        "temperature": 0,
        "stream": False,
    }
    status_code, response, elapsed_ms = _post_json(args.endpoint, payload, args.timeout)
    usage = _usage(response)
    actual_prompt_tokens = usage.get("prompt_tokens")
    truncated = isinstance(actual_prompt_tokens, (int, float)) and actual_prompt_tokens < args.target_tokens * 0.95
    receipt = {
        "schema": "wrench.native-context-probe.v1",
        "endpoint": args.endpoint,
        "model": args.model,
        "configured_max_model_len": args.max_model_len,
        "requested_target_tokens": args.target_tokens,
        "prompt_build_method": build_method,
        "prompt_salt": args.prompt_salt,
        "estimated_content_tokens": estimated_content_tokens,
        "tokenizer": str(args.tokenizer.resolve()) if args.tokenizer else None,
        "actual_prompt_tokens": actual_prompt_tokens,
        "truncated": truncated,
        "http_status": status_code,
        "prompt_utf8_bytes": len(prompt_bytes),
        "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
        "elapsed_ms": round(elapsed_ms, 3),
        "usage": usage,
        "max_tokens": args.max_tokens,
        "error": response.get("error") if isinstance(response, dict) else None,
        "native_context_pass": (
            status_code == 200
            and args.target_tokens <= args.max_model_len
            and isinstance(actual_prompt_tokens, (int, float))
            and actual_prompt_tokens >= args.target_tokens * 0.95
            and not truncated
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status_code, "actual_prompt_tokens": actual_prompt_tokens, "native_context_pass": receipt["native_context_pass"]}))
    return 0 if receipt["native_context_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
