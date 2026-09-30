# Model-size decision refresh: same-runner Iterations 157-158

Date: 2026-09-28 (America/Edmonton)  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Current recommendation

**Prioritize Qwen3.5-4B for the next aggressive context-pruning controller
experiment, with low confidence.** On the same three previously exercised
development tasks and the same runner/source hashes, 4B retained 3/3 answers
under related TOML-table context; 2B and 0.8B each retained 2/3. Both 2B and
4B retained 3/3 under the less aggressive answer-blind related-path context.
The 4B is therefore the most promising current candidate for testing whether
Wrench can remove more context while preserving answers.

This is an experiment-priority choice, not a validated overall product winner.
4B took 101.23 seconds and peaked at 10.92 GB CUDA allocated, compared with
67.40 seconds and 4.99 GB for 2B. It remained inside the 10% resource reserve,
but uses much more VRAM. 2B remains the resource-efficient fallback and may
prove the better LoRA-training choice after a measured training-fit package.
No candidate has a Wrench-trained LoRA or all-day coding evidence.

## Same-runner evidence

The 0.8B Iteration 155 receipt and the new 2B and 4B receipts share the same
fixture, request hashes, answer-blind manifest, context code, compact renderer,
verifier, and relevant source hashes. The tasks remain a tiny, reused,
experimenter-authored development set, so all pass rates have low confidence.

| Model | Related-path verified | Related-table verified | Related-path local model tokens | Related-table local model tokens | Total matrix seconds | Minimum free RAM / VRAM |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | 2/3 | 2/3 | 698 | 562 | 62.71 | 14.44% / 75.26% |
| Qwen3.5-2B | 3/3 | 2/3 | 694 | 562 | 67.40 | 12.13% / 61.40% |
| Qwen3.5-4B | 3/3 | 3/3 | 694 | 561 | 101.23 | 14.68% / 25.38% |

All three models receive identical Wrench-prepared text, so the context
token-reduction mechanism itself does not improve with parameter count. The
current table representation reduces the target tokenizer's input count from
19,297 to 977 tokens, or 94.937037%, still 12 tokens short of a 95% component
proxy. For 4B the *local model's* input-plus-output count falls from 26,221 to
561 (97.860493%), while the same 4B answers pass. These are local token counts,
not Frontier request usage or savings.

There were zero Frontier requests in all three local runs. Frontier-token
savings, real route rate, provider cost, all-in cost, and frontier-only success
retention remain undefined. The target of 95% full-lifecycle frontier-token
savings remains unproven.

## Decision gates still open

1. Train a Wrench-specific LoRA only after a candidate-specific reviewed
   package, data/split/rights hashes, storage reservation, and measured peak
   training fit are admitted. This decision does not authorize held-out access
   or activation.
2. Expand the answer-blind evaluation to new independent tasks with code edits,
   test execution, interruption, recovery, and repository variation. Do not
   promote the reused three-case set as a holdout.
3. Compare full lifecycle, not prompt proxies: capture actual API request
   contents and provider-returned usage after a hard numeric spend cap is
   established. SubRoute remains forced to OpenRouter; no provider request or
   route change was made in these iterations.
4. Measure energy, latency distribution, failures, retries, human rescue, and
   amortized training cost before making an all-in cost or all-day engineering
   claim.

See the detailed [Iteration 158 paired report](../../evals/wrench-gateway-model-research/iteration-158-common-battery-qwen2b-vs-4b-20260928.md)
for identities, resource measurements, failures, and receipt hashes.
