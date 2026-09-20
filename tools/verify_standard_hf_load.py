#!/usr/bin/env python3
"""Verify the standard Hugging Face config and tokenizer path for Wrench.

This is intentionally a metadata and tokenizer check. It does not load the
4B tensors or claim generation quality. Full model generation and long-context
serving remain backend-specific gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


MIN_TRANSFORMERS = (5, 17, 0)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _version_tuple(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for part in value.split("."):
        digits = "".join(character for character in part if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def verify(model_dir: Path, *, load_weights: bool = False) -> dict[str, Any]:
    import transformers

    version = str(transformers.__version__)
    if _version_tuple(version) < MIN_TRANSFORMERS:
        raise RuntimeError(
            f"Transformers {version} is too old; Wrench requires >= {'.'.join(map(str, MIN_TRANSFORMERS))}"
        )
    config = transformers.AutoConfig.from_pretrained(
        model_dir,
        trust_remote_code=True,
        local_files_only=True,
    )
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        model_dir,
        trust_remote_code=True,
        local_files_only=True,
    )
    mapped = transformers.AutoModelForImageTextToText._model_mapping.get(type(config), None)
    mapped_name = getattr(mapped, "__name__", None)
    if mapped_name != "Qwen3_5MoeForConditionalGeneration":
        raise RuntimeError(f"unexpected AutoModel mapping: {mapped_name!r}")
    model_max_length = int(getattr(tokenizer, "model_max_length", 0))
    if model_max_length < 4_000_000:
        raise RuntimeError(f"tokenizer model_max_length is {model_max_length}, expected at least 4000000")
    receipt: dict[str, Any] = {
        "schema": "wrench.standard-hf-load-receipt.v1",
        "status": "PASS_STANDARD_HF_CONFIG_TOKENIZER",
        "model_dir": str(model_dir.resolve()),
        "transformers_version": version,
        "config_class": type(config).__name__,
        "config_model_type": getattr(config, "model_type", None),
        "mapped_model_class": mapped_name,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_model_max_length": model_max_length,
        "declared_input_context_tokens": 4_000_000,
        "full_weight_load_verified": False,
        "full_weight_generation_verified": False,
        "native_long_context_quality_verified": False,
        "file_hashes": {
            name: _sha256(model_dir / name)
            for name in ("config.json", "tokenizer_config.json", "tokenization_wrench.py")
        },
    }
    if load_weights:
        import torch

        started = time.perf_counter()
        model = transformers.AutoModelForImageTextToText.from_pretrained(
            model_dir,
            dtype=torch.bfloat16,
            low_cpu_mem_usage=False,
            local_files_only=True,
        )
        receipt.update(
            {
                "full_weight_load_verified": True,
                "loaded_model_class": type(model).__name__,
                "loaded_parameter_count": sum(parameter.numel() for parameter in model.parameters()),
                "weight_load_elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            }
        )
        del model
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-weights", action="store_true")
    args = parser.parse_args()
    receipt = verify(args.model_dir.resolve(), load_weights=args.load_weights)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "transformers_version": receipt["transformers_version"],
        "full_weight_load_verified": receipt["full_weight_load_verified"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
