# OpenCode context-hook observation evaluation

Job: `W2-NS-E0-OPENCODE-HOOK-OBS-20260924`, nonce `HOBS-947A`
Base commit: `c0eb200c58eb358a8afbf76c7fe44dac7afb1d45`

## Result

The focused projection and hook-transition test module passed **62 tests** in
1.43 seconds with the existing Python 3.11.16 / pytest 8.3.5 environment. The
observer fixtures use synthetic callbacks and a fake monotonic clock. They
cover never invoked, returned once and repeatedly, synchronous throw, async
rejection, content-free error recording, and the 128-row cap. Callback errors
are re-raised unchanged. A larger-than-cap fake-clock delta confirms that both
the per-call and aggregate elapsed values clamp and set saturation; two
individually bounded calls also exercise aggregate overflow. Failed or invalid
clock samples produce unavailable per-call timing and increment a bounded
timing-error count. A failed start sample still invokes the callback; a failed
end sample preserves both callback returns and the original callback error.
Clock exception text is not retained. The observer schema, version, and public
exports are asserted. `git diff --check` passed.

The standalone observation has a schema and OpenCode hook version `2.0.15`.
Its fixed fields and capped ordered rows contain aggregate counts, available
durations, timing-error count, invocation indexes, and result categories only.
It is an unauthenticated local
structural observation. Absence means unobserved, not `not_invoked`, unless a
harness covers the entire invocation opportunity. A normal callback return
does not establish that OpenCode applied a context mutation.

## Scope boundary

No OpenCode plugin/client was registered or run. The primitive does not
establish a dispatch veto, provider cost, downstream tokens, tool/retry/resource
accounting, or any actual runtime measurement. It is not joined to the existing
caller-supplied lifecycle trace and establishes no production or utility claim.
