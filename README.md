# Wrench

**Affordable AI for the rest of us.**

Wrench uses local Qwen to do useful work before a coding agent needs its
stronger model. Our first objective is **at least 30% fewer frontier tokens
for comparable complex tasks, with completion quality preserved**. Local model
tokens are effectively free for this score. Every frontier retry, verification
and fallback call counts. Frontier spending is capped at $1 per task across
all arms and reruns.

The required comparison is frontier-only completion versus a Qwen-assisted
Wrench workflow that consumes verified local work. Useful local preparation,
reasoning, partial work or complete task work may contribute. A smaller prompt
alone or an unused local draft does not establish this objective.

## Start here

- [Current objective and reading order](GOAL.md)
- [Active 30% goal and next action](docs/goal/wrench-token30/GOAL.md)
- [Archived experiment findings](docs/archive/2026-10-08-clean-slate/LEARNINGS.md)
- [Working agreement](AGENTS.md) and [storage/recovery](docs/operations/STORAGE_AND_RECOVERY.md)

## Current evidence

The local diagnostic used pinned Qwen3.5-4B but had no frontier baseline, so
it could not measure frontier savings. Later MiniMax-M3 compression diagnostics
made no Qwen calls and failed their task quality gates. The target remains
unachieved; neither result is proof of a successful Qwen-assisted workflow.
The [active goal](docs/goal/wrench-token30/GOAL.md) links the preserved receipts.

The checkout contains worker, verifier, retrieval, context, routing and client
components. These are reusable implementation, not release or utility proof.
A routing LoRA is a possible later improvement after a base-Qwen workflow can
be measured. Training, feature expansion and publication are not the current
commitment. The archived findings preserve prior evidence without creating a
separate work queue.

## Local development

Python 3.11+ is required. Reserve bounded peak storage before artifact-producing
jobs and keep at least 10% RAM and VRAM free. All Wrench files and active
reservations must stay strictly below 50 GB decimal in aggregate.

```powershell
python tools/check_wrench_storage_budget.py status
python tools/check_token30_objective.py
python -m pytest tests/test_token30_objective.py
```

The learned model has no shell, credential, permission or mutation authority.
Host policy and independent verification bound local work. The bilingual
[documentation site](site/README.md) describes the product direction; historical
examples and synthetic passes do not establish paid savings or shipped support.
