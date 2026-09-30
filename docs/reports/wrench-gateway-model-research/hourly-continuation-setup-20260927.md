# Hourly continuation setup

Date: 2026-09-27
Worker: `/root`
Status: active; recurring continuation configured

## User outcome

Continue the full Wrench gateway goal until there is direct evidence for a
Wrench-specific LoRA, at least 95% verified local completion, at most 5% task
episodes with frontier use, at least 95% paired success retention, at least
95% fewer frontier tokens and at least 95% lower all-in cost than the paired
frontier-only baseline, sustained all-day engineering quality, and recorded
iteration progress. The user permits any pinned model below 10B parameters
when it runs smoothly on this machine; size alone is not a reason to reject a
candidate. These are acceptance targets, not observed results.

## Scheduling change

The existing hourly heartbeat `wrench-hourly-token-reduction-monitor` already
targets this thread. I updated it in place and kept it ACTIVE instead of
creating a duplicate. The separate `wrench-gateway-research` heartbeat remains
PAUSED. The active prompt now carries the 95/5/95, paired-success-retention,
95%-cheaper, and all-day goals, the broader under-10B candidate scope, one
concrete reviewable advance per hour, resource and storage checks,
no-duplicate job handling, staged LoRA and held-out rules, and the user's
requested port-4000 comparison route.

Verification: the automation tool returned `Updated automation` with status
`ACTIVE`. The local automation record confirms hourly cadence, the current
thread ID `01a0e15d-1974-7691-9584-372374c98560`, and prompt text containing
both the full frontier-token target and the under-10B candidate scope.

## Current experiment gate

A fresh host snapshot recorded 17.74% free RAM (5.66 GiB), 15,135 of 16,311
MiB free VRAM, and 145.75 GiB free on C:. The current 0.8B fit-02 attempt keeps
its 25% RAM start gate and was not launched. The existing 10% RAM and VRAM
runtime floors remain in force. Storage admission, including both Wrench
automation directories, was within the 50 GB ceiling. No model was downloaded,
no training or inference ran, and no service or process was stopped.

The existing port-4000 SubRoute is reserved for the paired frontier comparison.
Its live route remains mutable OpenRouter force mode; do not send generation
requests until the numeric USD cap, exact provider/model identity, and
auditable usage receipt method are established. Continue authorized no-cost
work while that gate remains open.

## Independent review results

- `WRENCH-MODEL-FIT-AUDIT-20260927-01` recommends Qwen3.5-2B for a later
  gateway-capacity comparison and Qwen2.5-Coder-1.5B for code-specific
  decisions. Neither has passed a LoRA preflight. It corrected the coder
  model's context from the stale 131K entry to the officially documented
  32,768 tokens.
- `WRENCH-EVAL-PROOF-AUDIT-20260927-01` confirmed that the 128-case
  synthetic labels cannot prove the requested target and that the prior goal
  omitted paired task-success retention and the original all-in 95%-cheaper
  claim. The completed audit and replacement design are in the
  [product proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md).

Both tasks used unique nonces, exact-hash handoffs, read-only scope, and
131,072-byte reservations; both reservations were released after the workers
completed with no files or other artifacts. Their findings were reviewed and
recorded in the proof design and research report. The next action is to obtain
an independent review of the new proof criteria, then continue the next
admitted experiment or a safe no-cost step.

## Latest no-cost research update (2026-09-27)

The proof-spec critique has now completed. It verified exact assigned hashes
at the expected HEAD, performed no heldout read/provider call/spend, and found
seven design gaps. The updated proof design now freezes the primary LoRA arm,
workload frame and grouped/time split, paired clean workspaces/order,
orthogonal route/outcome fields, 5% family-wise error plan, provider/cache
accounting, all-in labor/hardware amortization, and numerical workday gates.
The old "next action" above is superseded by that completed review and its
amendments.

A separate Qwen3.5-0.8B hybrid-LoRA placement preprint reports 24
attention-only modules / 1.08M trainable parameters versus 186 / 10.82M for
all-layer tuning, with task-dependent quality and a single-seed design. The
current Wrench trainer uses the all-module profile. Before full-fit 02, make a
reviewed design decision to compare or justify this profile; any code/profile
change requires a fresh exact-hash review and preflight. This research gate
does not lower the 25% RAM start threshold. See [the active gateway goal](../../goal/wrench-gateway-model-research/GOAL.md),
[fit protocol](../../evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md),
and [Qwen3.5 LoRA placement study](https://arxiv.org/abs/2604.22127).

The active hourly automation was updated in place to preserve this new LoRA
profile gate and the detailed proof accounting rules. It remains ACTIVE hourly.
The user replied "Specify cap and provider/route" to the spend question, but
did not supply the exact aggregate USD cap or upstream provider/model for the
port-4000 comparison. Its route remains closed to generation; no-cost local
work and protocol preparation continue.
