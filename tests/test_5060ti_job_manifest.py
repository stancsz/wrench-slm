from __future__ import annotations

from tools.build_5060ti_job_manifest import build_manifest


def test_manifest_is_self_contained_and_requires_host_reserves():
    manifest = build_manifest(
        source_commit="a" * 40,
        hf_revision="b" * 40,
        job_id="test-5060-job",
    )

    assert manifest["schema"] == "wrench.worker-job.v1"
    assert manifest["state"] == "pending"
    assert len(manifest["claim_nonce"]) == 32
    assert manifest["target"]["host_name"] == "DESKTOP-KET1SKP"
    assert manifest["resource_requirements"]["minimum_host_ram_free_fraction"] == 0.1
    assert manifest["resource_requirements"]["minimum_host_vram_free_fraction"] == 0.1
    assert manifest["boundaries"]["provider_spending"] is False
    assert manifest["boundaries"]["mutation_authority"] is False
    assert "a" * 40 in manifest["execution"]["command"]
    assert "b" * 40 in manifest["execution"]["command"]
    assert "claim_nonce" in manifest["required_receipt"]["must_echo"]


def test_manifest_can_bind_a_case_hash(tmp_path):
    cases = tmp_path / "cases.jsonl"
    cases.write_bytes(b'{"id":"one"}\r\n')
    manifest = build_manifest(
        source_commit="a" * 40,
        hf_revision="b" * 40,
        job_id="test-5060-cases",
        cases_path=cases,
    )

    assert manifest["inputs"]["cases"]["canonical_sha256"]
    assert manifest["inputs"]["raw_teacher_trace_upload"] is False
