# Selected snapshot subset coverage receipt

`build_snapshot_coverage_receipt` reports deterministic parser coverage for a
finite caller-selected path list in an admitted `SourceSnapshot`. Every source
is fetched with `retrieve_exact`; returned bytes are checked against the
snapshot and then processed under the structural indexer's 16-file, 64 KiB per
file, 512 KiB aggregate, and 4,096-symbol limits. It does not walk the
repository or infer which paths the caller omitted.

The receipt binds its payload hash to the validated snapshot SHA-256 and sets
`selected_subset_only=true`. It reports selected/requested and indexed counts,
per-file source path and hash, parser and language identifiers, observed
symbol counts, Python syntax errors, unsupported lexical fallback, limits,
missing files, stale files, and other errors. Counts for exact-read attempts,
successes, returned bytes, and finite retrieval statuses describe this call.
An overlong path selection is examined only through `MAX_FILES + 1` values,
marked incomplete, and causes no reads. Aggregate byte exhaustion marks the
remaining selected paths limited without reading them. If path iteration fails,
the receipt preserves the paths already observed as per-file errors, records
their observed count, and marks that request count incomplete.

This is a bounded structural coverage receipt for the explicit subset only.
`python_ast` results are syntax-tree-derived symbol candidates, not semantic
program understanding. Other extensions use the existing lexical fallback
and are marked unsupported even when it recognizes declaration-shaped lines.
The receipt is caller-supplied in-memory evidence; it is not persisted or
authenticated, and it does not establish repository completeness, runtime
integration, task utility, or E0 acceptance.

Verification and independent review: see the [coverage receipt evaluation](../../evals/wrench-e0-context-pipeline/selected-subset-coverage.md).
