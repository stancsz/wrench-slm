"""Build a bounded, content-free source lineage receipt for selected segments.

The receipt joins public preparation identities to public structural candidate
records. It never reads ContextLedger internals or contains source text.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from .e0_context_pipeline import SourceIdentity
from .snapshot_structure import StructuralCandidate


MAX_SELECTED_REFERENCES = 256
MAX_CANDIDATES = 32
MAX_RECEIPT_BYTES = 64 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SelectedSourceReferenceError(ValueError):
    """Raised when caller-supplied public lineage inputs are malformed."""


@dataclass(frozen=True)
class SelectedSourceReferenceReceipt:
    schema: str
    snapshot_sha256: str
    selected_segment_ids: tuple[str, ...]
    references: tuple[Mapping[str, object], ...]
    receipt_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "snapshot_sha256": self.snapshot_sha256,
            "selected_segment_ids": list(self.selected_segment_ids),
            "references": [dict(row) for row in self.references],
            "receipt_sha256": self.receipt_sha256,
        }


def _canonical_digest(value: object) -> str:
    digest = hashlib.sha256()
    byte_count = 0
    encoder = json.JSONEncoder(
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    try:
        for chunk in encoder.iterencode(value):
            encoded = chunk.encode("utf-8")
            byte_count += len(encoded)
            if byte_count > MAX_RECEIPT_BYTES:
                raise SelectedSourceReferenceError("receipt_limit_exceeded")
            digest.update(encoded)
    except SelectedSourceReferenceError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise SelectedSourceReferenceError("receipt_value_invalid") from exc
    return digest.hexdigest()


def _require_hash(value: object, label: str) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise SelectedSourceReferenceError(f"{label}_invalid")
    return value


def _source_id(snapshot_sha256: str, path: str, content_sha256: str) -> str:
    return "source-" + _canonical_digest([snapshot_sha256, path, content_sha256])


def _symbol_id(
    snapshot_sha256: str,
    path: str,
    content_sha256: str,
    name: str,
    start_line: int,
    end_line: int,
) -> str:
    return "symbol-" + _canonical_digest(
        [snapshot_sha256, path, content_sha256, name, start_line, end_line]
    )


def _unavailable_reference(segment_id: str) -> dict[str, object]:
    return {
        "segment_id": segment_id,
        "segment_kind": "unresolved",
        "source_path": None,
        "snapshot_sha256": None,
        "content_sha256": None,
        "artifact_handle_id": None,
        "span_status": "unavailable",
        "start_line": None,
        "end_line": None,
        "parser": None,
        "language": None,
        "summary_lineage_status": "unavailable",
        "summary_of": None,
    }


def build_selected_segment_source_references(
    *,
    snapshot_sha256: str,
    selected_segment_ids: Sequence[str],
    sources: Sequence[SourceIdentity],
    candidates: Sequence[StructuralCandidate] = (),
) -> SelectedSourceReferenceReceipt:
    """Join selected IDs to source identities and optional exact symbol spans.

    ``selected_segment_ids``, ``sources`` and ``candidates`` are caller-owned
    public records. Candidate rows must be the exact rows used to create
    symbol segments if exact spans are desired. Missing rows stay explicitly
    unavailable; no span or summary lineage is inferred from an ID alone.
    """
    snapshot_hash = _require_hash(snapshot_sha256, "snapshot_sha256")
    if type(selected_segment_ids) not in (tuple, list) or len(selected_segment_ids) > MAX_SELECTED_REFERENCES:
        raise SelectedSourceReferenceError("selected_segment_ids_invalid")
    if type(sources) not in (tuple, list) or len(sources) > MAX_SELECTED_REFERENCES:
        raise SelectedSourceReferenceError("sources_invalid")
    if type(candidates) not in (tuple, list) or len(candidates) > MAX_CANDIDATES:
        raise SelectedSourceReferenceError("candidates_invalid")

    selected = tuple(selected_segment_ids)
    if any(type(item) is not str or not item or len(item) > 256 for item in selected):
        raise SelectedSourceReferenceError("selected_segment_id_invalid")
    if len(set(selected)) != len(selected):
        raise SelectedSourceReferenceError("duplicate_selected_segment_id")

    source_by_id: dict[str, SourceIdentity] = {}
    source_by_path: dict[str, SourceIdentity] = {}
    for source in sources:
        if type(source) is not SourceIdentity:
            raise SelectedSourceReferenceError("source_identity_invalid")
        if (
            type(source.evidence_id) is not str or not source.evidence_id or len(source.evidence_id) > 256
            or type(source.path) is not str or not source.path or len(source.path) > 1024
        ):
            raise SelectedSourceReferenceError("source_identity_fields_invalid")
        if source.status == "ok":
            digest = _require_hash(source.content_sha256, "source_content_sha256")
            handle_id = _require_hash(source.artifact_handle_id, "artifact_handle_id")
            expected_id = _source_id(snapshot_hash, source.path, digest)
            if source.evidence_id != expected_id:
                raise SelectedSourceReferenceError("source_identity_mismatch")
            if source.path in source_by_path or source.evidence_id in source_by_id:
                raise SelectedSourceReferenceError("duplicate_source_identity")
            source_by_id[source.evidence_id] = source
            source_by_path[source.path] = source
        elif source.evidence_id in source_by_id:
            raise SelectedSourceReferenceError("duplicate_source_identity")

    candidate_by_id: dict[str, StructuralCandidate] = {}
    for candidate in candidates:
        if type(candidate) is not StructuralCandidate:
            raise SelectedSourceReferenceError("structural_candidate_invalid")
        if (
            type(candidate.path) is not str or not candidate.path or len(candidate.path) > 1024
            or type(candidate.name) is not str or not candidate.name or len(candidate.name) > 256
        ):
            raise SelectedSourceReferenceError("candidate_identity_fields_invalid")
        if _require_hash(candidate.snapshot_sha256, "candidate_snapshot_sha256") != snapshot_hash:
            raise SelectedSourceReferenceError("candidate_snapshot_mismatch")
        source = source_by_path.get(candidate.path)
        if (
            source is None
            or _require_hash(candidate.source_sha256, "candidate_source_sha256") != source.content_sha256
        ):
            raise SelectedSourceReferenceError("candidate_source_mismatch")
        if (
            type(candidate.start_line) is not int or type(candidate.end_line) is not int
            or not 1 <= candidate.start_line <= candidate.end_line <= 2**31 - 1
        ):
            raise SelectedSourceReferenceError("candidate_span_invalid")
        if (
            type(candidate.parser) is not str or not candidate.parser or len(candidate.parser) > 128
            or type(candidate.language) is not str or not candidate.language or len(candidate.language) > 128
        ):
            raise SelectedSourceReferenceError("candidate_metadata_invalid")
        candidate_id = _symbol_id(
            snapshot_hash,
            candidate.path,
            source.content_sha256,
            candidate.name,
            candidate.start_line,
            candidate.end_line,
        )
        if candidate_id in candidate_by_id:
            raise SelectedSourceReferenceError("duplicate_candidate_identity")
        candidate_by_id[candidate_id] = candidate

    references: list[dict[str, object]] = []
    for segment_id in selected:
        source = source_by_id.get(segment_id)
        if source is not None:
            references.append({
                "segment_id": segment_id,
                "segment_kind": "source",
                "source_path": source.path,
                "snapshot_sha256": snapshot_hash,
                "content_sha256": source.content_sha256,
                "artifact_handle_id": source.artifact_handle_id,
                "span_status": "whole_file",
                "start_line": None,
                "end_line": None,
                "parser": None,
                "language": None,
                "summary_lineage_status": "unavailable",
                "summary_of": None,
            })
            continue

        candidate = candidate_by_id.get(segment_id)
        if candidate is None:
            references.append(_unavailable_reference(segment_id))
            continue
        source = source_by_path[candidate.path]
        references.append({
            "segment_id": segment_id,
            "segment_kind": "symbol",
            "source_path": source.path,
            "snapshot_sha256": snapshot_hash,
            "content_sha256": source.content_sha256,
            "artifact_handle_id": source.artifact_handle_id,
            "span_status": "parser_reported_exact",
            "start_line": candidate.start_line,
            "end_line": candidate.end_line,
            "parser": candidate.parser,
            "language": candidate.language,
            "summary_lineage_status": "unavailable",
            "summary_of": None,
        })

    receipt_payload = {
        "schema": "wrench.selected-segment-source-references.v1",
        "snapshot_sha256": snapshot_hash,
        "selected_segment_ids": list(selected),
        "references": references,
    }
    digest = _canonical_digest(receipt_payload)
    return SelectedSourceReferenceReceipt(
        schema=receipt_payload["schema"],
        snapshot_sha256=snapshot_hash,
        selected_segment_ids=selected,
        references=tuple(MappingProxyType(row) for row in references),
        receipt_sha256=digest,
    )


__all__ = [
    "SelectedSourceReferenceError",
    "SelectedSourceReferenceReceipt",
    "build_selected_segment_source_references",
]
