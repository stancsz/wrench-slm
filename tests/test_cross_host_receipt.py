from tools.verify_cross_host_receipt import verify_receipt


SOURCE = "a" * 40
ARTIFACT = "b" * 40
MANIFEST = "c" * 64


def _receipt(**overrides):
    receipt = {
        "schema": "wrench.cross-host-receipt.v1",
        "host": "rtx-5060-ti",
        "source_commit": SOURCE,
        "artifact_commit": ARTIFACT,
        "artifact_manifest_sha256": MANIFEST,
        "artifact_hash_verified": True,
        "runtime_identity": "freetoken-test",
        "gpu_identity": "RTX 5060 Ti",
        "metrics": {"load_seconds": 12.5, "peak_memory_bytes": 123456},
    }
    receipt.update(overrides)
    return receipt


def test_cross_host_receipt_passes_with_matching_pins():
    result = verify_receipt(
        _receipt(),
        expected_source_commit=SOURCE,
        expected_artifact_commit=ARTIFACT,
    )
    assert result["status"] == "PASS_CROSS_HOST_RECEIPT"
    assert result["latency_scope"] == "host_specific_not_cross_host_comparable"


def test_cross_host_receipt_accepts_structured_runtime_identity():
    result = verify_receipt(
        _receipt(runtime_identity={"python": "3.12.11", "torch": "2.11.0+cu130"}),
        expected_source_commit=SOURCE,
        expected_artifact_commit=ARTIFACT,
    )
    assert result["status"] == "PASS_CROSS_HOST_RECEIPT"


def test_cross_host_receipt_blocks_commit_mismatch():
    result = verify_receipt(
        _receipt(source_commit="d" * 40),
        expected_source_commit=SOURCE,
        expected_artifact_commit=ARTIFACT,
    )
    assert result == {
        "status": "BLOCKED_CROSS_HOST_RECEIPT",
        "reasons": ["source_commit_mismatch"],
    }


def test_cross_host_receipt_blocks_unverified_artifact():
    result = verify_receipt(
        _receipt(artifact_hash_verified=False),
        expected_source_commit=SOURCE,
        expected_artifact_commit=ARTIFACT,
    )
    assert result["status"] == "BLOCKED_CROSS_HOST_RECEIPT"
    assert result["reasons"] == ["artifact_hash_not_verified"]
