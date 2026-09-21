# Phase 303: real harness metadata inventory

## Result

The metadata-only observations from the real local integration were profiled
without copying prompt or tool-result content into a new dataset:

- 2,054 observation rows
- 53,511,711 estimated raw input tokens
- 2,054 embedded mechanical-path rows
- 0 model calls
- 2,045 rows exposed a read/search client surface
- 128 rows exposed a mutation-capable client surface in surrounding harness
  metadata
- inventory SHA-256: `f252ce3fe8a0b49a148dba3cfb0579d4daa0bae762b205f88b41ae18bd792370`

Receipt: `metadata-inventory.json`

## What this changes

This is an evidence-backed workload inventory for the human-reviewed Wrench
portfolio. It identifies which protocols, wrapper tools, statuses, routing
sources, and token masses appear in real harness traffic. It is a safer input
to defining task families and weights than treating the synthetic 220-case
fixture as the product workload.

## Explicit limits

The inventory does not label tasks as approved eligible work. Client tool names
describe surrounding context and do not prove that Wrench accepted or executed
a mutation. The inventory is not used for training, prompt tuning, expert
selection, or final evaluation. Human review must still redact sensitive data,
assign stable task-family labels, define independent oracles, and freeze
calibration/development/final splits before quality claims.

## Reproduction

```powershell
python tools/profile_real_harness_observations.py `
  --source phases\phase-238-real-harness-integration\wrench-observations.jsonl `
           phases\phase-238-real-harness-integration\dsh-observations.jsonl `
  --output phases\phase-303-real-harness-inventory\metadata-inventory.json
```
