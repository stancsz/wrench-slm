# Iteration 025: measured context savings and request-boundary gap

Date: 2026-09-27  
Status: source/artifact audit complete; no new model or frontier experiment  
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Finding

The previous tokenizer-only screen is not close to the full 95% objective and
cannot be rerun or used for LoRA training. The exact content-free receipt
already on disk was rehashed as
`68d66186f4a78c4d6f577950b9256c285f8f41bfe8627ea7aba78565eb8fd870` and
reports `acceptance_status=FAIL`, seven positive cases, five passing source
evidence gates, two excluded function-location cases, and four of four
abstention boundaries passing. Among the five eligible pairs it measured
3,204 full-source baseline input tokens and 2,816 E0-prepared input tokens:
11.6359% mean and 12.1099% ratio-of-sums reduction. It made zero frontier
calls; `frontier_token_savings_percent` is `null`. This is synthetic input
compaction evidence only, not model performance, task success, billed use, or
frontier-token savings. The exposed one-shot screen must not be rerun or used
for training.

The current OpenCode hook projection includes `tools`, but its validated
context-transition code treats `agent`, `model`, `system`, `tools`, and
`options` as protected fields (`src/wrench_harness/opencode_hook_projection.py`
line 630; current SHA-256
`73f05f50a11ee2f312c9ee7de7a996cc0ce4367aa7e0220807df5a4b28227cc5a`). The
transition accepts a bounded context-message insertion while requiring those
fields to remain unchanged. This seam cannot filter tool schemas, so current
E0 context selection cannot claim the large repeated tool-schema savings
described in the literature. Tool-schema savings need a distinct, validated
request-boundary integration and full-payload accounting, with fixture tests
that preserve every required/authorized tool.

## Host and gate

At the start of this iteration, RAM was 3.38 / 31.94 GiB free (10.6%), GPU
memory was 15,260 / 16,311 MiB free, and C: had 131.13 GiB free. No matching
Wrench training, inference, or screen process was found. RAM remains below
fit-03's 25% start gate; no model was loaded and no experiment was started.
The 10% RAM/VRAM reserve and 25% candidate-specific start gate were not
changed.

## Next work

When fit-03 or another pinned under-10B candidate passes all current resource,
storage, runtime, data, and exact-hash gates, prioritize the bounded LoRA fit
and subsequent dev/held-out lifecycle. Until then, advance the full proof at
the correct request boundary: build a no-provider, source-bound request
accounting/fixture path that measures complete serialized messages, tool
schemas, history, file/tool output, retries, and cache-relevant input for
matched baseline and Wrench arms. Do not repeat literature-only or status-only
iterations, do not claim the 12.11% screen as frontier savings, and do not
modify the existing hook's protected tool set as a shortcut.

## Scope and storage

- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.
- No code, training data, model, provider configuration, or test result was
  changed or generated in this iteration.
- No model load, training, inference, localhost generation, or paid provider
  request occurred.
- Storage admission used job ID
  `WRENCH-GATEWAY-REQUEST-ACCOUNTING-ITER025-20260927-01`, reserving 200,000
  bytes and including the SubRoute checkout and automation directory. A final
  status after the report and hourly-prompt update returned `WITHIN_LIMIT`:
  10,991,534,125 actual bytes, 6,303,000 active reserved bytes including this
  job, and 10,997,837,125 projected bytes against the 50,000,000,000-byte
  ceiling. The reservation was released after that accounting; no large or
  model artifacts were produced.
