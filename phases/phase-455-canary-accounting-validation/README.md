# Phase 455: fail-closed canary accounting validation

Date: 2026-09-24

## Change

The paired-client canary now rejects incomplete or inconsistent gateway token
usage, and treats negative or non-finite gateway costs as unknown. It requires
unique nonblank request IDs and valid workflow-attempt identifiers before
counting hybrid trace tokens. Malformed JSONL rows and non-object rows no longer
crash aggregation. They leave token totals and raw-input estimates unknown,
while preserving separately verified client outcome results.

`accounting_complete` remains false. This phase validates evidence inputs only;
it does not add the missing three-arm replay, provider cost for local inference,
independent task outcomes, or verifier evidence.

## Verification

- Targeted accounting regressions: 11 passed.
- The full `tests/test_paired_client_canary.py` module: 57 passed. Three
  preflight tests now create their own synthetic, test-only workload manifests
  instead of depending on the absent Phase 395 workload file.
- Ruff on the changed runner and test module: passed.
- `git diff --check`: passed; Git emitted only configured LF-to-CRLF notices.

No paired canary, model inference, external provider call, or Phase 448 trace
content was accessed.

## Limits

These tests establish fail-closed accounting mechanics on local fixtures, not
the authenticity of provider receipts or production utility. Gate D remains
open: the current runner is one case and two arms, the Phase 448 candidate is
not replay-ready, and complete verifier, outcome, cost, retry, correction, and
weighted-coverage evidence is missing.
