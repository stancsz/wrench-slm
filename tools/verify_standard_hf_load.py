#!/usr/bin/env python3
"""Verify the standard Hugging Face config, tokenizer, and optional weights.

The default check is metadata and tokenizer only. ``--load-weights`` is an
explicit stronger probe. It must emit a structured failure receipt when a
backend cannot restore the packed artifact, rather than turning an exception
trace into an ambiguous result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


MIN_TRANSFORMERS = (5, 17, 0)
MIN_HYBRID_WORKING_CONTEXT = 64_000
LOGICAL_RAW_CONTEXT_LIMIT = 4_000_000


def _classify_weight_load_failure(error: BaseException) -> str:
    text = str(error).lower()
    if (
        "mismatched sizes" in text
        or "ignore_mismatched_sizes" in text
        or "shape" in text
    ):
        return "modelopt_nvfp4_shape_mismatch_or_unsupported_quantization"
    if "quant" in text or "modelopt" in text or "nvfp4" in text:
        return "modelopt_nvfp4_backend_support_gap"
    return "standard_transformers_weight_load_error"


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


def verify(
    model_dir: Path,
    *,
    load_weights: bool = False,
    require_native_context: bool = False,
) -> dict[str, Any]:
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
    # Transformers 5.17 no longer exposes the old private
    # AutoModelForImageTextToText._model_mapping attribute. The model config's
    # architecture list is the stable local artifact contract and is also what
    # AutoConfig resolved from this package.
    expected_architecture = "Qwen3_5MoeForConditionalGeneration"
    architectures = [str(item) for item in (getattr(config, "architectures", None) or [])]
    mapped_name = expected_architecture if expected_architecture in architectures else None
    if mapped_name is None:
        raise RuntimeError(
            f"unexpected model architectures: {architectures!r}; "
            f"expected {expected_architecture!r}"
        )
    model_max_length = int(getattr(tokenizer, "model_max_length", 0))
    if model_max_length < MIN_HYBRID_WORKING_CONTEXT:
        raise RuntimeError(
            f"tokenizer model_max_length is {model_max_length}, expected at least "
            f"{MIN_HYBRID_WORKING_CONTEXT} for the bounded hybrid working context"
        )
    native_context_supported = model_max_length >= LOGICAL_RAW_CONTEXT_LIMIT
    if require_native_context and not native_context_supported:
        raise RuntimeError(
            f"tokenizer model_max_length is {model_max_length}, expected at least "
            f"{LOGICAL_RAW_CONTEXT_LIMIT} for native dense context"
        )
    status = (
        "PASS_STANDARD_HF_CONFIG_TOKENIZER_NATIVE"
        if native_context_supported
        else "PASS_STANDARD_HF_CONFIG_TOKENIZER_HYBRID"
    )
    hash_names = ("config.json", "tokenizer_config.json", "tokenization_wrench.py")
    file_hashes = {
        name: _sha256(model_dir / name)
        for name in hash_names
        if (model_dir / name).is_file()
    }
    missing_optional_files = [
        name for name in hash_names if not (model_dir / name).is_file()
    ]
    receipt: dict[str, Any] = {
        "schema": "wrench.standard-hf-load-receipt.v1",
        "status": status,
        "model_dir": str(model_dir.resolve()),
        "transformers_version": version,
        "config_class": type(config).__name__,
        "config_model_type": getattr(config, "model_type", None),
        "mapped_model_class": mapped_name,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_model_max_length": model_max_length,
        "declared_logical_raw_input_context_tokens": LOGICAL_RAW_CONTEXT_LIMIT,
        "declared_effective_working_context_tokens": MIN_HYBRID_WORKING_CONTEXT,
        "native_tokenizer_context_supported": native_context_supported,
        "hybrid_raw_intake_contract": True,
        "native_context_required_by_probe": require_native_context,
        "weight_load_attempted": False,
        "full_weight_load_verified": False,
        "full_weight_generation_verified": False,
        "native_long_context_quality_verified": False,
        "file_hashes": file_hashes,
        "missing_optional_files": missing_optional_files,
    }
    if load_weights:
        import torch

        receipt["weight_load_attempted"] = True
        started = time.perf_counter()
        try:
            model = transformers.AutoModelForImageTextToText.from_pretrained(
                model_dir,
                dtype=torch.bfloat16,
                low_cpu_mem_usage=False,
                local_files_only=True,
                trust_remote_code=True,
            )
        except Exception as error:
            receipt.update(
                {
                    "status": "FAIL_STANDARD_HF_WEIGHT_LOAD",
                    "standard_weight_load_status": "FAIL_STANDARD_HF_WEIGHT_LOAD",
                    "weight_load_failure_class": _classify_weight_load_failure(error),
                    "weight_load_error_type": type(error).__name__,
                    "weight_load_error": str(error).splitlines()[0][:500],
                    "weight_load_elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                }
            )
            return receipt
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
    parser.add_argument(
        "--require-native-context",
        action="store_true",
        help="require the tokenizer itself to advertise the full 4M native context; hybrid mode is the default",
    )
    args = parser.parse_args()
    receipt = verify(
        args.model_dir.resolve(),
        load_weights=args.load_weights,
        require_native_context=args.require_native_context,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "transformers_version": receipt["transformers_version"],
        "full_weight_load_verified": receipt["full_weight_load_verified"],
    }))
    return 0 if not args.load_weights or receipt["full_weight_load_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
