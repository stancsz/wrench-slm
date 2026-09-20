from pathlib import Path


def test_materializer_rewrites_copy_command_without_duplicate_suffix(tmp_path):
    from tools.materialize_wrench_portable_package import materialize

    source = tmp_path / "source-native4M"
    target = tmp_path / "Wrench-4B-Qwen3.6-8E-NVFP4-native4M"
    source.mkdir()
    (source / "config.json").write_text("{}\n", encoding="utf-8")
    materialize(source, target, Path.cwd())
    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "--local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M" in readme
    assert "--local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-NVFP4-native4M" not in readme
    assert (
        './Wrench-4B-Qwen3.6-8E-NVFP4-native4M", load_model=False'
        in readme
    )
    assert "native4M-NVFP4-native4M\", load_model=False" not in readme
    launcher = (target / "serve_freetoken.ps1").read_text(encoding="utf-8")
    assert '[string]$FreeTokenExecutable = "ft.exe"' in launcher
    assert "[switch]$FastHistory" in launcher
    assert '$env:WRENCH_HISTORY_SKIP_LAYERS_BEFORE = "auto"' in launcher
    assert '$env:WRENCH_HISTORY_SKIP_KEEP_TOKENS = "$FastHistoryKeepTokens"' in launcher
    assert "$env:WRENCH_HISTORY_CONTROL_SUFFIX = \"1\"" in launcher
    assert '[string]$AllowedRoot = "."' in launcher
    assert '$env:WRENCH_ALLOWED_ROOT = (Resolve-Path -LiteralPath $AllowedRoot).Path' in launcher
    assert launcher.count('[string]$AllowedRoot = "."') == 1
    assert "[switch]$OllamaApi" in launcher
    assert "--upstream-url" in launcher
    assert "--mechanical-only" in launcher
    assert "$env:PYTHONPATH = $null" in launcher
    assert "[int]$MoeCacheSize = 0" in launcher
    assert "MoeCacheSize must be at least 16" in launcher
    assert "[int]$UpstreamTimeoutSeconds = 9" in launcher
    assert "--upstream-timeout-seconds" in launcher
    assert "native smoke response missing completion text" in launcher
    assert "RedirectStandardError" in launcher
    assert "native smoke readiness timeout" in launcher
    assert "Start-Process -FilePath $FreeTokenExecutable" in launcher
    assert "taskkill.exe /PID $nativeProcess.Id /T /F" in launcher
    assert "failed Windows startup can leak Torch workers" in launcher


def test_materializer_is_available_and_does_not_overwrite_by_contract():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert "refusing to overwrite existing target" in script
    assert "copy_cross_volume" in script
    assert "serve_freetoken.ps1" in script
    assert "wrench_toolbelt.py" in script
    assert "runtime_dir / \"toolbelt.py\"" in script
    assert 'tokenizer_config["model_max_length"] = 4_000_000' in script
    assert 'Transformers >=5.17.0 config/tokenizer verified' in script
    assert "EXPERIMENTAL_PUBLIC_ARTIFACT" in script
    assert "MATERIALIZED_PACKAGE_RUNTIME_EMBEDDED" in script
    assert "public_upload_authorized" in script
    assert '"target": str(target.resolve())' in script
    assert "NVFP4-W4A16-ModelOpt" in script
    assert "--huggingface-repo-id" in script


def test_standard_hf_load_verifier_is_metadata_only():
    script = Path("tools/verify_standard_hf_load.py").read_text(encoding="utf-8")
    assert "PASS_STANDARD_HF_CONFIG_TOKENIZER" in script
    assert "--load-weights" in script
    assert "full_weight_load_verified" in script
    assert "full_weight_generation_verified" in script
    assert "native_long_context_quality_verified" in script


def test_materializer_embeds_worker_runtime():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert "wrench_runtime/worker.py" in script
    assert "wrench_runtime/patching.py" in script
    assert "WrenchWorker" in script
    assert "--moe-cache-auto" in script
    assert "--kv-reserve-tokens $KvReserveTokens" in script
    assert "--num-tokens 4000000" in script
    assert '"--num-tokenizer", 0' in script
    assert '"--expert-load", "serial"' in script
    assert '"tokenizer_processes": 0' in script
    assert '"expert_load": "serial"' in script
    assert '$env:OPENBLAS_NUM_THREADS = "1"' in script
    assert '$env:CUDA_MODULE_LOADING = "LAZY"' in script
    assert "WRENCH_EMBEDDED_MECHANICAL_ROUTE" in script
    assert "WRENCH_ALLOWED_ROOT" in script
    assert "dynamic_staged_prefill" in script
    assert "FastHistoryKeepTokens" in script
    assert "WRENCH_HISTORY_SKIP_LAYERS_BEFORE" in script
    assert "WRENCH_HISTORY_SKIP_KEEP_TOKENS" in script
    assert '"fast_history_profile": "opt_in_reference_only"' in script
    assert "OllamaApi" in script
    assert "native smoke response missing completion text" in script


def test_materializer_keeps_toolbelt_distinct_from_verifier():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert 'src" / "wrench_harness" / "toolbelt.py", runtime_dir / "toolbelt.py"' in script
    assert 'src" / "wrench_harness" / "core.py", runtime_dir / "toolbelt.py"' not in script
    wrapper = Path("packaging/wrench_toolbelt.py").read_text(encoding="utf-8")
    assert "from wrench_runtime.toolbelt import *" in wrapper
