"""High-confidence, read-only mechanical proposal routing.

The parser is deliberately conservative. It can remove a model call for a
rigid developer-tool request, but every generated proposal still goes through
the normal verifier and multi-pass checks. Ambiguous text returns ``None`` so
the caller can preserve the original request and use the model fallback.
"""

from __future__ import annotations

import re
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


def _proposal(action: str, **fields: Any) -> dict[str, Any]:
    return {"schema": "wrench.proposal.v1", "action": action, **fields}


def _path(prompt: str) -> str | None:
    matches = _PATH_RE.findall(prompt)
    return matches[-1] if matches else None


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
        return True
    if re.search(r"\bapply\b", lowered) and not re.search(r"\b(?:do not|don't|never) apply\b|\bunapplied\b", lowered):
        return True
    return False


def mechanical_route(prompt: str) -> dict[str, Any] | None:
    """Return a proposal or explicit abstention for a high-confidence request.

    ``None`` means the request is ambiguous and should be sent to the model.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        return None
    lowered = prompt.casefold().strip()
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
            has_explicit_timeout = _TIMEOUT_RE.search(prompt) is not None or any(
                re.search(rf"\b{word}\s+second", lowered) for word in _WORD_NUMBERS
            )
            if has_explicit_timeout:
                timeout = _timeout(prompt)
                byte_limit = _limit(prompt, default=64 * 1024)
                return _proposal("health_read", url=url, timeout_seconds=timeout, max_bytes=byte_limit)

    if re.search(r"\b(patch|diff|change)\b", lowered) and re.search(r"\b(review[- ]only|leave .*unchanged|do not apply|unapplied)\b", lowered):
        if path:
            diff_match = re.search(r"---\s+a/.*?\n\+\+\+\s+b/.*?(?:\n\n|$)", prompt, re.DOTALL)
            if diff_match:
                return _proposal("patch_draft", files=[path], review_only=True, diff=diff_match.group(0).strip() + "\n")

    return None
