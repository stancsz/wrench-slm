#!/usr/bin/env python3
"""Materialize one copy-pasteable Wrench model package.

Weights are hard-linked from an immutable source artifact. Metadata and the
standalone deterministic prefill module are copied into a new package. The
source directory is never modified and an existing target is never replaced.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


PARAMETER_COUNT = 3_881_244_016
PARAMETER_CEILING = 4_250_000_000


def materialize(source: Path, target: Path, repo_root: Path) -> dict[str, object]:
    if not source.is_dir() or not (source / "config.json").is_file():
        raise ValueError(f"source artifact is missing config.json: {source}")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing target: {target}")
    target.mkdir(parents=True)
    try:
        for item in sorted(source.iterdir(), key=lambda path: path.name):
            if item.is_file() and item.suffix == ".safetensors":
                os.link(item, target / item.name)
            elif item.is_file():
                shutil.copy2(item, target / item.name)
        tokenizer_config_path = target / "tokenizer_config.json"
        if tokenizer_config_path.is_file():
            tokenizer_config = json.loads(tokenizer_config_path.read_text(encoding="utf-8"))
            tokenizer_config["tokenizer_class"] = "WrenchTokenizer"
            tokenizer_config["auto_map"] = {
                "AutoTokenizer": ["tokenization_wrench.WrenchTokenizer", None]
            }
            tokenizer_config_path.write_text(
                json.dumps(tokenizer_config, indent=2) + "\n", encoding="utf-8"
            )
        runtime_dir = target / "wrench_runtime"
        runtime_dir.mkdir()
        shutil.copy2(repo_root / "src" / "wrench_harness" / "prefill.py", runtime_dir / "prefill.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "prefill.py", target / "wrench_prefill.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "mechanical.py", target / "wrench_mechanical.py")
        shutil.copy2(repo_root / "runtime" / "wrench_model_package" / "tokenization_wrench.py", target / "tokenization_wrench.py")
        (runtime_dir / "__init__.py").write_text("\"\"\"Bundled Wrench deterministic runtime.\"\"\"\n", encoding="utf-8")
        shutil.copy2(repo_root / "docs" / "WRENCH_PORTABLE_DISTRIBUTION.md", target / "WRENCH_PORTABLE_DISTRIBUTION.md")
        package_manifest = {
            "schema": "wrench.portable-model-package.v1",
            "package_name": "Wrench",
            "release_status": "EXPERIMENTAL_NOT_PUBLISHABLE",
            "canonical_format": "huggingface-safetensors",
            "verified_total_parameters": PARAMETER_COUNT,
            "hard_parameter_ceiling": PARAMETER_CEILING,
            "context": {
                "declared_input_context_tokens": 4_000_000,
                "native_attention_context_tokens_target": 2_000_000,
                "native_attention_context_tokens_verified": None,
                "effective_working_context_tokens_default": 64_000,
                "hot_context_tokens_default": 48_000,
                "reference_card_tokens_default": 16_000,
            },
            "runtime": {
                "bundled": True,
                "entrypoint": "tokenization_wrench.py",
                "model_calls_for_mechanical_lookup": 0,
            },
            "backends": {
                "transformers": "requires Wrench model adapter",
                "freetoken": "local experimental backend",
                "vllm": "requires registered Wrench architecture",
                "ollama_gguf": "not verified",
            },
            "publication": {"public_upload_authorized": False},
        }
        (target / "wrench-package.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")
        receipt = {
            "schema": "wrench.portable-package-materialization.v1",
            "status": "MATERIALIZED_PACKAGE_RUNTIME_PENDING",
            "source": str(source.resolve()),
            "target": str(target.resolve()),
            "weight_link_count": len(list(target.glob("*.safetensors"))),
            "runtime_files": [
                "tokenization_wrench.py",
                "wrench_prefill.py",
                "wrench_mechanical.py",
                "wrench_runtime/__init__.py",
                "wrench_runtime/prefill.py",
            ],
            "quality_claim": False,
            "native_attention_claim": False,
            "next_required": [
                "validate package structure and hashes",
                "complete reducer-bypassed native attention probe",
                "register and verify backend adapters",
                "obtain explicit publication authorization before upload",
            ],
        }
        (target / "wrench-package-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return receipt
    except Exception:
        shutil.rmtree(target)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    receipt = materialize(args.source, args.target, args.repo_root)
    print(json.dumps({"status": receipt["status"], "target": receipt["target"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
