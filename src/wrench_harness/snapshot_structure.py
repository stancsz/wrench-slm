"""Bounded read-only structural symbol indexing over exact source snapshots."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Iterable

from .snapshot import RetrievalStatus, SourceRootBinding, SourceSnapshot, retrieve_exact
from .toolbelt import build_symbol_index, lookup_symbols


MAX_FILES = 16
MAX_FILE_BYTES = 64 * 1024
MAX_AGGREGATE_BYTES = 512 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_QUERY_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_SYMBOLS = 4096
MAX_CANDIDATES = 32
MAX_QUERY_CHARS = 256
MAX_PATH_CHARS = 1024
_SHA256_CHARS = frozenset("0123456789abcdef")
MAX_OUTPUT_DEPTH = 32
MAX_OUTPUT_NODES = 30_000


class StructuralStatus(str, Enum):
    OK = "ok"
    UNKNOWN_SNAPSHOT = "unknown_snapshot"
    UNKNOWN_SOURCE = "unknown_source"
    MISSING = "missing"
    STALE = "stale"
    UNSAFE = "unsafe"
    NON_TEXT = "non_text"
    LIMIT_EXCEEDED = "limit_exceeded"
    INVALID_PATH_SET = "invalid_path_set"
    SYMBOL_LIMIT_EXCEEDED = "symbol_limit_exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    PARSE_ERROR = "parse_error"
    INVALID_INDEX = "invalid_index"
    INVALID_QUERY = "invalid_query"
    NO_MATCHES = "no_matches"


@dataclass(frozen=True)
class StructuralSymbol:
    name: str
    kind: str
    path: str
    start_line: int
    end_line: int
    signature: str
    snapshot_sha256: str
    source_sha256: str
    parser: str
    language: str


@dataclass(frozen=True)
class StructuralFile:
    path: str
    source_sha256: str
    parser: str
    language: str
    symbols: tuple[StructuralSymbol, ...]


@dataclass(frozen=True)
class SnapshotSymbolIndex:
    snapshot_sha256: str
    files: tuple[StructuralFile, ...]
    symbol_count: int
    index_sha256: str
    serialized_bytes: int


@dataclass(frozen=True)
class SnapshotIndexResult:
    status: StructuralStatus
    index: SnapshotSymbolIndex | None = None
    path: str | None = None
    reason: str | None = None
    exact_read_attempts: int = 0
    exact_read_successes: int = 0
    exact_read_returned_bytes: int = 0
    exact_read_status_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class StructuralCandidate:
    name: str
    kind: str
    path: str
    start_line: int
    end_line: int
    signature: str
    match_score: int
    snapshot_sha256: str
    source_sha256: str
    parser: str
    language: str


@dataclass(frozen=True)
class CandidateQueryResult:
    status: StructuralStatus
    snapshot_sha256: str | None
    candidates: tuple[StructuralCandidate, ...] = ()
    reason: str | None = None


def _canonical_bytes(value: object, limit: int) -> bytes:
    """Canonicalize within the byte cap without constructing an oversized blob."""
    nodes = 0
    serialized_size = 0
    active: set[int] = set()

    def add_size(amount: int) -> None:
        nonlocal serialized_size
        serialized_size += amount
        if serialized_size > limit:
            raise OverflowError("structural_output_byte_limit_exceeded")

    def visit_string(item: str) -> None:
        if type(item) is not str or len(item) > limit:
            raise OverflowError("structural_output_byte_limit_exceeded")
        # Count the exact UTF-8 JSON string representation before json's
        # encoder can allocate an escaped chunk larger than the output cap.
        size = 2  # quotes
        for char in item:
            codepoint = ord(char)
            if 0xD800 <= codepoint <= 0xDFFF:
                raise ValueError("structural_output_invalid_unicode")
            if char in ('"', "\\") or codepoint in (8, 9, 10, 12, 13):
                size += 2
            elif codepoint < 0x20:
                size += 6
            elif codepoint <= 0x7F:
                size += 1
            elif codepoint <= 0x7FF:
                size += 2
            elif codepoint <= 0xFFFF:
                size += 3
            else:
                size += 4
            if size + serialized_size > limit:
                raise OverflowError("structural_output_byte_limit_exceeded")
        add_size(size)

    def visit(item: object, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_OUTPUT_NODES or depth > MAX_OUTPUT_DEPTH:
            raise OverflowError("structural_output_shape_limit_exceeded")
        if item is None or type(item) is bool:
            add_size(4 if item is None else (4 if item else 5))
            return
        if type(item) is int:
            if item.bit_length() > 256:
                raise OverflowError("structural_output_integer_limit_exceeded")
            add_size(len(str(item)))
            return
        if type(item) is StructuralStatus:
            visit_string(item.value)
            return
        if type(item) is str:
            visit_string(item)
            return
        if type(item) is float:
            if not math.isfinite(item):
                raise ValueError("structural_output_nonfinite_number")
            add_size(len(json.dumps(item, allow_nan=False, separators=(",", ":"))))
            return
        if type(item) in (dict, list, tuple):
            identity = id(item)
            if identity in active:
                raise ValueError("structural_output_cycle")
            if len(item) > MAX_OUTPUT_NODES:
                raise OverflowError("structural_output_collection_limit_exceeded")
            active.add(identity)
            try:
                if type(item) is dict:
                    first = True
                    add_size(2)
                    for key, nested in item.items():
                        if type(key) is not str:
                            raise ValueError("structural_output_key_invalid")
                        if not first:
                            add_size(1)
                        first = False
                        visit(key, depth + 1)
                        add_size(1)
                        visit(nested, depth + 1)
                else:
                    first = True
                    add_size(2)
                    for nested in item:
                        if not first:
                            add_size(1)
                        first = False
                        visit(nested, depth + 1)
            finally:
                active.remove(identity)
            return
        raise ValueError("structural_output_not_serializable")

    visit(value, 0)
    try:
        encoder = json.JSONEncoder(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        chunks: list[bytes] = []
        total = 0
        for chunk in encoder.iterencode(value):
            encoded = chunk.encode("utf-8")
            total += len(encoded)
            if total > limit:
                raise OverflowError("structural_output_byte_limit_exceeded")
            chunks.append(encoded)
        return b"".join(chunks)
    except OverflowError:
        raise
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise ValueError("structural_output_not_serializable") from exc


def _index_payload(snapshot_sha256: str, files: tuple[StructuralFile, ...], symbol_count: int) -> dict[str, object]:
    return {
        "schema": "wrench.snapshot-structural-index.v1",
        "snapshot_sha256": snapshot_sha256,
        "files": [
            {
                "path": file.path,
                "source_sha256": file.source_sha256,
                "parser": file.parser,
                "language": file.language,
                "symbols": [asdict(symbol) for symbol in file.symbols],
            }
            for file in files
        ],
        "symbol_count": symbol_count,
    }


def _is_sha256(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(char in _SHA256_CHARS for char in value)


def _bounded_text(value: object, max_chars: int, max_bytes: int) -> bool:
    if type(value) is not str or not value or len(value) > max_chars:
        return False
    size = 0
    for char in value:
        codepoint = ord(char)
        if 0xD800 <= codepoint <= 0xDFFF:
            return False
        size += 1 if codepoint <= 0x7F else 2 if codepoint <= 0x7FF else 3 if codepoint <= 0xFFFF else 4
        if size > max_bytes:
            return False
    return True


def _validate_index(index: object) -> bool:
    """Validate immutable shape, bounds, identities, and canonical hash first."""
    if type(index) is not SnapshotSymbolIndex:
        return False
    if not _is_sha256(index.snapshot_sha256) or not _is_sha256(index.index_sha256):
        return False
    if type(index.files) is not tuple or not 1 <= len(index.files) <= MAX_FILES:
        return False
    if (
        type(index.symbol_count) is not int
        or not 0 <= index.symbol_count <= MAX_SYMBOLS
        or type(index.serialized_bytes) is not int
        or not 1 <= index.serialized_bytes <= MAX_OUTPUT_BYTES
    ):
        return False

    seen_paths: set[str] = set()
    duplicate_keys: set[str] = set()
    total_symbols = 0
    previous_path: str | None = None
    for file in index.files:
        if type(file) is not StructuralFile:
            return False
        if not _bounded_text(file.path, MAX_PATH_CHARS, MAX_FILE_BYTES) or file.path in seen_paths:
            return False
        parts = file.path.split("/")
        if (
            "\\" in file.path or file.path.startswith("/") or ":" in file.path
            or any(part in ("", ".", "..") or part.endswith((".", " ")) for part in parts)
        ):
            return False
        duplicate_key = file.path.casefold() if os.name == "nt" else file.path
        if duplicate_key in duplicate_keys:
            return False
        duplicate_keys.add(duplicate_key)
        if previous_path is not None and file.path <= previous_path:
            return False
        previous_path = file.path
        seen_paths.add(file.path)
        if not _is_sha256(file.source_sha256):
            return False
        if not _bounded_text(file.parser, 32, 128) or file.parser not in {"python_ast", "lexical_fallback"}:
            return False
        if not _bounded_text(file.language, 32, 128):
            return False
        if type(file.symbols) is not tuple or len(file.symbols) > MAX_SYMBOLS:
            return False
        previous_symbol_key: tuple[int, str] | None = None
        for symbol in file.symbols:
            if type(symbol) is not StructuralSymbol:
                return False
            if not _bounded_text(symbol.name, 256, 1024) or not _bounded_text(symbol.kind, 64, 256):
                return False
            if not _bounded_text(symbol.path, MAX_PATH_CHARS, MAX_FILE_BYTES) or symbol.path != file.path:
                return False
            if not _bounded_text(symbol.signature, MAX_FILE_BYTES, MAX_FILE_BYTES):
                return False
            if not _is_sha256(symbol.snapshot_sha256) or symbol.snapshot_sha256 != index.snapshot_sha256:
                return False
            if not _is_sha256(symbol.source_sha256) or symbol.source_sha256 != file.source_sha256:
                return False
            if symbol.parser != file.parser or symbol.language != file.language:
                return False
            if (
                type(symbol.start_line) is not int
                or type(symbol.end_line) is not int
                or not 1 <= symbol.start_line <= symbol.end_line <= MAX_FILE_BYTES + 1
            ):
                return False
            symbol_key = (symbol.start_line, symbol.name)
            if previous_symbol_key is not None and symbol_key < previous_symbol_key:
                return False
            previous_symbol_key = symbol_key
            total_symbols += 1
            if total_symbols > MAX_SYMBOLS:
                return False
    if total_symbols != index.symbol_count:
        return False
    try:
        encoded = _canonical_bytes(_index_payload(index.snapshot_sha256, index.files, total_symbols), MAX_OUTPUT_BYTES)
    except (OverflowError, ValueError, TypeError):
        return False
    return len(encoded) == index.serialized_bytes and hashlib.sha256(encoded).hexdigest() == index.index_sha256


def build_snapshot_symbol_index(
    root: str | os.PathLike[str] | SourceRootBinding,
    snapshot: SourceSnapshot,
    paths: Iterable[str | os.PathLike[str]],
) -> SnapshotIndexResult:
    """Index only caller-enumerated, exact-read snapshot files; never scans."""
    exact_read_attempts = 0
    exact_read_successes = 0
    exact_read_returned_bytes = 0
    exact_read_status_counts: dict[str, int] = {}

    def result(
        status: StructuralStatus,
        index: SnapshotSymbolIndex | None = None,
        path: str | None = None,
        reason: str | None = None,
    ) -> SnapshotIndexResult:
        return SnapshotIndexResult(
            status, index, path, reason, exact_read_attempts, exact_read_successes,
            exact_read_returned_bytes, tuple(sorted(exact_read_status_counts.items())),
        )

    if isinstance(paths, (str, bytes)):
        return result(StructuralStatus.INVALID_PATH_SET, reason="paths_must_be_finite_iterable")
    try:
        iterator = iter(paths)
        selected_paths: list[str | os.PathLike[str]] = []
        for _ in range(MAX_FILES + 1):
            try:
                selected_paths.append(next(iterator))
            except StopIteration:
                break
    except (TypeError, RuntimeError) as exc:
        return result(StructuralStatus.INVALID_PATH_SET, reason=type(exc).__name__)
    if not selected_paths:
        return result(StructuralStatus.INVALID_PATH_SET, reason="empty_path_set")
    if len(selected_paths) > MAX_FILES:
        return result(StructuralStatus.LIMIT_EXCEEDED, reason="file_count_limit_exceeded")

    retrieved: list[tuple[str, bytes, str]] = []
    seen: set[str] = set()
    total_bytes = 0
    status_map = {
        RetrievalStatus.UNKNOWN_SNAPSHOT: StructuralStatus.UNKNOWN_SNAPSHOT,
        RetrievalStatus.UNKNOWN_SOURCE: StructuralStatus.UNKNOWN_SOURCE,
        RetrievalStatus.MISSING: StructuralStatus.MISSING,
        RetrievalStatus.CHANGED: StructuralStatus.STALE,
        RetrievalStatus.UNSAFE: StructuralStatus.UNSAFE,
    }
    for path in selected_paths:
        exact_read_attempts += 1
        retrieved_result = retrieve_exact(root, snapshot, path)
        exact_read_status_counts[retrieved_result.status.value] = exact_read_status_counts.get(retrieved_result.status.value, 0) + 1
        if type(retrieved_result.data) is bytes:
            exact_read_returned_bytes += len(retrieved_result.data)
            if retrieved_result.status is RetrievalStatus.OK:
                exact_read_successes += 1
        if retrieved_result.status in status_map:
            return result(status_map[retrieved_result.status], path=retrieved_result.path)
        if retrieved_result.status is not RetrievalStatus.OK or not isinstance(retrieved_result.data, bytes) or retrieved_result.path is None:
            return result(StructuralStatus.UNSAFE, path=retrieved_result.path)
        if retrieved_result.path in seen:
            return result(StructuralStatus.INVALID_PATH_SET, path=retrieved_result.path, reason="duplicate_normalized_path")
        seen.add(retrieved_result.path)
        if len(retrieved_result.data) > MAX_FILE_BYTES:
            return result(StructuralStatus.LIMIT_EXCEEDED, path=retrieved_result.path, reason="file_byte_limit_exceeded")
        total_bytes += len(retrieved_result.data)
        if total_bytes > MAX_AGGREGATE_BYTES:
            return result(StructuralStatus.LIMIT_EXCEEDED, path=retrieved_result.path, reason="aggregate_byte_limit_exceeded")
        try:
            text = retrieved_result.data.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return result(StructuralStatus.NON_TEXT, path=retrieved_result.path)
        source_sha256 = hashlib.sha256(retrieved_result.data).hexdigest()
        retrieved.append((retrieved_result.path, retrieved_result.data, text))

    if not isinstance(snapshot, SourceSnapshot):
        return result(StructuralStatus.UNKNOWN_SNAPSHOT)
    retrieved.sort(key=lambda row: row[0])
    try:
        parser_index = build_symbol_index((path, text) for path, _, text in retrieved)
    except (TypeError, ValueError, RecursionError, OverflowError) as exc:
        return result(StructuralStatus.PARSE_ERROR, reason=type(exc).__name__)

    if not isinstance(parser_index.get("files"), list):
        return result(StructuralStatus.PARSE_ERROR, reason="parser_index_invalid")
    source_hashes = {path: hashlib.sha256(data).hexdigest() for path, data, _ in retrieved}
    files: list[StructuralFile] = []
    count = 0
    for file_row in parser_index["files"]:
        if not isinstance(file_row, dict) or not isinstance(file_row.get("symbols"), list):
            return result(StructuralStatus.PARSE_ERROR, reason="parser_file_invalid")
        path = file_row.get("path")
        parser = file_row.get("parser")
        language = file_row.get("language")
        source_sha256 = source_hashes.get(path)
        if not all(isinstance(value, str) for value in (path, parser, language, source_sha256)):
            return result(StructuralStatus.PARSE_ERROR, reason="parser_identity_invalid")
        symbols: list[StructuralSymbol] = []
        for row in file_row["symbols"]:
            if not isinstance(row, dict):
                return result(StructuralStatus.PARSE_ERROR, path=path, reason="parser_symbol_invalid")
            try:
                symbol = StructuralSymbol(
                    name=row["name"], kind=row["kind"], path=path,
                    start_line=row["start_line"], end_line=row["end_line"], signature=row["signature"],
                    snapshot_sha256=snapshot.snapshot_sha256, source_sha256=source_sha256,
                    parser=parser, language=language,
                )
            except (KeyError, TypeError) as exc:
                return result(StructuralStatus.PARSE_ERROR, path=path, reason="parser_symbol_invalid")
            symbols.append(symbol)
            count += 1
            if count > MAX_SYMBOLS:
                return result(StructuralStatus.SYMBOL_LIMIT_EXCEEDED, path=path)
        files.append(StructuralFile(path, source_sha256, parser, language, tuple(symbols)))

    file_tuple = tuple(files)
    payload = _index_payload(snapshot.snapshot_sha256, file_tuple, count)
    try:
        encoded = _canonical_bytes(payload, MAX_OUTPUT_BYTES)
    except OverflowError:
        return result(StructuralStatus.OUTPUT_LIMIT_EXCEEDED, reason="index_output_byte_limit_exceeded")
    except ValueError as exc:
        return result(StructuralStatus.PARSE_ERROR, reason=str(exc))
    index_hash = hashlib.sha256(encoded).hexdigest()
    return result(StructuralStatus.OK, SnapshotSymbolIndex(snapshot.snapshot_sha256, file_tuple, count, index_hash, len(encoded)))


def query_snapshot_symbols(
    index: SnapshotSymbolIndex,
    query: str,
    *,
    limit: int = 16,
) -> CandidateQueryResult:
    """Return bounded structural candidates, with source identity metadata."""
    if not _validate_index(index):
        snapshot_hash = index.snapshot_sha256 if type(index) is SnapshotSymbolIndex and _is_sha256(index.snapshot_sha256) else None
        return CandidateQueryResult(StructuralStatus.INVALID_INDEX, snapshot_hash)
    if type(query) is not str or not query or len(query) > MAX_QUERY_CHARS:
        return CandidateQueryResult(StructuralStatus.INVALID_QUERY, index.snapshot_sha256)
    if type(limit) is not int or not 1 <= limit <= MAX_CANDIDATES:
        return CandidateQueryResult(StructuralStatus.LIMIT_EXCEEDED, index.snapshot_sha256, reason="candidate_limit_invalid")
    parser_files = [
        {
            "path": file.path,
            "symbols": [
                {
                    "name": symbol.name, "kind": symbol.kind, "path": symbol.path,
                    "start_line": symbol.start_line, "end_line": symbol.end_line,
                    "signature": symbol.signature,
                }
                for symbol in file.symbols
            ],
        }
        for file in index.files
    ]
    parser_index = {"files": parser_files}
    matches = lookup_symbols(query, parser_index, limit=MAX_SYMBOLS)
    if not matches:
        return CandidateQueryResult(StructuralStatus.NO_MATCHES, index.snapshot_sha256)
    file_by_path = {file.path: file for file in index.files}
    matches.sort(key=lambda row: (-row["match_score"], row["path"], row["start_line"], row["name"]))
    candidates: list[StructuralCandidate] = []
    for row in matches[:limit]:
        file = file_by_path[row["path"]]
        candidates.append(
            StructuralCandidate(
                row["name"], row["kind"], row["path"], row["start_line"], row["end_line"],
                row["signature"], row["match_score"], index.snapshot_sha256,
                file.source_sha256, file.parser, file.language,
            )
        )
    result = CandidateQueryResult(StructuralStatus.OK, index.snapshot_sha256, tuple(candidates))
    try:
        _canonical_bytes(asdict(result), MAX_QUERY_OUTPUT_BYTES)
    except (OverflowError, ValueError):
        return CandidateQueryResult(StructuralStatus.OUTPUT_LIMIT_EXCEEDED, index.snapshot_sha256, reason="candidate_output_byte_limit_exceeded")
    return result


__all__ = [
    "MAX_AGGREGATE_BYTES",
    "MAX_CANDIDATES",
    "MAX_FILE_BYTES",
    "MAX_FILES",
    "MAX_OUTPUT_BYTES",
    "MAX_QUERY_OUTPUT_BYTES",
    "MAX_QUERY_CHARS",
    "MAX_SYMBOLS",
    "CandidateQueryResult",
    "SnapshotIndexResult",
    "SnapshotSymbolIndex",
    "StructuralCandidate",
    "StructuralFile",
    "StructuralStatus",
    "StructuralSymbol",
    "build_snapshot_symbol_index",
    "query_snapshot_symbols",
]
