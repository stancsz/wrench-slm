from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import wrench_harness.snapshot_coverage as coverage
from wrench_harness.snapshot import SourceSnapshot, bind_source_root, create_snapshot
from wrench_harness.snapshot_coverage import (
    CoverageFileStatus,
    build_snapshot_coverage_receipt,
    build_snapshot_inventory_receipt,
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


def test_inventory_pages_entire_snapshot_and_is_order_independent(tmp_path):
    paths = []
    for index in range(37):
        name = f"src/file_{index:02}.py"
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / name).write_text(f"def item_{index}(): return {index}\n", encoding="utf-8")
        paths.append(name)
    binding = bind_source_root(tmp_path)
    first = create_snapshot(binding, paths)
    reverse_order = create_snapshot(binding, reversed(paths))

    receipt = build_snapshot_inventory_receipt(first, binding)
    reordered = build_snapshot_inventory_receipt(reverse_order, binding)

    assert receipt == reordered
    assert receipt.supplied_manifest_only is True
    assert receipt.complete is True
    assert receipt.entry_count == 37
    assert [page.entry_count for page in receipt.pages] == [16, 16, 5]
    assert [page.page_index for page in receipt.pages] == [0, 1, 2]
    assert sum(dict(receipt.status_counts).values()) == 37
    assert dict(receipt.status_counts)[CoverageFileStatus.INDEXED.value] == 37
    assert receipt.exact_read_attempts == receipt.exact_read_successes == 37
    assert len(receipt.receipt_sha256) == len(receipt.page_hash_chain_sha256) == 64
    assert len(receipt.pages) <= 16

    def chain_for(pages):
        chain = "0" * 64
        for page in pages:
            chain = hashlib.sha256(json.dumps(
                {"previous": chain, "page_sha256": page.page_sha256},
                sort_keys=True, separators=(",", ":"),
            ).encode("ascii")).hexdigest()
        return chain

    assert chain_for(receipt.pages) == receipt.page_hash_chain_sha256
    assert chain_for(tuple(reversed(receipt.pages))) != receipt.page_hash_chain_sha256


def test_inventory_rejects_duplicate_or_omitted_snapshot_manifest_rows(tmp_path):
    (tmp_path / "a.py").write_text("a = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("b = 2\n", encoding="utf-8")
    binding = bind_source_root(tmp_path)
    snapshot = create_snapshot(binding, ["a.py", "b.py"])

    duplicate = SourceSnapshot(
        snapshot.schema,
        (snapshot.sources[0], snapshot.sources[0]),
        snapshot.snapshot_sha256,
        snapshot.root_location_sha256,
        snapshot.root_identity,
    )
    omitted = SourceSnapshot(
        snapshot.schema,
        snapshot.sources[:1],
        snapshot.snapshot_sha256,
        snapshot.root_location_sha256,
        snapshot.root_identity,
    )

    for invalid in (duplicate, omitted):
        try:
            build_snapshot_inventory_receipt(invalid, binding)
        except ValueError as exc:
            assert str(exc) == "inventory_snapshot_invalid"
        else:
            raise AssertionError("invalid manifest accepted")


def test_inventory_stale_source_is_counted_and_marks_receipt_incomplete(tmp_path):
    (tmp_path / "stale.py").write_text("before = 1\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("ok = 1\n", encoding="utf-8")
    binding = bind_source_root(tmp_path)
    snapshot = create_snapshot(binding, ["ok.py", "stale.py"])
    (tmp_path / "stale.py").write_text("after = 2\n", encoding="utf-8")

    receipt = build_snapshot_inventory_receipt(snapshot, binding)

    assert receipt.complete is False
    assert receipt.entry_count == 2
    assert dict(receipt.status_counts)[CoverageFileStatus.INDEXED.value] == 1
    assert dict(receipt.status_counts)[CoverageFileStatus.STALE.value] == 1
    assert receipt.exact_read_attempts == 2
    assert dict(receipt.exact_read_status_counts)["changed"] == 1


def test_inventory_rejects_changed_root_binding(tmp_path):
    (tmp_path / "one.py").write_text("one = 1\n", encoding="utf-8")
    binding = bind_source_root(tmp_path)
    snapshot = create_snapshot(binding, ["one.py"])
    other_root = tmp_path / "other"
    other_root.mkdir()
    (other_root / "one.py").write_text("one = 1\n", encoding="utf-8")

    try:
        build_snapshot_inventory_receipt(snapshot, bind_source_root(other_root))
    except ValueError as exc:
        assert str(exc) == "inventory_root_binding_mismatch"
    else:
        raise AssertionError("changed root accepted")


def test_inventory_output_is_bounded(tmp_path, monkeypatch):
    for index in range(20):
        (tmp_path / f"file_{index:02}.py").write_text("x = 1\n", encoding="utf-8")
    binding = bind_source_root(tmp_path)
    snapshot = create_snapshot(binding, [f"file_{index:02}.py" for index in range(20)])
    monkeypatch.setattr(coverage, "MAX_INVENTORY_RECEIPT_BYTES", 300)

    try:
        build_snapshot_inventory_receipt(snapshot, binding)
    except ValueError as exc:
        assert str(exc) == "coverage_inventory_output_limit_exceeded"
    else:
        raise AssertionError("oversized receipt accepted")
