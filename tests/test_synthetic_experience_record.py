from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import inspect

import pytest

from wrench_harness.synthetic_experience_record import (
    SCHEMA,
    SyntheticExperienceRecordError,
    build_synthetic_experience_record,
    validate_synthetic_experience_record,
)


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "e0_synthetic_matched_tasks_v1"
MANIFEST = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
MANIFEST_SHA256 = (FIXTURE / "manifest.sha256").read_text(encoding="ascii").split()[0]
REVIEW_PATH = MANIFEST["admission"]["review"]["receipt_path"]
REVIEW_BYTES = (ROOT / REVIEW_PATH).read_bytes()
CASES = {
    case["case_id"]: (case, pair["group"])
    for pair in MANIFEST["pairs"]
    for case in pair["cases"]
}


def _build(case_id: str, candidate: object | None):
    return build_synthetic_experience_record(
        MANIFEST,
        manifest_sha256=MANIFEST_SHA256,
        review_receipt_path=REVIEW_PATH,
        review_receipt_bytes=REVIEW_BYTES,
        case_id=case_id,
        candidate_answer=candidate,
    )


def _validate(record):
    return validate_synthetic_experience_record(
        record,
        manifest=MANIFEST,
        manifest_sha256=MANIFEST_SHA256,
        review_receipt_path=REVIEW_PATH,
        review_receipt_bytes=REVIEW_BYTES,
    )


def test_match_record_is_canonical_content_free_and_valid():
    case, group = CASES["loc-a"]
    expected = case["answer_oracle"]["expected"]
    record = _build("loc-a", expected)

    payload = json.loads(record.payload_json)
    assert payload["schema"] == SCHEMA
    assert payload["comparison"] == "match"
    assert payload["candidate_sha256"] == payload["oracle_sha256"]
    assert payload["case_group"] == group
    assert payload["training_eligible"] is False
    assert payload["candidate_origin"] == "caller_supplied_untrusted"
    assert "prompt" not in payload and "path" not in payload
    assert "token_expiry_guard" not in record.payload_json
    assert _validate(record).valid


def test_mismatch_and_unknown_are_comparison_states_not_outcomes():
    mismatch = json.loads(_build("loc-a", {"status": "completed"}).payload_json)
    unknown = json.loads(_build("loc-a", None).payload_json)
    assert mismatch["comparison"] == "mismatch"
    assert "outcome" not in mismatch and "verified" not in mismatch
    assert unknown["comparison"] == "unknown"
    assert unknown["candidate_sha256"] is None


def test_candidate_content_and_paths_are_only_hashed():
    candidate = {"path": "private/source.py", "observation": "secret fixture text"}
    record = _build("loc-a", candidate)
    assert "private/source.py" not in record.payload_json
    assert "secret fixture text" not in record.payload_json
    assert json.loads(record.payload_json)["comparison"] == "mismatch"


def test_builder_is_bound_to_pinned_manifest_case_and_review():
    altered = json.loads(json.dumps(MANIFEST))
    altered["pairs"][0]["cases"][0]["files"][0]["content_utf8"] += "changed"
    altered_digest = hashlib.sha256(json.dumps(
        altered, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")).hexdigest()
    with pytest.raises(SyntheticExperienceRecordError, match="fixture_not_admitted"):
        build_synthetic_experience_record(
            altered,
            manifest_sha256=altered_digest,
            review_receipt_path=REVIEW_PATH,
            review_receipt_bytes=REVIEW_BYTES,
            case_id="loc-a",
            candidate_answer=CASES["loc-a"][0]["answer_oracle"]["expected"],
        )
    with pytest.raises(SyntheticExperienceRecordError, match="case_id_unknown_or_duplicated"):
        _build("unknown-case", {})
    with pytest.raises(SyntheticExperienceRecordError, match="fixture_not_admitted"):
        build_synthetic_experience_record(
            MANIFEST,
            manifest_sha256=MANIFEST_SHA256,
            review_receipt_path=REVIEW_PATH,
            review_receipt_bytes=b"wrong review",
            case_id="loc-a",
            candidate_answer={},
        )


def test_record_validator_rejects_training_claims_and_mutated_oracle_identity():
    record = _build("loc-a", CASES["loc-a"][0]["answer_oracle"]["expected"])
    payload = json.loads(record.payload_json)
    payload["training_eligible"] = True
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    forged = replace(record, payload_json=encoded, sha256=hashlib.sha256(encoded.encode()).hexdigest())
    result = _validate(forged)
    assert not result.valid
    assert "training_eligible_not_allowed" in result.errors

    payload = json.loads(record.payload_json)
    payload["oracle_sha256"] = "0" * 64
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    forged = replace(record, payload_json=encoded, sha256=hashlib.sha256(encoded.encode()).hexdigest())
    result = _validate(forged)
    assert not result.valid
    assert "oracle_digest_mismatch" in result.errors


def test_validator_rejects_noncanonical_or_corrupted_record_digest():
    record = _build("loc-a", None)
    assert not _validate(replace(record, sha256="0" * 64)).valid
    pretty = json.dumps(json.loads(record.payload_json), indent=2)
    result = _validate(replace(record, payload_json=pretty))
    assert not result.valid
    assert "record_not_canonical" in result.errors


def test_candidate_is_json_bounded_and_builder_has_no_usage_override():
    with pytest.raises(SyntheticExperienceRecordError, match="json_byte_limit_exceeded|string_invalid_or_too_large"):
        _build("loc-a", {"large": "x" * 9000})
    with pytest.raises(SyntheticExperienceRecordError, match="unsupported_json_type"):
        _build("loc-a", object())
    params = inspect.signature(build_synthetic_experience_record).parameters
    assert "requested_usage" not in params
    assert "training_eligible" not in params
