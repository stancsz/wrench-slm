# Phase 170: embedded TTC enforcement

The deterministic toolbelt's multi-pass verifier is now on the real package
execution path. It is no longer only an offline test helper.

## Runtime behavior

- Accepted mechanical proposals receive a
  `wrench.test-time-compute-receipt.v1`.
- Native-upstream proposals receive the same receipt after the package
  verifier parses the backend response.
- The fast, guarded, and deep profiles remain bounded and action-sensitive.
- Any failed TTC gate becomes a fail-closed
  `multi_pass_verification_failed` abstention.
- `wrench_runtime/ttc.py` is shipped inside the portable model package.

## Verification

- Full regression: `154 passed, 14 warnings`.
- v71 structural package validation: `PASS_STRUCTURAL_PACKAGE`.
- Local v71 4M mechanical route: `16.037 ms`, zero model calls.
- Local v71 embedded 4M prefill stress: `380.976 ms`, zero model calls.
- A fresh package-local accepted read returned a passed fast TTC receipt with
  schema, authority, evidence, consistency, and blind-critic checks all true.
- Correct package-local 220-case replay: `220/220` outcome matches,
  `120/120` exact eligible proposals, zero prohibited accepts, zero transport
  or runtime abstentions, zero model calls, `0.538 ms` median, and `40.040 ms`
  p95. The replay receipt recorded the TTC receipt on accepted cases.
- Public Hub revision: `ebe2f75c478cc7138fc8c08cb8577ced30d867b5`.
- Fresh Hub runtime hashes matched local v71 for `worker.py`, `server.py`,
  `ttc.py`, `toolbelt.py`, `serve_freetoken.ps1`, `README.md`, and
  `wrench-package.json`.

## Boundary

This strengthens the safety and observability path. It does not claim dense
native 2M/4M attention, MiniMax matched-workflow parity, or final production
enablement. The package remains an experimental public artifact until the
matched real-workflow gates pass.
