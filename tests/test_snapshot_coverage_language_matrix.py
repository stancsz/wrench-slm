from __future__ import annotations

import pytest

from wrench_harness.snapshot import create_snapshot
from wrench_harness.snapshot_coverage import (
    CoverageFileStatus,
    build_snapshot_coverage_receipt,
)


@pytest.mark.parametrize(
    ("path", "source", "expected_parser", "expected_language", "expected_status", "expected_symbols"),
    [
        (
            "worker.py",
            "class Worker:\n    def run(self):\n        return 1\n",
            "python_ast",
            "py",
            CoverageFileStatus.INDEXED,
            2,
        ),
        (
            "broken.py",
            "def broken(:\n    pass\n",
            "python_ast",
            "py",
            CoverageFileStatus.SYNTAX_ERROR,
            0,
        ),
        (
            "lookup.ts",
            "interface Lookup { value: string }\ntype Key = string;\n",
            "lexical_fallback",
            "ts",
            CoverageFileStatus.UNSUPPORTED,
            2,
        ),
        (
            "widget.js",
            "class Widget {}\nfunction render() {}\n",
            "lexical_fallback",
            "js",
            CoverageFileStatus.UNSUPPORTED,
            2,
        ),
        (
            "worker.go",
            "type Worker struct {}\nfunc Run() {}\n",
            "lexical_fallback",
            "go",
            CoverageFileStatus.UNSUPPORTED,
            1,
        ),
        (
            "worker.rs",
            "pub fn run() {}\npub struct Item;\n",
            "lexical_fallback",
            "rs",
            CoverageFileStatus.UNSUPPORTED,
            0,
        ),
        (
            "worker.pyi",
            "def run(value: int) -> None: ...\n",
            "lexical_fallback",
            "pyi",
            CoverageFileStatus.UNSUPPORTED,
            1,
        ),
    ],
)
def test_selected_snapshot_coverage_reports_exact_parser_matrix(
    tmp_path,
    path,
    source,
    expected_parser,
    expected_language,
    expected_status,
    expected_symbols,
):
    source_path = tmp_path / path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")
    snapshot = create_snapshot(tmp_path, [path])

    receipt = build_snapshot_coverage_receipt(tmp_path, snapshot, [path])

    assert receipt.selected_subset_only is True
    assert receipt.requested_count_complete is True
    assert receipt.requested_count == 1
    assert receipt.exact_read_attempts == receipt.exact_read_successes == 1
    assert receipt.indexed_count == int(expected_status is CoverageFileStatus.INDEXED)
    assert receipt.unsupported_count == int(expected_status is CoverageFileStatus.UNSUPPORTED)
    assert len(receipt.files) == 1
    row = receipt.files[0]
    assert row.requested_path == row.source_path == path
    assert row.parser == expected_parser
    assert row.language == expected_language
    assert row.status is expected_status
    assert row.symbol_count == expected_symbols
    if expected_status is CoverageFileStatus.SYNTAX_ERROR:
        assert row.syntax_error.startswith("SyntaxError:")
    else:
        assert row.syntax_error is None
