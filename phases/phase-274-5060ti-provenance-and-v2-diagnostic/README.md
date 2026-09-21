# Phase 274: 5060TI provenance fix and v2 diagnostic

Date: 2026-09-21

## Purpose

Close the cross-host evaluation provenance gap before using the independent
5060TI worker for the full 220-case verification. Windows archive/checkouts can
change JSONL line endings without changing any case content. A raw byte hash
alone can therefore reject a valid matching input or, worse, make two inputs
look comparable when their provenance was not checked.

## Worker receipt before the fix

The connected worker `DESKTOP-KET1SKP` reported an NVIDIA GeForce RTX 5060 Ti.
It created a temporary `origin/main` export and did not overwrite its dirty
checkout. No matching teacher receipt was present, so the worker correctly
did not claim parity.

The package-only v2 diagnostic ran all 220 rows and reported:

- 200 outcome matches
- 100 exact proposal matches
- 120 eligible rows, with 100 exact eligible accepts
- 0 prohibited accepts
- 0 transport/runtime abstentions
- 220 mechanical fast-path requests and 0 model calls
- 2.077 ms median and 107.235 ms p95 latency
- about 49.2% free system RAM and 15,037 MiB free of 16,311 MiB VRAM

The receipt status was `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY` with
`quality_claim=false`. It was not a teacher comparison.

## Provenance defect and repair

The worker's archived case bytes had raw SHA-256
`0a3c3ddaae05f72f27fb556649c3e43174a32382ff8fbc949567bffe57cb8d69`, while
the suite manifest and LF checkout had
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.
The difference was the CRLF versus LF line ending representation.

The repair adds `tools/evaluation_provenance.py`, which computes a canonical
JSONL hash after normalizing line endings and separately records the raw byte
hash. The teacher capture, diagnostic arms, package evaluation, deterministic
route scoring, and profile scoring now share the same canonical case hash.
`.gitattributes` pins JSON and JSONL files to LF for future checkouts.

## Verification

The new regression test proves that LF and CRLF copies have the same canonical
hash and different raw-byte hashes. Targeted verification passed:

```text
24 passed in 0.42s
```

## Post-fix 5060TI verification

After commit `aaf0c79` reached `origin/main`, the worker repeated the audit in
a fresh temporary export. It verified `origin/main=aaf0c79`, found both the
canonical hash and the LF-normalized exported case hash equal to
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`, and
confirmed that `evaluation_provenance.py` and `.gitattributes` were present.
The original dirty checkout was not pulled, reset, or modified.

The post-fix package-only diagnostic reported:

- 220 requests and 200 outcome matches
- 100 exact proposals and 100 exact accepts across 120 eligible rows
- 0 prohibited accepts, 0 transport/runtime abstentions, and 0 model calls
- 2.516 ms median and 108.383 ms p95 latency
- RTX 5060 Ti with RAM and VRAM reserves above 10%
- no matching MiniMax teacher capture, so no parity claim

The status remained `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`. This closes the
cross-host provenance defect, but it does not prove MiniMax parity, production
readiness, dense-native 4M decoder quality, or the 90% weighted
mechanical-workload gate. The worker audit and evaluation receipts remain
outside this checkout.
