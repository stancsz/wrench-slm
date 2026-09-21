# Phase 323: direct native 2M prefill performance boundary

This was an intentionally bounded reducer-bypassed probe against the current
portable candidate. It sent the raw payload directly to FreeToken's native
`/v1/chat/completions` endpoint after the model had loaded and configured its
4M KV capacity.

## Result

Status: `ABORTED_DIRECT_NATIVE_PREFILL_TOO_SLOW_FOR_PRODUCTION`

- Target: `2,000,000` raw tokens
- Candidate: `D:\models\_wrench-release-candidate-04090c1`
- The native backend accepted the request and began real prefill.
- The log recorded `13` 32,768-token prefill batches, approximately `425,984`
  tokens after the startup smoke, in about three minutes.
- The run was stopped before completion because this path is far too slow for
  Wrench's fast mechanical-worker product target. It left no receipt because
  the verifier was interrupted before the final response, but its stdout and
  stderr logs are retained and the exact process tree was cleaned up.
- GPU usage returned to approximately `0.8 GiB` after cleanup.

This does not invalidate native 4M capacity. It establishes the production
architecture boundary: accept 2M or 4M raw input at the model-local endpoint,
then use deterministic MapReduce, lookup, and the optional first-layer gate to
reduce expensive model work to the effective 32K to 64K context. Direct dense
native prefill remains a capacity and research probe, not the default worker
path.

Evidence: `phase-323-current-head-native-direct-2m.stdout.log` and
`phase-323-current-head-native-direct-2m.stderr.log`.
