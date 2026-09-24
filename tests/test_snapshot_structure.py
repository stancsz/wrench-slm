from __future__ import annotations

from dataclasses import replace

import pytest

import wrench_harness.snapshot_structure as structural
from wrench_harness.snapshot import create_snapshot
from wrench_harness.snapshot_structure import (
    StructuralStatus,
    build_snapshot_symbol_index,
    query_snapshot_symbols,
)


def _snapshot(root, paths):
    return create_snapshot(root, paths)


def test_indexes_python_and_lexical_declarations_with_source_identity(tmp_path):
    (tmp_path / "worker.py").write_text("class Worker:\n    def run(self):\n        return 1\n", encoding="utf-8")
    (tmp_path / "api.ts").write_text("interface Lookup { value: string }\nfunction lookup() {}\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["worker.py", "api.ts"])

    result = build_snapshot_symbol_index(tmp_path, snapshot, ["api.ts", "worker.py"])

    assert result.status is StructuralStatus.OK
    assert result.index.symbol_count == 4
    assert result.exact_read_attempts == result.exact_read_successes == 2
    assert result.exact_read_returned_bytes == sum((tmp_path / path).stat().st_size for path in ("worker.py", "api.ts"))
    assert result.exact_read_status_counts == (("ok", 2),)
    files = {file.path: file for file in result.index.files}
    assert files["worker.py"].parser == "python_ast"
    assert files["worker.py"].language == "py"
    assert {symbol.name for symbol in files["worker.py"].symbols} == {"Worker", "run"}
    assert files["api.ts"].parser == "lexical_fallback"
    assert {symbol.name for symbol in files["api.ts"].symbols} == {"Lookup", "lookup"}
    for file in result.index.files:
        assert file.source_sha256
        for symbol in file.symbols:
            assert symbol.snapshot_sha256 == snapshot.snapshot_sha256
            assert symbol.source_sha256 == file.source_sha256
            assert symbol.start_line >= 1 and symbol.end_line >= symbol.start_line

    candidates = query_snapshot_symbols(result.index, "worker run")
    assert candidates.status is StructuralStatus.OK
    assert candidates.candidates[0].name in {"Worker", "run"}
    assert candidates.candidates[0].snapshot_sha256 == snapshot.snapshot_sha256


def test_index_and_candidate_order_are_deterministic(tmp_path):
    (tmp_path / "a.py").write_text("def alpha():\n    pass\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def beta():\n    pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py", "b.py"])
    left = build_snapshot_symbol_index(tmp_path, snapshot, ["a.py", "b.py"]).index
    right = build_snapshot_symbol_index(tmp_path, snapshot, ["b.py", "a.py"]).index

    assert left.index_sha256 == right.index_sha256
    assert [file.path for file in left.files] == ["a.py", "b.py"]
    assert query_snapshot_symbols(left, "def", limit=8) == query_snapshot_symbols(right, "def", limit=8)


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("unknown_snapshot", StructuralStatus.UNKNOWN_SNAPSHOT),
        ("unknown_source", StructuralStatus.UNKNOWN_SOURCE),
        ("missing", StructuralStatus.MISSING),
        ("stale", StructuralStatus.STALE),
        ("unsafe", StructuralStatus.UNSAFE),
    ],
)
def test_retrieval_failures_never_return_partial_index(tmp_path, case, expected):
    (tmp_path / "a.py").write_text("def alpha(): pass\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def beta(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py", "b.py"])
    supplied_snapshot = snapshot
    paths = ["a.py", "b.py"]
    if case == "unknown_snapshot":
        supplied_snapshot = object()
    elif case == "unknown_source":
        paths = ["a.py", "missing.py"]
    elif case == "missing":
        (tmp_path / "b.py").unlink()
    elif case == "stale":
        (tmp_path / "b.py").write_text("def changed(): pass\n", encoding="utf-8")
    elif case == "unsafe":
        paths = ["a.py", "../b.py"]

    result = build_snapshot_symbol_index(tmp_path, supplied_snapshot, paths)

    assert result.status is expected
    assert result.index is None
    if case == "stale":
        assert result.exact_read_attempts == 2
        assert result.exact_read_successes == 1
        assert result.exact_read_returned_bytes == (tmp_path / "a.py").stat().st_size
        assert result.exact_read_status_counts == (("changed", 1), ("ok", 1))


def test_invalid_utf8_is_reported_without_index(tmp_path):
    (tmp_path / "bad.py").write_bytes(b"def bad(): \xff\n")
    snapshot = _snapshot(tmp_path, ["bad.py"])

    result = build_snapshot_symbol_index(tmp_path, snapshot, ["bad.py"])

    assert result.status is StructuralStatus.NON_TEXT
    assert result.index is None


