# Iteration 226: separate token efficiency from verified utility

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-ITER226-UTILITY-GATED-SAVINGS-20260930-01`  
Scope: source and protocol audit only; no tokenizer, model, provider or SubRoute calls.

## Decision

Wrench should report token reduction and task utility as separate, jointly required outcomes. A smaller token count from an abstention, failed answer, missing pair, or truncated run is not evidence of useful savings. Do not combine the percentages into one score or let a strong efficiency result compensate for lower verified completion.

## Evidence reviewed

- Iteration 217 reports a 95.6580% local full-lifecycle token reduction on one repeatedly used synthetic `retry-function` task. Iteration 218 correctly excludes it from the diverse pilot because its retrieval policy had been shaped by repeated observations of that same task.
- Iteration 219's corrected query-only screen ran on 12 authored synthetic episodes: 3,461 full-context versus 4,027 prepared input token IDs, a 16.35% increase. All 20 evidence quotes were visible. This measured tokenizer input only, with no generated output or task outcomes.
- Iteration 220's first stress screen used 12/12 full-context fallbacks after E0 admission failures. It measured 369,817 input IDs in both arms and credited 0% reduction. Iteration 223 wired the 65,536 source-ingestion limit into the screen, but explicitly did not rerun it. The next screen remains gated by goal identity.
- The frozen Iteration 219 model runner records each arm attempt's actual model-tokenizer input and output IDs, latency, verifier result, retry and recovery action. It aggregates all attempts, keeps the planned 12-episode denominator, and leaves frontier tokens and billed cost null. It is provider-free local-model instrumentation, not frontier-use evidence.
- The older `examples/gateway_context_mvp/run_demo.py` is not the current measurement harness; its result structure reports prompt input tokens only. Do not use it to support full-lifecycle savings.

## Required reporting contract

For each arm and each preregistered episode, define local model tokens as the sum of actual input IDs plus generated output IDs across every attempt. For a future frontier arm, define frontier tokens from the provider response's actual input/output usage across every request, including retries, recovery, cache misses, failed requests with usage, and verification-driven re-prompts. Never infer provider tokens from local tokenizer estimates.

Report these independently over the complete frozen denominator:

1. **Verified completion:** episodes passing the exact predeclared deterministic oracle, with failures, abstentions, timeouts, incomplete pairs and rescue shown explicitly.
2. **Success retention:** prepared/hybrid verified episodes divided by frontier-only verified episodes, with both raw counts and uncertainty. Also show absolute verified completion per arm.
3. **Token use:** total actual tokens by arm and lifecycle phase, with failures and retries included. Report the token-reduction ratio only beside the paired success results.
4. **Utility-conditioned efficiency:** among episodes where both arms pass their frozen oracle, show paired token deltas as a secondary diagnostic. This subset must never replace the all-episode token and outcome denominators.
5. **All-in cost and time:** include measured provider billing and cache treatment, local compute/energy, inference and verification latency, compaction, recovery, training amortization, and human/operator time. Unknown quantities remain null; tokenizer counts are not cost.

A run can be called *complete* when the preregistered measurement finished with all pairs accounted for. That status does not mean the tasks passed or any acceptance threshold was met. An incomplete pair or missing receipt remains visible in the denominator and cannot receive savings credit.

## Current result and next gate

No new efficacy result is produced by this review. The highest prior local token-reduction figure is a single repeatedly observed synthetic task; the 12-task input-only result increased tokens, and the 12-task noisy screen previously fell back with zero reduction. Those results do not estimate representative performance or frontier savings.

Iteration 220's corrected tokenizer-only screen may proceed only after the declared gateway goal identity is reconciled by the owner. Preserve the frozen manifest, query-only retrieval, current implementation hashes and the fail-closed preflight. If the screen passes, its claim remains local input-token reduction only. Local-model generation, task completion, Frontier usage and all-in cost require their own separately admitted paired study.

## Gate status

- Active heartbeat gateway goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`.
- On-disk `docs/goal/wrench-gateway-model-research/GOAL.md` SHA-256 observed in this review: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`.
- Identity mismatch remains unresolved. No model load or inference was attempted.
- The final held-out split remains sealed. No provider request, credential access, training, candidate activation or SubRoute modification occurred.

