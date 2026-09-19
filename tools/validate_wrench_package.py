#!/usr/bin/env python3
"""Validate the structural contract of a portable Wrench model directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("packaging/wrench-package-manifest.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors: list[str] = []
    required = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "tokenization_wrench.py",
        "wrench_prefill.py",
        "wrench_mechanical.py",
        "wrench_runtime/prefill.py",
    ]
    for name in required:
        if not (args.model_dir / name).is_file():
            errors.append(f"missing:{name}")
    safetensors = sorted(args.model_dir.glob("*.safetensors"))
    if not safetensors:
        errors.append("missing:safetensors")
    config: dict[str, object] = {}
    config_path = args.model_dir / "config.json"
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        text_config = config.get("text_config") if isinstance(config.get("text_config"), dict) else {}
        max_position = int(config.get("max_position_embeddings", 0) or text_config.get("max_position_embeddings", 0) or 0)
        if max_position < int(manifest["context"]["native_attention_context_tokens_target"]):
            errors.append("config:max_position_embeddings_below_2m_target")
    package_manifest = args.model_dir / "wrench-package.json"
    if not package_manifest.is_file():
        errors.append("missing:wrench-package.json")
    files = {}
    for path in [
        config_path,
        args.model_dir / "tokenizer.json",
        args.model_dir / "tokenizer_config.json",
        args.model_dir / "tokenization_wrench.py",
        args.model_dir / "wrench_prefill.py",
        args.model_dir / "wrench_mechanical.py",
        args.model_dir / "wrench_runtime" / "prefill.py",
        *safetensors,
        package_manifest,
    ]:
        if path.is_file():
            files[str(path.relative_to(args.model_dir)).replace("\\", "/")] = {
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
    result = {
        "schema": "wrench.portable-model-package-validation.v1",
        "model_dir": str(args.model_dir.resolve()),
        "status": "PASS_STRUCTURAL_PACKAGE" if not errors else "FAIL_STRUCTURAL_PACKAGE",
        "errors": errors,
        "config_max_position_embeddings": config.get("max_position_embeddings") or (
            config.get("text_config", {}).get("max_position_embeddings")
            if isinstance(config.get("text_config"), dict)
            else None
        ),
        "safetensors_shard_count": len(safetensors),
        "file_hashes": files,
        "quality_claim": False,
        "native_attention_claim": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": errors}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
