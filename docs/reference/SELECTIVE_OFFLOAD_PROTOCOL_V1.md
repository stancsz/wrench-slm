# Selective offload protocol V1

Updated: 2026-09-10

This protocol is the active experiment contract for selective local completion.
It supersedes neither the historical V2 broad-quality receipts nor the V21
release record. It asks a narrower question: can a public-context policy admit
a small subset of local actions while preserving complete outcomes and
reducing stronger-model work?

## Candidate and scope

- Candidate: immutable V21 package
  `artifacts/model-release/package-selected-v21`.
- Base: the pinned Qwen revision and base dependency already recorded in the
  V21 package manifest.
- Runtime: the checksummed packaged executor, maximum 1,536 input tokens and
  192 generated tokens.
- Scope: Windows developer-tool fixtures, bounded reads, literal search, Git
  inspection, loopback health reads, review-only file drafts, and explicit
  fallback cases.
- No retraining, production deployment, arbitrary shell, or new model tier is
  part of this experiment.

## Fresh data

The generator is `wrench/selective_tasks.py`, invoked by:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\build_selective_offload_v1.py `
  --output data\pilots\selective-offload-v1-rerun3
```

The current generated receipt has 24 development families and 120 evaluation
families, five instances per family, 12 task kinds, and 600 evaluation cases.
English and Chinese each contribute 300 evaluation cases. Ineligible cases
include ambiguity, unsupported work, missing tools, invalid ranges, and an
input-budget case. Private fixture and expected-answer fields never enter the
public record.

The current data hashes are recorded in
`data/pilots/selective-offload-v1-rerun3/manifest.json`:

- development: `28a8b07e8a51636156a616f0b692e7e984a4c392e3ec36f737116d0df70fabfe`
- evaluation: `20455d4658006d8446a240298502ccef3fe60f55655fe73c059d0071c47920ad`

The evaluation set is not used for development calibration or policy
selection.

## Policy and execution boundary

The policy is `wrench/selective_policy.py`. It uses only the public prompt and
context. It never reads `fixture`, `expected_answer`, `kind`, or private
arguments. It admits only:

- visible resource paths for `read_file`;
- positive, ordered line ranges;
- exact bounded Git, literal-search, or loopback-health commands;
- visible paths and prompt-visible content for review-only drafts.

Every accepted action is executed through `PilotEnvironment`, which validates
the visible tool schema, path boundary, command allowlist, and filesystem
fingerprint. A failed observation, formatter failure, timeout, or mutation is
not a local completion. It must fall back.

Three policy variants are calibrated on development data only:

| Variant | Admission rule |
| --- | --- |
| `agreement` | Publicly safe action and exact agreement with deterministic helper |
| `safe` | Publicly safe action, or exact helper agreement |
| `eligible` | Publicly safe action above the declared eligibility threshold |

The current implementation exposes thresholds and reason codes in every row.
The selected variant must be frozen before evaluation. A variant is eligible
for held-out scoring only if development shows a nonempty successful local
slice, zero wrong accepted completions, zero prohibited accepted actions, zero
unexpected mutations, and complete receipts for every assigned case.

## Development and evaluation commands

Run each candidate variant on development, inspect the receipts, then choose
at most one variant. Never choose using evaluation rows.

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-v1-rerun3 `
  --split development `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant agreement `
  --output artifacts\selective-offload\development-agreement
```

Repeat the command with `safe` and `eligible`, using a new output directory for
each run. Then run exactly one frozen choice on evaluation:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-v1-rerun3 `
  --split evaluation `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant <frozen-variant> `
  --output artifacts\selective-offload\evaluation-<frozen-variant>
```

## Required measurements

For every assigned task, including bypasses, record:

- policy variant, action, reason code, and eligibility score;
- local attempted, accepted, and successful states;
- complete observation and answer-format receipts;
- input and output token counts, local inference time, and total local time;
- fallback reason, tool errors, and filesystem fingerprint result.

Report accepted coverage as accepted local attempts divided by all requests,
correct local completions divided by all requests, accepted precision, accepted
error rate, unnecessary fallbacks, reason breakdown, and kind/language slices.
Cluster uncertainty by wording family. A zero-error observed slice is not a
zero-risk claim.

## Cloud workflow gate

Only after one frozen policy passes the fresh local gate may a fixed-model cloud
workflow be run. The workflow must compare:

- A: stronger-model-only;
- B: deterministic helper plus the same fallback;
- C: helper plus selectively admitted V21 plus the same fallback.

All arms use identical tasks, endpoint identity, outcome checks, bounded turns,
tool calls, attempts, token admission, and cost accounting. Report complete
episodes, prompt/completion/cached tokens, corrections, fallback overhead,
latency, local compute, and actual monetary usage. Any endpoint or explicit
spending ceiling not available is recorded as an external blocker, not treated
as zero cost.

The final result is one of:

- `MEASURED SELECTIVE BENEFIT`: fresh local gate passes, complete workflow
  preserves observed outcomes, and net cloud tokens are saved;
- `LOCAL CAPABILITY ONLY`: local gate passes but the cloud comparison cannot be
  run or is not yet complete;
- `NO MEASURED BENEFIT`: no bounded policy has useful reliable coverage or
  positive net value.

None of these outcomes authorizes production deployment.
