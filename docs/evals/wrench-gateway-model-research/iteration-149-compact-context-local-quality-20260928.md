# Iteration 149: compact-context local quality comparison

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-COMPACT-CONTEXT-ITER149`  
Status: **2B retained 3/3 answers with typed compact context; 0.8B scored 2/3, including one Wrench-context failure. The new format is not yet safe to adopt across the size range.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question and method

Does the typed `compact_json_segments` format from Iteration 147 preserve
answer quality when actually passed to the 0.8B and 2B local models? This
reuses the exact three answer-blind synthetic lookup tasks, fixture, 64-token
context budget, greedy generation settings and deterministic answer verifier
from the earlier paired model-size experiment. Each model sees full-fixture
and Wrench E0 arms.

The 2B invocation first exited before loading weights because it omitted the
approved Accelerate add-on path. No generation, receipt, or weight load
occurred on that attempt. The same job was retried with the previously
approved `WRENCH_LORA_ADDONS` directory; that run completed. No packages were
installed and no source or held-out data was read.

## Paired results

| Measure | Qwen3.5-0.8B BF16 | Qwen3.5-2B BF16 |
|---|---:|---:|
| Full-fixture verified | 2/3 | 3/3 |
| Wrench compact-context verified | **2/3** | **3/3** |
| Wrench failure | retry-policy: answered `250, 4000`; expected `3,250` | none |
| Target tokenizer input, full → Wrench | 19,297 → 1,162 | 19,297 → 1,162 |
| Target tokenizer input reduction | 93.978339% | 93.978339% |
| Local tokenizer input, full → Wrench | 26,196 → 741 | 26,196 → 741 |
| Local tokenizer input reduction | 97.171324% | 97.171324% |
| Local input + output tokens, full → Wrench | 26,226 → 770 | 26,221 → 766 |
| Local total-token reduction | 97.063982% | 97.078677% |
| Total runtime, including load | 44.0024 s | 50.4081 s |
| Peak CUDA allocated / reserved | 2.678 / 2.890 GB | 4.991 / 5.247 GB |
| Minimum sampled free RAM | 13.97% | 14.04% |
| Minimum sampled free VRAM | 75.07% | 61.35% |

The failed 0.8B Wrench answer had all required source quotes visible. Its
earlier legacy JSON-string run verified 3/3 Wrench answers. This is a concrete
format-related quality regression on this tiny fixture, not evidence that the
0.8B base is broadly incapable. The 2B compact-context arm matched its
full-context 3/3 result on this sample.

## Decision

Do not make compact serialization the default or claim it is non-inferior.
Retain it as an opt-in research mode while expanding the task battery. The
2B result supports further testing of the format on the current lead model;
the 0.8B failure means the smaller control cannot be treated as quality-safe
under this prompt form.

The target-tokenizer result remains **93.978339% prompt-input reduction**,
below the 95% component target. Iteration 148's 95.185780% quote-segment
variant is still only a tokenizer diagnostic selected with predeclared quote
annotations; this run did not test that pruning variant. None of these local
prompt counts is measured frontier-token saving.

## Identities and accounting

Both runs used Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
CUDA 13.2, and the RTX 5060 Ti. Both had zero frontier calls and $0 provider
spend. Frontier-token savings are N/A because the full-context arm is local,
not a frontier-only baseline. No LoRA adapter was loaded.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-compact-iter149-qwen35-2b.json` | 6,339 | `7F7ACEC275D59C09BE9AB725A7597B6C78C5C47F0DBF5DE6C55C3A808677AE92` |
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-compact-iter149-qwen35-08b.json` | 6,359 | `E63054CF85F8F112D0B75238F4E5EC1D24216EE848CBE8DC547F59F47250D863` |
| Paired runner `examples/gateway_context_mvp/run_paired_local_context_baseline.py` | — | `7AA0C083B69BC2F0783D37CED6E66ED7397E1ED5E731727F58E368EC89D7373C` |
| Prompt compiler `src/wrench_harness/prompt_compiler.py` | — | `BBF3D1F8A7698807E87EE997429FC1BCF3B6D5A65E51CE91E282294DBE62B213` |

The 2B run binds revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`, verified inventory
`23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`, and
snapshot receipt `59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014`.
The 0.8B run binds revision
`2fc06364715b967f1860aea9cf38778875588b17`, inventory
`64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`, and
snapshot receipt `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6`.

## Limits and next action

Three synthetic lookups cannot establish coding capability, 95% local task
coverage, all-day reliability, frontier success retention, frontier-token
savings or all-in cost. The tiny sample has no useful statistical power. The
measured 95.185780% input diagnostic has not been model-tested and is not a
frontier saving result.

Next, define an answer-blind pruning rule from required evidence IDs and
parser-reported spans, not expected answer strings. Compare pruned and full
typed context on a larger frozen set using the 0.8B control and 2B lead. Keep
the 95% target and all failure cases. Separately refresh the exact Fit-03
package review against the current goal hash before any LoRA training; this
iteration trained no adapter.
