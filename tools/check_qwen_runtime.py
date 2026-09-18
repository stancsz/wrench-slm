#!/usr/bin/env python3
"""Check whether the installed Python runtime can load Qwen3.6 metadata."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config_path = args.checkpoint / "config.json"
    if not config_path.is_file():
        raise SystemExit(f"missing config.json: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model_type = config.get("model_type")
    expected_class = "Qwen3_5MoeForConditionalGeneration"
    try:
        import transformers

        transformers_version = importlib.metadata.version("transformers")
        class_available = hasattr(transformers, expected_class)
    except Exception as exc:  # pragma: no cover - diagnostic path
        transformers_version = None
        class_available = False
        import_error = f"{type(exc).__name__}: {exc}"
    else:
        import_error = None

    result = {
        "schema": "wrench.qwen-runtime-check.v1",
        "checkpoint": str(args.checkpoint.resolve()),
        "model_type": model_type,
        "expected_transformers_class": expected_class,
        "transformers_version": transformers_version,
        "transformers_class_available": class_available,
        "import_error": import_error,
        "status": "READY" if class_available else "NOT_READY",
        "reason": None if class_available else "Installed Transformers does not expose the Qwen3.6 architecture.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if class_available else 2


if __name__ == "__main__":
    raise SystemExit(main())
