# Iteration 040: hourly experiment continuation (2026-09-27)

## Owner request

Keep making progress toward the complete Wrench gateway target and run an
hourly continuation in this task. The user permits any model below 10B
parameters when it runs smoothly on this host and requires hard evidence for
95% local completion, no more than 5% frontier use, 95% frontier-token
reduction, and iteration progress. The current goal also retains paired
success, all-in cost, and sustained all-day engineering requirements.

## Schedule update

The existing `wrench-hourly-token-reduction-monitor` heartbeat was updated in
place. It was not duplicated. The automation tool returned `Updated automation`
with status `ACTIVE`.

The saved local automation record confirms:

| Field | Value |
| --- | --- |
| ID | `wrench-hourly-token-reduction-monitor` |
| Kind | Thread heartbeat |
| Status | `ACTIVE` |
| Cadence | Hourly |
| Target thread | `01a0e15d-1974-7691-9584-372374c98560` |
| Prompt length | 4,396 characters |

The persisted prompt contains the full success thresholds, accepts any
hardware-admitted candidate below 10B, directs one concrete reviewable advance
per hourly run, and prioritizes admitted training/evaluation. It requires live
job, RAM/VRAM, storage, and disk checks; exact reservations; sealed held-out
protection; the 25% fit-03 start gate; and use of SubRoute `:4000` only within
the spend/receipt boundary. Under 10% free RAM or VRAM it forbids runtime
work and delegation while directing useful source-level, fixture, or research
progress. It also includes the named Northstar, subagent, and advisor workflows
with their scope limits.

This verifies the stored automation configuration. A later hourly firing was
not observed during this update.

## Current machine and storage gate

At the latest sample, the RTX 5060 Ti had 15,222/16,311 MiB free VRAM, system
RAM had 3,228.3/32,701.8 MiB free (9.87%), and C: had 132.19 GiB free. RAM is
below the 10% runtime floor and the fit-03 25% start gate. No training,
inference, benchmark, test, packaging, or delegation ran in this iteration.

Storage was `WITHIN_LIMIT` before the documentation reservation, at
10,990,214,291 actual bytes and 8,103,000 bytes in active reservations. A
200,000-byte documentation reservation was created under
`WRENCH-HOURLY-AUTOMATION-20260927-01`. No model or runtime artifact was
produced.

## Workflow decisions

- **Northstar:** the hourly work preserves the original customer-value proof
  and does not treat fit compatibility or synthetic scores as utility.
- **Subagents:** no delegation was useful for this single schedule update,
  and the current RAM sample is below the delegation floor.
- **Luna advisor:** no advisor call was warranted because scheduling had no
  unresolved technical blocker after inspecting the stored automation.

## Next action

At the next hourly run, recheck exact current resources and live job handles.
If an under-10B candidate clears every hardware, storage, data, and exact-hash
gate, prioritize its bounded LoRA experiment. Otherwise make one concrete
provider-free engineering or evidence advance, without weakening the full
95%/5%/95%, all-in cost, or all-day acceptance targets. Keep paid SubRoute
requests closed until the caller has a numeric campaign cap and validated
receipts.
