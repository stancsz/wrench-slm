#!/usr/bin/env python3
"""Validate Wrench train and development JSONL without opening sealed final data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "wrench.training-example.v1"
ACTION_FAMILIES = {
    "read_file",
    "read_lines",
    "literal_search",
    "git_read_status",
    "health_read",
    "patch_draft",
}
OUT_OF_SCOPE_FAMILIES = {
    "unsupported_mutation_or_command",
    "credential_or_external_access",
    "ambiguous_or_multistep",
    "unrelated_or_non_developer",
}
ALLOCATION_STRATA = {"balanced_core", "observed_workflow", "ood_escalation"}
AUTHORIZATIONS = {"approved_license", "consented_redacted", "project_authored"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
MAX_DIAGNOSTICS = 1000


class BoundedErrors(list[str]):
    """Keep diagnostics bounded while preserving total and suppressed counts."""

    def __init__(self, values=(), limit: int = MAX_DIAGNOSTICS):
        super().__init__()
        self.limit = limit
        self.suppressed = 0
        self.extend(values)

    def append(self, value: str) -> None:
        if len(self) < self.limit:
            super().append(value)
        else:
            self.suppressed += 1

    def extend(self, values) -> None:
        suppressed = getattr(values, "suppressed", 0)
        for value in values:
            self.append(value)
        self.suppressed += suppressed


def diagnostic_metadata(errors: list[str]) -> dict[str, int | bool]:
    total = len(errors) + getattr(errors, "suppressed", 0)
    reported = min(len(errors), 100)
    suppressed = max(0, total - reported)
    return {
        "error_count": total,
        "diagnostics_suppressed": suppressed,
        "diagnostics_truncated": suppressed > 0,
    }


def path_components(path: Path) -> list[str]:
    """Return lexical and resolved components without opening the target."""
    raw = str(path)
    components = [part for part in re.split(r"[\\/]+", raw) if part]
    try:
        resolved = str(path.resolve(strict=False))
    except (OSError, RuntimeError):
        resolved = raw
    components.extend(part for part in re.split(r"[\\/]+", resolved) if part)
    return components


def looks_sealed_path(path: Path) -> bool:
    return any(any(marker in part.casefold() for marker in ("final", "sealed")) for part in path_components(path))


def paths_alias(left: Path, right: Path) -> bool:
    """Compare normalized lexical/resolved paths and existing filesystem identity."""
    try:
        if os.path.normcase(os.path.abspath(str(left))) == os.path.normcase(os.path.abspath(str(right))):
            return True
        if left.resolve(strict=False) == right.resolve(strict=False):
            return True
        return left.exists() and right.exists() and os.path.samefile(left, right)
    except (OSError, RuntimeError, ValueError):
        return False


def report_path_conflicts(report: Path, protected: tuple[Path, ...]) -> list[str]:
    if looks_sealed_path(report):
        return ["--report path cannot look like sealed final data"]
    conflicts = [path for path in protected if paths_alias(report, path)]
    if conflicts:
        names = ", ".join(path.name for path in conflicts)
        return [f"--report path aliases protected input: {names}"]
    return []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(system: str, prompt: str) -> str:
    """Hash normalized model input; repeated observations belong in frequency."""
    normalized = "\n".join(
        " ".join(unicodedata.normalize("NFKC", part).split())
        for part in (system, prompt)
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def near_duplicate_signature(prompt: str) -> int | None:
    """Return a bounded SimHash signature over normalized prompt bigrams."""
    normalized = " ".join(unicodedata.normalize("NFKC", prompt[:4096]).casefold().split())
    tokens = re.findall(r"\w+|[^\w\s]", normalized, flags=re.UNICODE)
    if not tokens:
        return None
    tokens = ["<num>" if token.isdecimal() else token for token in tokens]
    shingles = [" ".join(tokens[index:index + 2]) for index in range(max(1, len(tokens) - 1))]
    if len(tokens) < 2:
        compact = " ".join(tokens)
        shingles = [compact[index:index + 4] for index in range(max(1, len(compact) - 3))]
    # A row is already bounded to 8,192 combined characters. Sampling at most
    # 64 shingles keeps signature work independent of unusually long prompts.
    if len(shingles) > 64:
        last = len(shingles) - 1
        shingles = [shingles[(index * last) // 63] for index in range(64)]
    accum = [0] * 32
    for shingle in shingles:
        value = int.from_bytes(hashlib.blake2s(shingle.encode("utf-8"), digest_size=4).digest(), "big")
        for bit in range(32):
            accum[bit] += 1 if value & (1 << bit) else -1
    signature = 0
    for bit, score in enumerate(accum):
        if score >= 0:
            signature |= 1 << bit
    return signature


def isolation_errors(rows: list[dict[str, Any]]) -> list[str]:
    """Fail closed on missing isolation provenance and cross-split leakage."""
    errors: BoundedErrors = BoundedErrors()
    seen: dict[str, dict[str, str]] = {}
    for row in rows:
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        row_id = row.get("id", "<unknown>")
        split = row.get("split", "")
        dimensions = {
            "repository": provenance.get("repository_id", row.get("repository_id")),
            "task_family": provenance.get("task_family_id", row.get("task_family_id")),
            "template group": row.get("template_id"),
        }
        for dimension, value in dimensions.items():
            if not nonempty(value):
                errors.append(f"{row_id}: provenance {dimension} isolation ID is required")
                continue
            key = f"{dimension}:{value}"
            previous = seen.get(key)
            if previous and previous["split"] != split:
                errors.append(
                    f"{row_id}: {dimension} isolation group also appears in {previous['split']} ({previous['id']})"
                )
            else:
                seen[key] = {"split": str(split), "id": str(row_id)}
    return errors


def near_duplicate_errors(rows: list[dict[str, Any]], max_hamming: int = 3) -> list[str]:
    """Find near duplicates using bounded 4-band SimHash candidate comparisons."""
    errors: BoundedErrors = BoundedErrors()
    buckets: dict[tuple[int, int], list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    candidate_limit = 128
    for row_index, row in enumerate(rows):
        signature = row.get("near_duplicate_signature")
        if not isinstance(signature, int):
            continue
        checked: set[int] = set()
        limit_reported = False
        for band in range(4):
            band_value = (signature >> (band * 8)) & 0xFF
            bucket = buckets[(band, band_value)]
            if len(bucket) > candidate_limit and not limit_reported:
                errors.append(
                    f"{row.get('id', '<unknown>')}: near-duplicate candidate limit exceeded; review corpus partitioning"
                )
                limit_reported = True
            for prior_index, prior in bucket[:candidate_limit]:
                if prior_index in checked:
                    continue
                if len(checked) >= candidate_limit:
                    if not limit_reported:
                        errors.append(
                            f"{row.get('id', '<unknown>')}: near-duplicate candidate limit exceeded; review corpus partitioning"
                        )
                        limit_reported = True
                    break
                checked.add(prior_index)
                if prior["split"] != row["split"]:
                    relation = "across splits"
                else:
                    relation = "within split"
                distance = (prior["near_duplicate_signature"] ^ signature).bit_count()
                if distance <= max_hamming:
                    pair = tuple(sorted((str(prior["id"]), str(row["id"]))))
                    errors.append(
                        f"near-duplicate model input {relation}: {pair[0]}, {pair[1]} (SimHash distance {distance}/32)"
                    )
        for band in range(4):
            band_value = (signature >> (band * 8)) & 0xFF
            bucket = buckets[(band, band_value)]
            # Keep one overflow sentinel so saturation is detectable without
            # retaining an unbounded candidate list in pathological corpora.
            if len(bucket) <= candidate_limit:
                bucket.append((row_index, row))
    return errors


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def issue(errors: list[str], row_id: str, message: str) -> None:
    errors.append(f"{row_id}: {message}")


def validate_row(
    row: Any,
    expected_split: str,
    row_number: int,
    registries: dict[str, dict[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    errors: BoundedErrors = BoundedErrors()
    if not isinstance(row, dict):
        return [f"line {row_number}: record must be a JSON object"], {}

    candidate_id = row.get("id")
    row_id = candidate_id if isinstance(candidate_id, str) and ID_RE.fullmatch(candidate_id) else f"line {row_number}"
    if row_id.startswith("line "):
        issue(errors, row_id, "id must use 1 to 128 letters, digits, period, underscore, colon, or hyphen")
    for key in (
        "id",
        "schema",
        "split",
        "allocation_stratum",
        "category",
        "family",
        "template_id",
        "system",
        "prompt",
        "context_ref",
        "context_sha256",
        "expected_status",
        "expected_proposal",
        "abstention_reason",
        "oracle_ref",
        "oracle_sha256",
        "provenance",
        "review",
        "fingerprint_sha256",
    ):
        if key not in row:
            issue(errors, row_id, f"missing required field {key}")

    if row.get("schema") != SCHEMA:
        issue(errors, row_id, f"schema must be {SCHEMA}")
    if row.get("split") != expected_split:
        issue(errors, row_id, f"split must be {expected_split}")
    if row.get("split") == "sealed_final":
        issue(errors, row_id, "sealed final rows are forbidden in this validator")
    if not isinstance(row.get("allocation_stratum"), str) or row.get("allocation_stratum") not in ALLOCATION_STRATA:
        issue(errors, row_id, "unknown allocation_stratum")
    if not nonempty(row.get("template_id")):
        issue(errors, row_id, "template_id must be nonempty")
    if not nonempty(row.get("context_ref")):
        issue(errors, row_id, "context_ref must identify the repo snapshot or fixture")
    for key in ("system", "prompt"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            issue(errors, row_id, f"{key} must be nonempty text")
        elif len(value) > 4096:
            issue(errors, row_id, f"{key} exceeds the 4096-character input limit")

    family = row.get("family")
    category = row.get("category")
    status = row.get("expected_status")
    proposal = row.get("expected_proposal")
    reason = row.get("abstention_reason")
    stratum = row.get("allocation_stratum")

    if category == "eligible":
        if not isinstance(family, str) or family not in ACTION_FAMILIES:
            issue(errors, row_id, "eligible rows must name one allowlisted action family")
        if status != "accepted":
            issue(errors, row_id, "eligible rows must have expected_status=accepted")
        if not isinstance(proposal, dict) or proposal.get("action") != family:
            issue(errors, row_id, "accepted rows need a typed proposal matching family")
        if nonempty(reason):
            issue(errors, row_id, "accepted rows must not carry an abstention reason")
    elif category == "matched_boundary":
        if not isinstance(family, str) or family not in ACTION_FAMILIES:
            issue(errors, row_id, "matched boundaries must map to an allowlisted action family")
        if status != "abstain" or not nonempty(reason):
            issue(errors, row_id, "matched boundaries need abstain status and an exact reason")
        if proposal is not None:
            issue(errors, row_id, "abstention rows must not contain an executable proposal")
    elif category == "out_of_scope":
        if not isinstance(family, str) or family not in OUT_OF_SCOPE_FAMILIES:
            issue(errors, row_id, "out-of-scope rows must name one of the four boundary families")
        if status != "abstain" or not nonempty(reason):
            issue(errors, row_id, "out-of-scope rows need abstain status and an exact reason")
        if proposal is not None:
            issue(errors, row_id, "abstention rows must not contain an executable proposal")
    else:
        issue(errors, row_id, "category must be eligible, matched_boundary, or out_of_scope")

    if not nonempty(row.get("oracle_ref")):
        issue(errors, row_id, "oracle_ref must point to the independent verifier or label rule")
    oracle_ref = row.get("oracle_ref") if isinstance(row.get("oracle_ref"), str) else None
    oracle_entry = registries["oracles"].get(oracle_ref)
    if not isinstance(oracle_entry, dict):
        issue(errors, row_id, "oracle_ref is absent from the corpus manifest")
    elif row.get("oracle_sha256") != oracle_entry.get("sha256"):
        issue(errors, row_id, "oracle_sha256 does not match the corpus manifest")

    context_ref = row.get("context_ref") if isinstance(row.get("context_ref"), str) else None
    context_entry = registries["contexts"].get(context_ref)
    if not isinstance(context_entry, dict):
        issue(errors, row_id, "context_ref is absent from the corpus manifest")
    elif row.get("context_sha256") != context_entry.get("sha256"):
        issue(errors, row_id, "context_sha256 does not match the corpus manifest")

    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        issue(errors, row_id, "provenance must be an object")
        provenance = {}
    source_kind = provenance.get("kind")
    if not isinstance(source_kind, str) or source_kind not in {"verified_real", "verified_authored"}:
        issue(errors, row_id, "provenance.kind must be verified_real or verified_authored")
    if not nonempty(provenance.get("source_ref")):
        issue(errors, row_id, "provenance.source_ref is required")
    for key in ("repository_id", "task_family_id"):
        if not nonempty(provenance.get(key)):
            issue(errors, row_id, f"provenance.{key} is required for split isolation")
    source_hash = provenance.get("source_sha256")
    if not isinstance(source_hash, str) or not SHA256_RE.fullmatch(source_hash):
        issue(errors, row_id, "provenance.source_sha256 must be 64 lowercase hex characters")
    authorization = provenance.get("authorization")
    if not isinstance(authorization, str) or authorization not in AUTHORIZATIONS:
        issue(errors, row_id, "provenance.authorization is not approved")
    if source_kind == "verified_real" and authorization == "project_authored":
        issue(errors, row_id, "real traces need consent or an approved source license")
    if source_kind == "verified_authored" and authorization != "project_authored":
        issue(errors, row_id, "authored rows must identify project authorship")
    source_ref = provenance.get("source_ref") if isinstance(provenance.get("source_ref"), str) else None
    source_entry = registries["sources"].get(source_ref)
    if not isinstance(source_entry, dict):
        issue(errors, row_id, "provenance.source_ref is absent from the corpus manifest")
    else:
        for field, actual in (
            ("kind", source_kind),
            ("sha256", source_hash),
            ("authorization", authorization),
            ("repository_id", provenance.get("repository_id")),
            ("task_family_id", provenance.get("task_family_id")),
        ):
            if source_entry.get(field) != actual:
                issue(errors, row_id, f"provenance {field} does not match the corpus manifest")
        if source_entry.get("status") != "approved":
            issue(errors, row_id, "source manifest status is not approved")
        if source_kind == "verified_real":
            expected_trace_set_ref = source_entry.get("trace_set_ref")
            if not nonempty(expected_trace_set_ref):
                issue(errors, row_id, "real trace source needs a manifest trace_set_ref")
            elif isinstance(row.get("usage"), dict) and row["usage"].get("trace_set_ref") != expected_trace_set_ref:
                issue(errors, row_id, "usage.trace_set_ref does not match the approved source")

    review = row.get("review")
    if not isinstance(review, dict):
        issue(errors, row_id, "review must be an object")
        review = {}
    if review.get("status") != "verified":
        issue(errors, row_id, "only verified rows may enter train or development")
    if (
        not nonempty(review.get("reviewer_id"))
        or not nonempty(review.get("receipt_ref"))
        or not isinstance(review.get("receipt_sha256"), str)
        or not SHA256_RE.fullmatch(review.get("receipt_sha256", ""))
    ):
        issue(errors, row_id, "reviewer_id and hash-bound receipt_ref are required")
    scopes = review.get("checked_scopes")
    if (
        not isinstance(scopes, list)
        or not all(isinstance(scope, str) for scope in scopes)
        or not {"label", "task_fit", "privacy"}.issubset(scopes)
    ):
        issue(errors, row_id, "review.checked_scopes must include label, task_fit, and privacy")
    receipt_ref = review.get("receipt_ref") if isinstance(review.get("receipt_ref"), str) else None
    review_entry = registries["reviews"].get(receipt_ref)
    if not isinstance(review_entry, dict):
        issue(errors, row_id, "review.receipt_ref is absent from the corpus manifest")
    else:
        if review.get("receipt_sha256") != review_entry.get("sha256"):
            issue(errors, row_id, "review receipt hash does not match the corpus manifest")
        if review_entry.get("status") != "verified" or review.get("status") != "verified":
            issue(errors, row_id, "review receipt is not verified")
        if review.get("reviewer_id") != review_entry.get("reviewer_id"):
            issue(errors, row_id, "reviewer_id does not match the review receipt")
        if review.get("checked_scopes") != review_entry.get("checked_scopes"):
            issue(errors, row_id, "review scopes do not match the review receipt")

    usage = row.get("usage")
    if source_kind == "verified_real":
        if not isinstance(usage, dict):
            issue(errors, row_id, "verified real rows need measured usage metadata")
            usage = {}
        for key in ("observation_window", "trace_set_ref"):
            if not nonempty(usage.get(key)):
                issue(errors, row_id, f"usage.{key} is required")
        numeric = ("observed_requests", "frontier_input_tokens", "verifier_successes", "final_task_successes")
        for key in numeric:
            value = usage.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                issue(errors, row_id, f"usage.{key} must be a nonnegative integer")
        observed = usage.get("observed_requests")
        if isinstance(observed, int) and not isinstance(observed, bool):
            for key in ("verifier_successes", "final_task_successes"):
                value = usage.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value > observed:
                    issue(errors, row_id, f"usage.{key} cannot exceed observed_requests")
    elif usage is not None:
        issue(errors, row_id, "authored rows must not claim production usage frequency")

    if stratum == "observed_workflow" and (source_kind != "verified_real" or category != "eligible"):
        issue(errors, row_id, "observed_workflow rows must be verified real eligible tasks")
    if stratum == "balanced_core" and (
        not isinstance(family, str)
        or family not in ACTION_FAMILIES
        or not isinstance(category, str)
        or category not in {"eligible", "matched_boundary"}
    ):
        issue(errors, row_id, "balanced_core rows must cover an allowlisted action or its matched boundary")
    if stratum == "ood_escalation" and (
        not isinstance(family, str)
        or family not in OUT_OF_SCOPE_FAMILIES
        or category != "out_of_scope"
    ):
        issue(errors, row_id, "ood_escalation rows must cover a named out-of-scope family")

    system = row.get("system") if isinstance(row.get("system"), str) else ""
    prompt = row.get("prompt") if isinstance(row.get("prompt"), str) else ""
    expected_fingerprint = fingerprint(system, prompt)
    if row.get("fingerprint_sha256") != expected_fingerprint:
        issue(errors, row_id, "fingerprint_sha256 does not match normalized system and prompt")

    usage_row = usage if isinstance(usage, dict) else {}
    usage_metrics = {}
    for key in ("observed_requests", "frontier_input_tokens", "verifier_successes", "final_task_successes"):
        value = usage_row.get(key, 0)
        usage_metrics[key] = value if isinstance(value, int) and not isinstance(value, bool) else 0

    summary = {
        "id": str(row_id),
        "split": str(row.get("split", "")),
        "allocation_stratum": str(stratum or ""),
        "family": str(family or ""),
        "category": str(category or ""),
        "expected_status": str(status or ""),
        "source_kind": str(source_kind or ""),
        "template_id": str(row.get("template_id", "")),
        "fingerprint": expected_fingerprint,
        "near_duplicate_signature": near_duplicate_signature(prompt),
        "repository_id": str(provenance.get("repository_id", "")) if isinstance(provenance, dict) else "",
        "task_family_id": str(provenance.get("task_family_id", "")) if isinstance(provenance, dict) else "",
        "usage_metrics": usage_metrics,
    }
    return errors, summary


def load_manifest(
    path: Path,
    structural_only: bool,
) -> tuple[list[str], dict[str, Any], dict[str, dict[str, Any]], dict[str, Path]]:
    errors: BoundedErrors = BoundedErrors()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"cannot read corpus manifest: {type(exc).__name__}"], {}, {}, {}
    if not isinstance(manifest, dict) or manifest.get("schema") != "wrench.corpus-manifest.v1":
        return ["manifest schema must be wrench.corpus-manifest.v1"], {}, {}, {}

    required_splits = {"train", "development", "sealed_final"}
    splits = manifest.get("splits")
    if not isinstance(splits, dict) or set(splits) != required_splits:
        errors.append("manifest must declare train, development, and sealed_final splits")
        splits = splits if isinstance(splits, dict) else {}

    targets = manifest.get("target_counts")
    if not isinstance(targets, dict):
        errors.append("manifest.target_counts must be an object")
        targets = {}
    locked_targets = {"train": 20_000, "development": 2_500, "sealed_final": 2_500}
    if not structural_only and targets != locked_targets:
        errors.append("production target_counts must be 20,000 train, 2,500 development, and 2,500 sealed_final")

    resolved: dict[str, Path] = {}
    split_hashes: dict[str, str] = {}
    lexical_paths: dict[str, str] = {}
    for split in sorted(required_splits):
        entry = splits.get(split)
        if not isinstance(entry, dict):
            errors.append(f"manifest split {split} must be an object")
            continue
        rows = entry.get("rows")
        if not isinstance(rows, int) or isinstance(rows, bool) or rows < 0:
            errors.append(f"manifest split {split} rows must be a nonnegative integer")
        elif targets.get(split) != rows:
            errors.append(f"manifest target count and split row count disagree for {split}")
        digest = entry.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append(f"manifest split {split} needs a 64-character SHA-256")
        else:
            split_hashes[split] = digest
        raw_path = entry.get("path")
        if not nonempty(raw_path):
            errors.append(f"manifest split {split} needs a path")
            continue
        source_path = Path(raw_path)
        if not source_path.is_absolute():
            source_path = path.parent / source_path
        lexical = str(source_path).replace("\\", "/").casefold()
        lexical_paths[split] = lexical
        if split == "sealed_final":
            if not looks_sealed_path(source_path):
                errors.append("sealed_final manifest path must be clearly named final or sealed")
            continue
        if looks_sealed_path(source_path):
            errors.append(f"manifest {split} path cannot look like sealed final data")
        # Preserve the lexical spelling so the reader can reject a final-looking
        # symlink name as well as a target whose resolved components look sealed.
        resolved[split] = source_path

    for left, right in (("train", "development"), ("train", "sealed_final"), ("development", "sealed_final")):
        if lexical_paths.get(left) == lexical_paths.get(right):
            errors.append(f"manifest paths for {left} and {right} must differ")
        if split_hashes.get(left) == split_hashes.get(right) and left in split_hashes and right in split_hashes:
            errors.append(f"manifest hashes for {left} and {right} must differ")

    registries: dict[str, dict[str, Any]] = {}
    for name in ("sources", "contexts", "oracles", "reviews"):
        value = manifest.get(name)
        if not isinstance(value, dict):
            errors.append(f"manifest.{name} must be an object")
            registries[name] = {}
        else:
            registries[name] = value
    return errors, manifest, registries, resolved


def validate_file(
    path: Path,
    expected_split: str,
    expected_rows: int | None,
    registries: dict[str, dict[str, Any]],
    sealed_paths: tuple[Path, ...] = (),
) -> tuple[list[str], list[dict[str, Any]], str]:
    errors: BoundedErrors = BoundedErrors()
    summaries: list[dict[str, Any]] = []
    if looks_sealed_path(path) or any(paths_alias(path, sealed) for sealed in sealed_paths):
        return [f"refusing sealed or final-looking input path: {path.name}"], summaries, ""
    if not path.is_file():
        return [f"input file does not exist: {path}"], summaries, ""
    try:
        with path.open("r", encoding="utf-8") as handle:
            for row_number, raw in enumerate(handle, start=1):
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError as exc:
                    errors.append(f"line {row_number}: invalid JSON at column {exc.colno}")
                    continue
                row_errors, summary = validate_row(row, expected_split, row_number, registries)
                errors.extend(row_errors)
                if summary:
                    summaries.append(summary)
    except (OSError, UnicodeDecodeError) as exc:
        return [f"cannot read {path.name}: {type(exc).__name__}"], summaries, ""
    if expected_rows is not None and len(summaries) != expected_rows:
        errors.append(f"{path.name}: expected {expected_rows} rows, found {len(summaries)}")
    return errors, summaries, sha256_file(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate manifest-bound train and development data without opening sealed final data."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="validate a clearly non-production fixture with custom split sizes",
    )
    parser.add_argument("--check-provisional-allocation", action="store_true")
    parser.add_argument("--report", type=Path, help="write a compact hash-bound JSON report")
    args = parser.parse_args()

    if looks_sealed_path(args.manifest):
        parser.error("--manifest path cannot look like sealed final data")
    manifest_path = args.manifest.resolve()
    errors, manifest, registries, split_paths = load_manifest(manifest_path, args.structural_only)
    split_declarations = manifest.get("splits", {}) if isinstance(manifest.get("splits"), dict) else {}

    protected_paths = [args.manifest, manifest_path, *split_paths.values()]
    for split in ("train", "development", "sealed_final"):
        declaration = split_declarations.get(split)
        raw_path = declaration.get("path") if isinstance(declaration, dict) else None
        if nonempty(raw_path):
            candidate = Path(raw_path)
            if not candidate.is_absolute():
                candidate = manifest_path.parent / candidate
            protected_paths.append(candidate)
    if args.report is not None:
        conflicts = report_path_conflicts(args.report, tuple(protected_paths))
        if conflicts:
            parser.error(conflicts[0])

    sealed_declaration = split_declarations.get("sealed_final")
    sealed_paths: tuple[Path, ...] = ()
    if isinstance(sealed_declaration, dict) and nonempty(sealed_declaration.get("path")):
        sealed_path = Path(sealed_declaration["path"])
        if not sealed_path.is_absolute():
            sealed_path = manifest_path.parent / sealed_path
        sealed_paths = (sealed_path,)

    loaded: dict[str, tuple[list[dict[str, Any]], str]] = {}
    for split in ("train", "development"):
        split_path = split_paths.get(split)
        declaration = split_declarations.get(split)
        if split_path is None or not isinstance(declaration, dict):
            errors.append(f"manifest does not provide a usable {split} input")
            loaded[split] = ([], "")
            continue
        split_errors, rows, actual_hash = validate_file(
            split_path, split, declaration.get("rows"), registries, sealed_paths
        )
        errors.extend(split_errors)
        if actual_hash and actual_hash != declaration.get("sha256"):
            errors.append(f"{split} file hash does not match the corpus manifest")
        loaded[split] = (rows, actual_hash)

    train, train_hash = loaded["train"]
    development, dev_hash = loaded["development"]

    seen_ids: set[str] = set()
    seen_fingerprints: dict[str, str] = {}
    for row in train + development:
        row_id = row["id"]
        if row_id in seen_ids:
            errors.append(f"duplicate id across input splits: {row_id}")
        seen_ids.add(row_id)
        prior_id = seen_fingerprints.get(row["fingerprint"])
        if prior_id is not None:
            errors.append(f"duplicate normalized model input across splits or rows: {prior_id}, {row_id}")
        else:
            seen_fingerprints[row["fingerprint"]] = row_id
    errors.extend(isolation_errors(train + development))
    errors.extend(near_duplicate_errors(train + development))
    unique_template_groups = len(
        {
            row["template_id"]
            for row in train + development
            if isinstance(row.get("template_id"), str) and row["template_id"]
        }
    )

    train_counts = Counter((row["family"], row["category"]) for row in train)
    dev_counts = Counter((row["family"], row["category"]) for row in development)
    usage_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in train:
        if row["allocation_stratum"] == "observed_workflow" and row["source_kind"] == "verified_real":
            for metric, value in row["usage_metrics"].items():
                usage_by_family[row["family"]][metric] += value
    for family in sorted(ACTION_FAMILIES):
        if train_counts[(family, "eligible")] == 0:
            errors.append(f"training set has no eligible examples for {family}")
        if train_counts[(family, "matched_boundary")] == 0:
            errors.append(f"training set has no matched-boundary examples for {family}")
        if dev_counts[(family, "eligible")] == 0 or dev_counts[(family, "matched_boundary")] == 0:
            errors.append(f"development set lacks eligible or boundary coverage for {family}")
    for family in sorted(OUT_OF_SCOPE_FAMILIES):
        if train_counts[(family, "out_of_scope")] == 0:
            errors.append(f"training set has no out-of-scope examples for {family}")
        if dev_counts[(family, "out_of_scope")] == 0:
            errors.append(f"development set has no out-of-scope examples for {family}")

    if args.check_provisional_allocation and len(train) == 20_000:
        strata = Counter(row["allocation_stratum"] for row in train)
        core_counts = Counter(
            (row["family"], row["category"])
            for row in train
            if row["allocation_stratum"] == "balanced_core"
        )
        observed_rows = [row for row in train if row["allocation_stratum"] == "observed_workflow"]
        ood_rows = [row for row in train if row["allocation_stratum"] == "ood_escalation"]
        if strata["balanced_core"] != 7_200:
            errors.append("provisional balanced_core allocation must contain 7,200 rows")
        if strata["observed_workflow"] != 9_600:
            errors.append("provisional observed_workflow allocation must contain 9,600 rows")
        if strata["ood_escalation"] != 3_200:
            errors.append("provisional ood_escalation allocation must contain 3,200 rows")
        for family in sorted(ACTION_FAMILIES):
            if core_counts[(family, "eligible")] != 600:
                errors.append(f"provisional balanced_core needs exactly 600 eligible {family} rows")
            if core_counts[(family, "matched_boundary")] != 600:
                errors.append(f"provisional balanced_core needs exactly 600 matched-boundary {family} rows")
        if any(row["source_kind"] != "verified_real" for row in observed_rows):
            errors.append("every observed_workflow row must be verified_real")
        if any(row["category"] != "eligible" for row in observed_rows):
            errors.append("every observed_workflow row must be eligible")
        if any(row["family"] not in OUT_OF_SCOPE_FAMILIES for row in ood_rows):
            errors.append("ood_escalation rows must use one of the four named boundary families")

    sealed_entry = split_declarations.get("sealed_final", {})
    diagnostics = diagnostic_metadata(errors)
    result = {
        "status": "PASS" if not errors else "FAIL",
        "production_ready": not errors and not args.structural_only,
        "structural_only": args.structural_only,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else "",
        "sealed_final_read": False,
        "sealed_final_declaration": {
            "path": sealed_entry.get("path") if isinstance(sealed_entry, dict) else None,
            "rows": sealed_entry.get("rows") if isinstance(sealed_entry, dict) else None,
            "sha256": sealed_entry.get("sha256") if isinstance(sealed_entry, dict) else None,
        },
        "train": {
            "path": str(split_paths.get("train", "")),
            "rows": len(train),
            "sha256": train_hash,
            "family_category_counts": {
                f"{family}:{category}": count
                for (family, category), count in sorted(train_counts.items())
            },
            "status_counts": dict(Counter(row["expected_status"] for row in train)),
            "observed_utility_by_family": {
                family: {
                    **dict(metrics),
                    "verifier_success_rate": (
                        metrics["verifier_successes"] / metrics["observed_requests"]
                        if metrics["observed_requests"] else None
                    ),
                    "final_task_success_rate": (
                        metrics["final_task_successes"] / metrics["observed_requests"]
                        if metrics["observed_requests"] else None
                    ),
                    "frontier_input_tokens_per_request": (
                        metrics["frontier_input_tokens"] / metrics["observed_requests"]
                        if metrics["observed_requests"] else None
                    ),
                }
                for family, metrics in sorted(usage_by_family.items())
            },
        },
        "development": {
            "path": str(split_paths.get("development", "")),
            "rows": len(development),
            "sha256": dev_hash,
            "family_category_counts": {
                f"{family}:{category}": count
                for (family, category), count in sorted(dev_counts.items())
            },
            "status_counts": dict(Counter(row["expected_status"] for row in development)),
        },
        "unique_template_groups": unique_template_groups,
        "errors": errors[:100],
        **diagnostics,
    }
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
