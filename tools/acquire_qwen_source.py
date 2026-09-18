#!/usr/bin/env python3
"""Guarded acquisition of the pinned unquantized Qwen source."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

EXPECTED_REPOSITORY = "Qwen/Qwen3.6-35B-A3B"
EXPECTED_REVISION = "995ad96eacd98c81ed38be0c5b274b04031597b0"
EXPECTED_BYTES = 71_903_645_408


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default=EXPECTED_REVISION)
    parser.add_argument("--expected-bytes", type=int, default=EXPECTED_BYTES)
    parser.add_argument(
        "--confirm-71gb",
        action="store_true",
        help="explicitly authorize downloading the pinned unquantized source",
    )
    args = parser.parse_args()
    if args.revision != EXPECTED_REVISION:
        raise SystemExit(f"refusing unpinned revision: {args.revision}")
    if args.expected_bytes != EXPECTED_BYTES:
        raise SystemExit(f"expected byte guard must remain {EXPECTED_BYTES}")
    if not args.confirm_71gb:
        raise SystemExit("refusing download: pass --confirm-71gb after reviewing the 71.9 GB acquisition")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    free_bytes = shutil.disk_usage(output.parent).free
    required = args.expected_bytes + 10 * 1024**3
    if free_bytes < required:
        raise SystemExit(f"insufficient free space: {free_bytes} < {required} bytes")

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise SystemExit("huggingface_hub is required for acquisition") from exc

    path = snapshot_download(
        repo_id=EXPECTED_REPOSITORY,
        revision=args.revision,
        local_dir=str(output),
        allow_patterns=[
            "config.json",
            "configuration.json",
            "generation_config.json",
            "model.safetensors.index.json",
            "model-*.safetensors",
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.json",
            "chat_template.jinja",
            "preprocessor_config.json",
            "video_preprocessor_config.json",
            "README.md",
            "LICENSE",
        ],
        resume_download=True,
    )
    print({"status": "PASS", "repository": EXPECTED_REPOSITORY, "revision": args.revision, "path": path})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
