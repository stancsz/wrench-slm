# Iteration 063: held-out read-order source audit

Timestamp: 2026-09-28 03:16 UTC (2026-09-27 America/Edmonton)

## Host gate

The current host sample measured 2,679.8 / 32,701.8 MiB free RAM (8.19%),
15,226 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 140.53 GB free on C:.
The process query found no Wrench training, inference, or benchmark process.
RAM is below the required 10% operating floor and the 25% fit-start gate, so
no test, runtime, workload, training, or delegation ran.

Storage was `WITHIN_LIMIT`: 10,991,333,358 bytes actual, 8,103,000 bytes in
active reservations, with no checker errors. This documentation update used
a 100,000-byte reservation under
`WRENCH-HELDOUT-READ-ORDER-ITER063-20260927`; release it after accounting.

## Static heldout boundary audit

The training runner hash was
`62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC`.
Its `split_rows` loop at lines 1106-1121 opens only train and dev payloads.
It reads heldout count and SHA-256 from the synthetic manifest but does not
resolve or read the heldout payload.

The scorer hash was
`0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5`.
Before opening heldout content, `run_score` verifies the completed fit-03
receipt, pinned model inventory, adapter files, training resources, exact
preflight receipt/log, and no prior heldout claim. It resolves the heldout
path, loads both model arms, validates the template and pinned input trees,
checks the live reservation, then writes global and job-level access markers.
The first heldout payload read in the current source is
`read_verified_split_bytes(...)` at line 1778. The protocol hash was
`EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5`.

No heldout payload was opened in this audit. This confirms source ordering
only. It does not prove runtime behavior, model quality, task completion,
token savings, or a completed independent package review. The current GOAL
and scorer scope still need that review before fit-03 can start.

## Next gate

The hourly automation remains `ACTIVE` and hourly. At current 8.19% free RAM,
do not run tests, inference, training, or delegated review. Once RAM clears
10%, obtain one bounded independent exact-hash review of the trainer, scorer,
protocol, current GOAL, and Iterations 008/009. Run fit-03 only after that
review passes, at least 25% RAM is free at launch, RAM/VRAM remain at least
10%, and fresh storage/disk checks pass.
