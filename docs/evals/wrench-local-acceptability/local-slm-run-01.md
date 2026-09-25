# Evaluation: local SLM acceptability run 01

Status: **NOT EVALUABLE for model quality; harness failed before generation.**

## Counts

| Outcome | Count |
| --- | ---: |
| Model calls | 0 |
| Completed cases | 0 |
| Failed before model output | 1 |
| Not run | 9 |
| Tool attempts or mutations | 0 |
| Prompt/completion tokens | 0 / 0 |
| Accepted task classes | 0 measured |

The failure was in runner input normalization: the pinned Qwen tokenizer
returned a `BatchEncoding`, while the runner parsed the wrapper as token IDs
instead of using its `input_ids` tensor. The model loaded successfully, but
the error happened before `model.generate`. It does not indicate whether the
model can perform localization or any other challenge task.

## Resource gate

The runner observed at least 10% free RAM and VRAM throughout its sampled model
load and case setup. Load minima were 45.18% RAM and 86.99% VRAM free; post-load
values were 48.59% and 85.17%. Sampling was not continuous and cannot rule out
shorter transient dips.

## Decision

Do not score this run against the class-screen rule. Preserve its durable
receipt and exclude it from quality aggregates. Run 02 is separately
preregistered after the adapter fix; it will stop on any generation/runtime
error without retrying. Frontier-token savings remain N/A because there are
no paired usage receipts.

Detailed evidence: [run 01 report](../../reports/wrench-local-acceptability/local-slm-run-01.md)
and durable JSON receipt
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\qwen35-0.8b-synthetic-20260925-01.json`.
