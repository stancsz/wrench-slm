#!/usr/bin/env python3
"""Instantiate a Qwen config on meta tensors without loading model weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "schema": "wrench.qwen-meta-load-check.v1",
        "checkpoint": str(args.checkpoint.resolve()),
        "status": "NOT_READY",
        "model_class": None,
        "config_class": None,
        "error": None,
    }
    try:
        from accelerate import init_empty_weights
        from transformers import AutoConfig, AutoModelForImageTextToText

        config = AutoConfig.from_pretrained(args.checkpoint, local_files_only=True)
        result["config_class"] = type(config).__name__
        with init_empty_weights():
            model = AutoModelForImageTextToText.from_config(config)
        result["model_class"] = type(model).__name__
        result["status"] = "PASS"
    except Exception as exc:  # pragma: no cover - diagnostic receipt
        result["error"] = f"{type(exc).__name__}: {exc}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
