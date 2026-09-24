# Wrench North Star

Updated: 2026-09-23 (America/Edmonton)

## Product thesis

Wrench is a local Layer 1 runtime that prepares context before a coding agent
uses a downstream model. Its users are individual developers and small teams
working in existing repositories on modest hardware, initially below 8 GB
of GPU memory. The developer chooses the install and any provider account.

Their repeated work is finding relevant code, filtering tool results,
recovering decisions, exposing tool schemas and choosing when to escalate.
Today that work often consumes the same model context and paid calls as hard
reasoning. Wrench aims to reduce that burden while preserving exact evidence
and task success. Integration must be reversible and require little setup.

The owner wants software free to use, with open source, weights and datasets.
Those are release commitments, not licenses or downloads already shipped.
Initial sustainability assumes local execution, user-supplied provider accounts
when needed, and maintainer/community support. Demand, support effort and
funding for centrally trained core releases remain unvalidated. No mandatory
hosted service or new revenue model is assumed.

## Owner decision for v2

Wrench is a **hybrid context runtime with self-learning LoRA**:

- Deterministic code parses, indexes, searches, filters, stores and verifies.
- A small controller chooses evidence, retrieval steps, context policy,
  tool namespaces and downstream routes within a fixed authority boundary.
- Frozen Qwen weights plus a versioned Wrench-Core LoRA define shared behavior.
- A small Continuous LoRA learns local habits in evaluated batches, with replay,
  immutable versions and rollback.
- Current code facts, decisions and source text remain in external memory.

"Layer 1 runtime" and the three weight layers are different uses of "layer".
The [architecture](V2_ARCHITECTURE.md) makes their roles explicit.
The owner-supplied [notes](inputs/README.md) remain design inputs; their
numerical examples and performance claims are not Wrench results.

## Value and proof

Primary value is less paid frontier use and less end-to-end work for the
same successfully completed task. Compare matched tasks against a direct
downstream baseline and a deterministic Wrench baseline. Measure every retry,
correction, fallback, context miss, local-model pass, cache effect and learning
cost. An adapter must earn its latency and maintenance overhead.

Keep the v1 ambitions of 95% net frontier-token savings, 90% weighted workload
coverage and 50% median/p95 successful-task latency improvement as long-term
targets. None is achieved or justified by the new architecture.
Experiment milestones have separate go/no-go signals and cannot be called a
production pass. [V2 experiment](V2_EXPERIMENT.md) defines the comparisons.

Frontier Token Share is a secondary diagnostic with a fixed source-token
denominator. It is not equivalent to savings versus a baseline. Repeated
local processing must not inflate the denominator to manufacture progress.

## Reference and differentiation

[Headroom](REFERENCES.md) is the primary product reference because it offers
local context compression and retrieval of stored originals for coding agents.
Aider supplies a focused code-navigation comparison. Wrench's proposed
difference is a code-aware context pipeline whose bounded decisions improve
from verified local experience. That difference remains a hypothesis.

Evaluate real workflows against the reference on context quality, recovered
details, final success, total latency, cost, installation/reversal, inspectable
decisions and maintainability. Vendor figures are background, not matched
Wrench evidence. [Reference review](REFERENCES.md) records what was checked.

## Durable standards

- All Wrench artifacts and reservations together stay below 50 GB decimal.
  [Storage/recovery policy](STORAGE_AND_RECOVERY.md) governs admission and recovery.
- Preserve hot code, active diffs, explicit user input and exact failures
  losslessly. Omitted material needs retrievable provenance.
- Fail closed on authority violations, stale source identity, missing required
  evidence or invalid output. Learned choices cannot rewrite safety policy.
- Experience requires permission, source/outcome identity, redaction and review.
  Isolate related repositories, task groups and time periods across splits.
- Training creates new adapter versions; never edit the sole good foundation,
  core, active personal adapter or source dataset in place.
- Hardware claims name actual device, memory, workload, quality, sustained
  latency and resources, with battery/thermals where relevant. Less than 2 GB,
  older phones and borrowed compute remain later targets.
- Unknown results stay unknown. Preserve negative results and exact identities.

## Current work

The [realignment goal](../goal/wrench-v2-realignment/GOAL.md) covers cleanup,
v1 lessons and the experiment definition. Next comes E0, the deterministic
context baseline. Full v2 implementation and learning have not been measured.
The [v1 postmortem](V1_LEARNINGS.md) explains the restart and the
[reuse inventory](../reports/wrench-v2-realignment/reuse-audit.md) identifies
surviving implementation and missing capabilities.
