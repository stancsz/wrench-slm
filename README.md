# Wrench

**Affordable AI for the rest of us.**

Wrench v2 is an experiment in a local **Layer 1 context runtime** for coding
agents. It turns repository state, tool results and conversation history into
a small, traceable working context before the next model call. Ordinary code
does parsing, indexing, filtering and verification. A small learned controller
makes bounded retrieval, tool-selection and routing decisions.

The planned learned component has three independently identified parts:

```text
frozen Qwen checkpoint
  + versioned Wrench-Core LoRA, frozen during use
  + personal Continuous LoRA, trained as an evaluated candidate
```

"Layer 1" describes Wrench's position before downstream reasoning. The three
weight layers describe its internal model. Only the personal adapter evolves
during normal use, through background batches, evaluation and promotion.
Facts remain in local state and source artifacts; adapters learn useful habits.

## Start here

- [North Star and owner standards](docs/northstar/README.md)
- [V2 architecture](docs/northstar/V2_ARCHITECTURE.md)
- [V2 experiment and acceptance](docs/northstar/V2_EXPERIMENT.md)
- [V1 failure lessons](docs/northstar/V1_LEARNINGS.md)
- [Current repository goal](GOAL.md)
- [Storage and recovery policy](docs/northstar/STORAGE_AND_RECOVERY.md)

## Current implementation

This checkout contains the v1 bounded worker, independent verifier, lexical
retrieval, Python AST helpers, context assembly and client/router code.
These are reuse candidates. V2's durable artifact store, incremental semantic
index, deferred tool registry, composed adapters, experience pipeline and
adapter promotion/recovery system are **not implemented or validated**.

The starting candidate is `Qwen/Qwen3.5-0.8B`, a natively small checkpoint.
Its pinned metadata lists 1,769,980,465 bytes for the complete repository.
This includes the vision component; v2 initially uses text. Runtime
compatibility and useful performance remain to prove. See the
[model manifest](docs/northstar/model-candidate.json).

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

The intended audience starts with developers using less than 8 GB of GPU
memory. A useful workflow below 2 GB and older phones remain future targets.
Free use and open source, weights and datasets are owner commitments;
release artifacts, licenses and hardware support require their own evidence.

The bilingual [documentation site](site/README.md) distinguishes the v2
experiment from retained v1 behavior. This realignment has not trained or
deployed v2.
