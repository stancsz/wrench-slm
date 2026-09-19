"""Deterministic logical-context storage and bounded context assembly.

This module does not claim native long-context model support. It keeps a
hashable logical session, indexes text once, retrieves relevant segments, and
assembles a bounded working set for a model call. Tool-call units are atomic
so compaction cannot silently split a call from its result.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Iterable


MAX_LOGICAL_CONTEXT_TOKENS = 2_000_000
RETENTION_TIERS = {"hot", "warm", "reference", "cold"}
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class ContextError(ValueError):
    """Base class for fail-closed logical-context errors."""


class ContextAdmissionError(ContextError):
    """Raised when a segment cannot be admitted without breaking invariants."""


class ContextSelectionError(ContextError):
    """Raised when required context cannot fit the active model budget."""


def _tokens(text: str) -> list[str]:
    return [match.casefold() for match in _TOKEN_RE.findall(text)]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class ContextSegment:
    """One immutable logical-context segment."""

    segment_id: str
    text: str
    source_order: int
    token_count: int
    role: str = "context"
    kind: str = "context"
    retention: str = "warm"
    unit_id: str | None = None
    summary_of: tuple[str, ...] = ()
    counts_toward_logical_limit: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def text_sha256(self) -> str:
        return _sha256(self.text.encode("utf-8"))

    def receipt(self) -> dict[str, object]:
        return {
            "segment_id": self.segment_id,
            "source_order": self.source_order,
            "token_count": self.token_count,
            "role": self.role,
            "kind": self.kind,
            "retention": self.retention,
            "unit_id": self.unit_id,
            "summary_of": list(self.summary_of),
            "counts_toward_logical_limit": self.counts_toward_logical_limit,
            "text_sha256": self.text_sha256,
        }


class ContextLedger:
    """Store a logical session and assemble a bounded active context.

    The default token counter is deliberately labelled as an estimate. A
    production caller should provide the exact tokenizer used by the target
    runtime or pass explicit token counts from that tokenizer.
    """

    def __init__(
        self,
        *,
        max_logical_tokens: int = MAX_LOGICAL_CONTEXT_TOKENS,
        token_counter: Callable[[str], int] | None = None,
        token_counter_name: str | None = None,
    ) -> None:
        if not isinstance(max_logical_tokens, int) or isinstance(max_logical_tokens, bool) or max_logical_tokens < 1:
            raise ValueError("max_logical_tokens must be a positive integer")
        self.max_logical_tokens = max_logical_tokens
        self._token_counter = token_counter
        default_counter_name = "custom" if token_counter is not None else "word_estimate_v1"
        if token_counter_name is not None and (not isinstance(token_counter_name, str) or not token_counter_name):
            raise ValueError("token_counter_name must be null or a non-empty string")
        self.token_counter_name = token_counter_name or default_counter_name
        self._segments: dict[str, ContextSegment] = {}
        self._source_orders: dict[int, str] = {}
        self._units: dict[str, list[str]] = defaultdict(list)
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
        self._logical_token_count = 0
        self._token_count_modes: set[str] = set()
        self._session_hash: str | None = None

    @property
    def logical_token_count(self) -> int:
        return self._logical_token_count

    @property
    def segment_count(self) -> int:
        return len(self._segments)

    @property
    def token_count_mode(self) -> str:
        if not self._token_count_modes:
            return "empty"
        if len(self._token_count_modes) == 1:
            return next(iter(self._token_count_modes))
        return "mixed"

    @property
    def effective_token_counter_name(self) -> str:
        if self.token_count_mode == "explicit":
            return "caller_explicit_counts"
        if self.token_count_mode == "mixed":
            return "mixed_sources"
        return self.token_counter_name

    def _count_tokens(self, text: str, explicit: int | None) -> tuple[int, str]:
        if explicit is not None:
            count = explicit
            mode = "explicit"
        elif self._token_counter is not None:
            count = self._token_counter(text)
            mode = "custom"
        else:
            count = len(_tokens(text))
            mode = "word_estimate"
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ContextAdmissionError("token_count must be a positive integer")
        return count, mode

    def add_segment(
        self,
        segment_id: str,
        text: str,
        source_order: int,
        *,
        token_count: int | None = None,
        role: str = "context",
        kind: str = "context",
        retention: str = "warm",
        unit_id: str | None = None,
        summary_of: Iterable[str] = (),
        counts_toward_logical_limit: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> ContextSegment:
        """Add one segment without mutating the ledger on validation failure."""

        if not isinstance(segment_id, str) or not segment_id:
            raise ContextAdmissionError("segment_id must be a non-empty string")
        if segment_id in self._segments:
            raise ContextAdmissionError("duplicate segment_id")
        if not isinstance(text, str) or not text:
            raise ContextAdmissionError("text must be a non-empty string")
        if not isinstance(source_order, int) or isinstance(source_order, bool) or source_order < 0:
            raise ContextAdmissionError("source_order must be a non-negative integer")
        if source_order in self._source_orders:
            raise ContextAdmissionError("duplicate source_order")
        if not isinstance(role, str) or not role or not isinstance(kind, str) or not kind:
            raise ContextAdmissionError("role and kind must be non-empty strings")
        if retention not in RETENTION_TIERS:
            raise ContextAdmissionError("invalid_retention_tier")
        if unit_id is not None and (not isinstance(unit_id, str) or not unit_id):
            raise ContextAdmissionError("unit_id must be null or a non-empty string")
        if not isinstance(counts_toward_logical_limit, bool):
            raise ContextAdmissionError("counts_toward_logical_limit must be boolean")
        references = tuple(summary_of)
        if any(not isinstance(item, str) or not item for item in references):
            raise ContextAdmissionError("summary_of must contain non-empty strings")
        if len(set(references)) != len(references):
            raise ContextAdmissionError("summary_of contains duplicates")
        counts, mode = self._count_tokens(text, token_count)
        if counts_toward_logical_limit and self._logical_token_count + counts > self.max_logical_tokens:
            raise ContextAdmissionError("logical_context_limit_exceeded")

        segment = ContextSegment(
            segment_id=segment_id,
            text=text,
            source_order=source_order,
            token_count=counts,
            role=role,
            kind=kind,
            retention=retention,
            unit_id=unit_id,
            summary_of=references,
            counts_toward_logical_limit=counts_toward_logical_limit,
            metadata=dict(metadata or {}),
        )
        self._segments[segment_id] = segment
        self._source_orders[source_order] = segment_id
        if counts_toward_logical_limit:
            self._logical_token_count += counts
        self._token_count_modes.add(mode)
        self._session_hash = None
        unit_key = unit_id or f"segment:{segment_id}"
        self._units[unit_key].append(segment_id)
        for term in set(_tokens(text)):
            self._inverted_index[term].add(segment_id)
        return segment

    def add_summary(
        self,
        segment_id: str,
        text: str,
        source_order: int,
        *,
        summary_of: Iterable[str],
        token_count: int | None = None,
        level: str = "segment",
        retention: str = "warm",
        metadata: dict[str, str] | None = None,
    ) -> ContextSegment:
        """Add a derived summary without double-counting source tokens."""

        references = tuple(summary_of)
        if not references or any(reference not in self._segments for reference in references):
            raise ContextAdmissionError("summary_of references missing source segments")
        summary_metadata = dict(metadata or {})
        summary_metadata["summary_level"] = level
        return self.add_segment(
            segment_id,
            text,
            source_order,
            token_count=token_count,
            kind="summary",
            retention=retention,
            summary_of=references,
            counts_toward_logical_limit=False,
            metadata=summary_metadata,
        )

    def _unit_for(self, segment_id: str) -> str:
        segment = self._segments[segment_id]
        return segment.unit_id or f"segment:{segment_id}"

    def _unit_segments(self, unit_id: str) -> list[ContextSegment]:
        return sorted((self._segments[item] for item in self._units[unit_id]), key=lambda item: item.source_order)

    def search(self, query: str, *, limit: int = 32) -> list[ContextSegment]:
        """Return indexed lexical matches without rescanning every segment."""

        if not isinstance(query, str):
            raise ContextSelectionError("query must be a string")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10_000:
            raise ContextSelectionError("invalid search limit")
        terms = Counter(_tokens(query))
        scores: Counter[str] = Counter()
        for term, weight in terms.items():
            for segment_id in self._inverted_index.get(term, ()):
                scores[segment_id] += weight
        return sorted(
            (self._segments[segment_id] for segment_id in scores),
            key=lambda item: (-scores[item.segment_id], -item.source_order, item.segment_id),
        )[:limit]

    def session_hash(self) -> str:
        if self._session_hash is not None:
            return self._session_hash
        canonical = [
            self._segments[segment_id].receipt()
            | {"text": self._segments[segment_id].text}
            for segment_id in sorted(self._segments, key=lambda item: self._segments[item].source_order)
        ]
        self._session_hash = _sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        return self._session_hash

    def assemble(
        self,
        query: str,
        *,
        active_token_budget: int,
        preserve_ids: Iterable[str] = (),
        search_limit: int = 32,
        receipt_detail: str = "full",
    ) -> dict[str, object]:
        """Build a bounded context and an auditable assembly receipt.

        Selection is whole-unit only. If one preserved ID belongs to a tool
        call/result unit, every member of that unit is selected or the call
        fails closed because the unit cannot fit.
        """

        if not isinstance(active_token_budget, int) or isinstance(active_token_budget, bool) or active_token_budget < 1:
            raise ContextSelectionError("active_token_budget must be positive")
        if active_token_budget > self.max_logical_tokens:
            raise ContextSelectionError("active_token_budget_exceeds_logical_limit")
        if receipt_detail not in {"full", "summary"}:
            raise ContextSelectionError("invalid_receipt_detail")
        preserve = tuple(preserve_ids)
        unknown = [item for item in preserve if item not in self._segments]
        if unknown:
            raise ContextSelectionError("preserved_segment_missing")

        ordered_units: list[str] = []
        ordered_unit_set: set[str] = set()
        mandatory_units: set[str] = set()
        for segment_id in preserve:
            unit_id = self._unit_for(segment_id)
            mandatory_units.add(unit_id)
            if unit_id not in ordered_unit_set:
                ordered_units.append(unit_id)
                ordered_unit_set.add(unit_id)
        # Recent hot/warm context is the default working set. Reference and
        # cold material remains queryable in the ledger but is not silently
        # forwarded to the model. Callers must explicitly preserve a reference
        # segment when it is needed for the current task.
        active_segments = [
            segment
            for segment in self._segments.values()
            if segment.retention in {"hot", "warm"}
        ]
        for segment in sorted(active_segments, key=lambda item: -item.source_order):
            unit_id = self._unit_for(segment.segment_id)
            if unit_id not in ordered_unit_set:
                ordered_units.append(unit_id)
                ordered_unit_set.add(unit_id)

        selected_ids: set[str] = set()
        omitted: dict[str, str] = {}
        selected_tokens = 0
        for unit_id in ordered_units:
            if selected_tokens >= active_token_budget:
                break
            members = self._unit_segments(unit_id)
            member_ids = [item.segment_id for item in members]
            unit_tokens = sum(item.token_count for item in members)
            if unit_id in mandatory_units and selected_tokens + unit_tokens > active_token_budget:
                raise ContextSelectionError("preserved_unit_exceeds_active_budget")
            if selected_tokens + unit_tokens <= active_token_budget:
                selected_ids.update(member_ids)
                selected_tokens += unit_tokens
            else:
                reason = "unit_exceeds_active_budget" if unit_tokens > active_token_budget else "active_token_budget"
                for member_id in member_ids:
                    omitted[member_id] = reason

        selected = sorted((self._segments[item] for item in selected_ids), key=lambda item: item.source_order)
        for segment_id in self._segments:
            if segment_id not in selected_ids and segment_id not in omitted:
                omitted[segment_id] = "not_selected"
        assembled_text = "\n\n".join(
            f"[context:{segment.segment_id}]\n{segment.text}" for segment in selected
        )
        omitted_ids = sorted(omitted, key=lambda item: self._segments[item].source_order)
        reason_counts = Counter(omitted.values())
        omitted_digest_builder = hashlib.sha256()
        omitted_digest_builder.update(b"[")
        omitted_rows: list[dict[str, object]] = []
        for index, segment_id in enumerate(omitted_ids):
            row = {"segment_id": segment_id, "reason": omitted[segment_id]}
            if index:
                omitted_digest_builder.update(b",")
            omitted_digest_builder.update(
                json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
            if receipt_detail == "full":
                omitted_rows.append(row)
        omitted_digest_builder.update(b"]")
        omitted_digest = omitted_digest_builder.hexdigest()
        return {
            "schema": "wrench.context-assembly.v1",
            "session_hash": self.session_hash(),
            "query_sha256": _sha256(query.encode("utf-8")),
            "logical_token_count": self.logical_token_count,
            "active_token_budget": active_token_budget,
            "selected_token_count": selected_tokens,
            "token_count_mode": self.token_count_mode,
            "token_counter_name": self.effective_token_counter_name,
            "selected_segments": [segment.receipt() for segment in selected],
            "receipt_detail": receipt_detail,
            "omitted_segment_count": len(omitted_ids),
            "omitted_reason_counts": dict(sorted(reason_counts.items())),
            "omitted_segments_digest": omitted_digest,
            "omitted_segments": omitted_rows if receipt_detail == "full" else [],
            "assembled_text": assembled_text,
        }
