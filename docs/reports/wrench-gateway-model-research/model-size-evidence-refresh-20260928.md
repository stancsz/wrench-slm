# Model-size evidence refresh: 0.5B to 12B

Date: 2026-09-28  
Scope: research prioritization for Wrench v2, not model/runtime/training admission  
Repository HEAD reviewed: `af01304824f079a64b6c3902397a2034b843511a`  
Active gateway goal before this refresh: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Decision

Keep **Qwen3.5-2B plus a Wrench-specific LoRA** as the first controller candidate. It is the smallest candidate in this comparison with direct, task-specific LoRA evidence for extracting useful information from tool output, and it has a pinned local inventory. That evidence is component-level only: it does not establish downstream coding success, the Wrench policy, sustained local execution, or the 95% product targets.

Add **Qwen3-4B-Instruct-2507 with the Paritok-style workflow** as the strongest nearby compression challenger and design reference. Its paper measures paired downstream SWE-bench Lite outcomes after intent-conditioned context compression, which is closer to Wrench than isolated observation labeling. However, the measured quality interval is too wide to establish 95% retention, the observed solved count decreased from 122/300 to 109/300 in the line-numbered comparison, and its reported training/deployment setup does not establish fit on this host's 16 GB GPU. This does not displace 2B as the first Wrench experiment.

The recommendation is role-specific. If Wrench is allowed to select different sizes for distinct bounded proposals, compare 2B for evidence selection/routing with a 4B compression challenger only after naming a 2B failure. If one model must itself do open-ended all-day repository engineering, **no model from 0.5B to 12B is proven** by the available evidence.

## Evidence comparison

| Size / candidate | Most relevant evidence | What it establishes | What remains unproven |
|---|---|---|---|
| 0.5B-0.8B Qwen3.5 | Wrench's prior general semantic screen failed; 0.8B synthetic LoRA diagnostic is staged but not run. | Retain as a low-cost control. A prior general-model failure does not reject a trained finite-action policy. | Useful Wrench policy, coding success, sustained engineering, savings. |
| **2B Qwen3.5** | Squeez reports a task-specific LoRA removing 92% of individual tool-observation input tokens on 618 manually reviewed observations, recall 0.86 and tolerant F1 0.80. Same-family benchmark scores exceed the 0.8B model. Wrench already has a pinned 2B tree. | Strongest small-model evidence for the proposed evidence-selection component; supports prioritizing 2B for the first controller experiment. | Squeez did not test full agent trajectories or downstream completion. Its scores and 92% component reduction are not Wrench results or frontier-token savings. |
| **4B Qwen3-4B-Instruct-2507 / Paritok** | Intent-conditioned extractive compressor evaluated on 300 SWE-bench Lite tasks. Line-numbered context was 27.8% of raw size; solved tasks were 122/300 uncompressed and 109/300 compressed; discordant pairs were 30 versus 17, McNemar p=.079, paired quality-retention interval [79.2%, 100%]. | Best located end-to-end task-linked compression comparator and useful design reference for typed intent, extractive preservation, and recovery. | Does not establish the required >=95% retained success. The interval is broad, compression can lose target identifiers, and the paper's no-retrieval evaluation omits Wrench's recovery loop. Reported training used one H100 80GB with BF16, 16K context, LoRA r32, 8-bit AdamW and gradient checkpointing; paper deployment assumes 24GB GPU. No 16GB-host fit is demonstrated. |
| 4B Qwen3.5 | Higher vendor coding/tool benchmarks than smaller Qwen3.5 variants; a pinned BF16 tree is known. | A reasonable hardware/runtime capacity challenger after exact package review. | Different base than Paritok; no Wrench LoRA result, admitted local fit, or paired coding outcomes. Do not transfer Paritok results to it. |
| 9B Qwen3.5 | Higher vendor coding/tool benchmarks. | Research ceiling for a local coding-worker comparison. | No Wrench task quality, all-day reliability, or local sustained-fit evidence. |
| 12B Gemma 4 | Vendor reports stronger coding benchmark results than its smaller family variants. | Upper-bound research comparator. | No pinned local inventory, Wrench adapter, runtime admission, or common-harness result. The existing staged training authority does not extend to 10B-12B. |

## Savings evidence and interpretation

The largest measured Wrench prompt-input reduction is the synthetic E0 context demo in Iteration 098: 86.4327% pooled (19,289 to 2,617 tokens), with all 7 required quotes visible. The cases contain 240 repetitive synthetic health-log lines and no real coding outcomes. The installed OpenCode read-tool cycle in Iteration 101 reached 42.2967% over two requests; its one-request, no-tool-needed upper-bound slice reached 42.5735% in Iteration 100. An earlier five-pair context-selection screen measured 12.11% and recorded two positive evidence-selection errors. These are distinct target-tokenizer input measurements on synthetic fixtures, not frontier tokens avoided, verified task success, or full-lifecycle savings.

The external Squeez 92% figure applies to an individual tool observation. Paritok's context-ratio figure applies to the evaluated input context. Neither can be added to schema-filter savings or projected to 95% total frontier-token savings. StateComp's coding slice and other long-horizon results support further state/context experiments, but do not prove the Wrench result. For every Wrench claim, use paired episode totals and count every remote continuation, retry, verification, compaction, recovery fetch, cache miss, and human rescue.

## Ranked research path

1. Keep deterministic parsing, source validation, exact retrieval, bounded context compilation, provenance, recovery, and permission decisions in code.
2. Resume and verify the existing stable-source E0 path. Measure source-only, transcript, and stateful-context arms on frozen paired coding episodes with a pinned tokenizer and correctness outcomes.
3. Keep 0.8B as a control; test the 2B Wrench LoRA against deterministic-only on approved train/dev material. Preserve the final split as sealed.
4. Introduce a 4B compression candidate only for a measured 2B capacity failure; require pinned full inventory, rights/runtime review, exact peak-memory accounting, safe storage admission, and host fit before any download or fit.
5. Progressively narrow tool profiles on representative episodes and select the highest reduction whose preregistered correctness bound passes. Do not optimize the synthetic no-tool upper bound as if it were useful engineering.
6. Keep the full acceptance gates: >=95% verified local completion without frontier calls, <=5% frontier-routed episodes, >=95% of frontier-only success retained, >=95% fewer total frontier tokens, >=95% lower all-in cost, and reliable sustained engineering. None is currently proven.

## Sources

- Squeez: [paper](https://arxiv.org/html/2604.04979)
- Paritok-4B: [paper](https://arxiv.org/abs/2608.24188), [HTML](https://arxiv.org/html/2608.24188), [official repository](https://github.com/Paritok-official/paritok-4b-v1)
- Pinned Qwen3.5-2B model card: [Hugging Face revision](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- Pinned Qwen3.5-9B model card: [Hugging Face revision](https://huggingface.co/Qwen/Qwen3.5-9B/blob/cc5442c03a5c0bff0bd4c6888d9a40029c637733/README.md)
- Gemma 4: [Google model card](https://ai.google.dev/gemma/docs/core/model_card_4)
- Wrench's request-shaping and context measurements: Iterations 098, 100 and 101 under `docs/evals/wrench-gateway-model-research/`.

## Admission

This is a documentation-only research decision. No model was downloaded, loaded, trained, benchmarked, or routed; no provider request was sent; and the held-out split was not opened. It does not authorize training or activation. The Fit-03 review is bound to the pre-refresh goal hash and must be refreshed if the goal file changes.
