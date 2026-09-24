"""Content-free regression records for the one pinned synthetic fixture.

These records compare a caller-supplied candidate with a frozen fixture oracle.
They do not authenticate route execution, admit learning data, or authorize
training. Only references and digests leave this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any

from .synthetic_fixture_admission import (
    SUPPORTED_MANIFEST_SHA256,
    SUPPORTED_PROVENANCE,
    SUPPORTED_REVIEW_PATH,
    SUPPORTED_USAGE,
    validate_synthetic_fixture_admission,
)


SCHEMA = "wrench.synthetic-experience-record.v1"
MAX_CANDIDATE_BYTES = 8 * 1024
MAX_RECORD_BYTES = 16 * 1024
MAX_NODES = 4096
MAX_DEPTH = 16
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_GROUPS = frozenset({
    "localization",
    "failing_test_log_triage",
    "context_selection",
    "missing_stale_ambiguous_evidence",
})
_ORACLE_KINDS = frozenset({
    "function_for_attribute",
    "log_error_type",
    "literal_paths",
    "availability",
    "ambiguous_sources",
    "config_value",
})
_FIELDS = frozenset({
    "schema", "provenance", "usage", "split", "record_scope", "case_id",
    "case_group", "oracle_kind", "manifest_sha256", "review_receipt_sha256",
    "oracle_sha256", "candidate_sha256", "comparison", "candidate_origin",
    "consent_basis", "training_eligible",
})


class SyntheticExperienceRecordError(ValueError):
    """Raised when fixture identity or bounded record structure is invalid."""


@dataclass(frozen=True)
class SyntheticExperienceRecord:
    """Canonical content-free record and its digest."""

    payload_json: str
    sha256: str


@dataclass(frozen=True)
class SyntheticExperienceRecordResult:
    """Validation result for a caller-supplied record."""

    valid: bool
    errors: tuple[str, ...] = ()


def _json_bytes(value: object, *, limit: int) -> bytes:
    """Validate JSON-only input under traversal bounds before encoding."""
    nodes = 0
    active: set[int] = set()

    def visit(item: object, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise SyntheticExperienceRecordError("json_shape_limit")
        if item is None or type(item) is bool:
            return
        if type(item) is int:
            if item.bit_length() > 64:
                raise SyntheticExperienceRecordError("integer_out_of_range")
            return
        if type(item) is float:
            if not math.isfinite(item):
                raise SyntheticExperienceRecordError("nonfinite_number")
            return
        if type(item) is str:
            if len(item) > limit or any(0xD800 <= ord(char) <= 0xDFFF for char in item):
                raise SyntheticExperienceRecordError("string_invalid_or_too_large")
            return
        if type(item) not in (dict, list):
            raise SyntheticExperienceRecordError("unsupported_json_type")
        identity = id(item)
        if identity in active:
            raise SyntheticExperienceRecordError("json_cycle")
        if len(item) > MAX_NODES:
            raise SyntheticExperienceRecordError("json_collection_limit")
        active.add(identity)
        try:
            if type(item) is dict:
                for key, nested in item.items():
                    if type(key) is not str:
                        raise SyntheticExperienceRecordError("json_key_invalid")
                    visit(key, depth + 1)
                    visit(nested, depth + 1)
            else:
                for nested in item:
                    visit(nested, depth + 1)
        finally:
            active.remove(identity)

    visit(value, 0)
    try:
        encoded = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise SyntheticExperienceRecordError("json_encoding_invalid") from exc
    if len(encoded) > limit:
        raise SyntheticExperienceRecordError("json_byte_limit_exceeded")
    return encoded


def _fixture_case(manifest: object, case_id: str) -> tuple[dict[str, Any], str]:
    if type(manifest) is not dict or type(manifest.get("pairs")) is not list:
        raise SyntheticExperienceRecordError("fixture_manifest_shape_invalid")
    if type(case_id) is not str or _CASE_ID.fullmatch(case_id) is None:
        raise SyntheticExperienceRecordError("case_id_invalid")
    matches: list[tuple[dict[str, Any], str]] = []
    for pair in manifest["pairs"]:
        if type(pair) is not dict or type(pair.get("cases")) is not list:
            raise SyntheticExperienceRecordError("fixture_pair_shape_invalid")
        group = pair.get("group")
        if type(group) is not str or group not in _GROUPS:
            raise SyntheticExperienceRecordError("fixture_group_invalid")
        for case in pair["cases"]:
            if type(case) is dict and case.get("case_id") == case_id:
                matches.append((case, group))
    if len(matches) != 1:
        raise SyntheticExperienceRecordError("case_id_unknown_or_duplicated")
    return matches[0]


def _review_digest(
    manifest: dict[str, Any], *, review_receipt_path: str, review_receipt_bytes: bytes
) -> str:
    if type(review_receipt_bytes) is not bytes:
        raise SyntheticExperienceRecordError("review_receipt_bytes_invalid")
    review = manifest.get("admission", {}).get("review")
    if type(review) is not dict or type(review.get("receipt_sha256")) is not str:
        raise SyntheticExperienceRecordError("review_receipt_missing")
    return review["receipt_sha256"]


def _record_errors(payload: object) -> list[str]:
    if type(payload) is not dict or set(payload) != _FIELDS:
        return ["record_fields_invalid"]
    errors: list[str] = []
    fixed = {
        "schema": SCHEMA,
        "provenance": SUPPORTED_PROVENANCE,
        "usage": SUPPORTED_USAGE,
        "split": "open_development",
        "record_scope": "fixture_regression_only",
        "candidate_origin": "caller_supplied_untrusted",
        "consent_basis": "not_applicable_authored_synthetic",
        "training_eligible": False,
    }
    for key, expected in fixed.items():
        if type(payload[key]) is not type(expected) or payload[key] != expected:
            errors.append(f"{key}_not_allowed")
    if type(payload["case_id"]) is not str or _CASE_ID.fullmatch(payload["case_id"]) is None:
        errors.append("case_id_invalid")
    if type(payload["case_group"]) is not str or payload["case_group"] not in _GROUPS:
        errors.append("case_group_invalid")
    if type(payload["oracle_kind"]) is not str or payload["oracle_kind"] not in _ORACLE_KINDS:
        errors.append("oracle_kind_invalid")
    for key in ("manifest_sha256", "review_receipt_sha256", "oracle_sha256"):
        if type(payload[key]) is not str or _SHA256.fullmatch(payload[key]) is None:
            errors.append(f"{key}_invalid")
    candidate_hash = payload["candidate_sha256"]
    if candidate_hash is not None and (type(candidate_hash) is not str or _SHA256.fullmatch(candidate_hash) is None):
        errors.append("candidate_sha256_invalid")
    comparison = payload["comparison"]
    if type(comparison) is not str or comparison not in {"match", "mismatch", "unknown"}:
        errors.append("comparison_invalid")
    elif comparison == "unknown" and candidate_hash is not None:
        errors.append("unknown_comparison_has_candidate")
    elif comparison == "match" and candidate_hash != payload["oracle_sha256"]:
        errors.append("match_digest_mismatch")
    elif comparison == "mismatch" and (candidate_hash is None or candidate_hash == payload["oracle_sha256"]):
        errors.append("mismatch_digest_inconsistent")
    return errors


def build_synthetic_experience_record(
    manifest: object,
    *,
    manifest_sha256: str,
    review_receipt_path: str,
    review_receipt_bytes: bytes,
    case_id: str,
    candidate_answer: object | None,
) -> SyntheticExperienceRecord:
    """Compare a supplied candidate with the frozen case oracle.

    ``candidate_answer`` is untrusted and never serialized into the record. A
    missing candidate produces ``unknown``. This function always requests the
    fixture's one development-only usage from the narrow admission validator.
    """
    if type(manifest) is not dict:
        raise SyntheticExperienceRecordError("fixture_manifest_shape_invalid")
    admission = validate_synthetic_fixture_admission(
        manifest,
        manifest_sha256=manifest_sha256,
        requested_usage=SUPPORTED_USAGE,
        review_receipt_path=review_receipt_path,
        review_receipt_bytes=review_receipt_bytes,
    )
    if not admission.admitted:
        raise SyntheticExperienceRecordError(f"fixture_not_admitted:{admission.reason}")
    case, group = _fixture_case(manifest, case_id)
    answer_oracle = case.get("answer_oracle")
    if type(answer_oracle) is not dict or type(answer_oracle.get("rule")) is not dict:
        raise SyntheticExperienceRecordError("fixture_oracle_shape_invalid")
    oracle_kind = answer_oracle["rule"].get("kind")
    expected = answer_oracle.get("expected")
    if oracle_kind not in _ORACLE_KINDS or type(expected) is not dict:
        raise SyntheticExperienceRecordError("fixture_oracle_unsupported")
    oracle_bytes = _json_bytes(expected, limit=MAX_CANDIDATE_BYTES)
    oracle_sha256 = hashlib.sha256(oracle_bytes).hexdigest()
    if candidate_answer is None:
        candidate_sha256 = None
        comparison = "unknown"
    else:
        candidate_bytes = _json_bytes(candidate_answer, limit=MAX_CANDIDATE_BYTES)
        candidate_sha256 = hashlib.sha256(candidate_bytes).hexdigest()
        comparison = "match" if candidate_bytes == oracle_bytes else "mismatch"
    payload = {
        "schema": SCHEMA,
        "provenance": SUPPORTED_PROVENANCE,
        "usage": SUPPORTED_USAGE,
        "split": "open_development",
        "record_scope": "fixture_regression_only",
        "case_id": case_id,
        "case_group": group,
        "oracle_kind": oracle_kind,
        "manifest_sha256": manifest_sha256,
        "review_receipt_sha256": _review_digest(
            manifest, review_receipt_path=review_receipt_path,
            review_receipt_bytes=review_receipt_bytes,
        ),
        "oracle_sha256": oracle_sha256,
        "candidate_sha256": candidate_sha256,
        "comparison": comparison,
        "candidate_origin": "caller_supplied_untrusted",
        "consent_basis": "not_applicable_authored_synthetic",
        "training_eligible": False,
    }
    errors = _record_errors(payload)
    if errors:
        raise SyntheticExperienceRecordError(errors[0])
    encoded = _json_bytes(payload, limit=MAX_RECORD_BYTES)
    return SyntheticExperienceRecord(encoded.decode("utf-8"), hashlib.sha256(encoded).hexdigest())


def validate_synthetic_experience_record(
    record: object,
    *,
    manifest: object,
    manifest_sha256: str,
    review_receipt_path: str,
    review_receipt_bytes: bytes,
) -> SyntheticExperienceRecordResult:
    """Validate bounded structure and fixture references, not claimed execution."""
    errors: list[str] = []
    if type(record) is not SyntheticExperienceRecord:
        return SyntheticExperienceRecordResult(False, ("record_type_invalid",))
    try:
        raw = record.payload_json.encode("utf-8")
        if len(raw) > MAX_RECORD_BYTES:
            return SyntheticExperienceRecordResult(False, ("record_too_large",))
        payload = json.loads(record.payload_json)
    except (AttributeError, UnicodeEncodeError, json.JSONDecodeError):
        return SyntheticExperienceRecordResult(False, ("record_json_invalid",))
    if hashlib.sha256(raw).hexdigest() != record.sha256:
        errors.append("record_digest_mismatch")
    try:
        if _json_bytes(payload, limit=MAX_RECORD_BYTES) != raw:
            errors.append("record_not_canonical")
    except SyntheticExperienceRecordError as exc:
        errors.append(str(exc))
    errors.extend(_record_errors(payload))
    if type(manifest) is not dict:
        errors.append("fixture_manifest_shape_invalid")
    else:
        admission = validate_synthetic_fixture_admission(
            manifest,
            manifest_sha256=manifest_sha256,
            requested_usage=SUPPORTED_USAGE,
            review_receipt_path=review_receipt_path,
            review_receipt_bytes=review_receipt_bytes,
        )
        if not admission.admitted:
            errors.append(f"fixture_not_admitted:{admission.reason}")
        if payload.get("manifest_sha256") != manifest_sha256 or manifest_sha256 != SUPPORTED_MANIFEST_SHA256:
            errors.append("manifest_identity_mismatch")
        if admission.admitted:
            try:
                case, group = _fixture_case(manifest, payload.get("case_id"))
                expected = case["answer_oracle"]["expected"]
                oracle_kind = case["answer_oracle"]["rule"]["kind"]
                expected_hash = hashlib.sha256(_json_bytes(expected, limit=MAX_CANDIDATE_BYTES)).hexdigest()
                if payload.get("case_group") != group or payload.get("oracle_kind") != oracle_kind:
                    errors.append("case_reference_mismatch")
                if payload.get("oracle_sha256") != expected_hash:
                    errors.append("oracle_digest_mismatch")
                if payload.get("review_receipt_sha256") != _review_digest(
                    manifest, review_receipt_path=review_receipt_path,
                    review_receipt_bytes=review_receipt_bytes,
                ):
                    errors.append("review_digest_mismatch")
            except (KeyError, TypeError, SyntheticExperienceRecordError) as exc:
                errors.append(f"fixture_reference_invalid:{type(exc).__name__}")
    return SyntheticExperienceRecordResult(not errors, tuple(dict.fromkeys(errors)))


__all__ = [
    "SCHEMA", "SyntheticExperienceRecord", "SyntheticExperienceRecordError",
    "SyntheticExperienceRecordResult", "build_synthetic_experience_record",
    "validate_synthetic_experience_record",
]
