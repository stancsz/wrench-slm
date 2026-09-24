# Artifact request pin-scope duration

## Change

`ArtifactRequest` now captures a monotonic timestamp when its one-shot scope
successfully opens and at its first close. The nullable
`pin_scope_duration_ns` property returns the elapsed nanoseconds only after
closure. If the close-time clock read fails, pin cleanup still completes and
the diagnostic remains unavailable. Repeated exits leave the original duration
unchanged.

This measures only the lifetime of process-local artifact pins. It is not task
latency, OpenCode/client latency, downstream request completion, or authenticated
telemetry, and it is not joined into the E0 partial trace or outcome receipt.

## Verification

The four new focused test functions use patched synthetic monotonic clocks and
cover a null value before/during closure, ordinary close, exception close with
a real pin and subsequent eviction, repeat-exit idempotence, and independent
scopes. The available Python environments do not include pytest. The four test
bodies were executed directly under Python 3.11.16 with a small pytest-fixture
shim; all four passed. This does not substitute for running the pytest suite.

Independent review is recorded in the paired evaluation. No client, provider,
model, network, or real task data was used.
