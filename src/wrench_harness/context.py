"""Deterministic logical-context storage and bounded context assembly.

This module does not claim native long-context model support. It keeps a
hashable logical session, indexes text once, retrieves relevant segments, and
assembles a bounded working set for a model call. Tool-call units are atomic
so compaction cannot silently split a call from its result.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from itertools import islice
from types import MappingProxyType
from typing import Callable, Iterable, Mapping


MAX_LOGICAL_CONTEXT_TOKENS = 2_000_000
MAX_CONTEXT_SEGMENTS = 10_000
MAX_CONTEXT_TEXT_BYTES = 4 * 1024 * 1024
MAX_CONTEXT_SEGMENT_BYTES = 256 * 1024
MAX_CONTEXT_AUX_BYTES = 16 * 1024 * 1024
MAX_CONTEXT_SUMMARY_REFS = 256
MAX_CONTEXT_METADATA_FIELDS = 64
MAX_CONTEXT_METADATA_BYTES = 1024
MAX_CONTEXT_ID_CHARS = 256
MAX_CONTEXT_LABEL_CHARS = 64
MAX_SEARCH_QUERY_CHARS = 4_096
MAX_SEARCH_QUERY_TERMS = 256
MAX_SEARCH_TERM_DOCUMENT_CHECKS = 100_000
MAX_RETRIEVAL_PAGE_SIZE = 32
MAX_RETRIEVAL_PAGES = 2
MAX_RETRIEVAL_CANDIDATES = MAX_RETRIEVAL_PAGE_SIZE * MAX_RETRIEVAL_PAGES
RETENTION_TIERS = {"hot", "warm", "reference", "cold"}
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContextError(ValueError):
    """Base class for fail-closed logical-context errors."""


class ContextAdmissionError(ContextError):
    """Raised when a segment cannot be admitted without breaking invariants."""


class ContextSelectionError(ContextError):
    """Raised when required context cannot fit the active model budget."""


class RetrievalDecision(str, Enum):
    """Caller-owned decision controlling one bounded candidate page."""

    ENOUGH = "enough"
    RETRIEVE_MORE = "retrieve_more"


class RetrievalPageStatus(str, Enum):
    """Outcome of one in-memory candidate page request."""

    STOPPED = "stopped"
    MORE_AVAILABLE = "more_available"
    EXHAUSTED = "exhausted"
    CANDIDATE_LIMIT = "candidate_limit"
    WORK_LIMIT = "work_limit"
    INVALID_CURSOR = "invalid_cursor"


@dataclass(frozen=True)
class RetrievalCursor:
    """Continuation reference bound to one immutable ledger/query pair.

    The digest detects accidental edits. It is not an authentication token.
    """

    schema: str
    session_sha256: str
    query_sha256: str
    next_offset: int
    page_count: int
    cursor_sha256: str


@dataclass(frozen=True)
class RetrievalPage:
    """Content-free result for one caller-controlled retrieval decision."""

    schema: str
    decision: RetrievalDecision
    status: RetrievalPageStatus
    session_sha256: str
    query_sha256: str
    candidate_ids: tuple[str, ...]
    cursor: RetrievalCursor | None


def _tokens(text: str) -> list[str]:
    return [match.casefold() for match in _TOKEN_RE.findall(text)]


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _retrieval_cursor_sha256(
    *, session_sha256: str, query_sha256: str, next_offset: int, page_count: int
) -> str:
    payload = {
        "schema": "wrench.context-retrieval-cursor.v1",
        "session_sha256": session_sha256,
        "query_sha256": query_sha256,
        "next_offset": next_offset,
        "page_count": page_count,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(encoded)


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
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

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
        self._inverted_index: dict[str, dict[str, int]] = defaultdict(dict)
        self._logical_token_count = 0
        self._stored_text_bytes = 0
        self._stored_aux_bytes = 0
        self._token_count_modes: set[str] = set()
        self._session_hash: str | None = None
        self._indexed_token_total = 0
        self._indexed_lengths: dict[str, int] = {}

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
        if len(segment_id) > MAX_CONTEXT_ID_CHARS:
            raise ContextAdmissionError("context_identifier_limit_exceeded")
        if segment_id in self._segments:
            raise ContextAdmissionError("duplicate segment_id")
        if not isinstance(text, str) or not text:
            raise ContextAdmissionError("text must be a non-empty string")
        if len(text) > MAX_CONTEXT_SEGMENT_BYTES:
            raise ContextAdmissionError("context_segment_byte_limit_exceeded")
        text_bytes = len(text.encode("utf-8"))
        if text_bytes > MAX_CONTEXT_SEGMENT_BYTES:
            raise ContextAdmissionError("context_segment_byte_limit_exceeded")
        if len(self._segments) >= MAX_CONTEXT_SEGMENTS:
            raise ContextAdmissionError("context_segment_count_limit_exceeded")
        if self._stored_text_bytes + text_bytes > MAX_CONTEXT_TEXT_BYTES:
            raise ContextAdmissionError("context_text_byte_limit_exceeded")
        if (
            not isinstance(source_order, int)
            or isinstance(source_order, bool)
            or not 0 <= source_order <= (2**63 - 1)
        ):
            raise ContextAdmissionError("source_order must be a non-negative integer")
        if source_order in self._source_orders:
            raise ContextAdmissionError("duplicate source_order")
        if not isinstance(role, str) or not role or not isinstance(kind, str) or not kind:
            raise ContextAdmissionError("role and kind must be non-empty strings")
        if len(role) > MAX_CONTEXT_LABEL_CHARS or len(kind) > MAX_CONTEXT_LABEL_CHARS:
            raise ContextAdmissionError("context_label_limit_exceeded")
        if not isinstance(retention, str) or retention not in RETENTION_TIERS:
            raise ContextAdmissionError("invalid_retention_tier")
        if unit_id is not None and (not isinstance(unit_id, str) or not unit_id):
            raise ContextAdmissionError("unit_id must be null or a non-empty string")
        if unit_id is not None and len(unit_id) > MAX_CONTEXT_ID_CHARS:
            raise ContextAdmissionError("context_identifier_limit_exceeded")
        if not isinstance(counts_toward_logical_limit, bool):
            raise ContextAdmissionError("counts_toward_logical_limit must be boolean")
        if isinstance(summary_of, (str, bytes)):
            raise ContextAdmissionError("summary_of must be an iterable of identifiers")
        try:
            references = tuple(islice(iter(summary_of), MAX_CONTEXT_SUMMARY_REFS + 1))
        except TypeError as exc:
            raise ContextAdmissionError("summary_of must be iterable") from exc
        if len(references) > MAX_CONTEXT_SUMMARY_REFS:
            raise ContextAdmissionError("summary_reference_limit_exceeded")
        if any(not isinstance(item, str) or not item for item in references):
            raise ContextAdmissionError("summary_of must contain non-empty strings")
        if any(len(item) > MAX_CONTEXT_ID_CHARS for item in references):
            raise ContextAdmissionError("context_identifier_limit_exceeded")
        if len(set(references)) != len(references):
            raise ContextAdmissionError("summary_of contains duplicates")
        if metadata is not None and not isinstance(metadata, dict):
            raise ContextAdmissionError("metadata must be a dictionary")
        metadata_values = {} if metadata is None else metadata
        if len(metadata_values) > MAX_CONTEXT_METADATA_FIELDS:
            raise ContextAdmissionError("context_metadata_field_limit_exceeded")
        metadata_bytes = 0
        for key, value in metadata_values.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ContextAdmissionError("metadata keys and values must be strings")
            if len(key) > MAX_CONTEXT_METADATA_BYTES or len(value) > MAX_CONTEXT_METADATA_BYTES:
                raise ContextAdmissionError("context_metadata_byte_limit_exceeded")
            metadata_bytes += len(key.encode("utf-8")) + len(value.encode("utf-8"))
        if metadata_bytes > MAX_CONTEXT_METADATA_BYTES:
            raise ContextAdmissionError("context_metadata_byte_limit_exceeded")
        aux_strings = (segment_id, role, kind, retention, *references)
        if unit_id is not None:
            aux_strings += (unit_id,)
        aux_bytes = sum(len(value.encode("utf-8")) for value in aux_strings) + metadata_bytes
        if self._stored_aux_bytes + aux_bytes > MAX_CONTEXT_AUX_BYTES:
            raise ContextAdmissionError("context_auxiliary_byte_limit_exceeded")
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
            metadata=dict(metadata_values),
        )
        self._segments[segment_id] = segment
        self._stored_text_bytes += text_bytes
        self._stored_aux_bytes += aux_bytes
        self._source_orders[source_order] = segment_id
        if counts_toward_logical_limit:
            self._logical_token_count += counts
        self._token_count_modes.add(mode)
        self._session_hash = None
        unit_key = unit_id or f"segment:{segment_id}"
        self._units[unit_key].append(segment_id)
        tokens = _tokens(text)
        term_frequencies = Counter(tokens)
        self._indexed_token_total += len(tokens)
        self._indexed_lengths[segment_id] = len(tokens)
        for term, frequency in term_frequencies.items():
            self._inverted_index[term][segment_id] = frequency
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

    def _search_candidates(
        self, query: str, *, limit: int
    ) -> tuple[list[ContextSegment], bool]:
        """Return bounded BM25 candidates and whether posting work was clipped."""
        if not isinstance(query, str):
            raise ContextSelectionError("query must be a string")
        if len(query) > MAX_SEARCH_QUERY_CHARS:
            raise ContextSelectionError("query_character_limit_exceeded")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10_000:
            raise ContextSelectionError("invalid search limit")
        terms = Counter(_tokens(query))
        if len(terms) > MAX_SEARCH_QUERY_TERMS:
            raise ContextSelectionError("query_term_limit_exceeded")
        if not terms:
            return [], False
        document_count = len(self._segments)
        average_length = self._indexed_token_total / max(1, document_count)
        k1 = 1.2
        b = 0.75
        scores: dict[str, float] = defaultdict(float)
        term_document_checks = 0
        truncated = False
        recent_segment_ids = sorted(
            self._segments,
            key=lambda segment_id: (-self._segments[segment_id].source_order, segment_id),
        )
        for term in sorted(terms):
            query_frequency = terms[term]
            posting = self._inverted_index.get(term, {})
            document_frequency = len(posting)
            if not document_frequency:
                continue
            inverse_document_frequency = math.log1p(
                (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            # Scan segments in source recency order so truncation keeps newer
            # evidence even when ingestion order differs from source order.
            for segment_id in recent_segment_ids:
                if term_document_checks >= MAX_SEARCH_TERM_DOCUMENT_CHECKS:
                    truncated = True
                    break
                term_document_checks += 1
                term_frequency = posting.get(segment_id)
                if term_frequency is None:
                    continue
                document_length = self._indexed_lengths[segment_id]
                normalization = k1 * (1.0 - b + b * document_length / max(1.0, average_length))
                term_score = inverse_document_frequency * (
                    term_frequency * (k1 + 1.0) / (term_frequency + normalization)
                )
                scores[segment_id] += query_frequency * term_score
            if truncated:
                break
        candidates = sorted(
            (self._segments[segment_id] for segment_id in scores),
            key=lambda item: (-scores[item.segment_id], -item.source_order, item.segment_id),
        )[:limit]
        return candidates, truncated

    def search(self, query: str, *, limit: int = 32) -> list[ContextSegment]:
        """Return BM25-ranked candidates under the configured posting-work cap."""

        candidates, _ = self._search_candidates(query, limit=limit)
        return candidates

    def retrieve_page(
        self,
        query: str,
        decision: RetrievalDecision,
        *,
        cursor: RetrievalCursor | None = None,
    ) -> RetrievalPage:
        """Return a caller-requested page of known BM25 candidate IDs.

        There is at most one continuation page. Each page contains up to 32
        IDs; the full ranked pool is bounded at 64 candidates plus one probe
        used to report ``candidate_limit``. A caller can stop at any time by
        sending ``ENOUGH``. Work-truncated rankings fail closed without IDs.
        This method is in-memory only and performs no source retrieval.
        Replaying a cursor or restarting from page one can repeat results;
        this bounds one continuation chain, not total caller invocations.
        """

        if type(decision) is not RetrievalDecision:
            raise ContextSelectionError("invalid retrieval decision")
        if (
            not isinstance(query, str)
            or len(query) > MAX_SEARCH_QUERY_CHARS
            or len(_tokens(query)) > MAX_SEARCH_QUERY_TERMS
        ):
            raise ContextSelectionError("invalid retrieval query")

        session_hash = self.session_hash()
        query_hash = _sha256(query.encode("utf-8"))
        if cursor is not None and not self._valid_retrieval_cursor(cursor, session_hash, query_hash):
            return RetrievalPage(
                "wrench.context-retrieval-page.v1", decision,
                RetrievalPageStatus.INVALID_CURSOR, session_hash, query_hash, (), None,
            )
        if decision is RetrievalDecision.ENOUGH:
            return RetrievalPage(
                "wrench.context-retrieval-page.v1", decision,
                RetrievalPageStatus.STOPPED, session_hash, query_hash, (), None,
            )

        if cursor is None:
            offset = 0
        else:
            offset = cursor.next_offset
        ranked, work_truncated = self._search_candidates(
            query, limit=MAX_RETRIEVAL_CANDIDATES + 1
        )
        if work_truncated:
            return RetrievalPage(
                "wrench.context-retrieval-page.v1", decision,
                RetrievalPageStatus.WORK_LIMIT, session_hash, query_hash, (), None,
            )

        end = offset + MAX_RETRIEVAL_PAGE_SIZE
        page_segments = ranked[offset:end]
        candidate_ids = tuple(segment.segment_id for segment in page_segments)
        if any(segment_id not in self._segments for segment_id in candidate_ids):
            # Defensive invariant: ranking may only reference admitted ledger IDs.
            return RetrievalPage(
                "wrench.context-retrieval-page.v1", decision,
                RetrievalPageStatus.WORK_LIMIT, session_hash, query_hash, (), None,
            )

        if offset == 0 and len(ranked) > end:
            next_cursor = self._make_retrieval_cursor(session_hash, query_hash, end, 1)
            status = RetrievalPageStatus.MORE_AVAILABLE
        elif len(ranked) > MAX_RETRIEVAL_CANDIDATES:
            next_cursor = None
            status = RetrievalPageStatus.CANDIDATE_LIMIT
        else:
            next_cursor = None
            status = RetrievalPageStatus.EXHAUSTED
        return RetrievalPage(
            "wrench.context-retrieval-page.v1", decision, status,
            session_hash, query_hash, candidate_ids, next_cursor,
        )

    @staticmethod
    def _make_retrieval_cursor(
        session_hash: str, query_hash: str, next_offset: int, page_count: int
    ) -> RetrievalCursor:
        digest = _retrieval_cursor_sha256(
            session_sha256=session_hash, query_sha256=query_hash,
            next_offset=next_offset, page_count=page_count,
        )
        return RetrievalCursor(
            "wrench.context-retrieval-cursor.v1", session_hash, query_hash,
            next_offset, page_count, digest,
        )

    @staticmethod
    def _valid_retrieval_cursor(
        cursor: RetrievalCursor, session_hash: str, query_hash: str
    ) -> bool:
        if type(cursor) is not RetrievalCursor:
            return False
        if (
            type(cursor.schema) is not str
            or type(cursor.session_sha256) is not str
            or type(cursor.query_sha256) is not str
            or type(cursor.next_offset) is not int
            or type(cursor.page_count) is not int
            or cursor.schema != "wrench.context-retrieval-cursor.v1"
            or cursor.session_sha256 != session_hash
            or cursor.query_sha256 != query_hash
            or cursor.next_offset != MAX_RETRIEVAL_PAGE_SIZE
            or cursor.page_count != 1
            or type(cursor.cursor_sha256) is not str
            or _SHA256_RE.fullmatch(cursor.cursor_sha256) is None
        ):
            return False
        expected = _retrieval_cursor_sha256(
            session_sha256=cursor.session_sha256,
            query_sha256=cursor.query_sha256,
            next_offset=cursor.next_offset,
            page_count=cursor.page_count,
        )
        return cursor.cursor_sha256 == expected

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
        on_preserved_overflow: str = "raise",
        search_limit: int = 32,
        receipt_detail: str = "full",
    ) -> dict[str, object]:
        """Build a bounded context and an auditable assembly receipt.

        Selection is whole-unit only. If one preserved ID belongs to a tool
        call/result unit, every member of that unit is selected or the call
        fails closed because the unit cannot fit. A higher-level caller with a
        required-evidence gate may set ``on_preserved_overflow="omit"`` to
        receive the explicit omission row and let that gate produce its
        structured rejection receipt. The default retains the original
        exception behavior.
        """

        if not isinstance(active_token_budget, int) or isinstance(active_token_budget, bool) or active_token_budget < 1:
            raise ContextSelectionError("active_token_budget must be positive")
        if active_token_budget > self.max_logical_tokens:
            raise ContextSelectionError("active_token_budget_exceeds_logical_limit")
        if receipt_detail not in {"full", "summary"}:
            raise ContextSelectionError("invalid_receipt_detail")
        if on_preserved_overflow not in {"raise", "omit"}:
            raise ContextSelectionError("invalid_preserved_overflow_policy")
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
        # Preserve hot evidence first, then add query-ranked candidates. This
        # makes reference/cold material retrievable without forwarding
        # unrelated history by default. Warm recency is the final fallback.
        hot_segments = [
            segment for segment in self._segments.values() if segment.retention == "hot"
        ]
        for segment in sorted(hot_segments, key=lambda item: -item.source_order):
            unit_id = self._unit_for(segment.segment_id)
            if unit_id not in ordered_unit_set:
                ordered_units.append(unit_id)
                ordered_unit_set.add(unit_id)

        retrieval_candidates, retrieval_truncated = self._search_candidates(
            query, limit=search_limit
        )
        for segment in retrieval_candidates:
            unit_id = self._unit_for(segment.segment_id)
            if unit_id not in ordered_unit_set:
                ordered_units.append(unit_id)
                ordered_unit_set.add(unit_id)

        warm_segments = [
            segment for segment in self._segments.values() if segment.retention == "warm"
        ]
        for segment in sorted(warm_segments, key=lambda item: -item.source_order):
            unit_id = self._unit_for(segment.segment_id)
            if unit_id not in ordered_unit_set:
                ordered_units.append(unit_id)
                ordered_unit_set.add(unit_id)

        selected_ids: set[str] = set()
        omitted: dict[str, str] = {}
        selected_tokens = 0
        for unit_index, unit_id in enumerate(ordered_units):
            if selected_tokens >= active_token_budget:
                for pending_unit_id in ordered_units[unit_index:]:
                    if pending_unit_id in mandatory_units:
                        if on_preserved_overflow == "raise":
                            raise ContextSelectionError("preserved_unit_exceeds_active_budget")
                        else:
                            for pending in self._unit_segments(pending_unit_id):
                                omitted[pending.segment_id] = "preserved_unit_exceeds_active_budget"
                break
            members = self._unit_segments(unit_id)
            member_ids = [item.segment_id for item in members]
            unit_tokens = sum(item.token_count for item in members)
            if unit_id in mandatory_units and selected_tokens + unit_tokens > active_token_budget:
                if on_preserved_overflow == "raise":
                    raise ContextSelectionError("preserved_unit_exceeds_active_budget")
                for member_id in member_ids:
                    omitted[member_id] = "preserved_unit_exceeds_active_budget"
                continue
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
            "schema": "wrench.context-assembly.v2",
            "session_hash": self.session_hash(),
            "query_sha256": _sha256(query.encode("utf-8")),
            "logical_token_count": self.logical_token_count,
            "active_token_budget": active_token_budget,
            "selected_token_count": selected_tokens,
            "retrieval_candidate_ids": [segment.segment_id for segment in retrieval_candidates],
            "retrieval_truncated": retrieval_truncated,
            "search_limit": search_limit,
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