def test_file_aggregate_symbol_query_and_output_caps(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("def alpha(): pass\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("def beta(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py", "b.py"])

    monkeypatch.setattr(structural, "MAX_FILES", 1)
    assert build_snapshot_symbol_index(tmp_path, snapshot, ["a.py", "b.py"]).status is StructuralStatus.LIMIT_EXCEEDED
    monkeypatch.setattr(structural, "MAX_FILES", 16)
    monkeypatch.setattr(structural, "MAX_FILE_BYTES", 4)
    assert build_snapshot_symbol_index(tmp_path, snapshot, ["a.py"]).status is StructuralStatus.LIMIT_EXCEEDED
    monkeypatch.setattr(structural, "MAX_FILE_BYTES", 64 * 1024)
    monkeypatch.setattr(structural, "MAX_AGGREGATE_BYTES", 10)
    assert build_snapshot_symbol_index(tmp_path, snapshot, ["a.py", "b.py"]).status is StructuralStatus.LIMIT_EXCEEDED

    monkeypatch.setattr(structural, "MAX_AGGREGATE_BYTES", 512 * 1024)
    index = build_snapshot_symbol_index(tmp_path, snapshot, ["a.py", "b.py"]).index
    monkeypatch.setattr(structural, "MAX_QUERY_CHARS", 2)
    assert query_snapshot_symbols(index, "alpha").status is StructuralStatus.INVALID_QUERY
    monkeypatch.setattr(structural, "MAX_QUERY_CHARS", 256)
    monkeypatch.setattr(structural, "MAX_CANDIDATES", 1)
    assert query_snapshot_symbols(index, "def", limit=2).status is StructuralStatus.LIMIT_EXCEEDED


def test_symbol_and_output_caps_never_return_partial_index(tmp_path, monkeypatch):
    (tmp_path / "many.py").write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["many.py"])
    monkeypatch.setattr(structural, "MAX_SYMBOLS", 1)

    result = build_snapshot_symbol_index(tmp_path, snapshot, ["many.py"])

    assert result.status is StructuralStatus.SYMBOL_LIMIT_EXCEEDED
    assert result.index is None

    monkeypatch.setattr(structural, "MAX_SYMBOLS", 4096)
    monkeypatch.setattr(structural, "MAX_OUTPUT_BYTES", 16)
    result = build_snapshot_symbol_index(tmp_path, snapshot, ["many.py"])
    assert result.status is StructuralStatus.OUTPUT_LIMIT_EXCEEDED
    assert result.index is None
    assert result.exact_read_attempts == result.exact_read_successes == 1
    assert result.exact_read_returned_bytes == (tmp_path / "many.py").stat().st_size


@pytest.mark.parametrize("mutation", [
    "list_files",
    "bad_index_hash",
    "wrong_symbol_count",
    "symbol_snapshot_mismatch",
    "symbol_source_mismatch",
    "bad_line_range",
    "bad_file_path",
    "oversized_signature",
])
def test_query_rejects_forged_or_malformed_index_without_candidates(tmp_path, mutation):
    (tmp_path / "a.py").write_text("def alpha(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py"])
    valid = build_snapshot_symbol_index(tmp_path, snapshot, ["a.py"]).index
    file = valid.files[0]
    symbol = file.symbols[0]
    if mutation == "list_files":
        forged = replace(valid, files=list(valid.files))
    elif mutation == "bad_index_hash":
        forged = replace(valid, index_sha256="z" * 64)
    elif mutation == "wrong_symbol_count":
        forged = replace(valid, symbol_count=valid.symbol_count + 1)
    elif mutation == "symbol_snapshot_mismatch":
        forged_symbol = replace(symbol, snapshot_sha256="0" * 64)
        forged = replace(valid, files=(replace(file, symbols=(forged_symbol,)),))
    elif mutation == "symbol_source_mismatch":
        forged_symbol = replace(symbol, source_sha256="0" * 64)
        forged = replace(valid, files=(replace(file, symbols=(forged_symbol,)),))
    elif mutation == "bad_line_range":
        forged_symbol = replace(symbol, start_line=0)
        forged = replace(valid, files=(replace(file, symbols=(forged_symbol,)),))
    elif mutation == "bad_file_path":
        forged = replace(valid, files=(replace(file, path="../a.py"),))
    else:
        forged_symbol = replace(symbol, signature="x" * (structural.MAX_FILE_BYTES + 1))
        forged = replace(valid, files=(replace(file, symbols=(forged_symbol,)),))

    result = query_snapshot_symbols(forged, "alpha")

    assert result.status is StructuralStatus.INVALID_INDEX
    assert result.candidates == ()


def test_query_output_overflow_returns_no_candidates(tmp_path, monkeypatch):
    (tmp_path / "a.py").write_text("def alpha(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py"])
    index = build_snapshot_symbol_index(tmp_path, snapshot, ["a.py"]).index
    monkeypatch.setattr(structural, "MAX_QUERY_OUTPUT_BYTES", 1)

    result = query_snapshot_symbols(index, "alpha")

    assert result.status is StructuralStatus.OUTPUT_LIMIT_EXCEEDED
    assert result.candidates == ()


def test_canonical_serializer_rejects_escaped_output_before_encoding():
    with pytest.raises(OverflowError):
        structural._canonical_bytes({"x": "\x00" * 1000}, 20)


def test_query_rejects_string_and_integer_subclasses_before_user_methods(tmp_path):
    (tmp_path / "a.py").write_text("def alpha(): pass\n", encoding="utf-8")
    snapshot = _snapshot(tmp_path, ["a.py"])
    index = build_snapshot_symbol_index(tmp_path, snapshot, ["a.py"]).index

    class HostileString(str):
        def __len__(self):
            raise AssertionError("query length must not be invoked")

    class HostileInt(int):
        def __lt__(self, other):
            raise AssertionError("limit comparison must not be invoked")

    assert query_snapshot_symbols(index, HostileString("alpha")).status is StructuralStatus.INVALID_QUERY
    assert query_snapshot_symbols(index, "alpha", limit=HostileInt(1)).status is StructuralStatus.LIMIT_EXCEEDED
