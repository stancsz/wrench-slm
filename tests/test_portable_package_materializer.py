from pathlib import Path


def test_materializer_rewrites_copy_command_without_duplicate_suffix(tmp_path):
    from tools.materialize_wrench_portable_package import materialize

    source = tmp_path / "source-native4M"
    target = tmp_path / "Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview"
    source.mkdir()
    (source / "config.json").write_text("{}\n", encoding="utf-8")
    materialize(source, target, Path.cwd())
    readme = (target / "README.md").read_text(encoding="utf-8")
    assert "--local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview" in readme
    assert "Set-Location Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview" in readme
    assert "--local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-NVFP4-native4M" not in readme
    assert (
        './Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview", load_model=False'
        in readme
    )
    assert "native4M-NVFP4-native4M\", load_model=False" not in readme
    launcher = (target / "serve_freetoken.ps1").read_text(encoding="utf-8")
    assert '[string]$FreeTokenExecutable = "ft.cmd"' in launcher
    assert "[switch]$FastHistory" in launcher
    assert "[switch]$DenseNativeGate" in launcher
    assert "[switch]$BypassDenseNativeGate" in launcher
    assert "BypassDenseNativeGate cannot be combined" in launcher
    assert '$env:WRENCH_DENSE_NATIVE_GATE = "1"' in launcher
    assert '$env:WRENCH_DENSE_NATIVE_GATE = "0"' in launcher
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
    assert '[string]$MoeStrategy = "offload"' in launcher
    assert '[string]$MoeCpuLayers = ""' in launcher
    assert '"--moe-strategy", $MoeStrategy' in launcher
    assert '"--moe-cpu-layers", $MoeCpuLayers' in launcher
    assert '"--moe-hybrid-max-fetch", $MoeHybridMaxFetch' in launcher
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
    assert "verify_freetoken_backend.py" in script
    assert "run_claude_code.ps1" in script
    assert "wrench_loopback_blocker.py" in script
    assert "opencode.wrench.json" in script
    assert "dsh-wrench.patch.yml" in script
    assert "wrench_toolbelt.py" in script
    assert "runtime_dir / \"toolbelt.py\"" in script
    assert 'tokenizer_config["model_max_length"] = 4_000_000' in script
    assert 'Transformers >=5.17.0 config/tokenizer verified; packed NVFP4 tensor load requires the FreeToken ModelOpt backend' in script
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
    assert "FAIL_STANDARD_HF_WEIGHT_LOAD" in script
    assert "weight_load_attempted" in script
    assert "weight_load_failure_class" in script
    assert "full_weight_generation_verified" in script
    assert "native_long_context_quality_verified" in script


def test_standard_hf_load_verifier_records_backend_failures():
    script = Path("tools/verify_standard_hf_load.py").read_text(encoding="utf-8")
    assert "standard_weight_load_status" in script
    assert "modelopt_nvfp4_shape_mismatch_or_unsupported_quantization" in script
    assert "return 0 if not args.load_weights" in script


def test_freetoken_native_backend_verifier_is_explicit_about_scope():
    script = Path("tools/verify_freetoken_backend.py").read_text(encoding="utf-8")
    assert "freetoken_modelopt_nvfp4" in script
    assert "PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION" in script
    assert "native_context_capacity_configured" in script
    assert "resource_reserve_maintained" in script
    assert "dense_native_quality_verified" in script
    assert 'taskkill", "/PID", str(process.pid), "/T", "/F"' in script
    assert "probe_payload_tokens" in script
    assert "PASS_DIRECT_RAW_CONTEXT" in script


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
    assert '"raw_input_limit_enforced": True' in script
    assert '"over_limit_behavior": "HTTP_400_fail_closed"' in script
    assert "FastHistoryKeepTokens" in script
    assert "WRENCH_HISTORY_SKIP_LAYERS_BEFORE" in script
    assert "WRENCH_HISTORY_SKIP_KEEP_TOKENS" in script
    assert "first_layer_required_when_enabled" in script
    assert "native_direct_input_enables_gate" in script
    assert "capacity_probe_bypass_switch" in script
    assert '"fast_history_profile": "opt_in_reference_only"' in script
    assert "OllamaApi" in script
    assert "native smoke response missing completion text" in script


def test_materializer_includes_isolated_claude_launcher():
    launcher = Path("packaging/run_claude_code.ps1").read_text(encoding="utf-8")
    blocker = Path("packaging/wrench_loopback_blocker.py").read_text(encoding="utf-8")
    assert 'CLAUDE_CODE_USE_GATEWAY = "1"' in launcher
    assert 'CLAUDE_GATEWAY_ALLOW_LOOPBACK = "1"' in launcher
    assert 'CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT = "1"' in launcher
    assert 'ANTHROPIC_BASE_URL = "http://127.0.0.1:$Port"' in launcher
    assert 'ANTHROPIC_AUTH_TOKEN = "wrench-local-only"' in launcher
    assert '$env:NO_PROXY = "127.0.0.1,localhost"' in launcher
    assert 'wrench_loopback_blocker.py' in launcher
    assert 'Start-Process -FilePath $python.Source' in launcher
    assert '"--allowed-tools"' in launcher
    assert '$claudeArguments += ($AllowedTools -join ",")' in launcher
    assert 'if ($Prompt) { $claudeArguments += $Prompt }' in launcher
    assert 'The external traffic blocker exited' in launcher
    assert 'serve_forever' in blocker
    assert '403 Forbidden' in blocker


def test_materializer_receipt_lists_claude_files():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert '"wrench_loopback_blocker.py"' in script
    assert '"run_claude_code.ps1"' in script


def test_portable_client_configs_declare_model_local_four_million_context():
    opencode = Path("packaging/opencode.wrench.json").read_text(encoding="utf-8")
    dsh = Path("packaging/dsh-wrench.patch.yml").read_text(encoding="utf-8")
    assert '"baseURL": "http://127.0.0.1:28900/v1"' in opencode
    assert '"context": 4000000' in opencode
    assert 'baseURL: http://127.0.0.1:28900/v1' in dsh
    assert "contextWindow: 4000000" in dsh
    assert "wrench-local" in opencode
    assert "wrench-local" in dsh
    assert "apiKey: wrench-local" in dsh


def test_portable_client_smoke_runner_has_fail_closed_receipt_contract():
    runner = Path("tools/smoke_portable_clients.ps1").read_text(encoding="utf-8")
    assert "wrench.portable-client-smoke.v1" in runner
    assert "wrench_server.py" in runner
    assert "--mechanical-only" in runner
    assert "opencode" in runner
    assert "deepseek_harness" in runner
    assert "model_calls" in runner
    assert "claims_not_authorized" in runner
    assert "Stop-Process -Id $serverProcess.Id" in runner


def test_materializer_keeps_toolbelt_distinct_from_verifier():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert 'src" / "wrench_harness" / "toolbelt.py", runtime_dir / "toolbelt.py"' in script
    assert 'src" / "wrench_harness" / "ttc.py", runtime_dir / "ttc.py"' in script
    assert 'src" / "wrench_harness" / "core.py", runtime_dir / "toolbelt.py"' not in script
    wrapper = Path("packaging/wrench_toolbelt.py").read_text(encoding="utf-8")
    assert "from wrench_runtime.toolbelt import *" in wrapper
