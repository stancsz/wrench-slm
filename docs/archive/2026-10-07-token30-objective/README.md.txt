# Wrench

**Affordable AI for the rest of us.**

Wrench is a local context and routing layer for coding agents. It aims to
intercept task families a small model can handle reliably and pass uncertain
or difficult tasks to the user's stronger model. It does not aim to replace
frontier models for every task.

Qwen supplies the small model's base capabilities. A Wrench-trained LoRA adds
task-routing behavior that Qwen does not provide by default. The LoRA proposes
a bounded route; deterministic policy controls allowed routes and dispatch;
independent checks verify local outcomes. The strongest route for a task family
must be earned through held-out evidence, including full local inference,
verification, fallback, and recovery cost.

The fastest credible product path is a complete paired workflow through one
supported client, followed by task-family quality and cost evidence, recovery
and installation checks, and a reproducible release package. Hugging Face
artifacts need cleared licenses and data provenance, exact hashes, reproducible
evaluation, hardware limits, known failures, and an honest model card.

## Start here

- [North Star and owner standards](docs/northstar/README.md)
- [Current architecture](docs/northstar/V2_ARCHITECTURE.md)
- [Current experiment and release gates](docs/northstar/V2_EXPERIMENT.md)
- [V1 failure lessons](docs/northstar/V1_LEARNINGS.md)
- [Current repository goal](GOAL.md)
- [Storage and recovery policy](docs/northstar/STORAGE_AND_RECOVERY.md)

## Current implementation

This checkout contains bounded worker, verifier, retrieval, context assembly,
and client/router components. They are reuse candidates, not proof that the
new selective routing product is integrated or release-ready. No Wrench
routing-LoRA candidate has established product utility. Historical Qwen
screens and snapshots remain scoped to their recorded task and runtime.

## What survives from v1

The owner reports filesystem corruption and data loss ended the first attempt.
Surviving audits also show data-quality and evaluation problems. The precise
filesystem cause remains unverified. Source and historical receipts survive;
the [v1 archive](docs/archive/2026-09-23-v1/README.md) captures the previous
direction, including uncommitted documentation.

The learned model has no shell, credential or mutation authority. Existing
bounded read-only and review-only actions stay behind independent validation.
V2 context decisions do not grant new execution permissions.

## Local development

Python 3.11+ is declared in [pyproject.toml](pyproject.toml). An existing
environment can run the retained no-model example and focused tests:

```powershell
python tools/check_wrench_storage_budget.py status
python examples/local_first.py
python -m pytest tests/test_context.py tests/test_toolbelt.py tests/test_policy.py tests/test_schema_evaluation.py
```

Before artifact-producing work, reserve bounded peak bytes as described in
[AGENTS.md](AGENTS.md). These commands demonstrate retained v1 behavior,
not the v2 learning stack.
The test command requires pytest; the broader historical training/pruning tests
also require optional model dependencies such as PyTorch.

## Product constraints

All Wrench-owned files and active peak reservations together must remain
**below 50 GB decimal**, including caches, temporary copies and worktrees.
Keep at least 10% RAM and VRAM free. Model size, destination free space,
checksums, bounded retention and recovery are admission requirements.

Hardware support is claimed only for named tested configurations. Lower-memory
devices and older phones remain future targets. Free use and open source,
weights and datasets are owner commitments; every published artifact still
needs compatible licenses, provenance, reproducibility, and release review.

The bilingual [documentation site](site/README.md) distinguishes the v2
experiment from retained v1 behavior. This realignment has not trained or
deployed v2.
