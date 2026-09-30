# Iteration 021: hourly continuation and experiment admission

Date: 2026-09-27

Status: hourly continuation verified; no model run admitted on this host sample

## User objective and schedule

The owner continues the full objective: train a Wrench-specific LoRA on a
pinned model below 10B if it runs smoothly here, demonstrate at least 95%
locally completed work with at most 5% frontier escalation, prove 95%
frontier-token savings, and measure engineering iteration progress. The new
conditional go-ahead authorizes progress on the staged local experiment when
the machine and job-specific gates pass. It does not waive the repository's
resource, storage, data, or exact-run requirements.

The existing `wrench-hourly-token-reduction-monitor` automation was inspected
in the local automation registry. It is `ACTIVE`, uses an hourly recurrence,
and targets this goal thread. Its prompt requires a fresh repo/job/resource/
storage inspection, one bounded advance per run, continued pursuit of every
acceptance target, and no provider call without the spend and receipt controls.
The duplicate `wrench-gateway-research` heartbeat is paused. Therefore this
goal already has one active hourly continuation; no duplicate job was added.

## Current host admission

At the live read, the host reported:

- RAM: 3,960.8 MiB free of 32,701.8 MiB, or 12.11%.
- GPU: RTX 5060 Ti, 15,228 MiB free of 16,311 MiB, 1% utilization.
- C: 131.13 GiB free.
- Processes: no Wrench trainer/inference runner. Python processes belonged to
  the FreeToken daemon and two local `http.server` instances. They were left
  running.

The existing 0.8B fit-03 candidate requires at least 25% free RAM at start;
the current 12.11% does not pass. Although current free RAM is above the
general 10% operating floor, the margin is only 2.11 percentage points and
does not justify a model load that could breach the floor. The current fit
protocol was not weakened.

The 12-case local evidence-selection screen remains explicitly
`PREPARATION ONLY`. Its exact-run admission manifest is absent, and its
one-shot marker makes any admitted attempt final even if the run fails. The
previous independent screen review accepted preparation/hash binding only;
it did not accept a run manifest, rehash every local model file, or grant
inference authority. This screen measures synthetic evidence-ID mechanics,
not repository coding, the 95/5 target, or token savings. No model file was
loaded and no inference or training was attempted.

## Decision and next gate

Keep the single hourly automation active. When current resources meet the
candidate's reviewed start/runtime gates and no matching job is live, use the
staged Wrench LoRA path as the first direct effectiveness experiment. If the
0.8B fit cannot meet those gates on this machine, evaluate another pinned
candidate below 10B with its own complete file inventory, storage/volume
admission, adapter/runtime review, and resource bounds; do not infer fit from
published estimates. Treat screen-01 as a mechanics diagnostic only and do
not spend its one-shot invocation as a substitute for LoRA or coding-quality
evidence.

SubRoute `:4000` received no generation request. A numerical aggregate USD cap
and durable billed-receipt controls are still required for a paid arm; local
training and evaluation can continue independently when admitted.

## Storage and verification

Before writing this report, the checker including
`C:\Users\stanc\github\subroute` reported `WITHIN_LIMIT`: 10,991,327,474
actual bytes and 6,103,000 existing reserved bytes, against the 50 GB decimal
ceiling. Job
`WRENCH-HOURLY-EXPERIMENT-ADMISSION-20260927-01` reserved 200,000 bytes for
this documentation update. The report was checked for whitespace and
`git diff --check`; no tests, model inference, training, downloads, or provider
calls were run. Final storage status and the reservation release are recorded
at closeout.
