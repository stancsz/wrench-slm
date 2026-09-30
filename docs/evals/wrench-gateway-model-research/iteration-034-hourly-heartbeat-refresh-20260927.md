# Iteration 034: hourly goal heartbeat refresh (2026-09-27)

## Request

Keep doing hourly work toward the full Wrench local-completion, 95/5 routing,
95% frontier-token-saving, quality-retention, all-in-cost, and sustained
engineering evidence requirements.

## Automation state

An active Wrench hourly heartbeat already existed for this exact goal and
thread. I updated it in place with the Codex automation tool instead of
creating a duplicate:

| Field | Value |
| --- | --- |
| ID | `wrench-hourly-token-reduction-monitor` |
| Name | `Wrench hourly gateway experiment` |
| Kind and cadence | Heartbeat, every hour |
| Status | `ACTIVE` |
| Target thread | `01a0e15d-1974-7691-9584-372374c98560` |

The updated prompt preserves the complete acceptance criteria, under-10B model
choice, staged LoRA/data/storage rules, 10% RAM and VRAM floors, fit-03's 25%
RAM start gate, no-spend boundary for SubRoute, and instruction to prefer a
passing full experiment over weaker screens or documentation. It adds the
current next action: recheck live jobs and resources, then run the final
eight-case campaign-ledger test against the exact current source hashes only
when RAM and VRAM are each at least 10%. If that exact test is already recorded
as passing, do not repeat it; next exercise the 4000 request-control path with
a no-provider test. The 4000 process remains untouched. The separate
`wrench-gateway-research` heartbeat remains paused, so there is one active
hourly heartbeat for this goal.

The existing SubRoute caller reservation
`WRENCH-SUBROUTE-BUDGET-CALLER-20260927-01` remains active for that pending
verification. This iteration's documentation reservation is
`WRENCH-HOURLY-HEARTBEAT-REFRESH-20260927-01` and should be released after this
report and goal update are accounted for.

## Current gate and outcome

The latest host sample had 2,551.2/32,701.8 MiB free RAM (7.80%) and
15,137/16,311 MiB free VRAM. C: had 131.3 GiB free. The storage checker
reported `WITHIN_LIMIT` at 10,989,957,112 actual bytes before reserving this
report's 100,000-byte peak. The RAM floor is currently missed, so I did not run
the pending test, inference, or training. No Wrench provider request was sent.

The automation tool returned `Updated automation in the app` with status
`ACTIVE`; a read-back of the authoritative automation file confirms the
hourly interval and current thread target. Scheduling does not satisfy any
model-quality or savings metric. The goal remains active and all 95/5, token,
cost, retention, and all-day engineering targets remain unproven.
