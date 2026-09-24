from __future__ import annotations

import hashlib

import pytest

import wrench_harness.candidate_identity as candidate_identity
from wrench_harness.candidate_identity import (
    CandidateIdentityError,
    verify_candidate_identity,
)


def _git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _fixture(tmp_path):
    root = tmp_path / "candidate"
    root.mkdir(parents=True)
    files = {
        "config.json": b'{"fixture":true}\n',
        "tokenizer.txt": b"tiny synthetic tokenizer\n",
    }
    for relative, data in files.items():
        (root / relative).write_bytes(data)
    metadata = {
        "schema": "wrench.model-candidate-metadata.v1",
        "status": "SYNTHETIC_FIXTURE_ONLY",
        "model_id": "synthetic/local-identity-test",
        "revision": "a" * 40,
        "repository_bytes": sum(map(len, files.values())),
        "files": [
            {
                "path": "config.json",
                "size_bytes": len(files["config.json"]),
                "upstream_sha256": hashlib.sha256(files["config.json"]).hexdigest(),
                "git_blob_id": _git_blob_id(files["config.json"]),
            },
            {
                "path": "tokenizer.txt",
                "size_bytes": len(files["tokenizer.txt"]),
                "upstream_sha256": None,
                "git_blob_id": _git_blob_id(files["tokenizer.txt"]),
            },
        ],
    }
    return root, files, metadata


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows lacks handle-relative no-follow opens")
def test_verifies_tiny_synthetic_files_and_returns_bounded_receipt(tmp_path):
    root, files, metadata = _fixture(tmp_path)

    receipt = verify_candidate_identity(metadata, root)

    assert receipt["status"] == "VERIFIED_LOCAL_FILES"
    assert receipt["verification_scope"] == "local_file_identity_only_no_model_load"
    assert receipt["revision"] == "a" * 40
    assert receipt["file_count"] == 2
    assert receipt["total_bytes"] == sum(map(len, files.values()))
    assert {row["identity_kind"] for row in receipt["files"]} == {
        "upstream_sha256", "git_blob_id"
    }
    assert len(receipt["receipt_sha256"]) == 64


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows lacks handle-relative no-follow opens")
def test_rejects_changed_file_identity(tmp_path):
    root, _, metadata = _fixture(tmp_path)
    (root / "config.json").write_bytes(b"changed bytes\n")

    with pytest.raises(CandidateIdentityError, match="snapshot_file_size_mismatch|snapshot_identity_mismatch"):
        verify_candidate_identity(metadata, root)


@pytest.mark.parametrize("relative", ["../escape", "/absolute", "C:/drive", "nested//empty"])
def test_rejects_unsafe_metadata_paths(tmp_path, relative):
    root, _, metadata = _fixture(tmp_path)
    metadata["files"][0]["path"] = relative

    with pytest.raises(CandidateIdentityError, match="metadata_path_invalid"):
        verify_candidate_identity(metadata, root)


def test_rejects_duplicate_paths_and_inconsistent_total(tmp_path):
    root, _, metadata = _fixture(tmp_path)
    metadata["files"][1]["path"] = metadata["files"][0]["path"]
    with pytest.raises(CandidateIdentityError, match="metadata_duplicate_path"):
        verify_candidate_identity(metadata, root)

    _, _, metadata = _fixture(tmp_path / "second")
    metadata["repository_bytes"] += 1
    with pytest.raises(CandidateIdentityError, match="metadata_total_mismatch"):
        verify_candidate_identity(metadata, tmp_path / "second" / "candidate")


def test_rejects_manifest_requiring_directory_traversal(tmp_path):
    root, files, metadata = _fixture(tmp_path)
    content = files["tokenizer.txt"]
    (root / "tokenizer.txt").unlink()
    (root / "nested").mkdir()
    (root / "nested" / "tokenizer.txt").write_bytes(content)
    metadata["files"][1]["path"] = "nested/tokenizer.txt"

    with pytest.raises(CandidateIdentityError, match="directory_manifest_requires_handle_relative_traversal"):
        verify_candidate_identity(metadata, root)


@pytest.mark.parametrize("mutation, expected", [
    ("missing", "snapshot_file_set_mismatch"),
    ("extra", "snapshot_unexpected_entry"),
])
@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows lacks handle-relative no-follow enumeration")
def test_rejects_missing_and_unexpected_files(tmp_path, mutation, expected):
    root, _, metadata = _fixture(tmp_path)
    if mutation == "missing":
        (root / "config.json").unlink()
    else:
        (root / "extra.bin").write_bytes(b"not admitted")

    with pytest.raises(CandidateIdentityError, match=expected):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows lacks handle-relative no-follow enumeration")
