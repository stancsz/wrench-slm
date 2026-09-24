# E0 snapshot to artifact store to context roundtrip

Status: bounded implementation slice accepted; E0 remains incomplete
Job: `W2-E0-SNAPSHOT-ARTIFACT-ROUNDTRIP-20260924`  
Nonce: `SAR-8d02ce`  
Baseline: `103f6bd440c819e1df3f23be9b901705fa013422`

## Outcome

Connect caller-selected source snapshots to the existing content-addressed
artifact store and bounded in-memory context ledger through an exact verified
roundtrip.

## Acceptance

- Require explicit source root, snapshot, path, existing store, ledger, and
  source order. Retrieve current source bytes before any artifact write.
- Persist only bytes returned by successful `retrieve_exact`, bound to its
  snapshot/path/content hashes.
- Pin and read the stored handle in a request scope; verify handle identity,
  exact bytes, and SHA-256 against retrieved bytes before decoding.
- Admit only strict UTF-8 non-empty text. Return typed outcomes for retrieval,
  store, roundtrip, non-text, and context failures; receipts include no bytes.
- Failed retrieval never writes an artifact. Failed ledger admission leaves
  the ledger unchanged; a successfully verified object may remain stored.
- Exercise exact success, deterministic identity, retrieval failures, a
  bounded artifact failure, and context rejection with fixture-only tests.

## Limits

The bridge does not scan sources, create a store, persist context, pin outside
the immediate request scope, select context for a model, or call a model or
provider. ArtifactStore's existing single-process and caller-owned-root
constraints still apply.

## Review

Independent review accepted the implementation and identified two missing
typed-error coverage cases. Focused tests were added for bounded store-write
failure and roundtrip identity mismatch; the expanded suite passed. E0 remains
incomplete and this does not authorize E1 model work.
