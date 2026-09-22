from tools.verify_hf_cross_host_receipt import verify_receipt
from tools.compose_hf_cross_host_receipt import compose_receipt, git_head


SOURCE = "a" * 40
REPO = "stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview"
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


def test_hf_receipt_passes_when_nonce_and_host_are_bound():
    result = verify_receipt(
        _receipt(job_id="job-1", claim_nonce="nonce-1", host_name="DESKTOP-KET1SKP"),
        expected_source_commit=SOURCE,
        expected_repo_id=REPO,
        expected_revision=REVISION,
        expected_job_id="job-1",
        expected_claim_nonce="nonce-1",
        expected_host_name="DESKTOP-KET1SKP",
    )
    assert result["status"] == "PASS_HF_PACKAGE_RECEIPT"


def test_hf_receipt_blocks_nonce_mismatch():
    result = verify_receipt(
        _receipt(job_id="job-1", claim_nonce="wrong", host_name="DESKTOP-KET1SKP"),
        expected_source_commit=SOURCE,
        expected_repo_id=REPO,
        expected_revision=REVISION,
        expected_job_id="job-1",
        expected_claim_nonce="nonce-1",
        expected_host_name="DESKTOP-KET1SKP",
    )
    assert result["reasons"] == ["claim_nonce_mismatch"]


def test_composer_echoes_nonce_and_actual_host(tmp_path):
    source_root = __import__("pathlib").Path.cwd()
    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "model.safetensors").write_bytes(b"weights")
    validation = tmp_path / "validation.json"
    validation.write_text(
        '{"status":"PASS_STRUCTURAL_PACKAGE","config_max_position_embeddings":4000000,"file_hashes":{"model":"x"}}',
        encoding="utf-8",
    )
    smoke = tmp_path / "smoke.json"
    smoke.write_text(
        '{"status":"PASS_HF_PACKAGE_MECHANICAL_SMOKE","proposal_status":"accepted"}',
        encoding="utf-8",
    )
    resources = tmp_path / "resources.json"
    resources.write_text(
        '{"status":"PASS_HOST_RESOURCE_RESERVE","before_download":{"ram_free_fraction":0.5,"gpus":[{"free_fraction":0.5}]},"after_download":{"ram_free_fraction":0.5,"gpus":[{"free_fraction":0.5}]}}',
        encoding="utf-8",
    )

    receipt = compose_receipt(
        host="rtx-5060-ti",
        source_root=source_root,
        source_commit=git_head(source_root),
        repo_id=REPO,
        revision=REVISION,
        package_root=package_root,
        validation_path=validation,
        smoke_path=smoke,
        resource_snapshot_path=resources,
        gpu_identity="NVIDIA GeForce RTX 5060 Ti",
        job_id="job-1",
        claim_nonce="nonce-1",
        host_name="DESKTOP-KET1SKP",
    )

    assert receipt["job_id"] == "job-1"
    assert receipt["claim_nonce"] == "nonce-1"
    assert receipt["host_name"] == "DESKTOP-KET1SKP"


def test_composer_accepts_windows_powershell_utf8_bom_receipts(tmp_path):
    source_root = __import__("pathlib").Path.cwd()
    package_root = tmp_path / "package"
    package_root.mkdir()
    (package_root / "model.safetensors").write_bytes(b"weights")
    validation = tmp_path / "validation.json"
    validation.write_text(
        '{"status":"PASS_STRUCTURAL_PACKAGE","file_hashes":{"model":"x"}}',
        encoding="utf-8-sig",
    )
    smoke = tmp_path / "smoke.json"
    smoke.write_text(
        '{"status":"PASS_HF_PACKAGE_MECHANICAL_SMOKE","proposal_status":"accepted"}',
        encoding="utf-8-sig",
    )
    resources = tmp_path / "resources.json"
    resources.write_text(
        '{"status":"PASS_HOST_RESOURCE_RESERVE","before_download":{"ram_free_fraction":0.5,"gpus":[{"free_fraction":0.5}]},"after_download":{"ram_free_fraction":0.5,"gpus":[{"free_fraction":0.5}]}}',
        encoding="utf-8-sig",
    )

    receipt = compose_receipt(
        host="rtx-5060-ti",
        source_root=source_root,
        source_commit=git_head(source_root),
        repo_id=REPO,
        revision=REVISION,
        package_root=package_root,
        validation_path=validation,
        smoke_path=smoke,
        resource_snapshot_path=resources,
        gpu_identity="NVIDIA GeForce RTX 5060 Ti",
    )

    assert receipt["status"] == "PASS_HF_PACKAGE_PREFLIGHT"


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
