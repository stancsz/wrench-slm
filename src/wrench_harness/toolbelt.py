"""Read-only deterministic helpers for the Wrench mechanical worker.

These helpers are model-side support tools, not autonomous agent authority.
They turn a large repository context into structured evidence that a model can
look up. They never write files, execute commands, or apply patches.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Iterable

from .core import OUT_OF_DOMAIN_MARKERS


_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INTENT_RE = re.compile(
    r"\b(read|inspect|find|search|check|compare|explain|draft|review|test|debug|fix|modify|write|delete|run|deploy)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    path: str
    start_line: int
    end_line: int
    signature: str


@dataclass(frozen=True)
class IntentState:
    intent: str
    source_message_index: int
    action_words: tuple[str, ...]
    confidence: float


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_source_ast(path: str, text: str) -> dict[str, object]:
    """Parse Python structure, or return a safe lexical fallback for other code."""

    if not isinstance(path, str) or not path:
        raise ValueError("path must be a non-empty string")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    symbols: list[Symbol] = []
    syntax_error: str | None = None
    if suffix == "py":
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            syntax_error = f"SyntaxError:{exc.lineno}:{exc.offset}:{exc.msg}"
        else:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    line = getattr(node, "lineno", 1)
                    end_line = getattr(node, "end_lineno", line)
                    symbols.append(Symbol(node.name, kind, path, line, end_line, text.splitlines()[line - 1].strip()))
    else:
        for index, line in enumerate(text.splitlines(), start=1):
            match = re.search(r"\b(?:function|class|def|interface|type)\s+([A-Za-z_$][\w$]*)", line)
            if match:
                symbols.append(Symbol(match.group(1), "lexical_declaration", path, index, index, line.strip()))
    symbols.sort(key=lambda item: (item.start_line, item.name))
    return {
        "schema": "wrench.source-ast.v1",
        "path": path,
        "source_sha256": _digest(text),
        "language": suffix or "unknown",
        "parser": "python_ast" if suffix == "py" else "lexical_fallback",
        "syntax_error": syntax_error,
        "symbols": [asdict(symbol) for symbol in symbols],
    }


def build_symbol_index(files: Iterable[tuple[str, str]]) -> dict[str, object]:
    """Build a hash-bound, read-only symbol index from supplied file contents."""

    rows = [parse_source_ast(path, text) for path, text in files]
    symbols = [symbol for row in rows for symbol in row["symbols"]]
    return {
        "schema": "wrench.symbol-index.v1",
        "files": rows,
        "symbol_count": len(symbols),
        "index_sha256": _digest(repr(rows)),
    }


def extract_dependencies(path: str, text: str) -> dict[str, object]:
    """Extract conservative import and call edges without executing code."""

    imports: list[str] = []
    calls: list[str] = []
    syntax_error: str | None = None
    if path.casefold().endswith(".py"):
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            syntax_error = f"SyntaxError:{exc.lineno}:{exc.offset}:{exc.msg}"
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.append(node.func.attr)
    return {
        "schema": "wrench.dependency-evidence.v1",
        "path": path,
        "source_sha256": _digest(text),
        "imports": sorted(set(imports)),
        "calls": sorted(set(calls)),
        "syntax_error": syntax_error,
        "read_only": True,
    }


def static_code_gate(files: dict[str, str]) -> dict[str, object]:
    """Run a local syntax and placeholder gate over proposed source text."""

    if not isinstance(files, dict):
        return {"schema": "wrench.static-code-gate.v1", "passed": False, "reason": "files_not_object"}
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for path, text in files.items():
        if not isinstance(path, str) or not isinstance(text, str):
            errors.append({"path": str(path), "reason": "invalid_source"})
            continue
        if path.casefold().endswith(".py"):
            try:
                ast.parse(text, filename=path)
            except SyntaxError as exc:
                errors.append({"path": path, "reason": f"SyntaxError:{exc.lineno}:{exc.offset}:{exc.msg}"})
        if re.search(r"\b(TODO|FIXME|pass\s+#\s*placeholder)\b", text, re.IGNORECASE):
            warnings.append({"path": path, "reason": "placeholder_marker"})
    return {
        "schema": "wrench.static-code-gate.v1",
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checked_files": sorted(files),
        "read_only": True,
    }


def build_repo_map(files: Iterable[dict[str, object]], *, limit: int = 10_000) -> dict[str, object]:
    """Build a compact repository map from already-read file metadata."""

    rows = list(files)
    if limit < 1 or len(rows) > limit:
        raise ValueError("repo map exceeds bounded file limit")
    normalized: list[dict[str, object]] = []
    for row in rows:
        path = row.get("path") if isinstance(row, dict) else None
        if not isinstance(path, str) or not path or path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/"):
            raise ValueError("repo map path must be relative and bounded")
        content = row.get("content") if isinstance(row, dict) else None
        normalized.append(
            {
                "path": path.replace("\\", "/"),
                "language": path.rsplit(".", 1)[-1].lower() if "." in path else "unknown",
                "bytes": len(content.encode("utf-8")) if isinstance(content, str) else row.get("bytes", 0),
                "sha256": _digest(content) if isinstance(content, str) else row.get("sha256"),
            }
        )
    normalized.sort(key=lambda item: str(item["path"]))
    return {
        "schema": "wrench.repo-map.v1",
        "file_count": len(normalized),
        "files": normalized,
        "map_sha256": _digest(repr(normalized)),
        "read_only": True,
    }


def select_relevant_tests(changed_paths: Iterable[str], test_paths: Iterable[str], *, limit: int = 32) -> dict[str, object]:
    """Suggest tests by stable path-token overlap, never execute them."""

    changed = [path for path in changed_paths if isinstance(path, str)]
    tests = [path for path in test_paths if isinstance(path, str)]
    tokens = {token.casefold() for path in changed for token in _WORD_RE.findall(path) if token.casefold() not in {"src", "tests", "test"}}
    ranked: list[tuple[int, str]] = []
    for path in tests:
        score = sum(1 for token in tokens if token in path.casefold())
        if score:
            ranked.append((score, path))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return {
        "schema": "wrench.test-selection.v1",
        "changed_paths": changed,
        "selected_tests": [{"path": path, "match_score": score} for score, path in ranked[:limit]],
        "read_only": True,
    }


def fingerprint_failure(text: str) -> dict[str, object]:
    """Extract a bounded, non-secret failure fingerprint from tool output."""

    if not isinstance(text, str):
        raise ValueError("failure text must be a string")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    salient = [line for line in lines if re.search(r"(error|exception|failed|failure|traceback|timeout|oom)", line, re.IGNORECASE)]
    selected = salient[:20]
    return {
        "schema": "wrench.failure-fingerprint.v1",
        "line_count": len(lines),
        "salient_lines": selected,
        "fingerprint_sha256": _digest("\n".join(selected)),
        "read_only": True,
    }


def track_recent_intent(messages: Iterable[dict[str, object]]) -> dict[str, object]:
    """Return the latest user intent without treating old text as authority."""

    rows = list(messages)
    for index in range(len(rows) - 1, -1, -1):
        message = rows[index]
        if message.get("role") != "user" or not isinstance(message.get("content"), str):
            continue
        content = message["content"].strip()
        if not content:
            continue
        words = tuple(dict.fromkeys(match.group(1).casefold() for match in _INTENT_RE.finditer(content)))
        intent = content[-2000:]
        return asdict(IntentState(intent, index, words, 1.0 if words else 0.65))
    return asdict(IntentState("", -1, (), 0.0))


def lookup_symbols(query: str, index: dict[str, object], *, limit: int = 16) -> list[dict[str, object]]:
    """Lexically rank symbol records as reference evidence."""

    terms = {term.casefold() for term in _WORD_RE.findall(query)}
    candidates: list[tuple[int, dict[str, object]]] = []
    for file_row in index.get("files", []):
        for symbol in file_row.get("symbols", []):
            haystack = " ".join(str(symbol.get(key, "")) for key in ("name", "kind", "path", "signature")).casefold()
            score = sum(1 for term in terms if term in haystack)
            if score:
                candidates.append((score, symbol))
    candidates.sort(key=lambda item: (-item[0], item[1].get("path", ""), item[1].get("start_line", 0)))
    return [symbol | {"match_score": score, "reference_only": True} for score, symbol in candidates[:limit]]


_ALLOWED_ACTIONS = {"read_file", "read_lines", "literal_search", "git_read_status", "health_read", "patch_draft"}
_REQUIRED_FIELDS = {
    "read_file": {"schema", "action", "path", "max_bytes"},
    "read_lines": {"schema", "action", "path", "start", "end"},
    "literal_search": {"schema", "action", "root", "literal", "max_matches"},
    "git_read_status": {"schema", "action", "repo_root"},
    "health_read": {"schema", "action", "url", "timeout_seconds", "max_bytes"},
    "patch_draft": {"schema", "action", "files", "review_only", "diff"},
}


def _pass(name: str, passed: bool, reason: str | None = None) -> dict[str, object]:
    row: dict[str, object] = {"name": name, "passed": passed}
    if reason:
        row["reason"] = reason
    return row


def multi_pass_verify(
    proposal: object,
    request_prompt: str | None,
    execution_result: object,
) -> dict[str, object]:
    """Run independent structural, authority, evidence, and final checks.

    This is deliberately a pure post-verifier. It receives the result from the
    existing bounded executor, but it cannot execute another action or mutate
    the workspace. A caller may use the receipt as a second opinion before
    returning a proposal to the router.
    """

    passes: list[dict[str, object]] = []
    structure_ok = isinstance(proposal, dict) and proposal.get("schema") == "wrench.proposal.v1"
    action = proposal.get("action") if isinstance(proposal, dict) else None
    if not structure_ok:
        passes.append(_pass("schema", False, "proposal_schema_invalid"))
    elif action not in _ALLOWED_ACTIONS:
        passes.append(_pass("schema", False, "action_not_allowlisted"))
    else:
        required = _REQUIRED_FIELDS[action]
        missing = sorted(field for field in required if field not in proposal)
        passes.append(_pass("schema", not missing, "missing:" + ",".join(missing) if missing else None))

    prompt = request_prompt.casefold() if isinstance(request_prompt, str) else ""
    authority_ok = True
    authority_reason: str | None = None
    if any(marker in prompt for marker in OUT_OF_DOMAIN_MARKERS):
        authority_ok = False
        authority_reason = "task_family_not_allowlisted"
    if action in _ALLOWED_ACTIONS and any(token in prompt for token in ("delete", "remove", "destroy", "erase")):
        authority_ok = False
        authority_reason = "action_not_allowlisted"
    passes.append(_pass("authority", authority_ok, authority_reason))

    evidence_ok = isinstance(execution_result, dict)
    evidence_reason: str | None = None
    if not evidence_ok:
        evidence_reason = "execution_result_invalid"
    elif execution_result.get("status") == "accepted":
        if execution_result.get("action") != action:
            evidence_ok = False
            evidence_reason = "accepted_action_mismatch"
        elif execution_result.get("mutated") is True or execution_result.get("applied") is True or (
            isinstance(execution_result.get("observation"), dict)
            and (
                execution_result["observation"].get("mutated") is True
                or execution_result["observation"].get("applied") is True
            )
        ):
            evidence_ok = False
            evidence_reason = "mutation_evidence_present"
        elif action == "patch_draft" and (proposal.get("review_only") is not True or execution_result.get("observation", {}).get("applied") is not False):
            evidence_ok = False
            evidence_reason = "patch_review_only_invariant_failed"
    elif execution_result.get("status") == "abstain":
        evidence_ok = isinstance(execution_result.get("fallback_reason"), str) and bool(execution_result.get("fallback_reason"))
        if not evidence_ok:
            evidence_reason = "abstain_reason_missing"
    else:
        evidence_ok = False
        evidence_reason = "execution_status_invalid"
    passes.append(_pass("evidence", evidence_ok, evidence_reason))

    consistency_ok = True
    consistency_reason: str | None = None
    if isinstance(proposal, dict) and action == "literal_search" and "regex" in prompt and proposal.get("mode", "literal") == "literal":
        consistency_ok = False
        consistency_reason = "literal_mode_required"
    if isinstance(proposal, dict) and action in _ALLOWED_ACTIONS and ("..\\" in prompt or "parent directory" in prompt or "outside the repository" in prompt):
        consistency_ok = False
        consistency_reason = "path_outside_allowed_root"
    passes.append(_pass("consistency", consistency_ok, consistency_reason))

    final_ok = all(bool(row["passed"]) for row in passes)
    return {
        "schema": "wrench.multi-pass-verifier.v1",
        "passed": final_ok,
        "passes": passes,
        "proposal_sha256": _digest(json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)) if isinstance(proposal, dict) else None,
        "execution_status": execution_result.get("status") if isinstance(execution_result, dict) else None,
    }
