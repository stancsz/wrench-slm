#!/usr/bin/env python3
"""Prepare a non-destructive long-context config candidate.

This writes only a config candidate. It does not alter weights and it does not
claim that positional extrapolation alone gives long-context quality. A direct
serving probe and long-context training or validation are still required.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("context length must be positive")
    return parsed


def prepare_config(source: dict[str, Any], target_tokens: int, *, rope_type: str = "yarn") -> dict[str, Any]:
    if target_tokens < 1:
        raise ValueError("target_tokens must be positive")
    text_config = source.get("text_config")
    if not isinstance(text_config, dict):
        raise ValueError("config must contain an object text_config")
    current = text_config.get("max_position_embeddings")
    if not isinstance(current, int) or current <= 0:
        raise ValueError("text_config.max_position_embeddings must be a positive integer")
    if target_tokens < current:
        raise ValueError("target context must not be smaller than source context")

    candidate = copy.deepcopy(source)
    candidate_text = candidate["text_config"]
    candidate_text["max_position_embeddings"] = target_tokens
    rope = candidate_text.get("rope_parameters")
    if not isinstance(rope, dict):
        raise ValueError("text_config.rope_parameters must be an object")
    rope["rope_type"] = rope_type
    rope["original_max_position_embeddings"] = current
    rope["factor"] = target_tokens / current
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_config", type=Path)
    parser.add_argument("--target-tokens", type=_positive_int, default=2_000_000)
    parser.add_argument("--rope-type", choices=("yarn", "default"), default="yarn")
    parser.add_argument("--output-config", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    source_bytes = args.source_config.read_bytes()
    source = json.loads(source_bytes.decode("utf-8"))
    candidate = prepare_config(source, args.target_tokens, rope_type=args.rope_type)
    output_bytes = (json.dumps(candidate, indent=2) + "\n").encode("utf-8")
    args.output_config.parent.mkdir(parents=True, exist_ok=True)
    args.output_config.write_bytes(output_bytes)
    receipt = {
        "schema": "wrench.native-context-config-candidate.v1",
        "status": "CONFIG_ONLY_NOT_QUALITY_PROOF",
        "source_config": str(args.source_config.resolve()),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "output_config": str(args.output_config.resolve()),
        "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "source_context_tokens": source["text_config"]["max_position_embeddings"],
        "target_context_tokens": args.target_tokens,
        "rope_type": args.rope_type,
        "rope_factor": candidate["text_config"]["rope_parameters"]["factor"],
        "weights_unchanged": True,
        "quality_proof": False,
        "next_required": [
            "load the complete standard artifact in the selected runtime",
            "send a direct model request and verify actual prompt_tokens",
            "run long-context recall and mechanical-worker task evaluation",
            "measure prefill, memory, throughput, and failure behavior",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "target_context_tokens": args.target_tokens}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
