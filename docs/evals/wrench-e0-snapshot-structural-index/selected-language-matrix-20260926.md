# Selected snapshot parser-language matrix evaluation

**Result: PASS for the authored selected-path regression matrix.** This is
evidence about current parser dispatch and the lexical fallback on seven small
fixtures. It is not language support, repository-wide coverage, semantic
analysis, utility evidence, or E0 acceptance.

## Reviewed evidence

- Implementation: `src/wrench_harness/toolbelt.py` and
  `src/wrench_harness/snapshot_coverage.py`.
- Regression: `tests/test_snapshot_coverage_language_matrix.py`.
- Worker report: [selected parser-language matrix](../../reports/wrench-e0-snapshot-structural-index/selected-language-matrix-20260926.md).
- Independent review job `W2-NS-W0-LANG-MATRIX-REVIEW-20260926`, nonce
  `W0-REV-7710`, returned PASS for claim accuracy and bounded deterministic
  scope. The reviewer inspected source, test, report, selected-subset evidence,
  and North Star constraints; it made no edits and ran no tests.

The cases select one exact snapshotted file at a time. The `.py` valid row is
`python_ast` / `py` / `indexed` with two symbols; malformed `.py` is
`python_ast` / `py` / `syntax_error` with zero symbols. `.ts`, `.js`, `.go`,
`.rs`, and `.pyi` use `lexical_fallback` with suffix-based language labels and
are `unsupported`, with fixture counts 2, 2, 1, 0, and 1 respectively. The
Go and Rust rows also show syntax forms the heuristic does not recognize.

## Verification

Supervisor run used Python 3.11.16 and the pre-existing cached pytest
dependencies. No package was installed or downloaded. With bytecode and pytest
plugin autoload disabled, and a fresh `--basetemp` under the admitted Wrench
scratch root, the focused command was:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider --basetemp 'C:\wrench-slm-data\tmp\W2-NS-W0-MULTILANGUAGE-COVERAGE-20260926\pytest-supervisor' tests/test_snapshot_coverage_language_matrix.py
```

Result: **7 passed in 0.59s**. An initial invocation without the cached
dependency path could not import pytest; a subsequent invocation with the
cache but before creating its requested basetemp failed during fixture setup.
After setting the approved dependency path and creating a unique basetemp,
the focused run passed.

At final admission check the storage checker reported `WITHIN_LIMIT`: actual
2,280,608,383 bytes and 15,103,000 bytes in active reservations, projected
2,295,711,383 bytes, with 47,704,288,616 bytes of headroom. The required
10,000,000-byte reservation remained active. Free memory was 13,562,675,200 of
34,290,302,976 RAM bytes and 15,218 of 16,311 MiB VRAM.

## Limits and next action

The parser dispatches only exact `.py` suffixes to Python AST. Other suffixes
use one line-oriented regex match per line for `function`, `class`, `def`,
`interface`, or `type`; their `UNSUPPORTED` status correctly describes the
lexical fallback, even when it sees declaration-shaped text. This matrix does
not assess comments, strings, multiline declarations, alternate syntax,
semantic references, or realistic repository distributions. W0 still needs
broader selected-subset evidence and a parser strategy decision before any
repository-coverage claim.
