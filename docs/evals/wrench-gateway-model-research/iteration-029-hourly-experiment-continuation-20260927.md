# Iteration 029: hourly experiment continuation

Date: 2026-09-27 (America/Edmonton)

Status: **ONE EXISTING HOURLY HEARTBEAT ACTIVE; TRAINING NOT ADMITTED ON THIS SAMPLE**

## Automation

Revalidated the existing `wrench-hourly-token-reduction-monitor` heartbeat and
updated it in place. It remains **ACTIVE**, runs hourly at minute 0, and targets
the current Wrench goal thread. No duplicate heartbeat was created. The
separate `wrench-gateway-research` heartbeat remains paused.

The preserved prompt continues the complete objective: train a Wrench LoRA on a
pinned sub-10B model; prove 95% local episode completion, no more than 5%
frontier escalation, 95% fewer frontier tokens, at least 95% verified success
retention, 95% lower all-in cost, and sustained all-day engineering. It records
the latest owner direction to use the Northstar skill, not anchor on one model
size, and start a bounded local experiment in an hourly run when candidate-
specific hardware, context, storage, and run-admission checks demonstrate a
smooth fit. Existing Codex Subagents and Luna-advisor boundaries remain in the
prompt. The full prompt retains the 50 GB storage, 10% RAM/VRAM, fit-03's 25%
RAM-start, provenance, sealed-holdout, rollback, and no-spend controls.

## Live resource recheck

- RAM: 3,745.2 / 32,701.8 MiB free (**11.45%**).
- GPU: RTX 5060 Ti, 15,227 / 16,311 MiB free, 0% utilization.
- No Wrench training, inference, or model-serving process was found. Two
  FreeToken daemons and two static HTTP servers were observed and left running.
- Storage checker: `WITHIN_LIMIT`, 10,989,607,617 actual bytes before this
  report reservation. The 50 GB aggregate cap remains satisfied.
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.

The staged fit-03 candidate remains below its explicit 25% free-RAM start gate.
The current 11.45% RAM sample is also too close to the hard 10% reserve to infer
that a different model would train smoothly from GPU free memory alone. No
training or inference started. The new owner direction removes the previous
model-size preference, but it does not waive per-candidate inventory, runtime,
context, storage, and resource admission. An admissible candidate should be
started by the hourly heartbeat in the same run, rather than deferred for more
documentation.

## Verification and next action

The automation tool returned `Updated automation in the app` with status
`ACTIVE`. The local automation record was re-read before editing and the live
machine process/resource state was checked. No provider request or external
model spend occurred. The stored goal remains active and all completion claims
remain unproven.

At the next hourly run, inspect live state again. If a fully inventoried,
reviewed under-10B candidate passes its exact smooth-fit and storage gates,
start and monitor the bounded LoRA/evaluation job. Otherwise make one useful
independent advance toward candidate-specific fit or full-request token
accounting, without lowering gates or sending a paid SubRoute request.
