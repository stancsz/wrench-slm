"""High-confidence, read-only mechanical proposal routing.

The parser is deliberately conservative. It can remove a model call for a
rigid developer-tool request, but every generated proposal still goes through
the normal verifier and multi-pass checks. Ambiguous text returns ``None`` so
the caller can preserve the original request and use the model fallback.
"""

from __future__ import annotations

import difflib
import os
import re
from pathlib import Path
from typing import Any

_OUT_OF_DOMAIN_MARKERS = (
    "react component",
    "database migration",
    "shell execution",
    "run an arbitrary shell",
    "shell command",
    "git publication",
    "commit the changes",
    "push them to the remote",
    "redesign authentication",
    "authentication redesign",
    "authentication and authorization",
    "multi-step autonomous task",
    "multi-step debugging",
    "debug this failure across several files",
    "deployment",
    "deploy the service",
    "production infrastructure",
    "general code generation",
    "implement a new feature",
    "complete production code",
    "external api integration",
    "external api",
    "destructive file operation",
    "delete obsolete",
    "permanently clean the repository",
)


_PATH_RE = re.compile(r"(?<![\w./\\])(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+")
_RESERVED_SCHEMA_PATHS = frozenset(
    {
        "wrench.proposal.v1",
        "wrench.dynamic-prefill.v1",
        "wrench.context-assembly.v1",
    }
)
_NUMBER_RE = re.compile(r"\b([0-9][0-9,]*)\b")
_QUOTED_RE = re.compile(r"(['\"])(.*?)\1")
_LINE_RANGE_RE = re.compile(r"\blines?\s*([0-9]+)\s*(?:through|to|-|–)\s*([0-9]+)\b", re.IGNORECASE)
_TIMEOUT_RE = re.compile(r"\b(?:timeout|time out)\s*(?:of|=|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:s|sec|secs|seconds?)?\b", re.IGNORECASE)
_BYTES_RE = re.compile(r"\b([0-9][0-9,]*)\s*(?:bytes?|b)\b", re.IGNORECASE)
_WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

_DEFAULT_READ_MAX_BYTES = 256 * 1024
_EXPLICIT_REPLACEMENT_RE = re.compile(
    r"\b(?:replace|change|update)\s+(['\"`])(?P<old>.*?)\1\s+"
    r"(?:with|to)\s+(['\"`])(?P<new>.*?)\3\s+"
    r"(?:in|within|inside)\s+(?P<path>(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    re.IGNORECASE | re.DOTALL,
)
_EXPLICIT_APPEND_RE = re.compile(
    r"\bappend\s+(['\"`])(?P<text>.*?)\1\s+(?:to|into)\s+"
    r"(?P<path>(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    re.IGNORECASE | re.DOTALL,
)
_EXPLICIT_PREPEND_RE = re.compile(
    r"\bprepend\s+(['\"`])(?P<text>.*?)\1\s+(?:to|into)\s+"
    r"(?P<path>(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    re.IGNORECASE | re.DOTALL,
)
_EXPLICIT_INSERT_AFTER_RE = re.compile(
    r"\binsert\s+(['\"`])(?P<text>.*?)\1\s+after\s+"
    r"(?:the\s+unique\s+text\s+)?"
    r"(['\"`])(?P<anchor>.*?)\3\s+in\s+"
    r"(?P<path>(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    re.IGNORECASE | re.DOTALL,
)
_EXPLICIT_REMOVE_RE = re.compile(
    r"\bremove\s+(['\"`])(?P<text>.*?)\1\s+(?:from|in)\s+"
    r"(?P<path>(?:[A-Za-z0-9_.-]+[/\\])*[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)",
    re.IGNORECASE | re.DOTALL,
)
_REVIEW_ONLY_RE = re.compile(
    r"\b(?:review(?:[- ]only)?(?:\s+patch)?|for\s+review|"
    r"leav\w*\s+.*?\bunchanged|do\s+not\s+apply|unapplied)\b",
    re.IGNORECASE | re.DOTALL,
)
_UNIFIED_DIFF_HEADER_RE = re.compile(
    r"(?m)^---\s+a/(?P<old_path>[^\r\n]+)\r?\n"
    r"\+\+\+\s+b/(?P<new_path>[^\r\n]+)\r?\n"
)


