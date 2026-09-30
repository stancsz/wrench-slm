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

## Data sources

The [training and evaluation source plan](DATA_SOURCES.md) proposes consented
real workflows, reviewed local-teacher candidates and exact fixtures for
separate purposes. Real workflow capture remains unauthorized. The owner has
authorized one fresh synthetic-only train/dev/held-out split for the bounded
gateway LoRA diagnostic; the fixed matched-task seed and exposed local screens
remain ineligible for that training. No real-work utility corpus is admitted.
Public benchmarks are limited challenge sets, and raw web/code dumps do not
stand in for verified Wrench outcomes. See the experiment-specific boundary in
the [data source plan](DATA_SOURCES.md).
See the [edge-case fixture report](../reports/wrench-e0-pilot-edge-cases/fixture.md).

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

On 2026-09-28 the owner removed a fixed model-size preference for the
gateway demo. The current host has a 16 GB RTX 5060 Ti, 32 GiB system memory,
and an AMD Ryzen 5 2600. Select any pinned and licensed model below 10B that
passes measured inference and LoRA-training fit, while preserving the 10%
RAM/VRAM reserve. Existing local Ollama tags include Qwen3.5-0.8B Q8_0 and
4B Q4_K_M. The 4B tag's current Ollama container has no GPU device and its
CPU-only smoke did not complete; an isolated `--gpus all` container also
lacked `/dev/nvidia0`. Neither result proves the host CUDA path cannot run the
model. Push a
provider-free demo MVP that combines Wrench context preparation, a local model,
deterministic code-task verification and exact input/output/latency/resource
receipts. A fixed mock may illustrate the frontier branch, never count as
frontier use or cost. Preserve the 95% local completion, <=5% routing, >=95%
success-retention, >=95% frontier-token and all-in-cost gates and the all-day
engineering study; the MVP cannot satisfy them by itself. The [active gateway
goal](../goal/wrench-gateway-model-research/GOAL.md) tracks the demo and
candidate gates.

On 2026-09-27 the owner directed a bounded experiment for a small local LoRA
gateway plus a stronger coding model, with targets of at least 95% of baseline
completed-task value and no more than 5% of baseline all-in cost. The owner
authorized new Wrench-authored synthetic train/dev/held-out data and a LoRA
candidate below 10B parameters when its exact inventory, compatibility,
storage, and hardware admission pass. The already-present 0.8B checkpoint is
the first comparison point, not the only permitted model. This narrows the
gateway LoRA's role to finite context and route proposals; it does not reopen
0.8B as a general coding agent or accept the 95/95 claim. The owner specified
the existing SubRoute at `127.0.0.1:4000`; fresh read-only GETs returned HTTP
200 and confirmed the `openrouter` force route resolves to
`openrouter/minimax/minimax-m3`. The latest `/model/info` response reports
`$0.30/M` input, `$1.20/M` output, and `supports_function_calling` plus
`supports_tool_choice` as true. Those metadata fields conflict with earlier
route snapshots and do not establish the selected upstream, successful tool
round trip, or billed cost. Keep the route unchanged until an explicitly
capped request produces a verifiable receipt. The version-matched OpenCode
provider setup is recorded in the [experiment goal](../goal/wrench-gateway-model-research/GOAL.md)
and [iteration 039](../evals/wrench-gateway-model-research/iteration-039-subroute-opencode-setup-20260927.md).
No generation will run until the user supplies a numeric aggregate spend cap
and the caller enforces hard cost and receipt checks. See the [active experiment goal](../goal/wrench-gateway-model-research/GOAL.md),
[research addendum](../reports/wrench-gateway-model-research/research-20260927.md),
[latest route iteration](../evals/wrench-gateway-model-research/iteration-015-subroute-mock-boundary-20260927.md),
[iteration 000](../evals/wrench-gateway-model-research/iteration-000-readiness-20260927.md),
and [LoRA protocol](../evals/wrench-gateway-model-research/lora-screen-01-protocol-20260927.md).

On 2026-09-26 the owner requested a fresh study of small LoRA models as local
gateway controllers after the tested 0.8B primary/semantic-controller
direction failed. The [research report](../reports/wrench-gateway-model-research/research-20260926.md)
recommended a narrower controller plus deterministic mechanics and a stronger
coding fallback. The 2026-09-27 decision above defines the new, limited
experiment authority; it does not change the prior 0.8B general-agent closure,
E0-E4 acceptance, real-work consent requirements, or production gates.

The owner closed the small local SLM semantic-controller experiment on
2026-09-26: using the tested 0.8B route as an OpenCode primary or semantic
controller is not feasible for the intended workflow. This does not establish
that all 2B models fail, and the 2B configuration was not tested. Synthetic
context-input reduction is not frontier savings; actual matched frontier
savings remain N/A. See the [decision record](../reports/wrench-local-acceptability/direction-closure-20260926.md).

The [realignment goal](../goal/wrench-v2-realignment/GOAL.md) covers cleanup,
v1 lessons and the experiment definition. E0 component slices exist, but the
deterministic context baseline is not integrated or accepted end to end. Full
v2 implementation and learning have not been accepted. The local-model
direction decision is scoped to the semantic controller and does not validate
or reject the deterministic context runtime's end-to-end savings hypothesis.
The [v1 postmortem](V1_LEARNINGS.md) explains the restart and the
[reuse inventory](../reports/wrench-v2-realignment/reuse-audit.md) identifies
surviving implementation and missing capabilities.
