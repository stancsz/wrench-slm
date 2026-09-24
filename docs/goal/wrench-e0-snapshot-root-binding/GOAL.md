# E0 configured-root-bound snapshot identity

Status: bounded v2 snapshot increment implemented and independently reviewed
Job: `W2-E0-ROOT-BOUND-20260924`
Started: 2026-09-24 (America/Edmonton)

## Outcome

Bind a source snapshot's content/path digest to the normalized lexical absolute
path that the caller configured as its root. Windows path case is normalized
before hashing. Exact retrieval recomputes that location digest before reading
and returns `unknown_snapshot` when the caller supplies a different root. The
safe read-root resolution is derived from the same single path conversion.
Keep the raw root path out of the snapshot value.

## Acceptance

- Version the manifest as `wrench.source-snapshot.v2` and include a
  `root_location_sha256` in the canonical snapshot payload.
- Normalize the configured root consistently at creation and retrieval;
  preserve Windows case-insensitive path semantics.
- Keep `create_snapshot(root, paths)` and `retrieve_exact(root, snapshot,
  path)` signatures unchanged.
- Fail closed for legacy v1 manifests and malformed/tampered location hashes.
- With identical source paths and bytes under different roots, produce
  different snapshot hashes and reject cross-root exact retrieval.
- Retain explicit exact-source hash checks, bounded caller-selected paths, and
  no source persistence or directory traversal.
- Independently review, document platform tests, and commit this slice.

## Limits

`root_location_sha256` hashes a normalized configured path. It is not a
physical directory identifier, authorization credential, or authorship proof.
A byte-identical directory replacement at the same path still matches, and
the public hashes can be recomputed by a caller that forges a manifest. A
checkout move or rename invalidates an old snapshot even when its contents are
unchanged. The unsalted digest is local pseudonymous metadata and can be
dictionary-tested; do not claim anonymization or export it as a stable user
identity.

The OpenCode V2 integration remains uninstalled and unrun. This slice does not
bind a snapshot to an authenticated client session, veto model dispatch,
establish provider tokenization, or complete E0.

## Verification

Focused snapshot, artifact-store, snapshot/context bridge, structural index,
context preparation, and outcome receipt suites, including the stateful-path
regression, passed on Windows Python 3.11.16 (**115 passed, 7 skipped**) and
Ubuntu 24.04 WSL Python 3.12.3 (**120 passed, 2 skipped**). Exact commands
and skip scopes are in the
[evaluation](../../evals/wrench-e0-snapshot-root-binding/review.md).

Independent review found no blocking correctness issue. Storage job
`W2-E0-ROOT-BOUND-FINAL-20260924` reserved 50,000,000 bytes; actual and
reserved totals remained far below the 50 GB ceiling. Full E0 acceptance,
E1-E4, and production gates remain open.
