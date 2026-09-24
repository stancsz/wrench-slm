# E0 preparation pin-scope accounting join

Job: `W2-NS-E0-PIN-DURATION-JOIN-20260925`
Nonce: `PINJOIN-6D31`
Base revision: `5310bb502aec24fd6adf22b0add8d7a9feda1812`

## Change

`prepare_e0_context` now records the actual closed `ArtifactRequest`'s
`pin_scope_duration_ns` in `PreparationMetrics`. Capture occurs after the
scope exits at the preparation producer boundary, so it records the duration
provided by the store instead of estimating it from the outer facade timer.
Preparation scopes that never enter and caller-owned scopes that remain open
when preparation returns retain `null`.

The canonical preparation accounting payload adds
`artifact_pin_scope_duration_ns` and advances its schema to
`wrench.e0.preparation-accounting.v2`. The accounting digest includes this
run-specific value and remains joined to the existing content preparation
aggregate. The content aggregate itself does not change. Preparation elapsed
wall time remains outside the canonical accounting digest.

This is same-process preparation pin-scope timing only. It does not measure
task, downstream request, or OpenCode/client latency, and it does not establish
that a client used the scope. Other external lifecycle activity remains
unmeasured.

## Verification

The named Windows Python 3.11 focused tests cover the actual closed-scope value,
nonnegative metric, inclusion in canonical accounting, digest invalidation
when the duration changes, and `null` for both caller-owned still-open scopes
and validation that returns before entering a scope. Test and storage
admission/release evidence is in the paired evaluation. This v2 record
supersedes the earlier v1 accounting companion for the current receipt schema.

No client, provider, model, network, real task data, or training was used.
