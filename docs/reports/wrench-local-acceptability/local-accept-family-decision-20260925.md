# Next local work-family decision

Status: design recommendation only. No cases were run or created.

- Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
- Job ID: `W2-LOCAL-ACCEPT-FAMILY-DECISION-20260925`
- Nonce: `LAFD-91C4`
- Inspected revision: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`

## Recommendation

Measure **evidence-preserving triage of failing-test/build logs** as the next
bounded coding-agent work family. On an explicitly supplied, immutable
snapshot, Wrench would select the exact failing-test identity, causal error
lines, and required source locations from noisy tool output, then return those
verbatim with source coordinates. The bounded local outcome is exact coverage
of a frozen evidence oracle plus correct abstention for missing, stale, or
ambiguous evidence. This tests useful context preparation without requiring
semantic edits or training. It is the best current savings hypothesis, not an
accepted local task class.

The exposed token screen gives a reason to prioritize it: its two log-triage
cases reduced full serialized input by 21.11% and 21.82% after passing their
evidence checks, while its two literal-search cases reduced input only about
2.3% (screen `docs/evals/wrench-local-acceptability/synthetic-context-token-reduction-screen-01.md:L20-L48`).
These tiny exposed fixture results are tokenizer-only design evidence, not
utility or frontier savings; that screen failed overall and reported zero
frontier pairs (`docs/evals/wrench-local-acceptability/synthetic-context-token-reduction-screen-01.md:L50-L60`).
The separate local SLM diagnostics accepted no generative class, including
failing-log triage, so this recommendation is for deterministic evidence
selection only, not local model answers (`docs/reports/wrench-local-acceptability/local-slm-run-02.md:L7-L30`).

## Existing harness fit

**No existing end-to-end harness can measure this family on a fresh fixture
without changing its fixture binding.** The Qwen challenge runner pins the
exposed `e0_synthetic_matched_tasks_v1` manifest and hash and hard-codes its
case prompts (`tools/run_local_synthetic_challenge.py:L22-L30,L81-L85`). The
token-reduction runner likewise fixes that manifest, challenge source, and
tokenizer path (`tools/measure_synthetic_context_token_reduction.py:L41-L61`).
The exact read/search evaluator pins the same manifest (`tools/measure_local_task_acceptability.py:L28-L42`).
The paired frontier reporter only validates and aggregates caller-supplied,
complete receipts; it is not a task or receipt producer
(`tools/report_paired_frontier_savings.py:L1-L11`).

Thus existing reports establish mechanics for bounded reads/searches and
context-selection mechanics, but do not measure a new held-out log-triage
family end-to-end. The North Star experiment calls for failing-test/log triage,
large required hot regions, stale/missing evidence and multiple
repositories/languages (`docs/northstar/V2_EXPERIMENT.md:L55-L65`).

## Next step and limits

Before measurement, separately authorize and preregister a fresh, independently
reviewed synthetic fixture family with frozen log/source hashes, exact evidence
and abstention oracles, and a context-size range large enough to test reduction.
Then parameterize a no-training offline harness to load that fixture and record
per-case complete serialized input tokens, evidence coverage, abstentions,
failures, latency, and resources. Keep exposed fixtures out of scoring. A
local-tokenizer reduction would remain only a proxy: paid frontier savings
require later matched downstream receipts with a pinned client/model/token
convention and complete lifecycle accounting. Current matched frontier pairs
are zero (`docs/evals/wrench-local-acceptability/frontier-token-readiness.md:L7-L24,L34-L39`).

Repository state at inspection was `git status --short`: modified
`src/wrench_harness/e0_context_pipeline.py`; untracked `tests/test_local_synthetic_challenge_runner.py`
and `uv.lock`. This report is the only path changed for this assignment; no
tests or benchmarks were run.
