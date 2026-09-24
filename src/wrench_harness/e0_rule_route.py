"""Provider-free, snapshot-bound E0 rule route for bounded reads.

This is a narrow W4 no-model lane. ``mechanical_route`` is used only as a
proposal parser; every byte returned to the caller is fetched through the
carried root binding and the supplied source snapshot. It cannot execute a
proposal against a live repository, call a model/provider, or grant tool
authority.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

from .core import MAX_LINES, MAX_MATCHES
from .mechanical import mechanical_route
from .snapshot import (
    MAX_SNAPSHOT_BYTES,
    MAX_SNAPSHOT_FILES,
    MAX_SOURCE_BYTES,
    RetrievalStatus,
    SourceRootBinding,
    SourceRecord,
    SourceSnapshot,
    _validate_snapshot,
    retrieve_exact,
)


MAX_REQUEST_CHARS = 16_000
MAX_ROUTE_FILES = 16
MAX_ROUTE_BYTES = 512 * 1024
MAX_READ_BYTES = 256 * 1024
MAX_SEARCH_LITERAL_CHARS = 4096
MAX_SEARCH_LINE_CHARS = 4096
_NEGATED_READ_INTENT = re.compile(
    r"\b(?:do\s+not|don't|dont|never|must\s+not|cannot|can't|avoid)\b"
    r".{0,160}\b(?:read|inspect|show|open|search|find|look\s+for|display|print|"
    r"tell|say|return|output|reveal|disclose|share|provide|include|quote|copy|content|contents|text)\b"
    r"|\bnot\s+(?:read|inspect|show|open|search|find|look\s+for|display|print|tell|say|return|"
    r"output|reveal|disclose|share|provide|include|quote|copy|content|contents|text)\b"
    r"|\bwithout\s+(?:reading|searching|consent|authorization|authorisation|permission|approval)\b",
    re.IGNORECASE | re.DOTALL,
)
_RESTRICTED_READ_OUTPUT = re.compile(
    r"(?<![-\w])(?:only|just)\s+(?:tell|say|report|return|answer|confirm|show|display|provide|output)\b"
    r"|\b(?:tell|say|report|return|answer|confirm|show|display|provide|output)\b"
    r".{0,40}(?<![-\w])(?:only|just)\b",
    re.IGNORECASE | re.DOTALL,
)
_READ_SEARCH_ACTION = re.compile(
    r"\b(?:read|inspect|show|open|search|find|look\s+for|locate)\b",
    re.IGNORECASE,
)
_DENIAL_AUTHORIZATION_MARKER = re.compile(
    r"\b(?:do\s+not|don't|dont|never|must\s+not|cannot|can't|unable|not|no|without|"
    r"unapproved|unauthorized|unconsented|lack(?:s|ing)?)\b.{0,80}\b"
    r"(?:consent\w*|authori[sz]\w*|permit\w*|allow\w*|approv\w*|permission)\b"
    r"|\b(?:consent|authorization|authorisation|permission|approval)\b.{0,80}\b"
    r"(?:denied|revoked|missing|absent|not\s+granted)\b"
    r"|\bno\s+(?:need\s+to|reading|searching)\b"
    r"|\bwithout\s+(?:reading|searching|consent|authorization|authorisation|permission|approval)\b",
    re.IGNORECASE,
)
_QUOTED_LITERAL = re.compile(
    r'"[^"\r\n]*"|`[^`\r\n]*`|(?<![A-Za-z])\'[^\'\r\n]*\'(?![A-Za-z])'
)


class RuleRouteStatus(str, Enum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class RuleRouteEvidence:
    """Content-free evidence identity for one attempted exact source read."""

    path: str | None
    status: str
    content_sha256: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True)
class RuleRouteResult:
    """Bounded result for a no-model rule route.

    ``route`` is always ``none`` because no model was called. ``unknown_evidence``
    records why a requested operation could not be completed. Search results
    describe only files in the supplied finite snapshot, never the whole live
    repository.
    """

    status: RuleRouteStatus
    route: str
    action: str | None
    observation: dict[str, Any] | None
    evidence: tuple[RuleRouteEvidence, ...]
    unknown_evidence: tuple[RuleRouteEvidence, ...]
    exact_read_attempts: int
    exact_read_successes: int
    exact_read_bytes: int
    reason: str | None = None


def run_e0_rule_route(
    prompt: str,
    *,
    root_binding: SourceRootBinding,
    snapshot: SourceSnapshot,
) -> RuleRouteResult:
    """Run a bounded deterministic read only when every source is snapshotted.

    Supported proposal actions are ``read_file``, ``read_lines`` and literal
    ``literal_search``. Search is limited to the files named by the finite
    snapshot and reports that scope explicitly. All other actions abstain.
    """

    empty = _unknown("invalid_input")
    if (
        not isinstance(prompt, str)
        or not prompt.strip()
        or len(prompt) > MAX_REQUEST_CHARS
        or type(root_binding) is not SourceRootBinding
        or type(snapshot) is not SourceSnapshot
    ):
        return empty

    sources = _validated_source_manifest(snapshot)
    if sources is None:
        return _unknown("snapshot_manifest_invalid")

    # The mechanical parser recognizes action words conservatively, but it is
    # not an intent or disclosure-policy authority. Reject explicit negation
    # and contradictory read/search instructions before exact retrieval.
    intent_text = prompt.replace("\u2018", "'").replace("\u2019", "'")
    intent_text = _QUOTED_LITERAL.sub(" ", intent_text)
    if not _READ_SEARCH_ACTION.search(intent_text):
        return _unknown("ambiguous_or_unsupported_request")
    if (
        _NEGATED_READ_INTENT.search(intent_text)
        or _RESTRICTED_READ_OUTPUT.search(intent_text)
        or (_READ_SEARCH_ACTION.search(intent_text) and _DENIAL_AUTHORIZATION_MARKER.search(intent_text))
    ):
        return _unknown("read_intent_denied_or_constrained")

    proposal = mechanical_route(prompt)
    if proposal is None:
        return _unknown("ambiguous_or_unsupported_request")
    if proposal.get("status") == "abstain":
        return _unknown(str(proposal.get("fallback_reason", "rule_abstained")))
    if proposal.get("schema") != "wrench.proposal.v1":
        return _unknown("proposal_schema_invalid")

    action = proposal.get("action")
    if action == "read_file":
        return _read_file(proposal, root_binding, snapshot, sources)
    if action == "read_lines":
        return _read_lines(proposal, root_binding, snapshot, sources)
    if action == "literal_search":
        return _literal_search(proposal, root_binding, snapshot, sources)
    return _unknown("action_not_allowlisted", action=action if isinstance(action, str) else None)


def _read_file(
    proposal: dict[str, Any], root_binding: SourceRootBinding, snapshot: SourceSnapshot,
    sources: tuple[SourceRecord, ...],
) -> RuleRouteResult:
    if set(proposal) != {"schema", "action", "path", "max_bytes"}:
        return _unknown("read_file_proposal_shape_invalid", action="read_file")
    path = _snapshot_member_path(proposal.get("path"), sources)
    limit = proposal.get("max_bytes")
    if path is None:
        return _unknown("source_not_in_snapshot", path=_path_or_none(proposal.get("path")), action="read_file")
    if type(limit) is not int or not 1 <= limit <= MAX_READ_BYTES:
        return _unknown("file_size_limit_invalid", path=path, action="read_file")
    read = _read_snapshot_file(path, root_binding, snapshot, action="read_file")
    if read[0] is not None:
        return read[0]
    data, evidence = read[1], read[2]
    if len(data) > limit:
        return _abstain("file_size_limit", action="read_file", evidence=(evidence,), attempts=1, successes=1, read_bytes=len(data))
    text = _decode_text(data)
    if text is None:
        return _abstain("non_text_source", action="read_file", evidence=(evidence,), attempts=1, successes=1, read_bytes=len(data))
    return _completed("read_file", {"path": path, "bytes": len(data), "text": text}, (evidence,), 1, len(data))


def _read_lines(
    proposal: dict[str, Any], root_binding: SourceRootBinding, snapshot: SourceSnapshot,
    sources: tuple[SourceRecord, ...],
) -> RuleRouteResult:
    if set(proposal) != {"schema", "action", "path", "start", "end"}:
        return _unknown("read_lines_proposal_shape_invalid", action="read_lines")
    path = _snapshot_member_path(proposal.get("path"), sources)
    start, end = proposal.get("start"), proposal.get("end")
    if path is None:
        return _unknown("source_not_in_snapshot", path=_path_or_none(proposal.get("path")), action="read_lines")
    if (
        type(start) is not int
        or type(end) is not int
        or start < 1
        or end < start
        or end - start + 1 > MAX_LINES
    ):
        return _unknown("invalid_line_bounds", path=path, action="read_lines")
    read = _read_snapshot_file(path, root_binding, snapshot, action="read_lines")
    if read[0] is not None:
        return read[0]
    data, evidence = read[1], read[2]
    text = _decode_text(data)
    if text is None:
        return _abstain("non_text_source", action="read_lines", evidence=(evidence,), attempts=1, successes=1, read_bytes=len(data))
    lines = text.splitlines()
    if end > len(lines):
        return _abstain("line_end_out_of_range", action="read_lines", evidence=(evidence,), attempts=1, successes=1, read_bytes=len(data))
    return _completed(
        "read_lines",
        {"path": path, "start": start, "end": end, "lines": lines[start - 1 : end]},
        (evidence,), 1, len(data),
    )


def _literal_search(
    proposal: dict[str, Any], root_binding: SourceRootBinding, snapshot: SourceSnapshot,
    sources: tuple[SourceRecord, ...],
) -> RuleRouteResult:
    if set(proposal) != {"schema", "action", "root", "literal", "max_matches"}:
        return _unknown("literal_search_proposal_shape_invalid", action="literal_search")
    root = _normalize_search_root(proposal.get("root"))
    literal, limit = proposal.get("literal"), proposal.get("max_matches")
    if root is None:
        return _unknown("search_root_invalid", action="literal_search")
    if not isinstance(literal, str) or not literal or len(literal) > MAX_SEARCH_LITERAL_CHARS:
        return _unknown("invalid_literal", action="literal_search")
    if type(limit) is not int or not 1 <= limit <= MAX_MATCHES:
        return _unknown("invalid_match_limit", action="literal_search")

    paths = tuple(
        record.path for record in sources
        if _path_is_in_search_root(record.path, root)
    )
    if not paths:
        return _unknown("search_scope_has_no_snapshot_sources", path=root, action="literal_search")
    if len(paths) > MAX_ROUTE_FILES:
        return _unknown("route_file_limit_exceeded", path=root, action="literal_search")
    records = {record.path: record for record in sources}
    if any(records[path].size_bytes > MAX_READ_BYTES for path in paths):
        return _unknown("source_size_limit_exceeded", path=root, action="literal_search")
    if sum(records[path].size_bytes for path in paths) > MAX_ROUTE_BYTES:
        return _unknown("route_byte_limit_exceeded", path=root, action="literal_search")

    evidence: list[RuleRouteEvidence] = []
    matches: list[dict[str, Any]] = []
    attempts = successes = total_bytes = 0
    truncated = False
    for path in paths:
        attempts += 1
        read = retrieve_exact(root_binding, snapshot, path)
        if read.status is not RetrievalStatus.OK or read.data is None:
            missing = RuleRouteEvidence(path, read.status.value)
            return _abstain(
                f"snapshot_read_{read.status.value}", action="literal_search",
                evidence=tuple(evidence), unknown=(missing,), attempts=attempts,
                successes=successes, read_bytes=total_bytes,
            )
        data = read.data
        successes += 1
        total_bytes += len(data)
        source_evidence = RuleRouteEvidence(path, "ok", hashlib.sha256(data).hexdigest(), len(data))
        evidence.append(source_evidence)
        if len(data) > MAX_SOURCE_BYTES:
            return _abstain("source_size_limit_exceeded", action="literal_search", evidence=tuple(evidence), attempts=attempts, successes=successes, read_bytes=total_bytes)
        if total_bytes > MAX_ROUTE_BYTES:
            return _abstain("route_byte_limit_exceeded", action="literal_search", evidence=tuple(evidence), attempts=attempts, successes=successes, read_bytes=total_bytes)
        text = _decode_text(data)
        if text is None:
            return _abstain(
                "non_text_source", action="literal_search", evidence=tuple(evidence),
                unknown=(RuleRouteEvidence(path, "non_text"),), attempts=attempts,
                successes=successes, read_bytes=total_bytes,
            )
        for line_number, line in enumerate(text.splitlines(), start=1):
            if literal in line:
                if len(line) > MAX_SEARCH_LINE_CHARS:
                    return _abstain(
                        "search_result_line_limit_exceeded", action="literal_search",
                        evidence=tuple(evidence), unknown=(RuleRouteEvidence(path, "result_line_too_long"),),
                        attempts=attempts, successes=successes, read_bytes=total_bytes,
                    )
                matches.append({"path": path, "line": line_number, "text": line})
                if len(matches) >= limit:
                    truncated = True
                    break
        if truncated:
            break

    result = _completed(
        "literal_search",
        {
            "root": root,
            "literal": literal,
            "matches": matches,
            "truncated": truncated,
            "scope": "supplied_snapshot_sources",
        },
        tuple(evidence), attempts, total_bytes,
    )
    if truncated:
        return RuleRouteResult(
            RuleRouteStatus.PARTIAL, result.route, result.action, result.observation,
            result.evidence, (RuleRouteEvidence(root, "match_limit_reached"),),
            result.exact_read_attempts, result.exact_read_successes,
            result.exact_read_bytes, "match_limit_reached",
        )
    return result


def _read_snapshot_file(
    path: str,
    root_binding: SourceRootBinding,
    snapshot: SourceSnapshot,
    *,
    action: str,
):
    read = retrieve_exact(root_binding, snapshot, path)
    if read.status is not RetrievalStatus.OK or read.data is None:
        miss = RuleRouteEvidence(path, read.status.value)
        return _abstain(
            f"snapshot_read_{read.status.value}", action=action,
            unknown=(miss,), attempts=1, successes=0, read_bytes=0,
        ), None, None
    evidence = RuleRouteEvidence(path, "ok", hashlib.sha256(read.data).hexdigest(), len(read.data))
    if len(read.data) > MAX_READ_BYTES:
        return _abstain(
            "source_size_limit_exceeded", action=action, evidence=(evidence,),
            attempts=1, successes=1, read_bytes=len(read.data),
        ), None, None
    return None, read.data, evidence


def _snapshot_member_path(value: object, sources: tuple[SourceRecord, ...]) -> str | None:
    normalized = _normalize_relative(value)
    if normalized is None:
        return None
    return next((record.path for record in sources if record.path == normalized), None)


def _validated_source_manifest(snapshot: SourceSnapshot) -> tuple[SourceRecord, ...] | None:
    """Bound public manifest inspection before any route-level iteration.

    ``retrieve_exact`` remains the integrity authority and revalidates the
    complete snapshot hash before returning bytes. This shape preflight keeps
    route planning itself bounded even for caller-constructed dataclasses.
    """
    if type(snapshot) is not SourceSnapshot or not _validate_snapshot(snapshot):
        return None
    if (
        snapshot.schema != "wrench.source-snapshot.v3"
        or type(snapshot.sources) is not tuple
        or not 1 <= len(snapshot.sources) <= MAX_SNAPSHOT_FILES
    ):
        return None
    total_bytes = 0
    seen: set[str] = set()
    for record in snapshot.sources:
        if type(record) is not SourceRecord:
            return None
        if (
            not isinstance(record.path, str)
            or not 1 <= len(record.path) <= 1024
            or _normalize_relative(record.path) != record.path
            or type(record.size_bytes) is not int
            or not 0 <= record.size_bytes <= MAX_SOURCE_BYTES
            or not isinstance(record.sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", record.sha256) is None
            or record.path in seen
        ):
            return None
        seen.add(record.path)
        total_bytes += record.size_bytes
        if total_bytes > MAX_SNAPSHOT_BYTES:
            return None
    return snapshot.sources


def _normalize_relative(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    value = value.replace("\\", "/")
    path = PurePosixPath(value)
    if path.is_absolute() or ":" in value or any(part in {"..", ""} for part in value.split("/")):
        return None
    normalized = "/".join(part for part in value.split("/") if part != ".")
    return normalized or None


def _normalize_search_root(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    value = value.replace("\\", "/")
    if value in {".", "./"}:
        return "."
    return _normalize_relative(value)


def _path_is_in_search_root(path: str, root: str) -> bool:
    return root == "." or path == root or path.startswith(root.rstrip("/") + "/")


def _decode_text(data: bytes) -> str | None:
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _path_or_none(value: object) -> str | None:
    return _normalize_relative(value)


def _completed(action: str, observation: dict[str, Any], evidence: tuple[RuleRouteEvidence, ...], attempts: int, read_bytes: int) -> RuleRouteResult:
    return RuleRouteResult(
        RuleRouteStatus.COMPLETED, "none", action, observation, evidence, (),
        attempts, attempts, read_bytes,
    )


def _abstain(
    reason: str,
    *,
    action: str | None = None,
    evidence: tuple[RuleRouteEvidence, ...] = (),
    unknown: tuple[RuleRouteEvidence, ...] = (),
    attempts: int = 0,
    successes: int = 0,
    read_bytes: int = 0,
) -> RuleRouteResult:
    return RuleRouteResult(
        RuleRouteStatus.ABSTAIN, "none", action, None,
        evidence, unknown, attempts, successes, read_bytes, reason,
    )


def _unknown(reason: str, *, path: str | None = None, action: str | None = None) -> RuleRouteResult:
    return _abstain(reason, action=action, unknown=(RuleRouteEvidence(path, "unknown"),))


__all__ = [
    "MAX_REQUEST_CHARS",
    "MAX_ROUTE_BYTES",
    "MAX_ROUTE_FILES",
    "RuleRouteEvidence",
    "RuleRouteResult",
    "RuleRouteStatus",
    "run_e0_rule_route",
]
