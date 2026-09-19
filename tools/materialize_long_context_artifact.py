#!/usr/bin/env python3
"""Create a standard long-context artifact without duplicating model weights.

The target receives a derived config and hardlinks for immutable weight files.
The source directory is never modified. The target must not already exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

try:
    from tools.prepare_native_context_config import prepare_config
except ModuleNotFoundError:  # direct `python tools/script.py` execution
    from prepare_native_context_config import prepare_config


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize(source: Path, target: Path, target_tokens: int) -> dict[str, Any]:
    if not source.is_dir() or not (source / "config.json").is_file():
        raise ValueError(f"source artifact is missing config.json: {source}")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing target: {target}")
    config = json.loads((source / "config.json").read_text(encoding="utf-8"))
    candidate = prepare_config(config, target_tokens)
    target.mkdir(parents=True)
    rows: list[dict[str, Any]] = []
    try:
        for item in sorted(source.iterdir(), key=lambda path: path.name):
            destination = target / item.name
            if item.name == "config.json":
                destination.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
                method = "derived_config"
            elif item.is_file() and item.suffix == ".safetensors":
                os.link(item, destination)
                method = "hardlink_immutable_weight"
            elif item.is_file():
                shutil.copy2(item, destination)
                method = "copied_metadata"
            else:
                continue
            rows.append({"name": item.name, "bytes": destination.stat().st_size, "method": method})
    except Exception:
        shutil.rmtree(target)
        raise
    receipt = {
        "schema": "wrench.native-context-artifact.v1",
        "status": "ARTIFACT_MATERIALIZED_RUNTIME_QUALITY_PENDING",
        "source": str(source.resolve()),
        "target": str(target.resolve()),
        "source_config_sha256": _sha256(source / "config.json"),
        "target_config_sha256": _sha256(target / "config.json"),
        "source_context_tokens": config["text_config"]["max_position_embeddings"],
        "target_context_tokens": target_tokens,
        "weights_copied": False,
        "weight_link_count": sum(row["method"] == "hardlink_immutable_weight" for row in rows),
        "files": rows,
        "quality_claim": False,
        "next_required": [
            "runtime health must pass rope and context checks",
            "direct prompt_tokens receipt at the target context",
            "long-context recall and mechanical-worker quality evaluation",
        ],
    }
    (target / "wrench-native-context-artifact.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--target-tokens", type=int, default=2_000_000)
    args = parser.parse_args()
    receipt = materialize(args.source, args.target, args.target_tokens)
    print(json.dumps({"status": receipt["status"], "target": receipt["target"], "target_context_tokens": receipt["target_context_tokens"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
