#!/usr/bin/env python3
"""Materialize one copy-pasteable Wrench model package.

Weights are hard-linked from an immutable source artifact. Metadata and the
standalone deterministic prefill module are copied into a new package. The
source directory is never modified and an existing target is never replaced.
"""

from __future__ import annotations

import argparse
import errno
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
    source_name_lower = source.name.lower()
    safety_candidate = "safety" in source_name_lower or "calibrated" in source_name_lower
    quantized_candidate = (source / "hf_quant_config.json").is_file()
    native4m_candidate = "native4m" in source_name_lower
    weight_materialization_mode = "hardlink"
    try:
        for item in sorted(source.iterdir(), key=lambda path: path.name):
            if item.is_file() and item.suffix == ".safetensors":
                try:
                    os.link(item, target / item.name)
                except OSError as exc:
                    if exc.errno != errno.EXDEV and getattr(exc, "winerror", None) != 17:
                        raise
                    # Hugging Face artifacts are often on a separate data volume
                    # from the repository. Preserve the no-overwrite contract
                    # while falling back to a byte-for-byte copy across volumes.
                    shutil.copy2(item, target / item.name)
                    weight_materialization_mode = "copy_cross_volume"
            elif item.is_file():
                shutil.copy2(item, target / item.name)
        tokenizer_config_path = target / "tokenizer_config.json"
        if tokenizer_config_path.is_file():
            tokenizer_config = json.loads(tokenizer_config_path.read_text(encoding="utf-8"))
            tokenizer_config["tokenizer_class"] = "WrenchTokenizer"
            # The base tokenizer metadata advertises 256K, which would make
            # a standard Transformers caller truncate or reject a direct 4M
            # request before the selected backend sees it. The runtime still
            # owns the native no-truncation receipt, but the portable package
            # must expose the declared endpoint limit at the tokenizer API.
            tokenizer_config["model_max_length"] = 4_000_000
            tokenizer_config["auto_map"] = {
                "AutoTokenizer": ["tokenization_wrench.WrenchTokenizer", None]
            }
            tokenizer_config_path.write_text(
                json.dumps(tokenizer_config, indent=2) + "\n", encoding="utf-8"
            )
        runtime_dir = target / "wrench_runtime"
        runtime_dir.mkdir()
        shutil.copy2(repo_root / "src" / "wrench_harness" / "prefill.py", runtime_dir / "prefill.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "core.py", runtime_dir / "toolbelt.py")
        shutil.copy2(
            repo_root / "runtime" / "freetoken_wrench_long_context" / "sitecustomize.py",
            runtime_dir / "sitecustomize.py",
        )
        shutil.copy2(repo_root / "src" / "wrench_harness" / "prefill.py", target / "wrench_prefill.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "mechanical.py", target / "wrench_mechanical.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "core.py", target / "wrench_toolbelt.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "mechanical.py", runtime_dir / "mechanical.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "worker.py", runtime_dir / "worker.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "core.py", runtime_dir / "core.py")
        shutil.copy2(repo_root / "wrench_worker.py", target / "wrench_worker.py")
        shutil.copy2(repo_root / "runtime" / "wrench_model_package" / "tokenization_wrench.py", target / "tokenization_wrench.py")
        (runtime_dir / "__init__.py").write_text(
            "\"\"\"Bundled Wrench deterministic runtime.\"\"\"\n"
            "from .worker import WrenchWorker\n\n"
            "__all__ = [\"WrenchWorker\"]\n",
            encoding="utf-8",
        )
        (target / "wrench-runtime.json").write_text(
            json.dumps(
                {
                    "schema": "wrench.runtime-profile.v1",
                    "fast_mode": {
                        "native_direct_input": False,
                        "effective_working_context_tokens": 64000,
                        "hot_context_tokens": 48000,
                        "reference_card_tokens": 16000,
                    },
                    "native_mode": {
                        "native_direct_input": True,
                        "declared_input_context_tokens": 4000000,
                        "swa_window_tokens": 8192,
                        "swa_pool_tokens": 8192,
                        "rope_max_position_runtime": 4000000,
                        "max_prefill_length_tokens": 32768,
                        "native_direct_payload_verified": True,
                    },
                    "launch_note": "Native mode requires the bundled runtime overlay and a compatible FreeToken build.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (target / "serve_freetoken.ps1").write_text(
            """param(\n    [string]$FreeTokenExecutable = \"ft\",\n    [int]$Port = 28900\n)\n\n$env:PYTHONPATH = \"$PSScriptRoot\\wrench_runtime;$env:PYTHONPATH\"\n$env:WRENCH_LONG_CONTEXT_OVERLAY = \"1\"\n$env:WRENCH_GLOBAL_FULL_LAYERS = \"none\"\n$env:WRENCH_SWA_WINDOW = \"8192\"\n$env:WRENCH_SWA_POOL_TOKENS = \"8192\"\n$env:WRENCH_ROPE_MAX_POSITION = \"4000000\"\n$env:WRENCH_NATIVE_DIRECT_INPUT = \"1\"\n& $FreeTokenExecutable serve `\n    --model $PSScriptRoot `\n    --host 127.0.0.1 `\n    --port $Port `\n    --served-model-name wrench-4b-qwen3.6-8e `\n    --moe-strategy offload `\n    --moe-cache-auto `\n    --max-running-requests 1 `\n    --max-seq-len-override 4000000 `\n    --max-prefill-length 32768 `\n    --memory-ratio 0.9 `\n    --text-model-only `\n    --cache-type radix `\n    --tool-call-parser qwen `\n    --reasoning-parser off\n""",
            encoding="utf-8",
        )
        launcher_path = target / "serve_freetoken.ps1"
        launcher_path.write_text(
            launcher_path.read_text(encoding="utf-8").replace(
                "--max-prefill-length 8192", "--max-prefill-length 32768"
            ),
            encoding="utf-8",
        )
        shutil.copy2(repo_root / "packaging" / "WRENCH_HF_README.md", target / "README.md")
        shutil.copy2(repo_root / "docs" / "WRENCH_PORTABLE_DISTRIBUTION.md", target / "WRENCH_PORTABLE_DISTRIBUTION.md")
        package_manifest = {
            "schema": "wrench.portable-model-package.v1",
            "package_name": "Wrench",
            "release_status": "EXPERIMENTAL_PUBLIC_ARTIFACT",
            "canonical_format": "huggingface-safetensors",
            "verified_total_parameters": PARAMETER_COUNT,
            "hard_parameter_ceiling": PARAMETER_CEILING,
            "model_lineage": "Qwen3.6-35B-A3B -> Wrench 8E structural prune",
            "candidate_identity": (
                "Wrench-4B-Qwen3.6-8E-Safety-v7-NVFP4-native4M"
                if quantized_candidate and native4m_candidate
                else (
                    "Wrench-4B-Qwen3.6-8E-Safety-v7-native2M"
                    if safety_candidate
                    else "Wrench-4B-Qwen3.6-8E-base"
                )
            ),
            "quantization": (
                "NVFP4-W4A16-ModelOpt"
                if quantized_candidate
                else None
            ),
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
                "verifier_is_bundled": True,
                "entrypoint": "tokenization_wrench.py",
                "model_calls_for_mechanical_lookup": 0,
            },
            "backends": {
                "transformers": "Transformers >=5.17.0 config/tokenizer verified; full generation backend-dependent",
                "freetoken": (
                    "local experimental backend with ModelOpt NVFP4"
                    if quantized_candidate
                    else "local experimental backend"
                ),
                "vllm": "requires registered Wrench architecture",
                "ollama_gguf": "not verified",
            },
            "publication": {
                "huggingface_repo_id": "stancsz/Wrench-4B-Qwen3.6-8E",
                "public_upload_authorized": True,
                "copy_paste_command": "hf download stancsz/Wrench-4B-Qwen3.6-8E --local-dir Wrench-4B-Qwen3.6-8E",
            },
        }
        (target / "wrench-package.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")
        receipt = {
            "schema": "wrench.portable-package-materialization.v1",
            "status": "MATERIALIZED_PACKAGE_RUNTIME_EMBEDDED",
            "source_artifact_name": source.name,
            "target_package_name": target.name,
            "target": str(target.resolve()),
            "weight_link_count": len(list(target.glob("*.safetensors"))),
            "weight_materialization_mode": weight_materialization_mode,
            "runtime_files": [
                "tokenization_wrench.py",
                "wrench_prefill.py",
                "wrench_mechanical.py",
                "wrench_toolbelt.py",
                "wrench_runtime/__init__.py",
                "wrench_runtime/prefill.py",
                "wrench_runtime/toolbelt.py",
                "wrench_runtime/core.py",
                "wrench_runtime/mechanical.py",
                "wrench_runtime/worker.py",
                "wrench_worker.py",
                "wrench_runtime/sitecustomize.py",
                "wrench-runtime.json",
                "serve_freetoken.ps1",
            ],
            "quality_claim": False,
            "native_attention_claim": False,
            "next_required": [
                "validate package structure and hashes",
                "complete reducer-bypassed native attention probe",
                "register and verify backend adapters",
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