def test_rejects_symlinked_snapshot_entry(tmp_path):
    root, _, metadata = _fixture(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("synthetic", encoding="utf-8")
    try:
        (root / "linked.txt").symlink_to(outside)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink privilege is unavailable")
        raise

    with pytest.raises(CandidateIdentityError, match="snapshot_link_forbidden"):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows lacks handle-relative no-follow opens")
def test_rejects_open_handle_resolved_outside_expected_snapshot(tmp_path, monkeypatch):
    root, _, metadata = _fixture(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(candidate_identity, "_opened_path", lambda _fd: outside)

    with pytest.raises(CandidateIdentityError, match="snapshot_path_changed"):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows fails closed before opening files")
def test_fails_closed_when_open_handle_path_is_unavailable(tmp_path, monkeypatch):
    root, _, metadata = _fixture(tmp_path)

    def unavailable(_fd):
        raise CandidateIdentityError("snapshot_handle_path_unavailable")

    monkeypatch.setattr(candidate_identity, "_opened_path", unavailable)
    with pytest.raises(CandidateIdentityError, match="snapshot_handle_path_unavailable"):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows fails closed before opening files")
def test_root_handle_must_match_initially_observed_directory(tmp_path):
    root, _, _ = _fixture(tmp_path)
    other = tmp_path / "other"
    other.mkdir()

    with pytest.raises(CandidateIdentityError, match="snapshot_root_changed"):
        candidate_identity._open_root_chain(root, other.stat())


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows fails closed before opening files")
def test_child_entry_inode_must_match_relative_nofollow_stat(tmp_path, monkeypatch):
    root, _, metadata = _fixture(tmp_path)
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"different synthetic file")
    original_stat_child_at = candidate_identity._stat_child_at

    def swapped_stat_child_at(root_fd, name):
        if name == "config.json":
            return replacement.stat()
        return original_stat_child_at(root_fd, name)

    monkeypatch.setattr(candidate_identity, "_stat_child_at", swapped_stat_child_at)
    with pytest.raises(CandidateIdentityError, match="snapshot_entry_changed"):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name == "nt", reason="Windows fails closed before opening files")
def test_rejects_path_replacement_after_file_hash(tmp_path, monkeypatch):
    root, files, metadata = _fixture(tmp_path)
    replacement = tmp_path / "replacement"
    original = files["config.json"]
    replacement.write_bytes(b"X" * len(original))
    original_stat_child_at = candidate_identity._stat_child_at
    config_calls = 0

    def replace_after_hash(root_fd, name):
        nonlocal config_calls
        if name == "config.json":
            config_calls += 1
            if config_calls == 2:
                (root / name).unlink()
                replacement.rename(root / name)
        return original_stat_child_at(root_fd, name)

    monkeypatch.setattr(candidate_identity, "_stat_child_at", replace_after_hash)
    with pytest.raises(CandidateIdentityError, match="snapshot_path_changed"):
        verify_candidate_identity(metadata, root)


@pytest.mark.skipif(candidate_identity.os.name != "nt", reason="Windows-only fail-closed contract")
def test_windows_fails_closed_without_handle_relative_nofollow(tmp_path):
    root, _, metadata = _fixture(tmp_path)

    with pytest.raises(CandidateIdentityError, match="handle_relative_no_follow_unavailable"):
        verify_candidate_identity(metadata, root)


def test_rejects_wrong_schema_and_oversized_receipt_inputs(tmp_path):
    root, _, metadata = _fixture(tmp_path)
    metadata["schema"] = "other"
    with pytest.raises(CandidateIdentityError, match="metadata_schema_invalid"):
        verify_candidate_identity(metadata, root)

    _, _, metadata = _fixture(tmp_path / "second")
    metadata["files"] *= 33
    with pytest.raises(CandidateIdentityError, match="metadata_file_count_invalid"):
        verify_candidate_identity(metadata, tmp_path / "second" / "candidate")


def test_rejects_oversized_extra_metadata_before_canonical_serialization(tmp_path):
    root, _, metadata = _fixture(tmp_path)
    metadata["extra"] = "x" * 300_000

    with pytest.raises(CandidateIdentityError, match="metadata_string_limit_exceeded"):
        verify_candidate_identity(metadata, root)
