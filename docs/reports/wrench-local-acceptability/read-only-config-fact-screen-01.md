# Read-only configuration fact screen 01

Goal: [Wrench local work acceptability](../../reports/wrench-local-acceptability/local-work-acceptability-map-20260926.md)
Worker: root orchestrator
Status: **completed; task class not accepted**
Date: 2026-09-26

## Work and result

Prepared and froze an independently reviewed, 20-case synthetic screen for
read-only configuration fact retrieval. Ran one pass of the pinned local
Qwen3.5-0.8B runtime under a 20-minute deadline, a 100 MB storage reservation,
16 MiB per-log caps, and 10% free RAM/VRAM floors. The model produced 0/12
exact grounded positive completions and 0/8 valid boundary abstentions. All 20
final outputs were invalid; no prohibited action or model tool call occurred.
The class fails its predeclared acceptance gate.

The full counts, model identity, token cost, latency, resources, receipt digest,
verification, and interpretation are in the
[evaluation result](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-result.md).
The pre-run design and frozen hashes are in the
[protocol](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-protocol.md).

## Changes and checks

- Added the synthetic fixture, bounded runner, and deadline/log-cap wrapper.
- Updated the local acceptability map and added the result evaluation.
- Independent static review passed; protocol, fixture, runner, and wrapper
  identities were checked before launch.
- `git diff --check` passed; runner and wrapper passed Python AST parsing.
- Storage admission passed. The child stopped, output bytes were accounted,
  and the screen reservation was released. Post-run inventory remained below
  the 50 GB ceiling.
- No test suite was run. No client, provider, training, download, or real-data
  capture was used.

## Next action

Keep training paused and do not reuse this fixture for tuning or reruns. For
the North Star total-token percentage, close the E0 actual-dispatch accounting
gap: join same-task baseline and Wrench requests to verified outcomes and
include local tokens, every downstream call, retries, repairs, verification,
and fallbacks. The current [offline OpenCode request boundary](../wrench-e0-opencode-context-adapter/offline-request-boundary.md)
does not observe authenticated downstream usage or task success. Do not claim a
savings percentage until successful matched pairs exist.
