# Model-size decision refresh: local evidence and role fit

Date: 2026-09-28 (America/Edmonton)  
Purpose: refresh the 0.5B-12B research decision against the active goal and Iteration 142; no model execution or training admission  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Recommendation

For a **bounded learned Wrench context controller**, Qwen3.5-2B remains the
strongest research candidate to compare next with the local 0.8B control. This
is a candidate ranking, not a selection backed by a local head-to-head. The
2B has the best located task-matched LoRA evidence for pruning coding-agent
tool observations, and Qwen's own same-family tool and long-context scores
show a clear 0.8B-to-2B increase. It is not proven to fit this host, train
successfully here, improve Wrench outcomes, save 95% of frontier tokens, or
work as a coding agent all day.

Keep two roles separate:

- **Wrench controller:** deterministic code owns parsing, retrieval, source
  identity, tool allowlists, token accounting, validation and recovery. A
  small LoRA may propose bounded context or route choices. The next comparison
  should be 0.8B versus 2B plus a deterministic-only arm on identical,
  answer-blind tasks.
- **Coding worker:** the local evidence does not identify an all-day winner
  below 12B. Qwen3.5-4B and 9B, plus Gemma 4 12B as a research-only upper
  bound, have stronger vendor coding scores than the 0.8B/2B controller
  evidence, but no Wrench paired engineering or sustained-host result.

The **overall decision confidence is low to moderate for experiment
prioritization and low for product selection**. If the owner requires one
working hypothesis today, use 2B for the LoRA controller, retain 0.8B as the
small control, and keep the coding worker as a separately measured role. Do
not promote this into a final winner until the common Wrench battery and exact
runtime gates are complete.

## New local evidence since the prior decision

The prior [model-size decision](model-size-decision-20260928.md) recommended
2B primarily from external task-specific evidence. Iteration 142 now adds
answer-blind, same-model local results for three synthetic lookup cases. The
0.8B model used no adapter; the two paired runs completed in about 43 seconds
each, with minimum sampled RAM free of 13.38% and 13.62% and VRAM free above
75%.

| Wrench context strategy | Verified by local 0.8B | Target-tokenizer input reduction | Interpretation |
|---|---:|---:|---|
| Exact code symbol spans, Iteration 140 | 3/3 | 92.123% (1,520 / 19,297 tokens) | Best current answer-blind local result; only three synthetic cases. |
| Required TOML table spans, Iteration 142 R2 | 3/3 | 91.515% (1,637 / 19,297 tokens) | Same tiny task set; less saving than symbol spans. |
| Required TOML assignment lines, Iteration 142 | 1/3 | 89.403% (2,045 / 19,297 tokens) | All cited quotes remained visible, but two answers reversed/misassociated values. |

This changes the engineering decision: keep the assignment-line TOML path
opt-in and disabled in the demo runner. Its quote-preservation check was not
enough to preserve field relationships. The table strategy's 3/3 observation
does not prove general quality and did not improve token count over symbol
spans. These are target-tokenizer prompt-input reductions, not frontier calls
avoided, full-lifecycle savings, or utility evidence. The 95% frontier-token
claim remains **unmeasured**.

The detailed paired receipts and source hashes are in [Iteration 142](../../evals/wrench-gateway-model-research/iteration-142-config-span-quality-20260928.md).

## Evidence-ranked candidates

| Size and candidate | Evidence that favors it | Evidence against promotion | Current role |
|---|---|---|---|
| 0.5B-0.8B, Qwen3.5-0.8B | Smallest available comparison; latest local answer-blind symbol/table variants passed 3/3 on the same three lookups. Existing complete pinned training snapshot and local CUDA path are known. | Individual-key context fell to 1/3. Earlier general semantic screen was 0/10. The local samples cover exact lookups only. No LoRA exists. Latest run's 13.38% minimum free RAM leaves little serving margin. | Control and deterministic-mechanics baseline, not the selected controller or an all-day coder. |
| **2B, Qwen3.5-2B** | Qwen's card reports BFCL-V4 43.6, TAU2 48.8 and LongBench v2 38.7 versus 0.8B's 25.3, 11.6 and 26.1. Squeez fine-tunes this exact family/size with LoRA; on 618 manually curated tool observations it reports 0.86 recall, 0.80 F1 and 92% observation-input reduction. Pinned upstream inventory has 2,274,069,824 parameters and 4,571,274,023 bytes across 13 files. | The card scores are vendor-reported and do not measure Wrench coding. Squeez measures one observation, not downstream task completion or full agent loops. The 2B tree is not present in the local HF cache observed for this refresh. Local CUDA/LoRA fit, end-to-end quality and 95% savings are unmeasured. | **First LoRA-controller challenger** after common task protocol and exact package/runtime admission. |
| 4B, Qwen3-4B / Paritok | Closest located task-linked compression test: on 300 SWE-bench Lite tasks, line-numbered Paritok retained 27.8% of context and solved 109/300 versus 122/300 uncompressed. | The paired quality-retention interval is [79.2%, 100%]; p=.079 is not proof of non-inferiority at 95%. Training used an H100 80GB, deployment reports target a 24GB GPU. This is Qwen3-4B, not Qwen3.5-4B or Wrench. | Compression challenger only after a named 2B capacity failure; no host training admission. |
| 4B, Qwen3.5-4B | Official card reports LiveCodeBench v6 55.8, BFCL-V4 50.3 and TAU2 79.9. A pinned BF16 tree of 9,342,907,469 bytes is inventoried. | The installed Q4 Docker route lacks a usable GPU path; that does not test host CUDA. BF16 inventory size is not peak VRAM. No common-task, Wrench LoRA or all-day result. | Plausible local coding-worker challenger after exact runtime admission, not evidence for controller size. |
| 9B, Qwen3.5-9B | Official card reports LiveCodeBench v6 65.6, BFCL-V4 66.1 and TAU2 79.1, higher than Qwen3.5-4B on some rows. | The upstream tree is 19.3 GB in the current card, larger than the GPU's 16,311 MiB VRAM before runtime state. No admitted quantized package or host test. | Research ceiling; serving/training require a separately inventoried quantization and measured admission. |
| 11.95B, Gemma 4 12B Unified | Google's current card reports LiveCodeBench v6 72.0 and Tau2 average 69.0; the card lists Apache 2.0. | Near the top of the research band and above the currently authorized sub-10B training range. No pinned local inventory, Wrench adapter, common-harness run or hardware admission. Vendor scores are not comparable head-to-head with Qwen. | Research-only upper bound unless execution authority is separately expanded. |

