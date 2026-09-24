# Selected snapshot parser language matrix

Job: `W2-NS-W0-LANG-MATRIX-IMPL-20260926`
Nonce: `W0-IMPL-AE92`
Baseline: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`

## Scope

This regression matrix exercises only the explicitly selected-path
`build_snapshot_coverage_receipt` flow, which retrieves each selected source
through its bound snapshot before invoking `parse_source_ast`. It does not
claim repository-wide parser coverage or end-to-end W0 completeness.

The implementation dispatches `.py` files to Python AST. Every other suffix
uses a line-oriented regex for the tokens `function`, `class`, `def`,
`interface`, and `type`. Non-Python files are reported as `UNSUPPORTED` even
when that fallback observes declaration-like tokens. A Python parse failure is
reported as `SYNTAX_ERROR`.

| Selected path | Parser | Language label | Coverage status | Observed symbols | Fixture boundary |
| --- | --- | --- | --- | ---: | --- |
| `worker.py` | `python_ast` | `py` | `indexed` | 2 | Python class and method |
| `broken.py` | `python_ast` | `py` | `syntax_error` | 0 | Malformed Python declaration |
| `lookup.ts` | `lexical_fallback` | `ts` | `unsupported` | 2 | `interface` and `type` tokens |
| `widget.js` | `lexical_fallback` | `js` | `unsupported` | 2 | `class` and `function` tokens |
| `worker.go` | `lexical_fallback` | `go` | `unsupported` | 1 | `type` is observed; Go `func` is not |
| `worker.rs` | `lexical_fallback` | `rs` | `unsupported` | 0 | Rust `fn` and `struct` are not observed |
| `worker.pyi` | `lexical_fallback` | `pyi` | `unsupported` | 1 | `def` token is observed despite Python stub suffix |

Every matrix case selects exactly one snapshotted path, performs one exact
read, and reports one coverage row. The test asserts parser identity, language
label, status, count, selected-subset marker and syntax-error shape.

## Limits

These are authored suffix/heuristic regression fixtures for current dispatch
and fallback behavior. They do not validate full language grammars,
name resolution, comments/strings handling, repository-scale parser coverage,
semantic references, or utility. The fallback checks each line independently
with one regex match; the Go and Rust rows demonstrate missed declaration
syntax and do not establish those languages as supported parsers.

## Verification

Python 3.11.16 focused command, with plugin autoload disabled, the existing
cached pytest dependencies and a Wrench-root temporary directory:

```powershell
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider tests/test_snapshot_coverage_language_matrix.py --basetemp C:\wrench-slm-data\tmp\W2-NS-W0-LANG-MATRIX-IMPL-20260926\pytest
```

Result: `7 passed in 0.80s`. The first attempt omitted the cached pytest
dependency path and could not import pytest; the corrected run used the
pre-existing cache and installed nothing.

Both deliverables remained untracked. Therefore the regular `git diff --check`
did not include them. I checked each new file with
`git diff --no-index --check -- NUL <path>`; both reported no whitespace
diagnostics and returned 1 because each comparison contains a new-file diff.
Git emitted only its expected LF-to-CRLF conversion warning for each file.

Final storage status at report update was `WITHIN_LIMIT`, approximately 2.281
GB actual plus 15,103,000 bytes in active reservations, with no
checker errors. The parent-owned 10,000,000-byte job reservation remains
active. During verification, system RAM had 13,207,179,264 bytes free of
34,290,302,976, and GPU memory had 15,177 MiB free of 16,311 MiB.

No source code, dependencies, shared goal/evaluation documents or commits were
changed by this worker.