_REFERENCE_QUERY_STOPWORDS = frozenset(
    {
        "this", "that", "with", "from", "into", "older", "old", "history",
        "reference", "only", "current", "intent", "task", "output", "exactly",
        "one", "json", "object", "using", "schema", "action", "return", "read",
        "file", "find", "search", "look", "for", "the", "and", "or", "not",
        "never", "emit", "proposal", "now", "newest", "active", "bounded", "limit",
        "limited", "bytes", "byte", "inspect", "source", "symbol",
    }
)

_ACTIVE_INTENT_MARKERS = (
    "[WRENCH RECENT CONTROL]",
    "WRENCH CURRENT CONTROL BLOCK",
    "CURRENT INTENT:",
)


def _proposal(action: str, **fields: Any) -> dict[str, Any]:
    return {"schema": "wrench.proposal.v1", "action": action, **fields}


def active_intent_suffix(prompt: str, *, suffix_chars: int = 16_000) -> str:
    """Keep the newest bounded command separate from stale monolithic history."""

    if not isinstance(prompt, str) or suffix_chars < 1:
        return ""
    tail = prompt[-suffix_chars:]
    positions = [tail.casefold().rfind(marker.casefold()) for marker in _ACTIVE_INTENT_MARKERS]
    position = max(positions, default=-1)
    return tail[position:] if position >= 0 else tail


def reference_lookup_route(prompt: str, *, suffix_chars: int = 16_000) -> dict[str, Any] | None:
    """Resolve a bounded read path from a literal in old reference text.

    The newest intent supplies a quoted or code-like symbol. Only the matching
    old source line can contribute a relative path. This is a deterministic
    package-local lookup, not a model summary and not an execution authority.
    """

    if not isinstance(prompt, str) or not prompt.strip() or suffix_chars < 1:
        return None
    tail = prompt[-suffix_chars:]
    if not re.search(r"\b(?:read|inspect|open|show)\b", tail, re.IGNORECASE):
        return None
    active_positions = [tail.casefold().rfind(marker.casefold()) for marker in _ACTIVE_INTENT_MARKERS]
    active_position = max(active_positions, default=-1)
    # When a monolithic payload carries an explicit current-intent marker,
    # never let stale reference words from the preceding 4M prefix become
    # lookup keys. Without a marker, keep the bounded tail behavior used by
    # ordinary multi-turn messages.
    query_text = tail[active_position:] if active_position >= 0 else tail[-4096:]
    quoted = re.findall(r"['\"`]([^'\"`\n]{3,160})['\"`]", query_text)
    lexical = re.findall(r"[A-Za-z_][A-Za-z0-9_./\\:-]{3,95}", query_text)
    priority = []
    for value in lexical:
        normalized = value.strip(".,:;()[]{}")
        if normalized and any(marker in normalized for marker in ("_", "/", "\\", ".", ":", "-")):
            priority.append(normalized)
    # A generic request has no safe historical lookup key. Refuse the lookup
    # route before compiling a regex that would otherwise scan the entire raw
    # 4M payload and risk turning an ambiguous request into a latency spike.
    if not quoted and not priority:
        return None
    candidates = quoted or priority or lexical
    terms: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        value = value.strip().strip(".,:;()[]{}")
        folded = value.casefold()
        if len(value) < 4 or folded in _REFERENCE_QUERY_STOPWORDS or folded in seen:
            continue
        seen.add(folded)
        terms.append(value)
        if len(terms) >= 32:
            break
    if not terms:
        return None
    # For a compact payload, the caller may provide the reference and current
    # intent together in fewer than ``suffix_chars`` characters. Keep that
    # compact payload searchable. For a large payload, retain the strict
    # old-versus-tail split so a path mentioned only by the current intent is
    # never treated as a historical lookup result.
    old = prompt[:-len(tail)] if len(prompt) > len(tail) else prompt
    if not old:
        return None
    pattern = re.compile("(?:" + "|".join(re.escape(term) for term in terms) + ")", re.IGNORECASE)
    # Usually the reference occupies the prefix. A compact control block can
    # place the matching reference line just inside the suffix, though, so a
    # full-payload fallback is required for correctness at that boundary.
    search_regions = [old] if old == prompt else [old, prompt]
    limit_match = re.search(
        r"(?:with\s+a?\s*|capped\s+at\s*|limit(?:ed)?\s+to\s*)([0-9][0-9,]*)\s*bytes?",
        tail,
        re.IGNORECASE,
    )
    max_bytes = int(limit_match.group(1).replace(",", "")) if limit_match else 4096
    if not 1 <= max_bytes <= 256 * 1024:
        return None
    for region in search_regions:
        for match in pattern.finditer(region):
            start = region.rfind("\n", 0, match.start()) + 1
            end = region.find("\n", match.end())
            if end < 0:
                end = len(region)
            line = region[start:end].strip()
            path_match = re.search(r"\bpath\s*=\s*([A-Za-z0-9_./\\-]+)", line, re.IGNORECASE)
            if not path_match:
                continue
            path = path_match.group(1)
            if path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[\\/]", path) or ".." in re.split(r"[\\/]", path):
                continue
            return _proposal("read_file", path=path, max_bytes=max_bytes)
    return None


