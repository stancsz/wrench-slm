# Iteration 064: SubRoute 4000 and realistic small-model fit research

Timestamp: 2026-09-28 03:22 UTC (2026-09-27 America/Edmonton)

Repository: Wrench `af01304824f079a64b6c3902397a2034b843511a`

SubRoute source inspected: `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`

## Recommendation

Keep the first LoRA experiment on the already pinned Qwen3.5-0.8B. Give that
model a narrow controller role: propose bounded actions, classify mechanical
work, compact context, and abstain or request escalation. Leave retrieval,
state, permissions, path resolution, command execution, and outcome checks in
deterministic code. The current 0.8B candidate is not a credible standalone
all-day repository engineer.

For local code generation, the next reasonable model to evaluate is
Qwen3.5-4B with bf16 LoRA, as a separate experiment after its own package
review and admission. Its complete remote inventory is pinned below. Vendor
and fine-tuning documentation make the hardware fit plausible on the current
16 GB RTX 5060 Ti, but no local fit/runtime has been measured. Do not silently
expand fit-03 from 0.8B to 4B or replace its identity.

Use the owner's SubRoute at `http://127.0.0.1:4000` for the stronger-model
comparison. The saved active route is `openrouter` forced by policy. Its
configured M3 alias declares streaming but not native tool calling, so it is
not currently an apples-to-apples baseline for a tool-using coding agent. Do
not switch aliases or alter force mode in this experiment. No generation was
sent: the numeric campaign USD cap, durable pre-reservation/settlement, and
verified billed-cost/provider receipt are still missing.

## Candidate roles and available evidence

