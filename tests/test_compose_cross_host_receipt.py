import json
import subprocess

import pytest

from tools.compose_cross_host_receipt import verify_artifact_manifest


def test_verify_artifact_manifest_hashes_declared_files(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    payload = artifact / "model.bin"
    payload.write_bytes(b"weights")
    digest = __import__("hashlib").sha256(b"weights").hexdigest()
    manifest = artifact / "artifact-manifest.json"
    manifest.write_text(
        json.dumps({"files": [{"path": "model.bin", "bytes": 7, "sha256": digest}]}),
        encoding="utf-8",
    )
    assert len(verify_artifact_manifest(artifact, manifest)) == 64


def test_verify_artifact_manifest_rejects_tampering(tmp_path):
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    payload = artifact / "model.bin"
    payload.write_bytes(b"weights")
    manifest = artifact / "artifact-manifest.json"
    manifest.write_text(
        json.dumps({"files": [{"path": "model.bin", "bytes": 7, "sha256": "0" * 64}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="artifact manifest verification failed"):
        verify_artifact_manifest(artifact, manifest)