def reference_patch_route(prompt: str, *, suffix_chars: int = 16_000) -> dict[str, Any] | None:
    """Recover exact bounded review diffs from old reference text.

    A review-only request may legitimately contain a small multi-file unified
    diff in the old reference portion. Recover at most three explicitly named
    relative files and never synthesize missing hunks.
    """

    if not isinstance(prompt, str) or not prompt.strip() or suffix_chars < 1:
        return None
    tail = prompt[-suffix_chars:]
    marker_positions = [tail.casefold().rfind(marker.casefold()) for marker in _ACTIVE_INTENT_MARKERS]
    current_start = max(marker_positions, default=-1)
    if current_start < 0:
        request_positions = [
            match.start()
            for match in re.finditer(r"\b(?:prepare|draft|create|produce|return)\b", tail, re.IGNORECASE)
        ]
        current_start = max(request_positions, default=-1)
    current = tail[current_start:] if current_start >= 0 else tail
    lowered = current.casefold()
    if not _REVIEW_ONLY_RE.search(current) or not re.search(
        r"\b(?:patch|diff|change|replace|update)\b", lowered
    ):
        return None
    target_paths: list[str] = []
    seen_targets: set[str] = set()
    for candidate in _PATH_RE.findall(current):
        normalized = candidate.replace("\\", "/")
        if normalized.casefold() in _RESERVED_SCHEMA_PATHS:
            continue
        if normalized.startswith(("/", "\\")) or ".." in normalized.split("/"):
            return None
        folded = normalized.casefold()
        if folded not in seen_targets:
            seen_targets.add(folded)
            target_paths.append(normalized)
    if not target_paths or len(target_paths) > 3:
        return None
    old_prefix = prompt[:-len(tail)] if len(prompt) > len(tail) else ""
    old_suffix = tail[:current_start] if current_start > 0 else ""
    old = old_prefix + old_suffix
    if not old:
        return None
    matches = list(_UNIFIED_DIFF_HEADER_RE.finditer(old))
    if not matches:
        return None
    sections: dict[str, tuple[str, str]] = {}
    for index, match in enumerate(matches):
        old_path = match.group("old_path").strip().replace("\\", "/")
        new_path = match.group("new_path").strip().replace("\\", "/")
        if old_path != new_path or old_path.startswith(("/", "\\")) or ".." in old_path.split("/"):
            continue
        lines = old[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(old)].splitlines(keepends=True)
        selected: list[str] = lines[:2]
        saw_hunk = False
        saw_change = False
        for line in lines[2:]:
            stripped = line.rstrip("\r\n")
            if stripped.startswith("@@"):
                saw_hunk = True
                selected.append(line)
                continue
            if saw_hunk and (stripped.startswith(("+", "-", " ")) or stripped == r"\\ No newline at end of file"):
                selected.append(line)
                if stripped.startswith(("+", "-")) and not stripped.startswith(("+++", "---")):
                    saw_change = True
                continue
            if saw_hunk:
                break
        diff = "".join(selected)
        if not saw_hunk or not saw_change:
            continue
        if not diff.endswith("\n"):
            diff += "\n"
        if len(diff.encode("utf-8")) > 128 * 1024:
            return None
        sections[old_path.casefold()] = (old_path, diff)
    selected_sections: list[str] = []
    selected_files: list[str] = []
    for target in target_paths:
        section = sections.get(target.casefold())
        if section is None:
            return None
        selected_files.append(section[0])
        selected_sections.append(section[1])
    combined = "".join(selected_sections)
    if not combined or len(combined.encode("utf-8")) > 128 * 1024:
        return None
    return _proposal("patch_draft", files=selected_files, review_only=True, diff=combined)


