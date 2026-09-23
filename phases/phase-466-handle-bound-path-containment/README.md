# Phase 466: handle-bound path containment for bounded file access

Date: 2026-09-23

## Change

`read_file`, `read_lines`, and `literal_search` record the allowed directory
identity and pin its handle. File contents are read from an opened handle after
containment checks. POSIX traverses from the pinned root descriptor and rejects
symlinks at each component. Windows opens each child name relative to the
already-pinned directory handle with `NtCreateFile`, asks the OS not to follow
the component if it is a reparse point, checks its attributes, and retains
opened directory handles until the file read finishes. Opens omit delete
sharing so traversed names cannot be renamed while held. `literal_search`
enumerates candidate names incrementally, then uses the same secure-open path
for file contents; it no longer sends candidate paths to ripgrep. Unsupported
or unverifiable opens fail closed. File reads use unbuffered binary handles so
the explicit byte limits also bound bytes returned by each read operation.

## Verification

- Added a POSIX interposition test that swaps an in-root leaf for an outside
  symlink immediately before the descriptor-relative open. It must abstain and
  must not return the outside sentinel.
- Added a POSIX root-path replacement test after path resolution. It confirms
  the pinned root descriptor keeps the read attached to the original root.
- Added a cross-platform same-path root replacement test between root
  validation and handle acquisition. The replacement identity must abstain
  before its sentinel can be read.
- Added Windows component-boundary normalization tests.
- Added a POSIX `literal_search` leaf-symlink swap test; the search must abstain
  without returning the outside sentinel.
- Added Windows runtime tests for normal nested reads, rename denial while an
  ancestor handle is held, and a directory junction installed after path
  resolution but before the component-relative open. The junction case
  abstains without returning the outside sentinel.
- Re-ran the complete harness module after the Windows traversal change:
  25 passed, 3 skipped. The three skips are POSIX-only race tests on this
  Windows host.
- Ruff and `git diff --check` passed; diff-check reports only the existing
  LF/CRLF working-copy notices.
- Existing read and line-range behavior remains covered by the focused harness
suite. On this Windows host, ordinary reads passed through the Windows handle
path; both POSIX race tests were skipped.

Commands:

- `py -3 -m pytest -q tests/test_harness.py -k "read_file or read_lines"`:
  6 passed, 2 skipped, 18 deselected.
- `py -3 -m pytest -q tests/test_harness.py -k "windows_handle_path_comparison"`:
  1 passed, 23 deselected.
- `ruff check src/wrench_harness/core.py tests/test_harness.py`: passed.
- `git diff --check`: passed with existing LF/CRLF working-copy notices.

## Limits

This improves `read_file`, `read_lines`, and the content-read phase of
`literal_search`; it does not establish safe directory enumeration under every
concurrent namespace change or every Windows filesystem. `git_read_status` and
`patch_draft` still use other pathname or subprocess paths. The Windows tests
exercise actual NTFS handle-relative opens and one junction replacement
interleaving, but do not cover every reparse type, network redirector, or
filesystem-specific behavior. The POSIX race tests are skipped on Windows.
These limits leave Gate B open. No model inference, training, workflow-trace
inspection, benchmark, provider call, or production deployment was performed.
