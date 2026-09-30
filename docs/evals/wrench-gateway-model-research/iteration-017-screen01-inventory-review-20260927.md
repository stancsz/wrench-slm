# Iteration 017: screen-01 inventory review

Date: 2026-09-27 19:09 UTC (America/Edmonton)

Status: **PREPARATION ACCEPTED; SCREEN INFERENCE NOT ADMITTED**

## Scope

This iteration verifies and records the pinned local model inventory for the
screen-01 preparation protocol, then independently reviews the exact artifact
hashes. It does not run the screen, load the model, train an adapter, or call a
provider. Wrench HEAD at review was
`af01304824f079a64b6c3902397a2034b843511a`.

## Inventory and review evidence

The existing snapshot verifier reported `VERIFIED_LOCAL_SNAPSHOT` for
`Qwen/Qwen3.5-0.8B`, revision
`2fc06364715b967f1860aea9cf38778875588b17`. The pinned snapshot contains 13
files totaling 1,769,980,465 bytes. The verifier output is
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-evidence-selection-screen-01-model-snapshot-verification.json`,
SHA-256
`64C38776F5D208C666E7033A0E121A63A240538F1F55B8865B5D31FDDC474519`.

The required screen inventory was built from that verifier output at
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-evidence-selection-screen-01-model-inventory.json`.
It contains per-file paths, byte lengths, and SHA-256 values, plus the pinned
chat-template identity. Its SHA-256 is
`C0DA144391B212875A9A142272636E63C3D0B9DF8291F2827CC8534A5C2F3CA1`.
This confirms the inventory is bound to the supplied snapshot-verification
artifact. The independent reviewer did not traverse and rehash the full 1.77
GB model tree.

Independent assignment `WRENCH-SCREEN01-INVENTORY-INDEPENDENT-REVIEW-20260927-01`,
nonce `bbb199f8-2ca6-4f80-bfce-740237391105`, returned
**ACCEPT-PREPARATION** for the exact-hash scope. The reviewer confirmed the
protocol, runner, fixture, runtime lock, candidate manifest, verifier,
verification JSON, and inventory hashes matched the assigned identities. No
files were changed by the review. It did not run a runtime preflight or grant
inference authority.

## Admission and resources

The protocol still requires a separate exact-run authority record and a
root-reviewed admission manifest. The required
`local-evidence-selection-screen-01.admission.json` and explicit root
acceptance remain absent. Inference disposition is therefore **HOLD**. No
one-shot marker was created.

At 19:09:59 UTC, RAM was 4,084 / 32,702 MiB free (12.49%). The RTX 5060 Ti
reported 15,259 / 16,311 MiB free and 0% utilization. RAM clears the general
10% runtime floor but fails fit-03's 25% start gate. No process was started or
unrelated application stopped.

The storage checker reported `WITHIN_LIMIT` before this report update:
10,958,011,984 actual bytes plus 6,303,000 bytes in active reservations,
including the approved model-data root and the SubRoute checkout.
Reservations for this inventory and its independent review were each 100,000
bytes. Both were released after the report and goal update were finalized.
The follow-up storage check after release returned `WITHIN_LIMIT`; the final
aggregate remained below the 50 GB limit.

## What this does and does not establish

The preparation artifact is now present and independently accepted within
the stated hash-review scope. The screen itself has not run. Its 12-case
mechanics result, if later authorized, cannot establish repository coding
quality, 95/5 routing, 95% frontier-token savings, 95% all-in cost savings,
or day-long engineering. Those remain open acceptance requirements in the
active goal. No adapter candidate or effectiveness result was produced here.

## Next gate

Keep screen-01 closed until the run-specific authority, root review, admission
manifest, current resource/storage checks, and exact runtime preflight all
pass. If the gate remains closed, continue bounded source research and
evaluation design. Do not infer production utility from an inventory or
synthetic screen.
