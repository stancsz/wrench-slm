# Current goal: 30% fewer frontier tokens

Status: in progress. The target is unproven.
Owner: human product owner; repository agent owns bounded execution and evidence.

## Objective

Use Wrench with local Qwen to reduce total frontier input plus output tokens by
at least 30% on comparable complex coding tasks while preserving completion
quality. Local-model tokens have zero weight. Frontier spending is capped at
$1 per stable task across all arms, attempts, retries, diagnostics and reruns.

The frozen baseline is frontier-only. The candidate must perform useful local
Qwen work and actually consume that output in the completed workflow. Compare
the same tasks, requirements and independent quality oracle. Count every
frontier request, including retries, verification, recovery and escalation.
Retain every failure. A result qualifies only with complete token usage,
successful completion in both arms and the same quality gate.

`reduction = 1 - candidate_frontier_tokens / baseline_frontier_tokens`

The active machine-readable contract is
[`objective.json`](objective.json). The plan guard is
[`check_token30_objective.py`](../../../tools/check_token30_objective.py); it
checks alignment only and does not dispatch or prove an outcome. Existing
tighter campaign limits and unknown-usage holds remain binding.

## Hard boundaries

- Keep Wrench-owned data strictly below 50,000,000,000 bytes in aggregate.
  Check status, reserve peak growth, and check destination free space before
  every artifact-producing job. Use `C:\wrench-slm-data` for generated data.
- Keep at least 10% of system RAM and VRAM free during local work. Bound time,
  context, calls and output growth even though local tokens are free.
- Use reviewed, permitted data. Preserve provenance, rights, consent,
  redaction and split boundaries. Never tune on sealed evaluation data.
- Freeze the model/runtime for each comparison. Record failures and exact
  tested identities. Synthetic mechanics are not product utility.
- The learned component proposes bounded work only. Deterministic policy
  retains routing, permissions, spending and verification authority.

Detailed storage admission and recovery rules live in
[`STORAGE_AND_RECOVERY.md`](../../operations/STORAGE_AND_RECOVERY.md).

## Evidence and current checkpoint

The prior Qwen-assisted frontier pair used 19,544 baseline tokens and 16,805
candidate tokens, a raw 14.01% reduction. Quality failed: baseline passed 2/6,
candidate passed 1/6, and no pair both passed with eligible Qwen output
consumed. It does not qualify as savings. Local-only runs have no frontier
denominator and cannot establish this goal.

The latest local-retry diagnostic completed with four local calls and zero
frontier calls. One local attempt passed; three were incomplete or failed the
deadline, while two other successes replayed reviewed parent repairs. This is
development evidence only and has no frontier denominator or representative
utility claim. Its result and source review are retained in
`C:\wrench-slm-data\artifacts\token30\local-retry-06`.

Condensed experiment findings and the pruning record are in
[`docs/archive/2026-10-08-clean-slate/LEARNINGS.md`](../../archive/2026-10-08-clean-slate/LEARNINGS.md).
Older goal files, reports and archives are historical references. They do not
create an active queue or authorize a separate campaign.

## Current checkpoint

**Unmet criterion:** a frozen, quality-passing matched comparison with at least 30% reduction in total frontier tokens and actual consumption of useful Qwen output.

**Next action / owner / check:** the repository agent will build and source-
review one bounded paired comparison using fresh, permitted tasks that are
not used to tune the candidate. The plan must name the concrete Qwen work,
consumption point, frontier accounting, independent oracle, frozen model and
runtime, cumulative task spend, storage reservation and resource limits. Run
the guard before dispatch; independently review outcomes afterward. Stop if
the plan cannot meet the $1 cap or 10% RAM/VRAM reserve. Do not count any
historical result as current success.

Any change to target, metric, task family or cap requires coordinated updates
to this goal, `objective.json` and `COLLABORATION_CONTRACT.json`. Historical
receipts remain unchanged and are never rescored.
