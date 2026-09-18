"""Independent verifier and executor for Wrench's narrow action portfolio.

The model may propose an action, but this module owns validation and execution.
It deliberately has no generic shell, write, commit, credential, or mutation
primitive. Every rejected proposal returns a stable fallback reason so a caller
can preserve the original request and escalate.
"""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


MAX_FILE_BYTES = 256 * 1024
MAX_LINES = 500
MAX_MATCHES = 200
MAX_DIFF_BYTES = 128 * 1024
ALLOWED_HEALTH_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_HEALTH_PATHS = {"/health", "/v1/models"}


def _abstain(reason: str, detail: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "abstain", "fallback_reason": reason}
    if detail:
        result["detail"] = detail
    return result


def _accept(action: str, observation: Any) -> dict[str, Any]:
    return {"status": "accepted", "action": action, "observation": observation}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _root(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value).expanduser().resolve()
    return candidate if candidate.is_dir() else None


def _bounded_path(value: Any, root: Path) -> Path | None:
    if not isinstance(value, str) or not value or "\x00" in value:
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    return candidate if _inside(candidate, root) else None


def _read_file(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    path = _bounded_path(proposal.get("path"), root)
    limit = proposal.get("max_bytes", MAX_FILE_BYTES)
    if path is None:
        return _abstain("path_outside_allowed_root")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_FILE_BYTES:
        return _abstain("invalid_byte_limit")
    if not path.is_file():
        return _abstain("missing_path")
    if path.stat().st_size > limit:
        return _abstain("file_size_limit")
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return _abstain("encoding_or_read_error", type(exc).__name__)
    return _accept("read_file", {"path": str(path), "bytes": len(text.encode("utf-8")), "text": text})


def _read_lines(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    path = _bounded_path(proposal.get("path"), root)
    start, end = proposal.get("start"), proposal.get("end")
    if path is None:
        return _abstain("path_outside_allowed_root")
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in (start, end)):
        return _abstain("invalid_line_bounds")
    if start < 1 or end < start or end - start + 1 > MAX_LINES:
        return _abstain("invalid_line_bounds")
    if not path.is_file():
        return _abstain("missing_path")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError) as exc:
        return _abstain("encoding_or_read_error", type(exc).__name__)
    if end > len(lines):
        return _abstain("line_end_out_of_range")
    return _accept("read_lines", {"path": str(path), "start": start, "end": end, "lines": lines[start - 1 : end]})


def _literal_search(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    search_root = _bounded_path(proposal.get("root"), root)
    literal = proposal.get("literal")
    limit = proposal.get("max_matches", MAX_MATCHES)
    if proposal.get("mode", "literal") != "literal":
        return _abstain("literal_mode_required")
    if search_root is None:
        return _abstain("search_root_outside_allowed_root")
    if not isinstance(literal, str) or not literal or len(literal) > 4096:
        return _abstain("invalid_literal")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_MATCHES:
        return _abstain("invalid_match_limit")
    if not search_root.exists():
        return _abstain("missing_search_root")
    paths = [search_root] if search_root.is_file() else sorted(p for p in search_root.rglob("*") if p.is_file())
    matches: list[dict[str, Any]] = []
    for path in paths:
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if literal in line:
                matches.append({"path": str(path), "line": line_number, "text": line})
                if len(matches) >= limit:
                    return _accept("literal_search", {"root": str(search_root), "literal": literal, "matches": matches, "truncated": True})
    return _accept("literal_search", {"root": str(search_root), "literal": literal, "matches": matches, "truncated": False})


def _git_read_status(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    repo = _bounded_path(proposal.get("repo_root"), root)
    if repo is None or not repo.is_dir() or not (repo / ".git").exists():
        return _abstain("repository_root_invalid")
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), "status", "--short", "--branch"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _abstain("git_read_error", type(exc).__name__)
    if completed.returncode != 0:
        return _abstain("git_read_error", completed.stderr.strip()[:500])
    return _accept("git_read_status", {"repo_root": str(repo), "output": completed.stdout, "mutated": False})


def _health_read(proposal: dict[str, Any]) -> dict[str, Any]:
    url = proposal.get("url")
    timeout = proposal.get("timeout_seconds", 3)
    limit = proposal.get("max_bytes", 64 * 1024)
    if not isinstance(url, str) or not isinstance(timeout, (int, float)) or not isinstance(limit, int):
        return _abstain("invalid_health_request")
    if timeout <= 0 or timeout > 5 or limit < 1 or limit > 64 * 1024:
        return _abstain("invalid_health_bounds")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_HEALTH_HOSTS or parsed.path not in ALLOWED_HEALTH_PATHS or parsed.query or parsed.fragment:
        return _abstain("health_endpoint_not_allowlisted")
    try:
        with urllib.request.urlopen(url, timeout=float(timeout)) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                return _abstain("health_response_size_limit")
            text = data.decode("utf-8")
            return _accept("health_read", {"url": url, "status": response.status, "body": text})
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, OSError) as exc:
        return _abstain("health_read_error", type(exc).__name__)


def _patch_draft(proposal: dict[str, Any], root: Path) -> dict[str, Any]:
    files = proposal.get("files")
    diff = proposal.get("diff")
    review_only = proposal.get("review_only")
    if not isinstance(files, list) or not files or len(files) > 3 or review_only is not True:
        return _abstain("patch_draft_requires_review_only")
    if not isinstance(diff, str) or not diff or len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        return _abstain("invalid_patch_diff")
    resolved: list[str] = []
    for value in files:
        path = _bounded_path(value, root)
        if path is None or not path.is_file() or any(part.startswith(".") for part in path.relative_to(root).parts):
            return _abstain("patch_file_invalid")
        resolved.append(str(path))
    if "+++" not in diff or "---" not in diff or "@@" not in diff:
        return _abstain("patch_not_unified_diff")
    return _accept("patch_draft", {"files": resolved, "diff": diff, "review_only": True, "applied": False})


def execute_proposal(proposal: Any, allowed_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Validate and execute one proposal under the fixed Wrench portfolio."""

    root = _root(str(allowed_root))
    if root is None:
        return _abstain("allowed_root_invalid")
    if not isinstance(proposal, dict) or proposal.get("schema") != "wrench.proposal.v1":
        return _abstain("proposal_schema_invalid")
    action = proposal.get("action")
    handlers = {
        "read_file": _read_file,
        "read_lines": _read_lines,
        "literal_search": _literal_search,
        "git_read_status": _git_read_status,
        "patch_draft": _patch_draft,
    }
    if action == "health_read":
        return _health_read(proposal)
    handler = handlers.get(action)
    if handler is None:
        return _abstain("action_not_allowlisted")
    return handler(proposal, root)


def execute_model_output(model_output: Any, allowed_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Parse one model response strictly, then route it through the verifier.

    Surrounding prose and markdown are rejected rather than heuristically
    extracted. This keeps the model outside the authority boundary.
    """

    if not isinstance(model_output, str) or not model_output.strip():
        return _abstain("model_output_not_text")
    try:
        proposal = json.loads(model_output)
    except json.JSONDecodeError:
        return _abstain("model_output_invalid_json")
    if not isinstance(proposal, dict):
        return _abstain("model_output_not_object")
    result = execute_proposal(proposal, allowed_root)
    result["model_output_validated"] = True
    return result


def json_result(result: dict[str, Any]) -> str:
    """Stable JSON rendering for receipts and callers."""

    return json.dumps(result, ensure_ascii=False, sort_keys=True)
