# Phase 165: prompt-complete workflow replay

The prompt-complete derived mechanical contract was run through the bundled
package HTTP endpoint and the independent `run_wrench_case_eval.py` verifier.
The evaluator used the same temporary fixture root that built the cases, with
the deterministic health fixture enabled.

## Receipt

- case count: 220
- eligible cases: 120
- outcome matches: 220/220
- exact eligible proposals: 120/120
- prohibited accepts: 0
- transport or runtime abstentions: 0
- mechanical fast-path requests: 220/220
- model calls: 0
- median latency: 0.595 ms
- p95 latency: 42.219 ms
- mean latency: 7.195 ms
- derived case fixture SHA-256:
  `72dfd13dd9d3607206ea282e4422c53ae09cc9297d815365fc06fd8e2d74458a`
- endpoint: `http://127.0.0.1:28970/v1/chat/completions`

The server process and its temporary fixture were stopped and kept outside the
repository after the replay.

## Boundary

This is executable mechanical-contract evidence. The derived fixture makes
patch content and health bounds explicit, so it is not a replacement for the
historical sealed fixture or an approved matched MiniMax trace set. It does not
prove native dense 2M/4M attention, teacher parity, or production enablement.
