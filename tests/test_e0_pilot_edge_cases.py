from __future__ import annotations

import builtins
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from wrench_harness.e0_rule_route import RuleRouteStatus, run_e0_rule_route
from wrench_harness.snapshot import bind_source_root, create_snapshot
from wrench_harness.synthetic_experience_record import (
    SyntheticExperienceRecordError,
    build_synthetic_experience_record,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "e0_pilot_edge_cases_v1"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
SIDECAR_PATH = FIXTURE_DIR / "manifest.sha256"
EXPECTED_MANIFEST_SHA256 = "63d21349dc1c4e1075618f37642f281149d9d6538400659d82ab8e842d693016"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _run_case(case: dict[str, Any], tmp_path: Path):
    root = tmp_path / case["case_id"]
    root.mkdir()
    for item in case["files"]:
        path = root.joinpath(*item["path"].split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item["content_utf8"].encode("utf-8"))

    binding = bind_source_root(root)
    snapshot = create_snapshot(binding, [item["path"] for item in case["files"]])
    mutation = case.get("mutation")
    if mutation is not None:
        changed_path = root.joinpath(*mutation["path"].split("/"))
        changed_path.write_bytes(mutation["content_utf8"].encode("utf-8"))
    return run_e0_rule_route(case["prompt"], root_binding=binding, snapshot=snapshot)


def test_fixture_identity_hashes_and_test_only_admission_labels_are_frozen():
    manifest = _manifest()
    sidecar_hash, filename = SIDECAR_PATH.read_text(encoding="ascii").strip().split()
    assert filename == MANIFEST_PATH.name
    assert sidecar_hash == EXPECTED_MANIFEST_SHA256
    assert sidecar_hash == hashlib.sha256(_canonical_bytes(manifest)).hexdigest()
    assert manifest["schema"] == "wrench.synthetic-e0-pilot-edge-cases.v1"
    assert manifest["provenance"] == "wrench_authored_synthetic_only"
    assert manifest["usage"] == "open_development_test_only"
    assert manifest["sealed"] is False
    assert manifest["final"] is False
    assert manifest["experience_record_eligible"] is False
    assert manifest["training_eligible"] is False
    assert manifest["utility_eligible"] is False
    assert manifest["not_a_utility_claim"] is True

    case_ids = [case["case_id"] for case in manifest["cases"]]
    assert len(case_ids) == len(set(case_ids)) == 6
    assert {case["repository_id"] for case in manifest["cases"]} == {
        "synthetic-py-cache", "synthetic-ts-cache"
    }
    assert {case["language"] for case in manifest["cases"]} == {"python", "typescript"}
    for case in manifest["cases"]:
        for source in case["files"]:
            assert hashlib.sha256(source["content_utf8"].encode("utf-8")).hexdigest() == source["sha256"]
        mutation = case.get("mutation")
        if mutation is not None:
            assert hashlib.sha256(mutation["content_utf8"].encode("utf-8")).hexdigest() == mutation["sha256"]


def test_edge_case_fixture_is_rejected_by_pinned_experience_record_path():
    manifest = _manifest()
    digest = SIDECAR_PATH.read_text(encoding="ascii").split()[0]
    with pytest.raises(SyntheticExperienceRecordError, match="fixture_not_admitted:fixture_identity_mismatch"):
        build_synthetic_experience_record(
            manifest,
            manifest_sha256=digest,
            review_receipt_path="docs/evals/wrench-e0-pilot-edge-cases/review.md",
            review_receipt_bytes=b"synthetic edge-case mechanics only",
            case_id="py-exact-near-search",
            candidate_answer=None,
        )


@pytest.mark.parametrize("case_id", [
    "py-exact-near-search",
    "ts-exact-near-search",
    "ts-multifile-triage-search",
    "py-stale-after-snapshot",
    "py-missing-evidence",
    "ts-injection-is-data",
])
def test_edge_cases_match_only_supported_snapshot_route_mechanics(case_id: str, tmp_path: Path):
    case = next(item for item in _manifest()["cases"] if item["case_id"] == case_id)
    expected = case["expected"]
    result = _run_case(case, tmp_path)

    assert result.status.value == expected["status"]
    assert result.action == expected["action"]
    assert result.route == "none"
    if expected["status"] == "completed":
        assert result.status is RuleRouteStatus.COMPLETED
        assert result.reason is None
        assert result.observation is not None
        if expected["action"] == "literal_search":
            assert result.observation["matches"] == expected["matches"]
            assert result.observation["truncated"] is False
            assert result.observation["scope"] == "supplied_snapshot_sources"
        else:
            assert result.observation["path"] == expected["observation_path"]
            assert result.observation["text"] == next(
                source["content_utf8"] for source in case["files"]
                if source["path"] == expected["observation_path"]
            )
        assert [row.path for row in result.evidence] == expected["evidence_paths"]
        assert result.unknown_evidence == ()
    else:
        assert result.status is RuleRouteStatus.ABSTAIN
        assert result.reason == expected["reason"]
        assert result.observation is None
        assert [row.path for row in result.unknown_evidence] == expected["unknown_paths"]

    if "exact_read_attempts" in expected:
        assert result.exact_read_attempts == expected["exact_read_attempts"]


def test_injection_bytes_cannot_expand_snapshot_scope_or_invoke_execution_tripwires(tmp_path, monkeypatch):
    case = next(item for item in _manifest()["cases"] if item["case_id"] == "ts-injection-is-data")

    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic repository bytes invoked a process or code executor")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    if hasattr(os, "execv"):
        monkeypatch.setattr(os, "execv", forbidden)
    monkeypatch.setattr(builtins, "eval", forbidden)
    monkeypatch.setattr(builtins, "exec", forbidden)

    result = _run_case(case, tmp_path)
    assert result.status is RuleRouteStatus.COMPLETED
    assert result.action == "read_file"
    assert result.route == "none"
    assert result.observation["path"] == "docs/notes.md"
    assert [row.path for row in result.evidence] == ["docs/notes.md"]
    assert result.exact_read_attempts == 1
    assert "SYNTHETIC_SECRET_SENTINEL_DO_NOT_RETURN" not in result.observation["text"]
