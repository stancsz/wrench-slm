#!/usr/bin/env python3
"""Run a bounded local load and generation smoke for a pruned Qwen checkpoint."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def run_smoke(model_path: Path, prompt: str, max_new_tokens: int) -> dict:
    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer

    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    torch.cuda.reset_peak_memory_stats()
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=False,
    ).to("cuda")
    loaded_at = time.perf_counter()
    batch = tokenizer(prompt, return_tensors="pt").to("cuda")
    generated = model.generate(
        **batch,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        use_cache=True,
    )
    torch.cuda.synchronize()
    finished = time.perf_counter()
    return {
        "schema": "wrench.qwen-pruned-runtime-smoke.v1",
        "model_path": str(model_path),
        "config_num_experts": int(model.config.text_config.num_experts),
        "config_num_experts_per_tok": int(model.config.text_config.num_experts_per_tok),
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "dtype": str(next(model.parameters()).dtype),
        "device": str(next(model.parameters()).device),
        "prompt": prompt,
        "input_tokens": int(batch["input_ids"].shape[1]),
        "output_tokens": int(generated.shape[1] - batch["input_ids"].shape[1]),
        "decoded_output": tokenizer.decode(generated[0], skip_special_tokens=True),
        "load_seconds": round(loaded_at - started, 3),
        "generation_seconds": round(finished - loaded_at, 3),
        "peak_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "gpu_identity": torch.cuda.get_device_name(0),
        "runtime_identity": {
            "python": __import__("platform").python_version(),
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
        },
        "status": "PASS_STRUCTURAL_LOAD_AND_FORWARD",
        "quality_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prompt", default="Return only the word OK.")
    parser.add_argument("--max-new-tokens", type=int, default=8)
    args = parser.parse_args()
    receipt = run_smoke(args.model.resolve(), args.prompt, args.max_new_tokens)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