| Candidate | Use to test | Evidence and limits |
| --- | --- | --- |
| [`Qwen/Qwen3.5-0.8B`](https://huggingface.co/Qwen/Qwen3.5-0.8B), existing pinned snapshot `2fc06364715b967f1860aea9cf38778875588b17` | Narrow controller, structured proposals, context selection/compaction, abstention | The published model card positions 0.8B for prototyping and task-specific tuning. Its reported general-agent and long-context scores are much lower than the 4B model. Good reason to constrain its role; not proof its Wrench LoRA succeeds. |
| [`Qwen/Qwen3.5-4B`](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a), revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | Separate local coding-worker candidate for small fixes and test-guided edits | The model card reports LiveCodeBench v6 55.8, BFCL-V4 50.3, and TAU2-Bench 79.9. These are model-card results, not repository-level or sustained-work results. Exact artifact inventory follows. |
| MiniMax M3 through SubRoute `:4000` | Stronger-model comparator and escalation route where current alias supports the task | OpenRouter's [MiniMax M3 listing](https://openrouter.ai/minimax/minimax-m3/pricing) lists 1.0M context, $0.23/M input, $0.96/M output, and $0.05/M cache reads. The OpenRouter endpoint says it does not accept `tools`; price/provider reports are not a verified bill from this local gateway. |

The [Qwen3.5-0.8B model card](https://huggingface.co/Qwen/Qwen3.5-0.8B) reports MMLU-Pro 29.7 and IFEval 52.1 in
non-thinking mode, BFCL-V4 25.3, TAU2-Bench 11.6, and LongBench v2 26.1 in
its listed settings. The Qwen3.5-4B card reports BFCL-V4 50.3, TAU2-Bench
79.9, and LongBench v2 50.0 in its respective tables. Use these only as
directional candidate-screen evidence: the model cards use their own prompts
and harnesses, and these tasks do not prove reliable code changes in Wrench.

## Complete Qwen3.5-4B inventory

Read-only [Hugging Face model metadata](https://huggingface.co/api/models/Qwen/Qwen3.5-4B?blobs=true) was inspected at the pinned revision.
No model file was downloaded. The API's file `size` values sum to
**9,342,907,469 bytes**. Its separate `usedStorage` field reports
9,332,636,078 bytes, so storage planning uses the larger enumerated sum.

| File | Bytes |
| --- | ---: |
| `.gitattributes` | 1,570 |
| `LICENSE` | 11,544 |
| `README.md` | 77,661 |
| `chat_template.jinja` | 7,756 |
| `config.json` | 3,161 |
| `merges.txt` | 3,353,259 |
| `model.safetensors-00001-of-00002.safetensors` | 5,329,398,688 |
| `model.safetensors-00002-of-00002.safetensors` | 3,990,429,408 |
| `model.safetensors.index.json` | 76,196 |
| `preprocessor_config.json` | 390 |
| `tokenizer.json` | 12,807,982 |
| `tokenizer_config.json` | 16,710 |
| `video_preprocessor_config.json` | 385 |
| `vocab.json` | 6,722,759 |
| **Exact sum** | **9,342,907,469** |

As a coarse duplicate allowance, three complete repository-sized copies
(Hub cache, active base snapshot, and a possible merged/deployment format
upper-bounded at the source size) plus a 1,000,000,000-byte job buffer would
project to 40,028,363,160 bytes after adding current Wrench actual usage
(10,991,337,753 bytes) and current reservations (8,103,000 bytes pre-existing
and this report's 200,000-byte reservation). This leaves 9,971,636,840 bytes
under the 50,000,000,000-byte ceiling. It is a planning scenario, not an
admission: the job buffer is provisional, and a real download/fit must account
for actual export format, cache behavior, checkpoints, runtime environments,
logs, temporary files, all external Wrench roots, and destination free space.
Run the storage checker and reserve the actual peak before acquisition.

## LoRA and runtime feasibility

Unsloth's [current Qwen3.5 guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune) estimates bf16 LoRA memory at 3 GB VRAM for
0.8B and 10 GB for 4B. It recommends Transformers v5 for Qwen3.5 and does not
recommend 4-bit QLoRA for this family because of higher quantization
differences. This puts 4B within plausible reach of a 16 GB card under a
bounded batch/context, but it is an estimate from a training stack, not a
measurement on this Windows host. Kernel compilation, runtime compatibility,
context/KV cache, loading overhead, throughput, and the mandatory free-memory
reserves remain to be measured.

Keep the sequence length and concurrency low at first, and preserve the
10% RAM/VRAM reserve and the experiment's 25% free-RAM launch gate. A separate
candidate requires a separate inventory, pinned runtime, LoRA target-module
review, storage admission, trainer/scorer protocol, and exact-hash review.
Do not treat availability of LoRA code or a falling training loss as evidence
of Wrench utility.

## What the research supports

The efficiency mechanism is plausible, but its reported best cases do not
transfer automatically to our task distribution:

- [RouteLLM](https://arxiv.org/abs/2406.18665) studies learned routing between stronger and weaker models and
  reports more than 2x cost reductions on its evaluated settings.
- [FrugalGPT](https://arxiv.org/abs/2305.05176) reports up to 98% cost reduction in its studied workload using
  prompt adaptation, model approximation, and cascades.
- [LLMLingua-2](https://arxiv.org/abs/2403.12968) trains a smaller token classifier for extractive prompt
  compression. It reports 2x-5x compression and end-to-end latency gains on
  its benchmarks.

These results justify testing routing and compaction. They do not establish
that a Wrench model can solve 95% of local tasks, preserve 95% of frontier
success, or reduce this product's total spend by 95%.

Compaction should protect the actionable state rather than maximize a raw
compression ratio. Retain user constraints, current objective, repository and
branch identity, changed paths, verified facts with sources, commands/tests
already run, failures, unresolved risks, and next action. Store mutable facts
outside the adapter. Test compaction by asking held-out recovery probes and
by continuing the original task from the compacted state; a fluent summary
that loses a path, test failure, or constraint is a failed compaction.

## How to prove overall effectiveness

Use paired task episodes with the same tool scaffold and acceptance checks in
at least these arms:

1. Frontier-only through the approved SubRoute path, when its active alias
   supports the task and the caller's numeric cap/receipt gate is in place.
2. Wrench plus the pinned 0.8B LoRA controller, with deterministic tools and
   verifier.
3. Deterministic Wrench plus frontier, as a separate control arm.
4. A local 4B worker only after its separate fit package is admitted.

Use fresh private repository tasks as the primary quality set. Stratify
mechanical operations, context recovery, single-file fixes, multi-file
features, test repair, refactoring, environment failures, and interruption
recovery. Preserve the final set as sealed; train only on reviewed,
outcome-backed examples in the allowed training split. Add a pinned
[Terminal-Bench 4.0](https://www.tbench.ai/news) release as a public external check, not as a replacement
for repository tasks or as proof of product utility. For all-day work, measure
whole sessions across repositories, task families, interruptions, context
recovery, tests, regressions, and human rescue; report operator time and
failures, not just the final patch score.

Keep all four gates separate:

- Provider calls occur on at most 5% of all planned episodes.
- Verified hybrid success retains at least 95% of frontier-only verified
  success on the same episodes.
- Total frontier tokens, including every retry, verification, compaction,
  fallback, and re-fetch, are no more than 5% of frontier-only tokens.
- All-in hybrid cost is no more than 5% of frontier-only cost after local
  compute/energy, LoRA training amortization, operator time, and rescue.

An episode-count route rate is not a token or dollar savings estimate. A small
number of long escalations can dominate remote usage; local inference and
human rescue also cost money. Use paired results, explicit denominators,
confidence bounds, and repository/task-family clustering. Preserve
abstentions, timeouts, regressions, and human rescue in the denominator.

## SubRoute 4000 source and call boundary

The user specified `http://127.0.0.1:4000`. The read-only snapshot on
2026-09-27 recorded `active_model=openrouter`, `mode=force`, and policy
version 4. Current static SubRoute config SHA-256 is
`05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735`.
It maps `openrouter` to `openrouter/minimax/minimax-m3`, with declared
capabilities `[streaming]`. The sibling `minimax` entry maps to
`minimax/MiniMax-M3`, with declared capabilities `[tools, streaming]`.
SubRoute config sets `num_retries: 0` and `fallbacks: []`, and disables spend
logs. These are source/config facts, not live end-to-end evidence. The prior
independent caller review found that the current Wrench capture seam does not
implement a durable campaign-wide spend ledger, and that public-proxy metadata
delivery/provider attribution/cost were not verified.

No completion POST, provider request, credential read, or paid call was made
for this iteration. Continue to use the specified port for future comparisons,
but keep generation closed until a numeric campaign cap and fail-closed
caller-side reservation/settlement are present. Do not ask the owner for the
cap again in each hourly turn.

## Current gates and next action

RAM is 8.40% free, below the 10% minimum for tests/runtime/inference and below
the 25% start gate for fit-03. No test, runtime, benchmark, fit, or delegated
review ran. The attention-only preflight-05 receipt is reusable as recorded;
the independent fresh package-review receipt for trainer, scorer, protocol,
current GOAL, and Iterations 008/009 is still absent. Once host RAM reaches
10%, obtain that bounded exact-hash review. Start fit-03 only after it passes
and RAM is at least 25% free at launch, VRAM/RAM remain above 10%, and a fresh
storage/disk admission passes. Do not open held-out content before the scored
fit gates.

The existing 128-case synthetic screen, public model-card numbers, and prior
source reviews do not prove real repository coding, 95/5 operation, 95% token
savings, 95% all-in cost reduction, or all-day engineering. Those product
claims remain open.