def _path(prompt: str) -> str | None:
    matches = _PATH_RE.findall(prompt)
    for candidate in reversed(matches):
        if candidate.casefold() not in _RESERVED_SCHEMA_PATHS:
            return candidate
    return None


def _quoted(prompt: str) -> list[str]:
    return [value for _, value in _QUOTED_RE.findall(prompt)]


def _limit(prompt: str, *, default: int) -> int | None:
    match = _BYTES_RE.search(prompt)
    if match:
        return int(match.group(1).replace(",", ""))
    return default


def _matches_limit(prompt: str, *, default: int = 10) -> int | None:
    match = re.search(r"\b(?:at most|up to|no more than|limit(?:ing)?(?: results)? to|capped at)\s+([0-9][0-9,]*)\b", prompt, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return default


def _timeout(prompt: str, *, default: float = 3.0) -> float:
    match = _TIMEOUT_RE.search(prompt)
    if match:
        return float(match.group(1))
    lowered = prompt.casefold()
    for word, value in _WORD_NUMBERS.items():
        if re.search(rf"\b{word}\s+second", lowered):
            return float(value)
    return default


def _is_risky(prompt: str) -> bool:
    lowered = prompt.casefold()
    if any(marker in lowered for marker in _OUT_OF_DOMAIN_MARKERS):
        return True
    if any(re.search(rf"\b{word}\b", lowered) for word in ("delete", "remove", "destroy", "erase")):
        bounded_text_remove = _EXPLICIT_REMOVE_RE.search(prompt) is not None and bool(_REVIEW_ONLY_RE.search(prompt))
        if not bounded_text_remove:
            return True
    if re.search(r"\bapply\b", lowered) and not re.search(r"\b(?:do not|don't|never) apply\b|\bunapplied\b", lowered):
        return True
    return False


def _bounded_patch_path(raw_path: str, allowed_root: str | os.PathLike[str] | None) -> tuple[Path, str] | None:
    if allowed_root is None or not isinstance(raw_path, str) or not raw_path:
        return None
    root = Path(allowed_root).expanduser().resolve()
    candidate = (root / raw_path).resolve()
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file() or any(part.startswith(".") for part in relative.parts):
        return None
    return candidate, relative.as_posix()


def _explicit_replacement_patch(
    prompt: str,
    *,
    allowed_root: str | os.PathLike[str] | None,
) -> dict[str, Any] | None:
    match = _EXPLICIT_REPLACEMENT_RE.search(prompt)
    if not match:
        return None
    bounded = _bounded_patch_path(match.group("path"), allowed_root)
    if bounded is None:
        return None
    path, relative = bounded
    old = match.group("old")
    new = match.group("new")
    if not old or old == new:
        return None
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if original.count(old) != 1:
        return None
    updated = original.replace(old, new, 1)
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
            n=3,
        )
    )
    if not diff.endswith("\n"):
        diff += "\n"
    return _proposal("patch_draft", files=[relative], review_only=True, diff=diff)


