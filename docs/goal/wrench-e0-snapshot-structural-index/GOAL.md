# E0 snapshot-backed structural symbol index

Status: accepted implementation slice; does not complete E0
Job: `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-20260924`
Nonce: `SSI-5b614d`
Baseline: `06210190ce6ea3ba4c004f7ca3486293c2485864`

## Outcome

Build a bounded deterministic structural symbol index and candidate query
from only caller-enumerated exact source snapshot files.

## Acceptance

- Require explicit root, valid `SourceSnapshot`, and finite caller paths; use
  `retrieve_exact` for every requested path and never scan directories.
- Fail without returning partial indexes when a read, strict UTF-8 decode,
  parser, file, aggregate, symbol, or output bound fails.
- Use the existing read-only structural parser and lexical fallback. Bind
  source and symbol candidates to snapshot/content hashes, normalized path,
  line range, parser, and language.
- Sort index and candidate results deterministically; keep query results to
  bounded structural candidates only. Validate public index shapes, limits,
  hash formats, canonical paths, and source/snapshot identity before query
  expansion; reject malformed handles without candidates.
- Tests cover Python declarations, lexical fallback, identities, deterministic
  ordering, retrieval failures, invalid UTF-8, query/index limits, malformed
  public index handles, and bounded query serialization.

## Review

Independent review job `W2-E0-SNAPSHOT-STRUCTURAL-INDEX-REVIEW3-20260924`
(nonce `SSIR3-699d33`) accepted the final implementation after two rounds of
boundedness fixes. Query validation rejects malformed or forged index shapes
before expansion, verifies canonical identity, preflights serialized bytes
before encoding, and rejects non-exact built-in query and limit types.

Final focused verification: 21 tests passed. Scoped `git diff --check` passed.
Storage remained `WITHIN_LIMIT`: 590,504,998 bytes actual plus a 20,000,000-byte
active reservation, for 610,504,998 projected bytes; C: free space was
186,293,911,552 bytes.

This component slice is accepted. The integrated E0 authority, utility, and
complete-accounting demonstration remains open.

## Limits

At most 16 files, 64 KiB per file, 512 KiB aggregate source bytes, 4 MiB
  serialized output, 4,096 symbols, 32 query candidates, 256 query characters,
  and a 32-candidate maximum query limit. Nothing is executed, persisted, or
  sent to a model/provider. Query strings and candidate limits require exact
  built-in `str` and `int` types before any length or comparison operation.

## Selected parser-language matrix follow-up (2026-09-24)

Job `W2-NS-W0-LANG-MATRIX-IMPL-20260926`, nonce `W0-IMPL-AE92`, added a
seven-row authored regression matrix for the selected-snapshot coverage
receipt. It checks Python AST valid and syntax-error rows plus TypeScript,
JavaScript, Go, Rust, and Python-stub suffixes routed through the lexical
fallback. The latter are explicitly marked unsupported. The worker report and
independent evaluation document the exact labels, counts, result, and limits:
[matrix report](../../reports/wrench-e0-snapshot-structural-index/selected-language-matrix-20260926.md),
[matrix evaluation](../../evals/wrench-e0-snapshot-structural-index/selected-language-matrix-20260926.md).

Focused Python 3.11.16 verification passed: 7 tests. This is selected-path
dispatch evidence only; it does not establish language support, repository
coverage, utility, or W0/E0 acceptance. The existing lexical fallback's
coverage limits remain open.
