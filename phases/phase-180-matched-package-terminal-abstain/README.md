# Phase 180: matched package replay with terminal mechanical abstention

Date: 2026-09-20

## What changed

The diagnostic runner now has an explicit
`--disable-client-mechanical-fast-path` mode. It sends every Wrench-arm case
through the configured model-local HTTP endpoint, so the benchmark measures
the downloaded package server rather than short-circuiting in the evaluation
client.

The fallback policy now matches the package contract. A response carrying
`mechanical_fast_path=true` is terminal whether it is an accepted bounded
proposal or a safe abstention. Only a non-mechanical local/model failure can
invoke the identical MiniMax fallback. The rules arm also passes the actual
allowed root into the mechanical router.

## Receipt

Command shape:

```text
python tools/run_diagnostic_worker_arms.py \
  --cases phases/phase-120-executable-mechanical-contract/cases.jsonl \
  --root phases/phase-120-executable-mechanical-contract/fixture \
  --teacher-traces phases/phase-178-prompt-complete-teacher-capture/teacher-220-max1024.json \
  --wrench-endpoint http://127.0.0.1:28900/v1/chat/completions \
  --wrench-model wrench-v73-package \
  --disable-client-mechanical-fast-path
```

The downloaded v73-style package server handled all 220 cases. The evaluator
receipt reports:

- status: `PASS_MECHANICAL_WORKER`;
- weighted mechanical frontier-token coverage: `93.5331%`;
- net frontier-token savings: `98.4379%`;
- Wrench weighted final success: `96.5767%`;
- teacher weighted final success: `68.6769%`;
- Wrench fallback count: `2/220`;
- Wrench frontier tokens: `1,012` versus teacher `64,785` in the weighted
  mechanical score denominator;
- zero prohibited accepts;
- zero unexpected mutations;
- median latency: `229.680 ms`;
- p95 latency: `440.378 ms`.

The two fallbacks were local health-read timeouts. Both remained abstentions
after the teacher attempt, so they did not create unsafe accepts.

## Boundary

This is strong evidence for the fast mechanical-worker lane and directly
supports the high-throughput product thesis. It is not the final release gate:
the input is still the historical 220-case executable contract, the teacher
capture is proposal-only, the final family-disjoint real-workflow trace set is
not sealed, and dense native 4M model attention is still unverified. The
package's direct 4M intake plus MapReduce path remains the production-value
mainline.

