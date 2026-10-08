# Gateway experiment findings

Archived: 2026-10-08. This is a concise record of the parked gateway and
routing research. The active objective and next experiment are defined only in
[`docs/goal/wrench-token30/GOAL.md`](../../goal/wrench-token30/GOAL.md).

## Reusable findings

- Provider-free three-arm receipts, manifests, fallback lineage, bounded token
  telemetry, spend guards, runtime identity checks, and frozen-development
  scoring were implemented and tested. They establish useful measurement and
  safety mechanics, not model utility.
- The gateway prototype reached healthy transport and synthetic end-to-end
  checks, but did not consume the parallel local result as a completed user
  answer. Frontier generation stayed disabled in the inspected runs; durable
  caller-side all-attempt accounting and a served Wrench routing adapter were
  not established.
- Two CPU-only Qwen3.5-4B context-selection probes reduced quoted text, but
  each failed exact-source validation. This does not qualify the model as a
  context worker or establish savings.
- Bounded second-pass consistency checks and context-reduction paths remained
  opt-in or unenabled. Agreement from the same model is not an independent
  correctness check. Unknown local usage and cancellation require explicit
  accounting.
- Runtime identity, held-out separation, data admission, route semantics,
  fallback, cancellation, and resource-boundary checks are reusable controls
  if future evidence makes them relevant.

## What was not proven

No gateway iteration established representative task completion, preserved
quality, a production-ready routing LoRA, or reduced frontier tokens on
completed matched tasks. Passing synthetic fixtures, unit tests, Docker
health checks, or model-format/scorer checks cannot substitute for that
comparison. The old iteration reports and experimental runners are pruned from
the working tree; their high-level outcomes and limits are retained here.

Do not resume the gateway feature queue or treat its former architecture,
spend, release, and training plans as current authority. Use only specific
controls that directly support the active paired experiment.