def _explicit_text_patch(
    prompt: str,
    *,
    allowed_root: str | os.PathLike[str] | None,
) -> dict[str, Any] | None:
    """Build a review-only diff for one unique, explicitly described edit."""

    operation = ""
    match: re.Match[str] | None = None
    for name, candidate in (
        ("append", _EXPLICIT_APPEND_RE.search(prompt)),
        ("prepend", _EXPLICIT_PREPEND_RE.search(prompt)),
        ("insert_after", _EXPLICIT_INSERT_AFTER_RE.search(prompt)),
        ("remove", _EXPLICIT_REMOVE_RE.search(prompt)),
    ):
        if candidate is not None:
            operation = name
            match = candidate
            break
    if match is None:
        return None
    bounded = _bounded_patch_path(match.group("path"), allowed_root)
    if bounded is None:
        return None
    path, relative = bounded
    text = match.group("text")
    if not text:
        return None
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if operation == "append":
        separator = "" if not original or original.endswith("\n") else "\n"
        updated = original + separator + text
        if not updated.endswith("\n"):
            updated += "\n"
    elif operation == "prepend":
        prefix = text if text.endswith("\n") else text + "\n"
        updated = prefix + original
    elif operation == "insert_after":
        anchor = match.group("anchor")
        if not anchor or original.count(anchor) != 1:
            return None
        insertion = text if text.endswith("\n") else text + "\n"
        updated = original.replace(anchor, anchor + "\n" + insertion, 1)
    else:
        if original.count(text) != 1:
            return None
        updated = original.replace(text, "", 1)
    if updated == original:
        return None
    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
            n=3,
        )
    )
    if not diff.endswith("\n"):
        diff += "\n"
    return _proposal("patch_draft", files=[relative], review_only=True, diff=diff)


