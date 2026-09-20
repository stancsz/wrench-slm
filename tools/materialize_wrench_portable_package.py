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


def materialize(
    source: Path,
    target: Path,
    repo_root: Path,
    huggingface_repo_id: str = "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M",
) -> dict[str, object]:
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
            # Python bytecode is machine- and interpreter-specific noise.  It
            # must not become part of a portable Hub model snapshot.
            if item.name == "__pycache__" or item.suffix == ".pyc":
                continue
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
        # Keep the read-only lookup helpers separate from the execution
        # verifier.  The package ships both modules, and callers may import
        # the toolbelt directly from the downloaded directory.
        shutil.copy2(repo_root / "src" / "wrench_harness" / "toolbelt.py", runtime_dir / "toolbelt.py")
        shutil.copy2(
            repo_root / "runtime" / "freetoken_wrench_long_context" / "sitecustomize.py",
            runtime_dir / "sitecustomize.py",
        )
        shutil.copy2(repo_root / "src" / "wrench_harness" / "prefill.py", target / "wrench_prefill.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "mechanical.py", target / "wrench_mechanical.py")
        shutil.copy2(
            repo_root / "packaging" / "wrench_toolbelt.py",
            target / "wrench_toolbelt.py",
        )
        # Transformers dynamic-module loading resolves the relative import
        # used by wrench_prefill.py from the model root. Keep the canonical
        # toolbelt available under that exact module name as well as through
        # the convenience wrench_toolbelt.py wrapper.
        shutil.copy2(repo_root / "src" / "wrench_harness" / "toolbelt.py", target / "toolbelt.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "core.py", target / "core.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "mechanical.py", runtime_dir / "mechanical.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "patching.py", runtime_dir / "patching.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "worker.py", runtime_dir / "worker.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "server.py", runtime_dir / "server.py")
        shutil.copy2(repo_root / "src" / "wrench_harness" / "core.py", runtime_dir / "core.py")
        shutil.copy2(repo_root / "wrench_worker.py", target / "wrench_worker.py")
        shutil.copy2(repo_root / "wrench_server.py", target / "wrench_server.py")
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
                        "dynamic_staged_prefill": True,
                    },
                    "native_mode": {
                        "native_direct_input": True,
                        "declared_input_context_tokens": 4000000,
                    "kv_capacity_tokens_override": 4000000,
                    "swa_window_tokens": 8192,
                    "swa_pool_tokens": 8192,
                    "expert_cache": "auto",
                    "expert_load": "serial",
                    "tokenizer_processes": 0,
                    "shared_tokenizer_detokenizer": True,
                    "rope_max_position_runtime": 4000000,
                        "max_prefill_length_tokens": 32768,
                        "native_direct_payload_verified": True,
                        "fast_history_profile": "opt_in_reference_only",
                        "fast_history_keep_tokens_default": 64000,
                        "fast_history_boundary_mode": "request_relative_auto",
                    },
                    "launch_note": "Native mode requires the bundled runtime overlay and a compatible FreeToken build.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        shutil.copy2(repo_root / "packaging" / "run_wrench.ps1", target / "run_wrench.ps1")
        (target / "serve_freetoken.ps1").write_text(
            """param(\n    [string]$FreeTokenExecutable = \"ft\",\n    [int]$Port = 28900,\n    [int]$MoeCacheSize = 16\n)\n\n$env:PYTHONPATH = \"$PSScriptRoot\\wrench_runtime;$env:PYTHONPATH\"\n$env:WRENCH_LONG_CONTEXT_OVERLAY = \"1\"\n$env:WRENCH_GLOBAL_FULL_LAYERS = \"none\"\n$env:WRENCH_SWA_WINDOW = \"8192\"\n$env:WRENCH_SWA_POOL_TOKENS = \"8192\"\n$env:WRENCH_ROPE_MAX_POSITION = \"4000000\"\n$env:WRENCH_NATIVE_DIRECT_INPUT = \"1\"\n& $FreeTokenExecutable serve `\n    --model $PSScriptRoot `\n    --host 127.0.0.1 `\n    --port $Port `\n    --served-model-name wrench-4b-qwen3.6-8e `\n    --moe-strategy offload `\n    --moe-cache-size $MoeCacheSize `\n    --max-running-requests 1 `\n    --max-seq-len-override 4000000 `\n    --max-prefill-length 32768 `\n    --memory-ratio 0.9 `\n    --text-model-only `\n    --cache-type radix `\n    --tool-call-parser qwen `\n    --reasoning-parser off\n""",
            encoding="utf-8",
        )
        launcher_path = target / "serve_freetoken.ps1"
        launcher_text = launcher_path.read_text(encoding="utf-8").replace(
            "--max-prefill-length 8192", "--max-prefill-length 32768"
        )
        # FreeToken's default starts an extra tokenizer process. Sharing the
        # tokenizer with the detokenizer materially lowers Windows startup
        # pressure when the native model also has to load CUDA DLLs.
        launcher_text = launcher_text.replace(
            "    --moe-strategy offload `\n",
            "    --moe-strategy offload `\n    --num-tokenizer 0 `\n",
        )
        launcher_text = launcher_text.replace(
            '$env:WRENCH_LONG_CONTEXT_OVERLAY = "1"',
            '$env:WRENCH_LONG_CONTEXT_OVERLAY = "1"\n'
            '$env:CUDA_MODULE_LOADING = "LAZY"\n'
            '$env:PYTORCH_NVML_BASED_CUDA_CHECK = "1"\n'
            '$env:OPENBLAS_NUM_THREADS = "1"\n'
            '$env:OMP_NUM_THREADS = "1"\n'
            '$env:MKL_NUM_THREADS = "1"\n'
            '$env:NUMEXPR_NUM_THREADS = "1"',
        )
        launcher_text = launcher_text.replace(
            '[string]$FreeTokenExecutable = "ft"',
            '[string]$FreeTokenExecutable = "ft.cmd"',
        )
        launcher_text = launcher_text.replace(
            "    [int]$MoeCacheSize = 16",
            "    [int]$KvReserveTokens = 8192",
        )
        launcher_text = launcher_text.replace(
            "    [int]$KvReserveTokens = 8192",
            "    [int]$KvReserveTokens = 8192,\n    [int]$MoeCacheSize = 0,\n    [ValidateSet(\"offload\", \"cpu\", \"hybrid\", \"fused\")] [string]$MoeStrategy = \"offload\",\n    [string]$MoeCpuLayers = \"\",\n    [int]$MoeCpuThreads = 0,\n    [int]$MoeHybridMaxFetch = -1,\n    [switch]$FastHistory,\n    [int]$FastHistoryKeepTokens = 64000,\n    [int]$FastHistoryControlPrefixTokens = 4096,\n    [switch]$NativeDirectInput,\n    [switch]$OllamaApi,\n    [int]$NativePort = 28901,\n    [int]$UpstreamTimeoutSeconds = 9",
        )
        launcher_text = launcher_text.replace(
            "    [int]$Port = 28900,\n",
            "    [int]$Port = 28900,\n    [string]$AllowedRoot = \".\",\n",
        )
        launcher_text = launcher_text.replace(
            "    --moe-cache-size $MoeCacheSize `",
            "    --moe-cache-auto `\n    --kv-reserve-tokens $KvReserveTokens `\n    --num-tokens 4000000 `",
        )
        launcher_text = launcher_text.replace(
            '$env:WRENCH_NATIVE_DIRECT_INPUT = "1"',
            'if ($NativeDirectInput) {\n'
            '    $env:WRENCH_NATIVE_DIRECT_INPUT = "1"\n'
            '} else {\n'
            '    $env:WRENCH_NATIVE_DIRECT_INPUT = "0"\n'
            '}\n'
            '$env:WRENCH_ALLOWED_ROOT = (Resolve-Path -LiteralPath $AllowedRoot).Path\n'
            '$env:WRENCH_EMBEDDED_MECHANICAL_ROUTE = "1"',
        )
        launcher_text = launcher_text.replace(
            '$env:WRENCH_EMBEDDED_MECHANICAL_ROUTE = "1"',
            '$env:WRENCH_EMBEDDED_MECHANICAL_ROUTE = "1"\n'
            'if ($FastHistory) {\n'
            '    if ($FastHistoryKeepTokens -lt 1 -or $FastHistoryKeepTokens -ge 4000000) {\n'
            '        throw "FastHistoryKeepTokens must be between 1 and 3999999"\n'
            '    }\n'
            '    $env:WRENCH_HISTORY_SKIP_LAYERS_BEFORE = "auto"\n'
            '    $env:WRENCH_HISTORY_SKIP_KEEP_TOKENS = "$FastHistoryKeepTokens"\n'
            '    $env:WRENCH_HISTORY_CONTROL_PREFIX_TOKENS = "$FastHistoryControlPrefixTokens"\n'
            '    $env:WRENCH_HISTORY_CONTROL_SUFFIX = "1"\n'
            '    $env:WRENCH_HISTORY_CONTROL_SUFFIX_CHARS = "16000"\n'
            '}',
        )
        launcher_text = launcher_text.replace(
            '    [int]$FastHistoryControlPrefixTokens = 4096\n',
            '    [int]$FastHistoryControlPrefixTokens = 4096,\n'
            '    [switch]$OllamaApi,\n'
            '    [int]$NativePort = 28901,\n'
            '    [int]$UpstreamTimeoutSeconds = 9\n',
        )
        # Optional Ollama API mode keeps the native backend private to the
        # downloaded model directory. The package-local server owns the public
        # API and verifies native text before returning it.
        launcher_head, launcher_marker, _launcher_tail = launcher_text.partition(
            '& $FreeTokenExecutable serve `\n'
        )
        if not launcher_marker:
            raise RuntimeError("generated FreeToken launcher command not found")
        launcher_text = launcher_head + launcher_marker.replace(
            '& $FreeTokenExecutable serve `\n',
            '$nativeServePort = if ($OllamaApi) { $NativePort } else { $Port }\n'
            '$nativeArguments = @(\n'
            '    "serve",\n'
            '    "--model", $PSScriptRoot,\n'
            '    "--host", "127.0.0.1",\n'
            '    "--port", $nativeServePort,\n'
            '    "--served-model-name", "wrench-4b-qwen3.6-8e",\n'
            '    "--moe-strategy", $MoeStrategy,\n'
            '    "--expert-load", "serial",\n'
            '    "--num-tokenizer", 0,\n'
            '    "--kv-reserve-tokens", $KvReserveTokens,\n'
            '    "--num-tokens", 4000000,\n'
            '    "--max-running-requests", 1,\n'
            '    "--max-seq-len-override", 4000000,\n'
            '    "--max-prefill-length", 32768,\n'
            '    "--memory-ratio", 0.9,\n'
            '    "--text-model-only",\n'
            '    "--cache-type", "radix",\n'
            '    "--tool-call-parser", "qwen",\n'
            '    "--reasoning-parser", "off"\n'
            ')\n'
            'if ($MoeCacheSize -gt 0) {\n'
            '    if ($MoeCacheSize -lt 16) { throw "MoeCacheSize must be at least 16 for the 8-expert Wrench package" }\n'
            '    $nativeArguments += @("--moe-cache-size", $MoeCacheSize)\n'
            '} else {\n'
            '    $nativeArguments += "--moe-cache-auto"\n'
            '}\n'
            'if ($MoeCpuLayers) {\n'
            '    $nativeArguments += @("--moe-cpu-layers", $MoeCpuLayers)\n'
            '}\n'
            'if ($MoeCpuThreads -gt 0) {\n'
            '    $nativeArguments += @("--moe-cpu-threads", $MoeCpuThreads)\n'
            '}\n'
            'if ($MoeStrategy -eq "hybrid" -and $MoeHybridMaxFetch -ge 0) {\n'
            '    $nativeArguments += @("--moe-hybrid-max-fetch", $MoeHybridMaxFetch)\n'
            '}\n'
            'if (-not $OllamaApi) {\n'
            '    & $FreeTokenExecutable @nativeArguments\n'
            '    exit $LASTEXITCODE\n'
            '}\n'
            '$nativeStdout = Join-Path $PSScriptRoot "native-startup.log"\n'
            '$nativeStderr = Join-Path $PSScriptRoot "native-startup-error.log"\n'
            '$nativeProcess = Start-Process -FilePath $FreeTokenExecutable -ArgumentList $nativeArguments -WindowStyle Hidden -RedirectStandardOutput $nativeStdout -RedirectStandardError $nativeStderr -PassThru\n'
            'try {\n'
            '    $ready = $false\n'
            '    for ($attempt = 0; $attempt -lt 120; $attempt++) {\n'
            '        try {\n'
            '            $smokeBody = @{\n'
            '                model = "wrench-4b-qwen3.6-8e"\n'
            '                messages = @(@{ role = "system"; content = "Return exactly one JSON object and no prose." }, @{ role = "user"; content = "Return a bounded proposal object now." })\n'
            '                max_tokens = 1\n'
            '                temperature = 0\n'
            '                stream = $false\n'
            '            } | ConvertTo-Json -Depth 5 -Compress\n'
            '            $smoke = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$NativePort/v1/chat/completions" -ContentType "application/json" -Body $smokeBody -TimeoutSec 5\n'
            '            $smokeContent = $smoke.choices[0].message.content\n'
            '            if (-not ($smoke.choices -and $smokeContent)) { throw "native smoke response missing completion text" }\n'
            '            $ready = $true\n'
            '            break\n'
            '        } catch {\n'
            '            if ($nativeProcess.HasExited) {\n'
            '                $errorTail = if (Test-Path $nativeStderr) { (Get-Content $nativeStderr -Tail 12 -ErrorAction SilentlyContinue) -join " | " } else { "" }\n'
            '                throw "FreeToken exited before native smoke readiness on port $NativePort. $errorTail"\n'
            '            }\n'
            '            Start-Sleep -Milliseconds 1000\n'
            '        }\n'
            '    }\n'
            '    if (-not $ready) { throw "FreeToken native smoke readiness timeout on port $NativePort" }\n'
            '    if ($UpstreamTimeoutSeconds -lt 1 -or $UpstreamTimeoutSeconds -gt 600) { throw "UpstreamTimeoutSeconds must be between 1 and 600" }\n'
            '    $python = (Get-Command python -ErrorAction Stop).Source\n'
            '    $server = Join-Path $PSScriptRoot "wrench_server.py"\n'
            '    $savedPythonPath = $env:PYTHONPATH\n'
            '    # The native backend needs the FreeToken overlay, but the\n'
            '    # package API process must not auto-import that sitecustomize.\n'
            '    $env:PYTHONPATH = $null\n'
            '    try {\n'
            '        & $python $server --model-dir $PSScriptRoot --allowed-root $AllowedRoot --port $Port --mechanical-only --upstream-url "http://127.0.0.1:$NativePort/v1/chat/completions" --upstream-timeout-seconds $UpstreamTimeoutSeconds --max-request-bytes 536870912\n'
            '        $exitCode = $LASTEXITCODE\n'
            '    } finally {\n'
            '        $env:PYTHONPATH = $savedPythonPath\n'
            '    }\n'
            '} finally {\n'
            '    if ($nativeProcess) {\n'
            '        # FreeToken spawns scheduler/tokenizer children. Kill the\n'
            '        # whole tree even when the parent already exited, otherwise\n'
            '        # a failed Windows startup can leak Torch workers and\n'
            '        # consume the next run''s commit/pagefile budget.\n'
            '        try { & taskkill.exe /PID $nativeProcess.Id /T /F 2>$null | Out-Null } catch { }\n'
            '        Wait-Process -Id $nativeProcess.Id -Timeout 10 -ErrorAction SilentlyContinue\n'
            '    }\n'
            '}\n'
            'exit $exitCode\n',
        )
        launcher_path.write_text(launcher_text, encoding="utf-8")
        readme_path = target / "README.md"
        shutil.copy2(repo_root / "packaging" / "WRENCH_HF_README.md", readme_path)
        readme = readme_path.read_text(encoding="utf-8").replace(
            "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M", huggingface_repo_id
        )
        if quantized_candidate:
            readme = readme.replace(
                "This Hub repository currently contains the safety-calibrated v7 native-2M\n"
                "candidate, distributed as a 4M-declared portable package.",
                "This Hub repository contains the safety-calibrated v7 NVFP4 native-4M\n"
                "candidate, distributed as a 4M-declared portable package.",
            )
            readme = readme.replace(
                "It contains 3,881,244,016 parameters and stays below the 4.25B parameter ceiling.",
                "It contains 3,881,244,016 parameters, uses ModelOpt NVFP4 W4A16 weights, "
                "and stays below the 4.25B parameter ceiling.",
            )
        package_dir_name = huggingface_repo_id.rsplit("/", 1)[-1]
        readme = readme.replace(
            "--local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M",
            f"--local-dir {package_dir_name}",
        )
        readme = readme.replace(
            "./Wrench-4B-Qwen3.6-8E-NVFP4-native4M", f"./{package_dir_name}"
        )
        readme_path.write_text(readme, encoding="utf-8")
        distribution_doc = target / "WRENCH_PORTABLE_DISTRIBUTION.md"
        shutil.copy2(repo_root / "docs" / "WRENCH_PORTABLE_DISTRIBUTION.md", distribution_doc)
        distribution_text = distribution_doc.read_text(encoding="utf-8").replace(
            "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M", "__WRENCH_HF_URL__"
        )
        # Replace the documented package directory as a whole.  A prefix-only
        # replacement would duplicate the suffix when the package name itself
        # already contains `Wrench-4B-Qwen3.6-8E`.
        distribution_text = distribution_text.replace(
            "Wrench-4B-Qwen3.6-8E-NVFP4-native4M", package_dir_name
        ).replace("__WRENCH_HF_URL__", huggingface_repo_id)
        distribution_doc.write_text(distribution_text, encoding="utf-8")
        candidate_identity = (
            "Wrench-4B-Qwen3.6-8E-Safety-v7-NVFP4-native4M"
            if quantized_candidate and native4m_candidate
            else (
                "Wrench-4B-Qwen3.6-8E-Safety-v7-native2M"
                if safety_candidate
                else "Wrench-4B-Qwen3.6-8E-base"
            )
        )
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8").replace(
                "Wrench-4B-Qwen3.6-8E-Safety-v7-native2M", candidate_identity
            ),
            encoding="utf-8",
        )
        shutil.copy2(repo_root / "packaging" / "Modelfile", target / "Modelfile")
        package_manifest = {
            "schema": "wrench.portable-model-package.v1",
            "package_name": "Wrench",
            "release_status": "EXPERIMENTAL_PUBLIC_ARTIFACT",
            "canonical_format": "huggingface-safetensors",
            "verified_total_parameters": PARAMETER_COUNT,
            "hard_parameter_ceiling": PARAMETER_CEILING,
            "model_lineage": "Qwen3.6-35B-A3B -> Wrench 8E structural prune",
            "candidate_identity": candidate_identity,
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
                "embedded_mechanical_route": True,
                "dynamic_staged_prefill": True,
                "model_prefill_budget_tokens": 64000,
            "entrypoint": "tokenization_wrench.py",
            "server_entrypoint": "wrench_server.py",
            "model_calls_for_mechanical_lookup": 0,
            },
            "backends": {
                "transformers": "Transformers >=5.17.0 config/tokenizer verified; full generation backend-dependent",
                "freetoken": (
                    "local experimental backend with ModelOpt NVFP4, pinned 4M KV capacity, and auto expert cache"
                    if quantized_candidate
                    else "local experimental backend"
                ),
                "vllm": "requires registered Wrench architecture",
                "ollama_safetensors": "experimental local import via bundled Modelfile; must be runtime-verified",
                "ollama_gguf": "not verified",
            },
            "publication": {
                "huggingface_repo_id": huggingface_repo_id,
                "public_upload_authorized": True,
                "copy_paste_command": f"hf download {huggingface_repo_id} --local-dir {huggingface_repo_id.rsplit('/', 1)[-1]}",
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
                "toolbelt.py",
                "core.py",
                "wrench_runtime/__init__.py",
                "wrench_runtime/prefill.py",
                "wrench_runtime/toolbelt.py",
                "wrench_runtime/core.py",
                "wrench_runtime/mechanical.py",
                "wrench_runtime/patching.py",
                "wrench_runtime/worker.py",
                "wrench_worker.py",
                "wrench_server.py",
                "run_wrench.ps1",
                "wrench_runtime/sitecustomize.py",
                "wrench_runtime/server.py",
                "wrench-runtime.json",
                "serve_freetoken.ps1",
                "Modelfile",
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
    parser.add_argument(
        "--huggingface-repo-id",
        default="stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M",
        help="Hub repo id embedded in the portable package copy command",
    )
    args = parser.parse_args()
    receipt = materialize(args.source, args.target, args.repo_root, args.huggingface_repo_id)
    print(json.dumps({"status": receipt["status"], "target": receipt["target"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
