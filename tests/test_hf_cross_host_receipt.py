from tools.verify_hf_cross_host_receipt import verify_receipt


SOURCE = "a" * 40
REPO = "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M"
REVISION = "b" * 40


def _receipt(**overrides):
    receipt = {
        "schema": "wrench.huggingface-cross-host-receipt.v1",
        "status": "PASS_HF_PACKAGE_PREFLIGHT",
        "host": "rtx-5060-ti",
        "source_commit": SOURCE,
        "huggingface_repo_id": REPO,
        "huggingface_revision": REVISION,
        "hub_revision_pinned": True,
        "gpu_identity": "RTX 5060 Ti",
        "safetensors_shard_count": 9,
        "package_validation": {
            "status": "PASS_STRUCTURAL_PACKAGE",
            "file_hash_count": 24,
        },
        "mechanical_smoke": {
            "status": "PASS_HF_PACKAGE_MECHANICAL_SMOKE",
            "proposal_status": "accepted",
        },
    }
    receipt.update(overrides)
    return receipt


def test_hf_receipt_passes_with_source_and_hub_pins():
    result = verify_receipt(
        _receipt(),
        expected_source_commit=SOURCE,
        expected_repo_id=REPO,
        expected_revision=REVISION,
    )
    assert result["status"] == "PASS_HF_PACKAGE_RECEIPT"
    assert result["quality_claim"] is False
    assert result["native_attention_claim"] is False


def test_hf_receipt_blocks_revision_mismatch():
    result = verify_receipt(
        _receipt(),
        expected_source_commit=SOURCE,
        expected_repo_id=REPO,
        expected_revision="c" * 40,
    )
    assert result == {
        "status": "BLOCKED_HF_PACKAGE_RECEIPT",
        "reasons": ["huggingface_revision_mismatch"],
    }


def test_hf_receipt_blocks_structural_validation_failure():
    result = verify_receipt(
        _receipt(package_validation={"status": "FAIL_STRUCTURAL_PACKAGE", "file_hash_count": 24}),
        expected_source_commit=SOURCE,
        expected_repo_id=REPO,
        expected_revision=REVISION,
    )
    assert result["status"] == "BLOCKED_HF_PACKAGE_RECEIPT"
    assert result["reasons"] == ["package_validation_not_passed"]
