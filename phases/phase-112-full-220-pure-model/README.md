# Phase 112: full 220-case pure model evaluation

## Result

The NVFP4 portable checkpoint was served by FreeToken with the embedded
mechanical route disabled. The canonical 220-case fixture was then sent to
the actual model endpoint and every response was passed through the Wrench
verifier.

Receipt: `full-220-pure-model-v2.json`.

| Metric | Result |
| --- | ---: |
| Requests | 220/220 |
| Mechanical fast-path requests | 0/220 |
| Correct expected outcomes | 51/220 |
| Exact eligible proposals | 3/120 |
| Prohibited accepts | 6 |
| Transport/runtime abstentions | 0 |
| Median latency | 344.246 ms |
| p95 latency | 878.825 ms |
| Mean latency | 424.926 ms |

The direct model path is therefore not a release candidate. It can produce a
schema-shaped response on simple prompts, but it is not yet a safe 90%
mechanical worker. The embedded deterministic route remains essential and is
currently much stronger on the same historical fixture.

## Boundary

This is a real model-generation receipt, not a toolbelt result. It does not
establish MiniMax parity or approved matched-workflow value. The six prohibited
accepts are an immediate safety failure for any learned-only route, so the
portable package must keep the fail-closed mechanical verifier and fallback
router in front of the model.
