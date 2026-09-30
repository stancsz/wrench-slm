# Iteration 042: versioned OpenCode context adapter (2026-09-27)

## Change

Implemented an explicit OpenCode v2.0.12 identity path through the existing
offline E0 context preparation and transition accounting. The historical
v2.0.15 default remains unchanged so old receipts retain their original
identity.

The adapter version now travels with `OpenCodePreparationJoin`. The selected
version controls prompt-message validation, context projection, prepared
message insertion, and transition verification. Lifecycle accounting rejects
a projection whose version differs from its preparation join, rejects an
observer whose version differs from the projection, and revalidates each
projection under its declared version. Cross-version transition pairs fail
closed. Only v2.0.12 and the historical v2.0.15 are accepted.

Focused regression coverage was added for both preparation formats, explicit
v2.0.12 projection and observation identities, unknown-version rejection,
cross-version transition and observation rejection, version-bound
materialization, and matching lifecycle receipts. The tests have **not** been
run.

## Current route and machine gate

Read-only GETs to `http://127.0.0.1:4000/health/liveliness` and
`/api/active-model` returned a live response and `openrouter` / `force` / policy
version 4. No provider POST or generation occurred; a numeric campaign-wide
USD cap and validated billing receipt path are still required before paid
calls.

RAM was 3,310.1/32,701.8 MiB free (10.12%); VRAM was 15,227/16,311 MiB free.
The 10% RAM reserve has only about 40 MiB of headroom, and fit-03 separately
requires 25% free RAM at start. Therefore no test suite, OpenCode runtime
preflight, inference, training, benchmark, or delegation ran. The storage check
before edits was `WITHIN_LIMIT` at 10,990,286,808 actual bytes with 8,103,000
bytes in prior reservations; this job reserved 500,000 bytes for source, tests,
and this report.

A later pre-test sample fell to 3,304.3/32,701.8 MiB free (10.10%), only about
34 MiB above the runtime floor. The focused test process was not launched.

## Limits and next action

This is still a provider-free offline adapter. It does not register a live
OpenCode plugin, prove the transport veto, measure provider-token reduction,
or establish model effectiveness. The next concrete step is to connect the
explicit v2.0.12 path to the existing opt-in OpenCode plugin, then run the
focused suites and a no-provider runtime preflight when RAM can stay above the
required reserve. The full LoRA and paired-task criteria remain unchanged and
unproven.

## Workflow decisions

- **Northstar:** addressed the observed runtime-version mismatch without
  treating source compatibility as product utility.
- **Subagents:** no delegated job was started because host RAM was only
  0.12 percentage points above its minimum reserve; code integration is also
  tightly coupled across the projection and lifecycle validators.
- **Luna advisor:** not used because local source inspection resolved the
  versioning question. The missing spend cap is an authority boundary, not an
  advisor question.
