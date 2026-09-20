from pathlib import Path


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
