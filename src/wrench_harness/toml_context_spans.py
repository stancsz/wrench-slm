"""Bounded exact TOML assignment spans for deterministic evidence retrieval."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass


MAX_TOML_CHARS = 64 * 1024
MAX_TOML_LINES = 4096
MAX_TOML_MATCHES = 64
MIN_TABLE_QUERY_TOKEN_MATCHES = 2
_TABLE_HEADER = re.compile(r"^\s*\[([A-Za-z0-9_.-]+)\]\s*(?:#.*)?$")
_KEY_ASSIGNMENT = re.compile(r"^\s*([A-Za-z0-9_-]+)\s*=")
_TOKEN = re.compile(r"[A-Za-z0-9]+")
_NUMBER = re.compile(r"(?<![A-Za-z0-9])\d+(?![A-Za-z0-9])")


@dataclass(frozen=True)
class TomlKeySpan:
    """One parser-validated, source-exact TOML assignment line."""

    name: str
    start_line: int
    end_line: int
    text: str
    match_score: int


@dataclass(frozen=True)
class TomlTableSpan:
    """One parser-validated TOML table, including its header and assignments."""

    name: str
    start_line: int
    end_line: int
    text: str
    match_score: int


def _tokens(value: str) -> frozenset[str]:
    return frozenset(item.lower() for item in _TOKEN.findall(value))


def _matches(query_token: str, source_token: str) -> bool:
    if query_token == source_token:
        return True
    if query_token.isdigit() or source_token.isdigit():
        return False
    return len(query_token) >= 4 and len(source_token) >= 4 and (
        query_token.startswith(source_token) or source_token.startswith(query_token)
    )


def extract_toml_key_spans(source_text: str, query: str) -> tuple[TomlKeySpan, ...]:
    """Return matching exact assignment lines, or empty for whole-file fallback.

    Only simple one-line bare-key assignments are narrowed. The complete file
    and each candidate assignment must parse with Python's TOML parser.
    Unsupported but valid TOML stays on the caller's whole-file path.
    """
    if (
        type(source_text) is not str
        or type(query) is not str
        or not source_text
        or len(source_text) > MAX_TOML_CHARS
        or len(query) > 256
        or "'''" in source_text
        or '"""' in source_text
    ):
        return ()
    lines = source_text.splitlines(keepends=True)
    if not lines or len(lines) > MAX_TOML_LINES:
        return ()
    try:
        tomllib.loads(source_text)
    except (tomllib.TOMLDecodeError, TypeError, ValueError):
        return ()

    query_tokens = _tokens(query)
    if not query_tokens:
        return ()
    current_table = ""
    entries: list[TomlKeySpan] = []
    for line_index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        candidate = stripped.strip()
        if not candidate or candidate.startswith("#"):
            continue
        if candidate.startswith("["):
            header = _TABLE_HEADER.fullmatch(stripped)
            if header is None:
                return ()
            current_table = header.group(1)
            continue
        assignment = _KEY_ASSIGNMENT.match(stripped)
        if assignment is None:
            return ()
        key = assignment.group(1)
        qualified_name = f"{current_table}.{key}" if current_table else key
        parser_input = (f"[{current_table}]\n" if current_table else "") + stripped + "\n"
        try:
            tomllib.loads(parser_input)
        except (tomllib.TOMLDecodeError, TypeError, ValueError):
            return ()
        entry_tokens = _tokens(qualified_name) | frozenset(_NUMBER.findall(stripped))
        score = sum(
            1 for query_token in query_tokens
            if any(_matches(query_token, source_token) for source_token in entry_tokens)
        )
        if score:
            entries.append(
                TomlKeySpan(
                    name=qualified_name,
                    start_line=line_index + 1,
                    end_line=line_index + 1,
                    text=line,
                    match_score=score,
                )
            )
        if len(entries) > MAX_TOML_MATCHES:
            return ()
    entries.sort(key=lambda item: (-item.match_score, item.start_line, item.name))
    return tuple(entries)


def extract_toml_table_spans(source_text: str, query: str) -> tuple[TomlTableSpan, ...]:
    """Return complete tables relevant to the query, preserving table meaning.

    The whole document must parse, and every selected table must consist of
    simple one-line bare-key assignments. Unsupported or multiline TOML
    returns an empty result so callers can keep the original whole file.
    """
    if (
        type(source_text) is not str
        or type(query) is not str
        or not source_text
        or len(source_text) > MAX_TOML_CHARS
        or len(query) > 256
        or "'''" in source_text
        or '"""' in source_text
    ):
        return ()
    lines = source_text.splitlines(keepends=True)
    if not lines or len(lines) > MAX_TOML_LINES:
        return ()
    try:
        tomllib.loads(source_text)
    except (tomllib.TOMLDecodeError, TypeError, ValueError):
        return ()

    query_tokens = _tokens(query)
    if not query_tokens:
        return ()

    blocks: list[tuple[str, int, int]] = []
    table_name = ""
    block_start = 0
    for line_index, line in enumerate(lines):
        stripped = line.rstrip("\r\n")
        candidate = stripped.strip()
        if not candidate or candidate.startswith("#"):
            continue
        if candidate.startswith("["):
            header = _TABLE_HEADER.fullmatch(stripped)
            if header is None:
                return ()
            if line_index > block_start or table_name:
                blocks.append((table_name, block_start, line_index))
            table_name = header.group(1)
            block_start = line_index
            continue
        if _KEY_ASSIGNMENT.match(stripped) is None:
            return ()
    blocks.append((table_name, block_start, len(lines)))
    if len(blocks) > MAX_TOML_MATCHES:
        return ()

    matches: list[TomlTableSpan] = []
    for name, start, end in blocks:
        block_lines = lines[start:end]
        if not block_lines:
            continue
        block_text = "".join(block_lines)
        try:
            tomllib.loads(block_text)
        except (tomllib.TOMLDecodeError, TypeError, ValueError):
            return ()
        matched_query_tokens: set[str] = set()
        for line in block_lines:
            stripped = line.rstrip("\r\n")
            candidate = stripped.strip()
            if not candidate or candidate.startswith("#") or candidate.startswith("["):
                continue
            assignment = _KEY_ASSIGNMENT.match(stripped)
            if assignment is None:
                return ()
            qualified_name = f"{name}.{assignment.group(1)}" if name else assignment.group(1)
            source_tokens = _tokens(qualified_name) | frozenset(_NUMBER.findall(stripped))
            matched_query_tokens.update(
                query_token for query_token in query_tokens
                if any(_matches(query_token, source_token) for source_token in source_tokens)
            )
        score = len(matched_query_tokens)
        if score >= MIN_TABLE_QUERY_TOKEN_MATCHES:
            matches.append(
                TomlTableSpan(
                    name=name,
                    start_line=start + 1,
                    end_line=end,
                    text=block_text,
                    match_score=score,
                )
            )
    matches.sort(key=lambda item: (-item.match_score, item.start_line, item.name))
    return tuple(matches)


__all__ = ["TomlKeySpan", "TomlTableSpan", "extract_toml_key_spans", "extract_toml_table_spans"]
