# OpenCode hook observation lifecycle join

Job: `W2-NS-E0-HOOK-TRACE-JOIN-20260925`  
Nonce: `HTRACE-31C9`  
Base HEAD: `6b651a159ad737a803dd506bb01b23a30a97cc4e`

## Change

Added optional per-invocation session binding to
`OpenCodeContextHookObserver`. A caller-provided `session_id_getter` may read
the invocation arguments and return the session ID. The observer computes
SHA-256 over that ID and stores only the digest on the row. Since this changes
the public observation row shape, the observation schema is now v2. Getter
failures, including `BaseException` subclasses, and invalid IDs produce an
unscoped row; getter errors are swallowed and do not prevent callback
invocation. The caller-provided getter must be side-effect-free: it receives
the original arguments and must not mutate or retain them or other callback
content. The observer does not retain callback arguments, raw session IDs,
result values, exceptions, or message content.

`build_partial_lifecycle_trace` accepts an optional observation. When supplied,
it adds a bounded, content-free summary only after validating the exact schema
and OpenCode source version, complete ordered invocation rows, row and aggregate
counts, elapsed-time sum, uncapped and unsaturated state, and the SHA-256
session binding on every row. The producer can record at most one timing error
per invocation; a completed row with `elapsed_ns=None` accounts for exactly
one, so the join verifies that equality. It rejects absent/unscoped row
bindings, mixed session bindings, and malformed or incomplete snapshots.
Calls that omit this argument retain the prior payload shape.

The envelope keeps schema v4 when `context_hook_observation` is omitted, which
preserves the legacy payload shape and version. When the validated observation
summary is included, both the envelope and payload declare schema v5 so strict
consumers can distinguish the expanded shape.

The joined fields are explicitly caller-supplied and unauthenticated. They do
not establish runtime hook provenance or atomic capture, actual OpenCode
execution, mutation application, a veto, the final provider request, or client
runtime identity. Runtime hook event provenance and atomic capture remain an
unavailable dimension.

## Verification

Focused command using the existing Python 3.11.16 / pytest environment, with
pytest scratch under the reserved job directory:

```powershell
C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_opencode_hook_projection.py tests/test_e0_lifecycle_accounting.py -q --basetemp C:\wrench-slm-data\tmp\W2-NS-E0-HOOK-TRACE-JOIN-20260925\pytest-final-review
```

Result: **89 passed in 5.98s**. Coverage includes scoped digest collection,
ordinary and `BaseException` getter failures that do not prevent callback
invocation, successful trace join, the side-effect-free getter contract,
omitted-observation v4 and included-observation v5 envelopes, the v2
observation schema, and rejection of unscoped, mixed-session, incomplete,
capped, saturated, timing-inconsistent, and version/schema-mismatched
observations, including hostile equality values. `git diff --check` passed.

The first test invocation could not create pytest's `--basetemp` because the
authorized job parent directory did not yet exist. After creating that parent
under `C:\wrench-slm-data\tmp`, the focused rerun above passed. No package or
dependency was installed.

In the initial execution, the pre-release storage check was `WITHIN_LIMIT`:
1,710,447,263 bytes actual plus 5,103,000 bytes in active reservations,
including this job's 5,000,000 bytes. After output accounting, this job's
reservation was released; the post-release check remained `WITHIN_LIMIT` and
listed 103,000 bytes in other active reservations. For the follow-up, the same
5,000,000-byte job reservation was recreated for the two focused test modules.
Its latest pre-release check was `WITHIN_LIMIT`: 1,710,479,381 bytes actual
plus 5,103,000 bytes active reservations, leaving 48,284,417,618 bytes
headroom. This follow-up reservation was released after final accounting. For
the schema v2 / envelope v5 review follow-up, the same 5,000,000-byte
reservation was recreated and remains active through independent review. The
latest pre-review check was `WITHIN_LIMIT`: 1,710,538,652 bytes actual plus
5,103,000 bytes in active reservations, leaving 48,284,358,347 bytes headroom.
The supervisor will release this reservation after review and final
accounting. System free RAM before this test was 13,798,016 KiB, the RTX 5060
Ti reported 15,224 MiB free VRAM, and C: had 182,609,321,984 bytes free. No
download, provider request, prompt, inference, client install, or deployment
occurred.
