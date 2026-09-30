# Iteration 229: refresh the 2B versus 4B candidate decision

Date: 2026-09-30 (America/Edmonton)
Job ID: `WRENCH-ITER229-2B-VS-4B-OFFICIAL-EVIDENCE-REFRESH-20260930-01`
Scope: primary-source model-card and pinned-inventory review; no download, inference, training, or provider call.

## Decision

Keep **Qwen3.5-2B as the first Wrench controller candidate to test**, with a Wrench LoRA limited to bounded evidence/context proposals. Treat Qwen3.5-4B as the coding/tool-use challenger if the product instead needs one local model to author code. This is a role-based experiment order, not a claim that 2B is a proven overall winner.

The new official evidence supports the 2B candidate's size and fine-tuning rationale, but does not give it a direct coding benchmark result comparable to 4B. The 4B card reports stronger coding and agent benchmarks, but those vendor scores do not establish local Wrench utility or training fit.

## Pinned artifacts and license

The 2B official repository is pinned at revision `15852e8c16360a2fea060d615a32b45270f8a8fc`. Its official model API inventories 13 files, `2,274,069,824` BF16 parameter bytes, and `4,571,274,023` total storage bytes. The model card labels the license Apache-2.0 and states task-specific fine-tuning as an intended use. The `Qwen3.5-2B-Base` card additionally documents efficient LoRA-style PEFT with the official chat template. These establish a compatible research path, not Wrench's exact Transformers/PEFT runtime or LoRA fit.

The local research inventory pins Qwen3.5-4B at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 14 files, `9,342,907,469` bytes. Its card is also Apache-2.0; the 4B base card documents LoRA-style PEFT. Both are inside the owner's below-10B model-size authority, subject to exact runtime and storage admission.

## What the official scores do and do not say

- The 2B model card reports BFCL-V4 `43.6` and TAU2-Bench `48.8`; its paired 0.8B column reports `25.3` and `11.6`. It does not show a LiveCodeBench score for 2B in that table.
- The 4B model card reports LiveCodeBench v6 `55.8`, BFCL-V4 `50.3`, and TAU2-Bench `79.9`.
- These are model-vendor scores, not results from one Wrench harness. The cards present different comparison tables and experimental settings, so do not subtract them as a causal size effect. They do support a practical distinction: 2B is plausible for extractive controller work; 4B is a stronger coding/tool-use challenger on published vendor metrics.
- The official 2B Base documentation's LoRA claim and external Squeez extraction result support feasibility of a 2B LoRA experiment. Neither proves Wrench-specific LoRA behavior, exact-evidence retention on coding repositories, 95% task completion, or all-in savings.

## Hardware and experiment implication

2B's pinned weights are about half the bytes of the existing 4B BF16 snapshot. This increases the 2B candidate's hardware margin on the RTX 5060 Ti, but file size alone is not runtime admission: multimodal/runtime overhead, working context/KV cache, activation memory and LoRA optimizer state still need exact measurement. The fresh host was above the general 10% RAM/VRAM floor, but below the 25% Fit-03 training start gate in the last confirmed RAM sample; remeasure before any run.

The 0.8B direct CUDA coding smoke failed syntax verification and took 65.233 seconds. This is one failed code-writing episode, not evidence that a 2B bounded controller will fail. Conversely, the official card is not evidence that the 2B controller can work all day. Keep mechanical context parsing, tokenization, provenance, compaction, deterministic verification and recovery in code; let a LoRA propose only bounded decisions.

## Next decision gate

No model size is promoted from provisional research lead to selected Wrench candidate until the same frozen, answer-blind battery compares deterministic-only, 0.8B control, 2B LoRA, and 4B challenger where each passes exact runtime/resource admission. Start with the 2B LoRA arm only after its package and data identities are independently reviewed, the active-goal hash is reconciled, and peak storage/RAM/VRAM are admitted. If 2B has a named measured capacity failure, compare 4B on the same episodes. Keep final held-out data sealed.

Active goal identity remains unresolved: on-disk SHA-256 `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`; heartbeat-declared SHA-256 `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`. No local model work was started. No frontier, SubRoute, or advisor completion request was sent. The campaign remains without a numeric spend cap, and this report grants no spending authority.

## Primary sources

- [Pinned Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- [Pinned Qwen3.5-2B inventory API](https://huggingface.co/api/models/Qwen/Qwen3.5-2B?blobs=true&revision=15852e8c16360a2fea060d615a32b45270f8a8fc)
- [Qwen3.5-2B license](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/LICENSE)
- [Qwen3.5-2B-Base fine-tuning and LoRA notes](https://huggingface.co/Qwen/Qwen3.5-2B-Base)
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Qwen3.5-4B-Base fine-tuning and LoRA notes](https://huggingface.co/Qwen/Qwen3.5-4B-Base)
- [Wrench's pinned 4B inventory and size decision](model-size-decision-20260928.md)
- [Wrench's 0.8B CUDA coding smoke](../../evals/wrench-gateway-model-research/iteration-106-qwen35-08b-cuda-coding-smoke-20260928.md)
