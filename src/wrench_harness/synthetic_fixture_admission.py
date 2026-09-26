"""Fail-closed structural admission for the one open synthetic seed format.

This validates declared fixture metadata. It does not grant rights or authorize
real, customer, benchmark, sealed, or training data.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


SUPPORTED_SCHEMA = "wrench.synthetic-matched-tasks.v2"
SUPPORTED_MANIFEST_SHA256 = "871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5"
SUPPORTED_PROVENANCE = "wrench_authored_synthetic_only"
SUPPORTED_USAGE = "open_development_fixture_only"
SUPPORTED_REVIEW_PATH = "docs/evals/wrench-e0-synthetic-matched-tasks/review.md"
SUPPORTED_REVIEW_STATE = "fixture_mechanics_reviewed"
SUPPORTED_REVIEW_SCOPES = frozenset({"fixture_integrity", "mechanics", "oracle_consistency"})

# Separate one-entry admission identity for the tokenizer-only localization
# profile. Keep this independent from the historical matched-task manifest
# identity above: adding an open synthetic profile must not broaden or mutate
# the legacy admission contract.
LOCALIZATION_PROFILE_ID = "localization-screen-02"
LOCALIZATION_PROFILE_SCHEMA = "wrench.e0-localization-token-profile.v1"
LOCALIZATION_PROFILE_MANIFEST_SHA256 = "b7bc026058361e70edcafcb230f8427a8f9a55630510fdef1323674bd7b0c368"


@dataclass(frozen=True)
class SyntheticFixtureAdmission:
    admitted: bool
    usage: str | None
    reason: str | None


def validate_synthetic_fixture_admission(
    manifest: Any,
    *,
    manifest_sha256: str,
    requested_usage: str,
    review_receipt_path: str,
    review_receipt_bytes: bytes,
) -> SyntheticFixtureAdmission:
    """Validate the sole supported open synthetic fixture admission contract.

    The caller must provide the exact review receipt bytes. A successful result
    is only a local development-fixture classification, not legal authority.
    """

    def reject(reason: str) -> SyntheticFixtureAdmission:
        return SyntheticFixtureAdmission(False, None, reason)

    if type(manifest) is not dict:
        return reject("manifest_not_object")
    try:
        canonical = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return reject("manifest_not_canonicalizable")
    actual_manifest_hash = hashlib.sha256(canonical).hexdigest()
    if (
        type(manifest_sha256) is not str
        or manifest_sha256 != SUPPORTED_MANIFEST_SHA256
        or actual_manifest_hash != SUPPORTED_MANIFEST_SHA256
    ):
        return reject("fixture_identity_mismatch")
    if manifest.get("schema") != SUPPORTED_SCHEMA:
        return reject("unknown_schema")
    if manifest.get("provenance") != SUPPORTED_PROVENANCE:
        return reject("unknown_or_non_synthetic_origin")
    if manifest.get("usage") != SUPPORTED_USAGE:
        return reject("usage_disallowed")
    if manifest.get("not_a_utility_claim") is not True:
        return reject("utility_claim_not_explicitly_disclaimed")

    admission = manifest.get("admission")
    if type(admission) is not dict:
        return reject("admission_metadata_missing")
    if admission.get("origin") != SUPPORTED_PROVENANCE:
        return reject("unknown_or_non_synthetic_origin")

    declared = admission.get("declared_usage")
    if type(declared) is not list or not declared or any(type(item) is not str for item in declared):
        return reject("usage_undeclared")
    if len(set(declared)) != len(declared):
        return reject("usage_undeclared")
    if any(item != SUPPORTED_USAGE for item in declared):
        return reject("usage_disallowed")
    if requested_usage not in declared or requested_usage != SUPPORTED_USAGE:
        return reject("requested_usage_disallowed_or_undeclared")

    if admission.get("sealed") is not False or admission.get("final") is not False:
        return reject("sealed_or_final_data")
    if admission.get("split") != "open_development":
        return reject("invalid_split")

    lineage = admission.get("lineage")
    if type(lineage) is not dict:
        return reject("lineage_missing")
    if (
        lineage.get("kind") != "wrench_authored_inline_synthetic"
        or lineage.get("parent_manifest_sha256") is not None
    ):
        return reject("invalid_lineage")

    review = admission.get("review")
    if type(review) is not dict or review.get("state") != SUPPORTED_REVIEW_STATE:
        return reject("invalid_review_state")
    if review.get("scopes") != sorted(SUPPORTED_REVIEW_SCOPES):
        return reject("invalid_review_scopes")
    if review.get("receipt_path") != SUPPORTED_REVIEW_PATH or review_receipt_path != SUPPORTED_REVIEW_PATH:
        return reject("review_receipt_path_mismatch")
    expected_hash = review.get("receipt_sha256")
    if (
        type(expected_hash) is not str
        or type(review_receipt_bytes) is not bytes
        or hashlib.sha256(review_receipt_bytes).hexdigest() != expected_hash
    ):
        return reject("review_receipt_hash_mismatch")

    return SyntheticFixtureAdmission(True, SUPPORTED_USAGE, None)


def validate_localization_profile_admission(
    manifest: Any,
    *,
    manifest_sha256: str,
    profile_id: str,
    requested_usage: str,
) -> SyntheticFixtureAdmission:
    """Validate the separately pinned tokenizer-only localization fixture.

    This is structural admission for one Wrench-authored open-development
    fixture. It neither represents an independent-review receipt nor grants
    authority for inference, training, customer data, or utility claims.
    """

    def reject(reason: str) -> SyntheticFixtureAdmission:
        return SyntheticFixtureAdmission(False, None, reason)

    if type(manifest) is not dict:
        return reject("manifest_not_object")
    try:
        canonical = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return reject("manifest_not_canonicalizable")
    actual_digest = hashlib.sha256(canonical).hexdigest()
    if (
        profile_id != LOCALIZATION_PROFILE_ID
        or manifest_sha256 != LOCALIZATION_PROFILE_MANIFEST_SHA256
        or actual_digest != LOCALIZATION_PROFILE_MANIFEST_SHA256
    ):
        return reject("localization_profile_identity_mismatch")
    if (
        manifest.get("schema") != LOCALIZATION_PROFILE_SCHEMA
        or manifest.get("profile_id") != LOCALIZATION_PROFILE_ID
        or manifest.get("fixture_id") != "wrench-localization-screen-02-e0-tokenizer-only-v1"
    ):
        return reject("localization_profile_schema_or_id_mismatch")
    if (
        manifest.get("provenance") != "wrench_authored_fresh_synthetic_only"
        or manifest.get("usage") != SUPPORTED_USAGE
        or requested_usage != SUPPORTED_USAGE
        or manifest.get("not_a_utility_claim") is not True
    ):
        return reject("localization_profile_usage_or_claim_mismatch")
    admission = manifest.get("admission")
    if type(admission) is not dict:
        return reject("localization_profile_admission_missing")
    if (
        admission.get("profile_id") != LOCALIZATION_PROFILE_ID
        or admission.get("declared_usage") != [SUPPORTED_USAGE]
        or admission.get("sealed") is not False
        or admission.get("final") is not False
        or admission.get("split") != "open_development"
        or admission.get("lineage") != {
            "kind": "independent_inline_synthetic", "parent_manifest_sha256": None
        }
    ):
        return reject("localization_profile_admission_fields_invalid")

    cases = manifest.get("cases")
    if type(cases) is not list or len(cases) != 8:
        return reject("localization_profile_case_set_invalid")
    case_ids: set[str] = set()
    for case in cases:
        if type(case) is not dict or type(case.get("case_id")) is not str or case["case_id"] in case_ids:
            return reject("localization_profile_case_set_invalid")
        case_ids.add(case["case_id"])
        files = case.get("files")
        if type(files) is not list or not files:
            return reject("localization_profile_sources_invalid")
        source_paths: set[str] = set()
        for source in files:
            if type(source) is not dict or type(source.get("path")) is not str or type(source.get("content_utf8")) is not str:
                return reject("localization_profile_sources_invalid")
            path = source["path"]
            content = source["content_utf8"]
            if path in source_paths or "\\" in path or path.startswith("/") or any(part in {"", ".", ".."} for part in path.split("/")):
                return reject("localization_profile_source_path_invalid")
            source_paths.add(path)
            if source.get("sha256") != hashlib.sha256(content.encode("utf-8")).hexdigest():
                return reject("localization_profile_source_hash_mismatch")
        mutation = case.get("mutate_after_snapshot")
        if mutation is not None:
            if type(mutation) is not dict or mutation.get("path") not in source_paths or type(mutation.get("content_utf8")) is not str:
                return reject("localization_profile_mutation_invalid")
            if mutation.get("sha256") != hashlib.sha256(mutation["content_utf8"].encode("utf-8")).hexdigest():
                return reject("localization_profile_mutation_hash_mismatch")
    if case_ids != {
        "loc02-positive-01", "loc02-positive-02", "loc02-positive-03", "loc02-positive-04",
        "loc02-boundary-missing", "loc02-boundary-stale", "loc02-boundary-unsupported",
        "loc02-boundary-context-budget",
    }:
        return reject("localization_profile_case_set_invalid")
    return SyntheticFixtureAdmission(True, SUPPORTED_USAGE, None)