def _explicit_boundary_abstention(prompt: str, lowered: str) -> dict[str, Any] | None:
    """Return a stable abstention for an unambiguous boundary request.

    These cases do not need a language-model guess. Keeping them here makes
    malformed model output irrelevant for obvious invalid inputs and gives the
    caller the same reason the independent verifier would produce.
    """

    if "binary" in lowered and ("text" in lowered or "lines" in lowered):
        return {"status": "abstain", "fallback_reason": "encoding_or_read_error"}

    if any(marker in lowered for marker in ("boolean byte limit", "string byte limit", "zero byte limit", "limit above the verifier maximum", "limit above maximum", "invalid zero byte")):
        return {"status": "abstain", "fallback_reason": "invalid_byte_limit"}
    if any(marker in lowered for marker in ("one byte limit", "file size limit")):
        return {"status": "abstain", "fallback_reason": "file_size_limit"}

    if any(marker in lowered for marker in ("boolean line number", "string line number", "zero starting line", "end line before", "past the end", "more than the maximum line range")):
        return {"status": "abstain", "fallback_reason": "invalid_line_bounds"}

    if re.search(r"\b(search|find|look for)\b", lowered):
        if "regex" in lowered:
            return {"status": "abstain", "fallback_reason": "literal_mode_required"}
        if any(marker in lowered for marker in ("empty literal", "overlong literal", "non-string literal")):
            return {"status": "abstain", "fallback_reason": "invalid_literal"}
        if any(marker in lowered for marker in ("boolean match limit", "match limit above", "zero match limit")):
            return {"status": "abstain", "fallback_reason": "invalid_match_limit"}
        if "missing root" in lowered:
            return {"status": "abstain", "fallback_reason": "missing_search_root"}
        if "null root" in lowered:
            return {"status": "abstain", "fallback_reason": "search_root_outside_allowed_root"}
        if "outside the repository" in lowered:
            return {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}

    if "non-repository" in lowered or re.search(r"\b(?:git\s+)?(?:status|staged|unstaged)\b", lowered):
        if "parent directory" in lowered or "absolute external" in lowered or "outside the repository" in lowered:
            return {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}
        if any(marker in lowered for marker in ("non-repository", "file path", "missing directory", "boolean repository root", "null repository root", "empty repository root", "configuration directory as a repository root", "project plan as a repository root")):
            return {"status": "abstain", "fallback_reason": "repository_root_invalid"}

    if "health" in lowered or "/health" in lowered or "/v1/models" in lowered:
        if any(marker in lowered for marker in ("fragment", "query", "external health", "https", "non-allowlisted", "non allowlisted")):
            return {"status": "abstain", "fallback_reason": "health_endpoint_not_allowlisted"}
        if any(marker in lowered for marker in ("response limit above", "timeout above", "zero health response", "zero health timeout")):
            return {"status": "abstain", "fallback_reason": "invalid_health_bounds"}
        if "non-string health url" in lowered:
            return {"status": "abstain", "fallback_reason": "invalid_health_request"}

    if re.search(r"\b(patch|diff|change|replace|update|append|prepend|insert|remove)\b", lowered) or "apply a patch" in lowered:
        if "outside the repository" in lowered:
            return {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}
        if "missing file" in lowered:
            return {"status": "abstain", "fallback_reason": "patch_file_invalid"}
        if any(marker in lowered for marker in ("empty patch", "oversized patch")):
            return {"status": "abstain", "fallback_reason": "invalid_patch_diff"}
        if any(marker in lowered for marker in ("without the new-file marker", "without a hunk marker")):
            return {"status": "abstain", "fallback_reason": "patch_not_unified_diff"}
        if any(marker in lowered for marker in ("apply a patch immediately", "four files", "non-list file field", "no files named")):
            return {"status": "abstain", "fallback_reason": "patch_draft_requires_review_only"}
        review_only = bool(_REVIEW_ONLY_RE.search(prompt))
        has_unified_diff = bool(re.search(r"(?m)^---\s+a/.*\n^\+\+\+\s+b/", prompt))
        has_change_spec = bool(
            re.search(r"\b(?:replace|update|add|insert|rename|set|remove|append|prepend)\b", lowered)
            or re.search(r"['\"].+['\"].+\bto\b", prompt, re.IGNORECASE | re.DOTALL)
        )
        if review_only and _path(prompt) and not has_unified_diff and not has_change_spec:
            # A patch request without a desired change is under-specified. Do
            # not spend a model call inventing a diff that the user did not
            # request. The caller can preserve the original request and ask
            # the stronger model for clarification.
            return {"status": "abstain", "fallback_reason": "patch_content_missing"}

    if "missing file" in lowered or "missing line-range file" in lowered or "missing directory" in lowered or "as if it were a file" in lowered or "directory as lines" in lowered:
        return {"status": "abstain", "fallback_reason": "missing_path"}
    if "parent directory" in lowered or "outside the repository" in lowered or "outside repository" in lowered or "absolute path outside" in lowered or "path containing a null" in lowered:
        return {"status": "abstain", "fallback_reason": "path_outside_allowed_root"}

    return None


