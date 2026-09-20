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
    assert "WRENCH_EMBEDDED_MECHANICAL_ROUTE" in script
    assert "dynamic_staged_prefill" in script


def test_materializer_keeps_toolbelt_distinct_from_verifier():
    script = Path("tools/materialize_wrench_portable_package.py").read_text(encoding="utf-8")
    assert 'src" / "wrench_harness" / "toolbelt.py", runtime_dir / "toolbelt.py"' in script
    assert 'src" / "wrench_harness" / "core.py", runtime_dir / "toolbelt.py"' not in script
    wrapper = Path("packaging/wrench_toolbelt.py").read_text(encoding="utf-8")
    assert "from wrench_runtime.toolbelt import *" in wrapper
