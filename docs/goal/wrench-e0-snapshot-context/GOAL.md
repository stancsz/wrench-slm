# E0 snapshot to context admission

Status: bounded implementation slice accepted; E0 remains incomplete
Job: `W2-E0-SNAPSHOT-CONTEXT-20260924`
Nonce: `SCX-6f3a9`
Baseline: `ee9bf186ef8c72f33ab614a93d74dae5bcd248a1`

## Outcome

Bridge verified exact source bytes from the caller's `SourceSnapshot` into the
existing in-memory bounded `ContextLedger`. This slice admits strict UTF-8,
non-empty text only and reports explicit misses without changing the ledger.

## Acceptance

- Require the caller to provide root, snapshot, relative path, ledger, and
  source order. Use `retrieve_exact` as the authority for byte identity.
- Report unknown snapshot/source, missing, stale, unsafe, non-text, and ledger
  rejection outcomes explicitly.
- Derive a deterministic segment ID from snapshot hash, normalized path, and
  verified content hash; retain those identities in bounded metadata.
- Return a receipt without source bytes. Never scan, persist, pin, or call a
  model/provider from this bridge.
- On any failed retrieval, decoding, or ledger admission, leave the ledger
  unchanged.

## Limits

The bridge uses the ledger's existing token-count behavior and admission caps.
It does not select context for a model call, guarantee that a segment will fit
a later active prompt budget, or add persistence or concurrency controls.

## Review

Independent review accepted this slice with no blocking findings. This is
component acceptance only; it does not establish the integrated E0 baseline
or authorize E1 model work.
