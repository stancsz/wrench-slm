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
    assert "wrench_toolbelt.py" in manifest["required_files"]
    assert "wrench_runtime/toolbelt.py" in manifest["required_files"]
    assert "wrench_runtime/worker.py" in manifest["required_files"]
    assert "wrench_worker.py" in manifest["required_files"]
    assert manifest["retrieval"]["verifier_is_bundled"] is True
