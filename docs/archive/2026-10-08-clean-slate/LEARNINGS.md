# Experiment archive and restart notes

Archived: 2026-10-08. This is a record of prior evidence, not an execution
queue. The only active objective and next action are in
[`docs/goal/wrench-token30/GOAL.md`](../../goal/wrench-token30/GOAL.md).

## Objective kept

Reduce total frontier input plus output tokens by at least 30% for the same
type of complex tasks while preserving completion quality. Local-model tokens
are free for this metric and have zero weight. Frontier spend is capped at $1
per stable task across every attempt and run. The reset changes organization
and removes stale data; it does not weaken these criteria.

## Findings that survive the reset

| Experiment | Result | What it establishes |
| --- | --- | --- |
| Frontier-only compression diagnostics | No Qwen calls; quality failed | Prompt compression alone is not the objective. |
| Qwen-assisted paired run `qwen-paired-02` | 19,544 baseline frontier tokens; 16,805 candidate; raw reduction 14.01%. Baseline passed 2/6, candidate 1/6; zero pairs passed both arms with eligible Qwen output consumed. | Not qualifying savings. Preserve the failed quality result; do not reuse 14.01% as success. |
| Greedy local repair `verified-local-01` | 18 local calls; zero verified completions | Schema-valid output can be semantically wrong. Local tokens do not prove utility. |
| Thinking diagnostic `thinking-local-01` | 6 local calls; one verified repair; no frontier calls | A useful development signal, but no frontier denominator or controlled comparison. |
| Local retry `local-retry-01` to `-05` | Setup/runtime failures before a reliable local comparison | Fix and review bootstrap, tokenizer, runtime and reservation order before dispatch. These runs do not establish model utility. Their bulky per-run folders were deleted after recording these causes. |
| Local retry `local-retry-06` | 4 local calls; 1 local success, 3 incomplete/deadline failures, 2 successes replayed reviewed parent repairs; 0 frontier calls | Latest result is a development diagnostic only. It does not establish representative utility or token savings. Retain the result, manifest and source-review receipt pending a dedicated outcome review. |

Two cache proposals failed a collision oracle. File selection produced the same
deterministic import-closure packet, so it did not show marginal Qwen value.
Finite host-authored repairs can solve exposed fixtures without Qwen; future
tasks must be fresh and representative enough to test useful local work.

The prior review found a local-call bootstrap ordering defect: the approved
runtime add-ons must be installed before tokenizer/shared configuration. The
current retry source moved bootstrap before validation, checks the full 200 MB
reservation before setup and again before model construction, and passed 41
focused source tests. Its source review did not execute inference; the
post-run outcome still requires independent review.

## Evidence accounting

Accepted historical outcome receipts and frozen reports remain at their
recorded paths. Hash-bound receipts were not edited. For `local-retry-06`,
`result.json` records manifest SHA256
`8e888bd42fae10659e4871f72f2e58932e1eb8020e9d148b0eb4c796947265a2` and the
source-review receipt records that same frozen manifest plus the source and
test hashes. See
`C:\wrench-slm-data\artifacts\token30\local-retry-06`.

The token30 artifact root was inventoried before pruning. The only experiment
folders deleted in this cleanup were `local-retry-01` through
`local-retry-05` (206 files, 4,675,548 bytes). Their file paths, byte counts
and SHA-256 hashes are preserved in
[`pruned-artifacts.json`](pruned-artifacts.json). They contained setup-failure scratch,
repeated source snapshots and traces with no successful inference. The
`local-retry-06` result, manifest, source review and supporting files remain.
Other runs, ledgers, models, datasets, caches and unrelated task artifacts were
not removed. Immediately before pruning, the checker reported 39,549,154,640
actual bytes, 9,132,103,000 bytes in unrelated active reservations and
1,318,742,359 bytes of headroom. After pruning and archiving the inventory it
reported 39,544,533,877 actual bytes, 9,132,103,000 reserved and
1,323,363,122 bytes of headroom. The two stopped `local-retry-06`
reservations were released after final files were accounted.

## Rules for the fresh comparison

- Freeze the same task cohort, requirements and independent oracle for both
  arms. Do not tune on the held-out evaluation tasks.
- State the concrete useful Qwen work and the exact place its output enters
  the completed solution. Compare against deterministic alternatives.
- Count every frontier input and output token, including retries, recovery,
  verification and escalation. Retain failed tasks and unknown-usage holds.
- Require both arms to pass the same quality gate and require at least 30%
  aggregate reduction before claiming success.
- Freeze model, adapter, runtime, prompts, source identities and accounting
  before dispatch. Independently review source and outcomes.
- Enforce the $1 stable-task cap, storage admission and 10% RAM/VRAM reserves.
  Local tokens remain zero-weight, but local time and artifact growth stay
  bounded.

Historical files can inform these checks; their old next-step instructions,
product objectives and run plans have no authority. Do not resume an old
campaign or reinterpret a past result as success.
