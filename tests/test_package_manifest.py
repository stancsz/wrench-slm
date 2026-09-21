import json
from pathlib import Path


def test_portable_manifest_keeps_native_and_effective_context_separate():
    manifest = json.loads(Path("packaging/wrench-package-manifest.json").read_text(encoding="utf-8"))
    context = manifest["context"]
    assert context["declared_input_context_tokens"] == 4_000_000
    assert context["native_attention_context_tokens_target"] == 2_000_000
    assert context["native_attention_context_tokens_verified"] is None
    assert context["effective_working_context_tokens_default"] == 64_000
    assert manifest["publication"]["public_upload_authorized"] is True
    assert manifest["publication"]["huggingface_repo_id"] == "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview"
    assert "NVFP4-native4M" in manifest["publication"]["copy_paste_command"]
    assert "wrench_toolbelt.py" in manifest["required_files"]
    assert "wrench_runtime/toolbelt.py" in manifest["required_files"]
    assert "wrench_runtime/worker.py" in manifest["required_files"]
    assert "wrench_worker.py" in manifest["required_files"]
    assert manifest["retrieval"]["verifier_is_bundled"] is True
    assert manifest["retrieval"]["embedded_mechanical_route"] is True
    assert manifest["retrieval"]["dynamic_staged_prefill"] is True
    assert manifest["retrieval"]["model_prefill_budget_tokens"] == 64_000
    gate = manifest["retrieval"]["context_gate"]
    assert gate["stage"] == "first_model_side_pruner_cherrypicker"
    assert gate["declared_raw_input_context_tokens"] == 4_000_000
    assert gate["effective_working_context_tokens"] == 64_000
    assert gate["dense_native_gate"] == "conditional_optional"
