# Model-size decision refresh: Iteration 155 common local battery

Date: 2026-09-28 (America/Edmonton)  
Decision scope: next model-size experiment for the Wrench context controller  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Recommendation

**Keep Qwen3.5-2B as the leading Wrench-controller experiment candidate, with
low confidence.** The Iteration 155 matched local battery gives the first
same-runner comparison against the 0.8B control: 2B completed all three
verified lookups with full or answer-blind related-path context, while 0.8B
failed the retry-policy case even with the full fixture. This is useful
capacity evidence for the context controller on one harder mechanical task.
It is not evidence that 2B is the global model-size winner, that a 2B LoRA
will help, or that either model can code all day.

For an all-day coding worker, there is still **no demonstrated winner** in
the 0.5B-12B research band. The 4B/9B/12B scores and task-linked compression
studies in the previous [size decision](model-size-decision-20260928.md) are
not paired Wrench engineering outcomes or proof of host fit. Keep the worker
question separate from the controller selection.

## New paired evidence

The two candidate runs used the same three frozen synthetic requests,
repository fixture, answer-blind path manifest, target tokenizer, Wrench
context code, compact prompt rendering, and deterministic verifier. Exact
receipts and limits are in [Iteration 155](../../evals/wrench-gateway-model-research/iteration-155-common-battery-qwen08b-vs-2b-20260928.md).

| Comparison | Qwen3.5-0.8B | Qwen3.5-2B |
|---|---:|---:|
| Full-fixture verified | 2/3 | 3/3 |
| E0 all-path verified | 2/3 | 3/3 |
| E0 related-path verified | 2/3 | 3/3 |
| E0 related TOML-table verified | 2/3 | 2/3 |
| Related-path target-tokenizer input | 1,096 / 19,297 | 1,096 / 19,297 |
| Related-table target-tokenizer input | 977 / 19,297 | 977 / 19,297 |
| Minimum RAM / VRAM free during run | 14.44% / 75.26% | 11.75% / 61.42% |
| End-to-end three-case run time | 62.71 s | 63.55 s |

The 0.8B answered the retry-policy question with `250, 4000` under every
context arm, instead of `3,250`. The 2B returned `3,250` with the full, E0,
and related-path contexts, but returned `2,250` under table-only pruning.
Both passed the session and function cases. The table-only context strategy
is therefore rejected for this workload, despite its lower local-model token
count. It also missed the 95% target-tokenizer input proxy at 94.94%.

The 2B fit the inference run within the required 10% runtime resource reserve,
but its minimum RAM margin was only 1.75 percentage points above the floor.
This does not establish LoRA training fit. Neither run used an adapter.
All tasks are previously exercised synthetic lookups, so results are low
confidence and not a product-utility estimate.

## Candidate ranking and evidence quality

| Size band | Current evidence | Decision for the Wrench controller | Decision for an all-day coding worker |
|---|---|---|---|
| 0.5B-0.8B | Small footprint; 0.8B is locally runnable, but Iteration 155 missed one of three requests even with full context. | Keep as the small control; do not choose it solely for lower memory. | No evidence. |
| **2B** | Stronger tool-use and long-context vendor scores than 0.8B; task-linked pruning literature; now 3/3 with full and related-path Wrench context versus 2/3 for 0.8B on the same three tasks. No LoRA. | **Lead candidate to train and compare after exact package, data, storage, and training-fit review.** | No evidence of sustained coding. |
| 4B | Better vendor coding/tool scores than 2B in the prior refresh; on-host Q4 Docker path lacks GPU and is not a valid CUDA test. | Challenger only if 2B fails broader controller capacity or quality tests. | Worth an exact local runtime and coding battery if its pinned files and peak memory pass admission. |
| 9B | Stronger vendor coding scores; published BF16 tree exceeds physical VRAM before runtime state. No admitted quantized artifact or host test. | Research only until exact quantization, storage, and hardware gates pass. | Candidate hypothesis only; no local evidence. |
| 10B-12B | Strong public coding scores for Gemma 4 12B, but outside current <10B training authorization and no host package or Wrench trial. | Research only; do not train under current scope. | Research-only upper bound. |

The external evidence and its limitations are summarized in the earlier
[Iteration 143 evidence refresh](model-size-decision-refresh-iter143-20260928.md).
Vendor benchmark numbers are not comparable across families, and none is a
substitute for the paired result above.

## Decision and next gates

1. **Experiment-priority choice:** use Qwen3.5-2B as the leading bounded
   controller candidate; retain 0.8B as the control. Confidence is low because
   the local comparison has only three non-independent synthetic cases.
2. **LoRA:** no candidate has a trained Wrench adapter. The next training
   package must name the exact base/tokenizer/runtime, reviewed train/dev
   examples, split and rights hashes, target modules, rank, optimizer state,
   checkpoint duplication peak, timeout, and output ceiling. Get an
   independent review against the current goal hash, then measure actual
   training peak RAM/VRAM before fitting. Keep base, installed core and heldout
   data unchanged; leave any candidate inactive.
3. **95% savings:** no frontier call occurred in either run. The 94.32%-94.94%
   figures are prompt-input proxies only. The 95% Frontier-token and all-in
   cost claims remain unmeasured and cannot be inferred from local token
   counts.
4. **Engineering worker:** run a broader answer-blind battery with code
   changes, tests, interrupted tasks and recovery before considering larger
   models. Preserve the full acceptance scope and report every failure.

No model download, training, heldout access, provider call, route change, or
adapter activation occurred in this decision update.
