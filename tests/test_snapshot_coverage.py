from __future__ import annotations

from dataclasses import replace

import wrench_harness.snapshot_coverage as coverage
from wrench_harness.snapshot import create_snapshot
from wrench_harness.snapshot_coverage import (
    CoverageFileStatus,
    build_snapshot_coverage_receipt,
)


def test_selected_coverage_binds_exact_snapshot_and_reports_parser_limits(tmp_path):
    (tmp_path / "worker.py").write_text("class Worker:\n    def run(self):\n        return 1\n", encoding="utf-8")
    (tmp_path / "api.ts").write_text("interface Lookup {}\nfunction lookup() {}\n", encoding="utf-8")
    (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["worker.py", "api.ts", "broken.py"])

    receipt = build_snapshot_coverage_receipt(tmp_path, snapshot, ["worker.py", "api.ts", "broken.py"])

    assert receipt.snapshot_sha256 == snapshot.snapshot_sha256
    assert receipt.selected_subset_only is True
    assert receipt.requested_count == receipt.indexed_count + receipt.unsupported_count + 1
    assert receipt.requested_count_complete is True
    assert receipt.missing_count == receipt.stale_count == receipt.error_count == receipt.limit_count == 0
    files = {row.source_path: row for row in receipt.files}
    assert files["worker.py"].status is CoverageFileStatus.INDEXED
    assert files["worker.py"].parser == "python_ast"
    assert files["worker.py"].language == "py"
    assert files["worker.py"].symbol_count == 2
    assert files["api.ts"].status is CoverageFileStatus.UNSUPPORTED
    assert files["api.ts"].parser == "lexical_fallback"
    assert files["api.ts"].symbol_count == 2
    assert files["broken.py"].status is CoverageFileStatus.SYNTAX_ERROR
    assert files["broken.py"].syntax_error.startswith("SyntaxError:")
    assert all(row.source_sha256 for row in receipt.files)
    assert receipt.receipt_sha256 == build_snapshot_coverage_receipt(
        tmp_path, snapshot, ["worker.py", "api.ts", "broken.py"]
    ).receipt_sha256


def test_selected_coverage_counts_missing_stale_and_other_errors(tmp_path):
    (tmp_path / "missing.py").write_text("def missing(): pass\n", encoding="utf-8")
    (tmp_path / "stale.py").write_text("def before(): pass\n", encoding="utf-8")
    (tmp_path / "binary.py").write_bytes(b"def invalid(): \xff\n")
    snapshot = create_snapshot(tmp_path, ["missing.py", "stale.py", "binary.py"])
    (tmp_path / "missing.py").unlink()
    (tmp_path / "stale.py").write_text("def after(): pass\n", encoding="utf-8")

    receipt = build_snapshot_coverage_receipt(
        tmp_path, snapshot, ["missing.py", "stale.py", "unknown.py", "binary.py"]
    )

    statuses = {row.requested_path: row.status for row in receipt.files}
    assert statuses["missing.py"] is CoverageFileStatus.MISSING
    assert statuses["stale.py"] is CoverageFileStatus.STALE
    assert statuses["unknown.py"] is CoverageFileStatus.ERROR
    assert statuses["binary.py"] is CoverageFileStatus.NON_TEXT
    assert receipt.missing_count == 1
    assert receipt.stale_count == 1
    assert receipt.error_count == 2
    assert receipt.exact_read_attempts == 4
    assert receipt.exact_read_successes == 1
    assert dict(receipt.exact_read_status_counts) == {"changed": 1, "missing": 1, "ok": 1, "unknown_source": 1}


def test_selected_coverage_stops_at_file_and_aggregate_caps(tmp_path, monkeypatch):
    (tmp_path / "large.py").write_text("x" * 32, encoding="utf-8")
    (tmp_path / "next.py").write_text("def n(): pass\n", encoding="utf-8")
    (tmp_path / "later.py").write_text("x=1\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["large.py", "next.py", "later.py"])
    monkeypatch.setattr(coverage, "MAX_FILE_BYTES", 16)

    file_limited = build_snapshot_coverage_receipt(tmp_path, snapshot, ["large.py", "next.py"])

    assert [row.status for row in file_limited.files] == [
        CoverageFileStatus.LIMIT_EXCEEDED,
        CoverageFileStatus.INDEXED,
    ]
    assert file_limited.limit_count == 1

    monkeypatch.setattr(coverage, "MAX_FILE_BYTES", 64 * 1024)
    monkeypatch.setattr(coverage, "MAX_AGGREGATE_BYTES", 16)
    aggregate_limited = build_snapshot_coverage_receipt(tmp_path, snapshot, ["next.py", "large.py", "later.py"])

    assert [row.status for row in aggregate_limited.files] == [
        CoverageFileStatus.INDEXED,
        CoverageFileStatus.LIMIT_EXCEEDED,
        CoverageFileStatus.LIMIT_EXCEEDED,
    ]
    assert aggregate_limited.exact_read_attempts == 2
    assert aggregate_limited.limit_count == 2


def test_selected_coverage_limits_oversized_path_set_without_reads(tmp_path, monkeypatch):
    (tmp_path / "one.py").write_text("def one(): pass\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["one.py"])
    monkeypatch.setattr(coverage, "MAX_FILES", 1)

    receipt = build_snapshot_coverage_receipt(tmp_path, snapshot, ["one.py", "one.py"])

    assert receipt.requested_count == 2
    assert receipt.requested_count_complete is False
    assert receipt.limit_count == 2
    assert receipt.exact_read_attempts == 0
    assert all(row.status is CoverageFileStatus.LIMIT_EXCEEDED for row in receipt.files)


def test_selected_coverage_marks_invalid_snapshot_as_error_without_hash_binding(tmp_path):
    (tmp_path / "one.py").write_text("def one(): pass\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["one.py"])
    forged = replace(snapshot, snapshot_sha256="z" * 64)

    receipt = build_snapshot_coverage_receipt(tmp_path, forged, ["one.py"])

    assert receipt.snapshot_sha256 is None
    assert receipt.error_count == 1
    assert receipt.exact_read_attempts == 1
    assert receipt.files[0].status is CoverageFileStatus.ERROR


def test_selected_coverage_preserves_paths_observed_before_iterator_failure(tmp_path):
    (tmp_path / "one.py").write_text("def one(): pass\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["one.py"])

    def broken_paths():
        yield "one.py"
        raise RuntimeError("synthetic iterator failure")

    receipt = build_snapshot_coverage_receipt(tmp_path, snapshot, broken_paths())

    assert receipt.requested_count == 1
    assert receipt.requested_count_complete is False
    assert receipt.error_count == 1
    assert receipt.exact_read_attempts == 0
    assert receipt.files[0].requested_path == "one.py"
    assert receipt.files[0].status is CoverageFileStatus.ERROR


def test_selected_coverage_bounds_display_of_overlong_path(tmp_path):
    (tmp_path / "one.py").write_text("def one(): pass\n", encoding="utf-8")
    snapshot = create_snapshot(tmp_path, ["one.py"])

    receipt = build_snapshot_coverage_receipt(tmp_path, snapshot, ["x" * 1_000_000])

    assert receipt.files[0].status is CoverageFileStatus.ERROR
    assert len(receipt.files[0].requested_path) == coverage.MAX_PATH_CHARS