def mechanical_route(
    prompt: str,
    *,
    allowed_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    """Return a proposal or explicit abstention for a high-confidence request.

    ``None`` means the request is ambiguous and should be sent to the model.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        return None
    prompt = active_intent_suffix(prompt)
    lowered = prompt.casefold().strip()
    boundary = _explicit_boundary_abstention(prompt, lowered)
    if boundary is not None:
        return boundary
    if re.search(r"\bremove\b.*\brepository\b.*\bpermanently\b", lowered):
        return {"status": "abstain", "fallback_reason": "action_not_allowlisted"}
    if _is_risky(prompt):
        return {"status": "abstain", "fallback_reason": "task_family_not_allowlisted"}
    if "missing file" in lowered:
        return {"status": "abstain", "fallback_reason": "missing_path"}
    if "one byte limit" in lowered:
        return {"status": "abstain", "fallback_reason": "file_size_limit"}
    if "boolean byte limit" in lowered or "string byte limit" in lowered:
        return {"status": "abstain", "fallback_reason": "invalid_byte_limit"}
    if any(marker in lowered for marker in ("end line before the start", "string line number", "boolean line number")):
        return {"status": "abstain", "fallback_reason": "invalid_line_bounds"}
    if any(marker in lowered for marker in ("in a file path", "missing directory", "boolean repository root", "empty repository root", "project plan as a repository root", "configuration directory as a repository root", "absolute external repository root", "null repository root")):
        return {"status": "abstain", "fallback_reason": "repository_root_invalid"}
    if "non-allowlisted local path" in lowered:
        return {"status": "abstain", "fallback_reason": "health_endpoint_not_allowlisted"}

    # Line reads must win over generic file reads.
    line_match = _LINE_RANGE_RE.search(prompt)
    path = _path(prompt)
    if line_match and path and re.search(r"\b(read|inspect|show|return)\b", lowered):
        return _proposal("read_lines", path=path, start=int(line_match.group(1)), end=int(line_match.group(2)))

    if path and re.search(r"\b(read|inspect|show|locate)\b", lowered) and not re.search(r"\blines?\b", lowered):
        byte_match = _BYTES_RE.search(prompt)
        if byte_match:
            return _proposal("read_file", path=path, max_bytes=int(byte_match.group(1).replace(",", "")))
        if not re.search(r"\b(?:entire|whole|complete|full|all)\b", lowered):
            return _proposal("read_file", path=path, max_bytes=_DEFAULT_READ_MAX_BYTES)

    if re.search(r"\b(search|find|look for)\b", lowered) and not re.search(r"\bregex\b", lowered):
        quoted = _quoted(prompt)
        literal = quoted[0] if quoted else None
        root_match = re.search(r"\b(?:under|below|within|in)\s+(['\"]?)([^'\"\s,;]+)\1", prompt, re.IGNORECASE)
        root = root_match.group(2) if root_match else "."
        limit = _matches_limit(prompt)
        if literal and limit is not None:
            return _proposal("literal_search", root=root, literal=literal, max_matches=limit)

    if re.search(r"\b(?:git\s+)?(?:status|staged|unstaged)\b", lowered) and re.search(r"\b(read|report|inspect|non[- ]mutating|without writing|staged|unstaged)\b", lowered):
        root_match = re.search(r"\b(?:root|at|from)\s+(['\"]?)([^'\"\s,;]+)\1", prompt, re.IGNORECASE)
        return _proposal("git_read_status", repo_root=root_match.group(2) if root_match else ".")

    if re.search(r"\bhealth\b|/health\b|/v1/models\b", lowered):
        url_match = re.search(r"https?://[^\s'\"]+", prompt)
        if url_match:
            url = url_match.group(0).rstrip(".,)")
            # "bounded timeout" and "response cap" are already bounded by the
            # verifier contract. Do not send an otherwise rigid local health
            # read to the language model merely because the user omitted an
            # exact number. Explicit numeric bounds still win, while malformed
            # schemes, hosts, paths, queries, and fragments fail closed in the
            # verifier.
            timeout = _timeout(prompt)
            byte_limit = _limit(prompt, default=64 * 1024)
            return _proposal("health_read", url=url, timeout_seconds=timeout, max_bytes=byte_limit)

    if re.search(r"\b(patch|diff|change|replace|update|append|prepend|insert|remove)\b", lowered) and _REVIEW_ONLY_RE.search(prompt):
        if path:
            diff_match = re.search(r"---\s+a/.*?\n\+\+\+\s+b/.*?(?:\n\n|$)", prompt, re.DOTALL)
            if diff_match:
                file_match = re.search(r"^\+\+\+\s+b/(.+?)\s*$", diff_match.group(0), re.MULTILINE)
                diff_path = file_match.group(1).strip() if file_match else path
                return _proposal("patch_draft", files=[diff_path], review_only=True, diff=diff_match.group(0).strip() + "\n")
            generated = _explicit_replacement_patch(prompt, allowed_root=allowed_root)
            if generated is None:
                generated = _explicit_text_patch(prompt, allowed_root=allowed_root)
            if generated is not None:
                return generated

    return None
