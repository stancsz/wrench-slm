# Phase 94: current deterministic route replay

Status: diagnostic coverage evidence, not the final matched MiniMax gate.

The new `tools/evaluate_mechanical_route.py` replays the current
`mechanical_route` implementation over the canonical 220-case fixture without
starting a model server. It measures route classification and expected
outcome semantics only. It deliberately does not execute file scans, Git, or
health requests, because those belong to the full workflow-arm evaluator and
would make latency depend on the size of the dirty development repository.

Current result:

- 220 total requests
- 200 deterministic mechanical routes
- 20 model-fallback-required requests
- 200/220 expected outcome matches
- 0 prohibited accepts
- 6.758 ms total replay time
- 90.91% mechanical route coverage by case count

Family breakdown:

- `read_file`: 30/30 routed
- `read_lines`: 30/30 routed
- `literal_search`: 30/30 routed
- `git_read_status`: 30/30 routed
- `health_read`: 30/30 routed
- `out_of_domain`: 40/40 deterministic abstentions
- `patch_draft`: 10/30 routed, 20 intentionally left for model/fallback because
  the prompt does not contain a concrete diff to route mechanically

Receipt: `replay-220.json`.

This proves the current source still meets the historical 90% mechanical
case-count target. It does not prove weighted frontier-token coverage, teacher
parity, final workflow success, or production readiness.