Vendor benchmarks above use different prompts, decoding, benchmark versions
and model families. They rank research candidates only. In particular,
LiveCodeBench coding scores for 4B/9B/12B do not establish that those sizes
are better context controllers; BFCL and TAU2 do not establish autonomous
repository engineering.

## Why the candidate is not final

The evidence currently supports two different statements:

1. **The 0.8B can perform a tiny, known mechanical lookup when Wrench supplies
   source-shaped context.** Iteration 140 and the table-span arm both passed
   three cases, but that workload cannot distinguish model-size capacity.
2. **A 2B LoRA is the strongest externally supported size for learned coding
   tool-output pruning.** Squeez is closely task-aligned but measures span
   recall/F1 on a single observation. It does not prove Wrench's outcome or
   the user's 95% gate.

There is no paired 0.8B-versus-2B Wrench run, no trained Wrench LoRA, and no
frontier-only task pair. The most credible next selector is therefore an
answer-blind development battery that contains tool-output extraction,
configuration relationship lookups, changed-code/diff preservation, stale
source recovery, and a small mechanical edit with deterministic tests. Freeze
cases before model runs. Compare deterministic-only, base 0.8B, and base 2B
under the same exact context, decoding, output schema, timeout and verifier;
then compare 2B plus a Wrench LoRA only after training admission. Keep the
held-out split unopened until the development choice is frozen.

## Current blockers and boundaries

- Current RAM sample: 6,430,140 KiB free of 33,486,624 KiB (19.20%); RTX
  5060 Ti VRAM free: 15,251 / 16,311 MiB. This permits documentation work and
  exceeds the general 10% floor, but not Fit-03's 25% free-RAM start gate.
- The current HF cache has the Qwen3.5-0.8B snapshot; the pinned Qwen3.5-2B
  inventory is not present there. No model was downloaded or loaded in this
  refresh.
- Fit-03's prior exact-goal review is stale because the active goal hash is now
  `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`. Obtain
  a fresh exact-hash package review before any fit, then meet the separate 25%
  RAM start gate and every storage/peak-memory condition.
- SubRoute at `127.0.0.1:4000` remains force-routed to OpenRouter without a
  numeric campaign spend cap. No provider call, credentials, endpoint setting,
  held-out data or adapter activation was touched.
- Storage status, including the Docker WSL model volume and automation root,
  reported 15,434,739,174 actual bytes and 7,103,000 active reserved bytes,
  within the strict 50 GB aggregate ceiling. C: had 139,309,588,480 bytes
  free.

## Sources

- Qwen model-card comparison and exact 2B pin: [Qwen3.5-2B at pinned revision](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- Qwen 4B pinned card and inventory: [Qwen3.5-4B at revision 851bf6e](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)
- Qwen 9B model card and file inventory: [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)
- Direct LoRA tool-output pruning evidence: [Squeez paper](https://arxiv.org/abs/2604.04979)
- Paired coding-task compression evidence and intervals: [Paritok-4B paper](https://arxiv.org/abs/2608.24188)
- 12B coding/tool scores and license: [Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- Local matched observations: [Iteration 140](../../evals/wrench-gateway-model-research/iteration-140-exact-symbol-span-paired-20260928.md) and [Iteration 142](../../evals/wrench-gateway-model-research/iteration-142-config-span-quality-20260928.md)

## Next action

Prepare and independently review the answer-blind 0.8B/2B common development
battery and exact 2B runtime package. Do not download or run either candidate
until complete model identity, destination/headroom, peak-memory estimate,
storage reservation, and current resource guards are admitted. The selected
model-size recommendation remains provisional; the 95% product claims remain
unproven.
