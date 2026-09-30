# Iteration 219: repair the diverse pilot's no-op tasks

Date: 2026-09-29 (America/Edmonton)  
Static review job: `WRENCH-CODETASK-ITER219-STATIC-FIX-20260930-01`  
Nonce: `e95ba433-18b9-4f20-b7c3-aa8df4603266`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat-declared gateway goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch remains open)

## Static finding before any model run

Iteration 218 froze 12 synthetic tasks, but all three tasks labeled `bounded_code_repair` already passed their own stated behavior cases without a code change:

- `api-02`: the initial `retry_delay` already clamps negative attempts and the configured maximum.
- `cache-02`: the initial `bounded_ttl` already clamps to both configured bounds.
- `batch-02`: the initial `bounded_batch_size` already clamps to the stated minimum and maximum.

Running that pilot would have mistaken copying correct code for repair capability. No model inference used the Iteration 218 fixture; its original manifest and protocol are preserved unchanged as an unexecuted, rejected-before-run design.

## Corrected manifest and preflight contract

`examples/gateway_context_mvp/iteration219_diverse_pilot_manifest.json` retains 12 episodes across three fictional repositories and four task families. The three repair tasks now start from failing behavior or an incompatible signature: retry cap/negative-attempt handling, TTL upper-bound handling, and quantum-normalized batch sizing. The diagnosis tasks compare incident reports with exact test, implementation, and configuration evidence.

Added `src/wrench_harness/gateway_pilot_contracts.py` to:

1. Validate repository/task/family counts, unique IDs, safe relative paths, rendered query templates, source-backed evidence quotes, and supported oracle schemas.
2. Execute only a single parsed candidate function inside an empty-builtins namespace with a small arithmetic and `min`/`max` AST allowlist.
3. Reject a code-repair episode before inference when its initial fixture already passes every declared case.
4. Check exact JSON values, required evidence/answer terms, and bounded function behavior while retaining per-case failures.

Added `examples/gateway_context_mvp/run_diverse_local_pilot_iter219.py` as the paired local runner. It uses the pinned Qwen3.5-4B BF16 snapshot without LoRA, prepares full and E0/Wrench contexts from the same frozen fixture, alternates arm order from the nonce, permits one predeclared retry with a full-context recovery fetch for the Wrench arm, and records every attempt's actual model-tokenizer input/output IDs, latency, verification, prompt/answer hashes, resources and source identities. It requires a caller-provided live storage reservation ID, checks C: free space, rechecks goal and storage admission between repository groups, runs offline, and blocks Python socket connects. The active-goal hash check precedes imports of Torch and model loading.

The Iteration 218 manifest is intentionally used in a negative regression: it must fail preflight with `code_repair_task_is_noop_on_initial_fixture`. The Iteration 219 manifest must pass preflight and all three proposed repairs must satisfy their frozen cases.

## Verification

Focused regressions: `tests/test_gateway_pilot_contracts_iter219.py` and `tests/test_diverse_runner_preflight_iter219.py`, **11 passed**. `git diff --check` completed without errors; it emitted only existing line-ending warnings for unrelated dirty files. A real preflight probe against the current files returned `active_goal_identity_mismatch` with `model_load_started=False`, as intended.

The focused test covers balanced manifest validation, no-op rejection of Iteration 218, corrected code-task behavior, rejection of unsafe AST and a negative-attempt regression, evidence terms and exact quotes, and strict JSON equality. It is contract-level verification only, not a model run or task-success result.

## Frozen artifact identities

- Iteration 219 manifest: `6c49b5a12d18176fd0dd2c1837b861bfd4bdbedd402fd3ed6861516d227548fa`.
- Contract implementation: `f4b687a80abd5b01444f8e27c2181260c8ba9dde0b63f9230aaecb3dfd352371`.
- Focused regression file: `c85f3e681b42d72b39b5df7a3b83b36a2aae65ddf2deb5bd61008a2b7b6d6eac`.
- Paired runner: `de3fcac7ce39a1964883c57bd3971d401024b0acd5b98e175977732254b51946`.
- Runner preflight regression file: `8fffb6c1af0bc958f027dbbf4bca31fd45d04a0e377eaa8ffa9cb4b4bb18d5e9`.
- Iteration 218 manifest preserved as the no-op rejection fixture: `ba39473ac216c7c1a337d7abcbd824d3c9f40e19e1c50a789980f9c09a4d2e79`.

## Scope and remaining gates

No inference, training, provider/SubRoute request, credential read, sealed-split access, or adapter activation occurred. The paired runner is prepared, but no per-arm receipt or model result exists. The declared active goal hash still conflicts with the actual goal file hash, so the runner correctly stops before model load and no hash-bound inference admission is ready. Frontier usage/cost, representative success, the LoRA contribution, model-size winner, and all-day engineering remain unproven.

The next model run requires a separate exact admission: reconcile the goal identity, freeze runner and manifest hashes, verify the pinned local model/runtime and output paths, reserve storage, verify destination headroom and fresh RAM/VRAM, then execute only the bounded provider-free pilot while recording all 12 paired episodes and failures.

## Query-only context preparation dry run (2026-09-30)

A tokenizer-only dry run exercised all 12 frozen Iteration 219 episodes through Wrench E0 context preparation. It used the exact Qwen3.5-4B tokenizer from the pinned local runtime, but did not load model weights or generate output. Every episode was prepared successfully; all 20 source-backed oracle quotes were present in the prepared context, with zero retrieval misses.

The corrected query-only measurement was **3,461 full-context input token IDs versus 4,027 Wrench-prepared input token IDs**, a **16.35% increase** (prepared minus baseline, divided by baseline). Prepared context was larger on each of the 12 episodes. These deliberately small fixtures are dominated by segment and provenance framing. This measures only prompt input IDs for this tokenizer; there are no output IDs, verified task outcomes, frontier requests or billed-cost observations. It is not evidence of frontier-token savings.

An earlier dry run accidentally supplied oracle `required_paths` to retrieval. That exposed answer labels to the context selector and reported an apparent 3,461-to-3,002 reduction. **That result is invalid and withdrawn; it must not be used in any efficacy or savings claim.** The runner now retrieves from the frozen query alone and checks oracle quote visibility only afterward as a diagnostic. Missing quotes remain in the denominator. The first runner probes also found and fixed a byte-tokenizer input issue and a malformed symbol-query route; the final focused tests below pass after these fixes.

This result closes the implementation question of whether the runner can measure query-only preparation without label leakage, but it shows that the current fixtures cannot demonstrate context savings. Do not load the model on this battery. The next pilot revision must add realistic, semantically plausible irrelevant repository and log content, freeze it before scoring, and retain the query-only retrieval boundary. Goal-hash reconciliation remains required before any model load.

Current runner SHA-256: `51ca577da73ea5b4a806acb3807cfda029173bd2eaab01c5775e9a6f4ffbcc76`. Manifest SHA-256 remains `6c49b5a12d18176fd0dd2c1837b861bfd4bdbedd402fd3ed6861516d227548fa`. The paired local model runner has not been executed.
