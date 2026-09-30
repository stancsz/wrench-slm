# Iteration 158: same-runner Qwen3.5-2B vs 4B common battery

Date: 2026-09-28 (America/Edmonton)  
Assignments: `WRENCH-QWEN35-4B-COMMON-BATTERY-ITER157-20260928` and `WRENCH-QWEN35-2B-COMMON-BATTERY-ITER158-20260928`  
Status: **Both models passed full, E0, and answer-blind related-path context on all three known development cases. Only 4B passed the aggressive related-table arm on all three.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Paired method and scope

The 0.8B result from Iteration 155 and the 2B and 4B runs here used the same
three experimenter-authored development requests, source fixture, answer-blind
path manifest, compact JSON segment rendering, context budget, verifier, and
runner/source hashes. The manifest binds to the Iteration 153 fixture. These
are previously exercised development cases, not a fresh holdout or a
representative repository-engineering benchmark. Each model ran as an untrained
BF16 base with no adapter. No frontier request was made.

The paired runner and relevant Wrench source hashes matched across all three
model receipts. All runs used Python 3.13.15, PyTorch 2.14.0+cu132,
Transformers 5.17.0, CUDA 13.2, and an RTX 5060 Ti. Iterations 157 and 158
loaded Qwen3.5-4B and Qwen3.5-2B with Accelerate 1.15.0 and psutil 7.2.2.
The first 4B launch stopped before model loading because Accelerate was absent;
the dependency was installed in the approved local environment and the same
assignment then completed. This setup failure is retained as an operational
failure, not counted as a task episode.

## Verified task results

| Model | Full fixture | E0 all paths | Answer-blind related paths | Related TOML tables |
|---|---:|---:|---:|---:|
| Qwen3.5-0.8B | 2/3 | 2/3 | 2/3 | 2/3 |
| Qwen3.5-2B | 3/3 | 3/3 | 3/3 | 2/3 |
| Qwen3.5-4B | 3/3 | 3/3 | 3/3 | 3/3 |

The shared failure was `retry-policy` under the related-table arm. Qwen3.5-2B
answered `2,250` instead of `3,250`; the 4B returned `3,250`. The 4B also
passed the other two table cases. The 2B and 4B each passed all three cases
with the less aggressive answer-blind related-path arm. This is one repeat
comparison on a known task, so the 4B result is a promising capacity signal,
not a general accuracy estimate.

## Context and token accounting

Context preparation was deterministic and produced identical inputs for all
three model sizes. The target tokenizer counted 19,297 full-fixture input
tokens, 1,096 related-path tokens, and 977 related-table tokens. Thus the
related-path component proxy is **94.320361%** lower and the table component
proxy is **94.937037%** lower. The table arm remains 12 tokens above the
95% input-proxy threshold.

The model tokenizers counted 26,196 full-fixture input tokens and 536
related-table input tokens. With model outputs included, the 4B table arm used
561 versus 26,221 local-model tokens, a **97.860493% local-model token
reduction**. The comparable 2B table arm used 562 tokens but failed one task.
These local counts and the target-tokenizer component proxy are not measured
Frontier request usage. The runner reports `frontier_calls=0`,
`frontier_token_savings_percent=null`, and `$0` provider spend. Frontier token
savings and routing-rate acceptance therefore remain unmeasured.

## Hardware, runtime, and identity

| Model | Revision | Model load | Three-case matrix | Minimum free RAM / VRAM | Peak CUDA allocated / reserved |
|---|---|---:|---:|---:|---:|
| Qwen3.5-0.8B | `2fc06364715b967f1860aea9cf38778875588b17` | 6.16 s | 62.71 s | 14.44% / 75.26% | prior receipt |
| Qwen3.5-2B | `15852e8c16360a2fea060d615a32b45270f8a8fc` | 14.49 s | 67.40 s | 12.13% / 61.40% | 4.99 / 5.25 GB |
| Qwen3.5-4B | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 31.36 s | 101.23 s | 14.68% / 25.38% | 10.92 / 11.40 GB |

Both new runs completed without OOM, crash, resource-monitor error, or breach
of the required 10% RAM/VRAM floor. The 4B used considerably more VRAM and
took 1.50x as long as 2B on the same three-case matrix. Transformers lacked
`causal_conv1d` and `flash-linear-attention`, so it used slower reference
kernels; no optional kernel packages were installed. These are short-run
feasibility results, not proof of smooth all-day operation or LoRA-training
fit.

4B identity: inventory SHA-256
`30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a`,
snapshot receipt SHA-256
`8ff3a6587850b5bbd68a047f94d8d9dd28fd082a6d23a1f189c216ac2ebc8bd2`.
Its local inventory has 14 files totaling 9,342,907,469 bytes. 2B inventory
SHA-256: `23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`.

## Decision and limitations

For the next **aggressive context-pruning/controller** experiment, prioritize
Qwen3.5-4B: it is the only candidate in this same-runner comparison to retain
all three known answers with the related-table representation. Keep 2B as the
lower-VRAM and faster challenger; it retains 3/3 when related source paths are
used, so the table result alone does not justify treating it as generally
inferior. The decision is low confidence and does not yet account for adapter
training fit, energy, all-in cost, or a broad coding battery. The 0.8B remains
the smallest control, not the current lead.

This evaluation does not show that a LoRA improves either model, that local
agents can complete 95% of a representative workload, that 5% or fewer tasks
need frontier routing, or that frontier tokens/cost fall by 95%. It contains no
code edit, test repair, interruption/recovery, repository switching, or
all-day session. Keep the table strategy opt-in until it passes a fresh,
broader task set; do not use this reused three-case result as held-out evidence.

## Receipts

| Receipt | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-table-iter157-qwen35-4b.json` | 30,212 | `0e90c715a349ee09c42747a256011ff75f5bf70f43773bb00f4f371aeb1b530f` |
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-table-iter158-qwen35-2b.json` | 30,125 | `7b09c3a4791d416aedfa46adc8923bf53e6417ce7f74afec7427ede6b12e8969` |
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter156-qwen35-4b-local-inventory.json` | 2,515 | `30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a` |

No adapter training, held-out access, Frontier call, route change, or credential
access occurred.
