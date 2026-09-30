# Iteration 024: hourly job execution priority

Date: 2026-09-27

Status: active hourly automation updated; local training remains gated by live RAM

## Change

The owner asked for hourly continuation and authorized the local experiment
when the hardware can run it. The existing automation already inspected the
goal and resources each hour, but its action priority did not explicitly say
to launch the full local experiment when every gate passed. I updated the
existing automation `wrench-hourly-token-reduction-monitor` in place.

Its added execution rule is: when no matching job is live and a fully reviewed
candidate passes all exact admission checks, start the highest-priority
bounded local training/evaluation job in that run, then monitor the returned
handle. Fit-03 remains first only when its 25% RAM start gate and its hash,
runtime, storage, disk-space, and data gates pass. If it does not pass, the
job must not lower the gate; it continues independent work and may evaluate a
different pinned under-10B candidate only with a separate complete inventory,
adapter/runtime review, and resource admission. Paid frontier work remains
closed without a numeric aggregate USD cap and validated receipts.

## Verification of the scheduled job

The local automation record after update retains:

- ID `wrench-hourly-token-reduction-monitor`.
- Status `ACTIVE`.
- Hourly recurrence `RRULE:FREQ=HOURLY;INTERVAL=1;BYMINUTE=0`.
- Target thread `01a0e15d-1974-7691-9584-372374c98560`.
- The new execution-priority instruction is present in the stored prompt.

The duplicate `wrench-gateway-research` remains `PAUSED`. No second job was
created. The newly checked local process list contained only the FreeToken
daemon and two static HTTP servers; no Wrench training/inference job or fit-03
output was present.

## Current admission

At the initial check RAM was 3,613.4 / 32,701.8 MiB free (11.05%), below
fit-03's 25% start requirement. VRAM was 15,231 / 16,311 MiB free at 3%
utilization, and C: had 131.13 GiB free. The GPU headroom does not compensate
for the RAM start gate. No model was loaded, no training/inference ran, and
no provider request was made.

## Storage and verification

Before updating the automation, storage status included both the SubRoute
checkout and the automation directory and returned `WITHIN_LIMIT`: 10,991,410,901
actual bytes with 6,103,000 active reservations. Job
`WRENCH-HOURLY-PRIORITIZE-ADMITTED-EXPERIMENT-20260927-01` reserved 50,000
bytes for the automation and documentation update. `git diff --check` and
whitespace checks are recorded at closeout. No tests, model runs, downloads,
or provider calls were made.
