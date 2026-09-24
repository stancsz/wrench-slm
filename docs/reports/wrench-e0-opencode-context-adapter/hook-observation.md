# OpenCode context-hook callback observation primitive

Job: `W2-NS-E0-OPENCODE-HOOK-OBS-20260924`
Nonce: `HOBS-947A`
Base commit: `c0eb200c58eb358a8afbf76c7fe44dac7afb1d45`
OpenCode source pin: `v2.0.15`, hook schema version `2.0.15`

## Change

Added `OpenCodeContextHookObserver` beside the existing projection and
transition APIs. It wraps a synthetic or caller-supplied callback at the local
awaited callback boundary, measures monotonic elapsed nanoseconds around the
callback and any returned awaitable, and re-raises callback errors unchanged.
Its independent observation summary carries a schema and the pinned OpenCode
hook version, aggregate invocation/completion/return/error counts, total elapsed
time over calls with valid timing samples, a bounded timing-error count, and at
most 128 ordered per-call rows containing only invocation index, elapsed
nanoseconds (or `None` when unavailable), and `returned` or `error`. Aggregate
counts and both aggregate and per-call elapsed nanoseconds are capped at fixed
integer bounds. `saturated` is set when a value is clamped or aggregate
addition exceeds its bound. Failed or non-integer clock samples produce an
unavailable duration and increment the timing-error count. Clock exceptions are
not retained and cannot prevent callback invocation or replace its return or
error. No callback argument, return value, exception object, exception text,
stack, or message content is retained. Accessing the observation before the
wrapper is invoked returns `None`.

This is an unauthenticated structural observation of this wrapper instance. A
missing observation means unobserved; it does not establish that a callback was
not invoked unless a harness observes the entire opportunity. `returned` means
only that the wrapped callback returned. It does not prove that OpenCode applied
the mutation.

## Verification

Focused command using an existing Python 3.11.16 / pytest 8.3.5 environment,
without package installation:

```powershell
C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_opencode_hook_projection.py -q --basetemp C:\wrench-slm-data\tmp\W2-NS-E0-OPENCODE-HOOK-OBS-20260924\pytest-clock-failure-fix
```

Result: **62 passed in 1.43s**. Synthetic fixtures use a fake monotonic clock
for a single return and repeated returns, a synchronous throw, and an async
rejection. They also verify that an unused observer has no observation, errors
are re-raised without appearing in the summary, the public observer API is
exported, per-call rows are ordered and capped, per-call clamping, overflow from
two individually bounded durations, failed start/end clock reads, invalid
clock samples, and preservation of callback behavior when timing fails.
`git diff --check` passed.

Storage admission and host check before the test: `WITHIN_LIMIT`, 2,287,088,073
bytes actual plus 10,103,000 bytes active reservations, with
`C:\Users\stanc\AppData\Local\npm-cache` included; 14,093,713,408 bytes free
system RAM and 15,212 MiB free VRAM. Test scratch is under the authorized job
directory and remained within its 5 MB limit.

## Limits

The observation is local and unauthenticated. No OpenCode plugin or client was
registered or run. No dispatch veto, provider cost, downstream token count,
tool/retry/resource accounting, or actual runtime measurement is established.
This is one source-only observer primitive, not E0 acceptance or task-utility
evidence.
