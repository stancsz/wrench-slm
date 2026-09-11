# Selective offload bounded result

Updated: 2026-09-10

## Verdict

The bounded local selector study passed its revised fresh local safety gate.
The observed result is **local capability only**. It is not yet evidence of
net token savings, faster complete workflows, production reliability, or a
general-purpose local developer model.

The first frozen policy was rejected by its held-out data and remains a
negative result. Its replacement was limited to one public-intent revision
with new family IDs. No weights were changed.

## Frozen identity

- Candidate: immutable V21 package `artifacts/model-release/package-selected-v21`
- Package manifest SHA-256: `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`
- Adapter SHA-256: `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Revision: `intent-v2`
- Policy: `eligible`, threshold `0.85`, public prompt and context only
- Evaluation manifest SHA-256: `79f7c7d3afed753bc450c5f1b1a350716ab0f903cc4b00b6eb39ca3978f88a6f`
- Evaluation split SHA-256: `8558f329139f4e58bd96c61e597c5441c9372c36e4794f7d29c2f3386ae6ef0f`
- Receipt: `artifacts/selective-offload/revision1-evaluation-eligible/summary.json`

## Fresh held-out result

The evaluation assigned 600 requests in 120 disjoint families, five requests
per family, across 12 task kinds and two languages. All requests were scored,
including fallback and adversarial requests.

| Measure | Observed |
| --- | ---: |
| Local accepted completions | 305 / 600, 50.83% |
| Correct local completions over all requests | 305 / 600, 50.83% |
| Accepted precision | 305 / 305, 100% |
| Accepted error rate | 0 / 305, 0% |
| Accepted ineligible requests | 0 |
| Unexpected mutations | 0 |
| Unnecessary fallbacks | 0 |
| Model-abstention fallbacks | 242 |
| Intent-mismatch fallbacks | 50 |
| Draft-content visibility fallbacks | 3 |
| Local duration p50 / p95 | 1.45s / 2.91s |

The family-clustered bootstrap receipt is produced with:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\analyze_selective_offload.py `
  --rows artifacts\selective-offload\revision1-evaluation-eligible\rows.jsonl `
  --output artifacts\selective-offload\revision1-evaluation-eligible\family-bootstrap.json
```

The observed 95% family-bootstrap interval is 41.83% to 59.83% for both
accepted coverage and useful coverage. Accepted precision is 100% in this
bootstrap because every accepted task was correct. The interval is exploratory
because the authored families are not a sample of
real traffic. It treats each family as the uncertainty unit and does not treat
five instances as five independent families.

## Kind and language slices

| Kind | Accepted / assigned | Correct / assigned |
| --- | ---: | ---: |
| config | 50 / 50 | 50 / 50 |
| lines | 40 / 50 | 40 / 50 |
| search | 50 / 50 | 50 / 50 |
| git_status | 35 / 50 | 35 / 50 |
| git_log | 45 / 50 | 45 / 50 |
| health | 50 / 50 | 50 / 50 |
| draft | 35 / 50 | 35 / 50 |
| ambiguous | 0 / 50 | 0 / 50 |
| unsupported | 0 / 50 | 0 / 50 |
| missing_tool | 0 / 50 | 0 / 50 |
| invalid_range | 0 / 50 | 0 / 50 |
| over_budget | 0 / 50 | 0 / 50 |

English accepted 155/300 and Chinese accepted 150/300. Both language slices
had 100% observed accepted precision. Coverage is therefore useful but
selective, not broad.

## Why the first policy was rejected

The first frozen `eligible` policy used only structural safety checks. On its
fresh 600-request evaluation it accepted 347 requests, completed 333
correctly, and accepted 14 wrong local outcomes, including nine unsupported
requests. The complete receipt is
`artifacts/selective-offload/evaluation-eligible/summary.json`.

The bounded `intent-v2` revision added public request-intent alignment. It used
new development and evaluation families and was frozen before the 600-request
run. The revised result must not be combined with or used to erase the first
result.

## M1 route evidence

`wrench/selective_runtime.py` now provides a callable local-or-fallback route.
It has explicit reason codes for operator bypass, model abstention, policy
rejection, local timeout, local tool error, failed outcome verification, and
unexpected mutation. `run_episode` can use the same route for B and C. The
targeted test receipt is `7 passed` in `tests/test_selective_offload.py` and
covers zero-cloud local completion, operator bypass, timeout, tool error,
invalid proposals, unsupported requests, and mutation checks.

## What is not measured

No matched A/B/C cloud workflow was run. Therefore these values remain
unknown: provider prompt/completion/cached tokens, calls, corrections,
fallback overhead, complete-workflow latency, monetary usage, paired family
quality uncertainty, and net cloud tokens saved. The local gateway was
reachable and advertised `minimax/minimax-m3`, but an explicit authorized
spending ceiling was not found in this workspace. The next run must use the
same endpoint and model for A, B, and C with a predeclared ceiling.

The prepared runner is `scripts/selective_pilot_run.py`. It verifies the frozen
selection receipt and hashes before starting, refuses provider calls without
both an explicit attempt/token ceiling and `--authorize-paid-run`, and writes
under `artifacts/selective-offload-v1/<run-id>/`. The companion analyzer is
`scripts/analyze_selective_workflow.py`.

The authored task mix is not real traffic. Production frequency, distribution
shift, and live user impact remain unmeasured.

## Reproduction

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-revision1 `
  --split evaluation `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant eligible `
  --revision intent-v2 `
  --output artifacts\selective-offload\revision1-evaluation-eligible
```

For an immediate local-evaluation bypass, add `--bypass`. For the matched
workflow, add `--bypass-local`; the latter skips local proposal/completion for
B and C and routes them directly to the stronger model. Both paths record the
operator bypass explicitly.

The recommended current posture is to keep the learned path disabled in any
cloud workflow until the matched comparison is authorized and completed. The
rules and fallback implementation are useful bounded local capability, not a
measured economic benefit yet.

Verification completed on the scoped repository suite with the archived
artifact tree excluded: `177 passed, 1 warning`. A default repository-wide
pytest invocation still encounters duplicate test-module names under
`artifacts/repository-cleanup/clean-export/tests`; that is a collection hygiene
issue, not a failing test result in the active source tree.
