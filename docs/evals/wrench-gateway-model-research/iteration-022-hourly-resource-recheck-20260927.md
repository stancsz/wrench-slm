# Iteration 022: hourly resource recheck

Date: 2026-09-27

Status: admission rechecked; no local model job is safe to start at this sample

## Objective and active schedule

The full goal remains unchanged: train a Wrench-specific LoRA on a pinned
under-10B model if it runs smoothly on this machine, then produce verified
evidence for 95% local completion, no more than 5% frontier escalation, and
95% frontier-token savings. Sustained engineering remains a separate
acceptance requirement.

The local automation registry still shows one `ACTIVE` hourly heartbeat,
`wrench-hourly-token-reduction-monitor`, targeting this goal thread. The
duplicate `wrench-gateway-research` remains paused. No scheduler change was
needed.

## Live resource and job evidence

- RAM: 3,376.7 / 32,701.8 MiB free (10.33%). This is only about 106.5 MiB
  above the 10% minimum operating reserve.
- GPU: NVIDIA GeForce RTX 5060 Ti, 15,243 / 16,311 MiB VRAM free, 1% use.
- C: 131.13 GiB free.
- No Wrench trainer or inference process was found. The Python processes were
  a FreeToken daemon and two local static HTTP servers; none was stopped.
- `local-evidence-selection-screen-01.admission.json`, its `.used` marker,
  and its output receipt are absent. The screen remains preparation-only and
  is not a substitute for LoRA or repository-engineering evidence.

The 0.8B fit-03 experiment's 25% RAM start gate fails. The present 10.33%
sample is also too close to the general floor to risk importing/loading a model
for a one-shot test whose watchdog could stop after the one-shot marker is
consumed. No model load, inference, training, download, or provider call ran.
No unrelated service was stopped to increase headroom.

## Next action

Keep the hourly heartbeat active. If a future fresh sample passes fit-03's
25% RAM start gate plus its exact storage, runtime, hash, and destination-space
checks, perform that bounded Wrench LoRA experiment. If not, continue
independent protocol/runtime work or prepare a candidate-specific admission
for another pinned model below 10B; do not lower the existing gate or treat
this resource observation as model-quality evidence. Keep the paid SubRoute
arm closed until its numeric aggregate cap and durable provider receipts are
available.

## Storage and verification

The storage checker including `C:\Users\stanc\github\subroute` returned
`WITHIN_LIMIT` before this documentation update: 10,991,353,958 actual bytes
plus 6,103,000 bytes already reserved, below the 50,000,000,000-byte limit.
Documentation job `WRENCH-HOURLY-RESOURCE-RECHECK-20260927-02` reserved
120,000 bytes. Whitespace and `git diff --check` are checked at closeout. No
tests were added or run.
