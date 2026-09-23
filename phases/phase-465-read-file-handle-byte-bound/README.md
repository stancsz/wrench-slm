# Phase 465: read_file handle byte bound

Date: 2026-09-23

## Change

`read_file` now opens the selected file once and reads at most the caller's
`max_bytes` plus one byte. It abstains with `file_size_limit` when that bounded
read proves the file is too large. UTF-8 validation and the previous universal
newline normalization are preserved. The returned byte count is the number of
bytes read from the file, before newline normalization.

This removes the size-check/read race where a file could grow after `stat()`
and cause `read_text()` to load more than the configured cap.

## Regression coverage

- An oversized file with `max_bytes=32` is rejected after exactly 33 bytes are
  returned by the file handle.
- Existing accepted `read_file`, bounded `read_lines`, oversized-line, and
  invalid-UTF-8 cases still pass.

Commands:

- `py -3 -m pytest -q tests/test_harness.py -k "read_file or read_lines"`:
  4 passed, 18 deselected.
- `ruff check src/wrench_harness/core.py tests/test_harness.py`: passed.
- `git diff --check`: passed with existing LF/CRLF working-copy notices.

## Limits

This closes the unbounded-read-after-size-check gap. It does not close the
separate path-containment time-of-check/time-of-use risk: `_bounded_path`
resolves and checks containment before the later open. Handle-based containment
remains a separate review item. No model inference, benchmark, provider call,
capture access, or production deployment was performed.
