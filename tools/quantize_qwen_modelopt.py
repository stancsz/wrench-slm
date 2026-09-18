#!/usr/bin/env python3
"""Quantize a pruned Qwen checkpoint's routed experts with ModelOpt NVFP4."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def quantize(model_path: Path, output: Path, calibration: Path, limit: int, config_name: str) -> dict:
    import torch
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from modelopt.torch import quantization as mtq
    from modelopt.torch.export import export_hf_checkpoint

    if output.exists():
        raise ValueError(f"refusing to overwrite existing output: {output}")
    rows = [json.loads(line) for line in calibration.read_text(encoding="utf-8").splitlines() if line.strip()][:limit]
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=False,
    ).to("cuda")
    model.eval()

    def forward_loop(quantized_model) -> None:
        with torch.inference_mode():
            for row in rows:
                batch = tokenizer(row["prompt"], return_tensors="pt", truncation=True, max_length=512).to("cuda")
                quantized_model(**batch, use_cache=False)

    if config_name == "experts-only":
        quant_cfg = mtq.NVFP4_EXPERTS_ONLY_CFG
    elif config_name == "w4a16":
        quant_cfg = mtq.W4A16_NVFP4_CFG
    else:
        raise ValueError(f"unknown quantization config: {config_name}")
    quantized = mtq.quantize(model, quant_cfg, forward_loop)
    export_hf_checkpoint(
        quantized,
        dtype=torch.bfloat16,
        export_dir=output,
        save_modelopt_state=False,
        max_shard_size="4GB",
    )
    # ModelOpt writes weights and quantization metadata, but does not copy the
    # tokenizer assets needed by FreeToken's chat-template path.
    for source_file in model_path.iterdir():
        if not source_file.is_file() or source_file.name in {"config.json", "generation_config.json"}:
            continue
        if source_file.suffix in {".safetensors", ".ftw"} or source_file.name == "model.safetensors.index.json":
            continue
        shutil.copy2(source_file, output / source_file.name)
    receipt = {
        "schema": "wrench.qwen-modelopt-nvfp4.v1",
        "status": "PASS_MODELOPT_EXPORT",
        "source": str(model_path.resolve()),
        "output": str(output.resolve()),
        "calibration": str(calibration.resolve()),
        "calibration_rows": len(rows),
        "quant_config": config_name,
        "quality_claim": False,
    }
    (output / "wrench-quantization-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--config", choices=("experts-only", "w4a16"), default="experts-only")
    args = parser.parse_args()
    receipt = quantize(args.model.resolve(), args.output.resolve(), args.calibration.resolve(), args.limit, args.config)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
