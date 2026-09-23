# BFCL V4 Irrelevance adapter

## Why it is retained as a diagnostic, not a showcase score

BFCL V4 supplies an established irrelevance category and outside model scores.
That category asks whether the agent avoids invoking functions that do not fit
the user request. This directly probes Wrench's bounded-call and abstention
policy. It is not a test of broad API coverage.

## Pinned upstream

- Repository: `https://github.com/ShishirPatil/gorilla`
- Leaderboard reproduction commit: `f7cf7359b7ac615a0b294831c5ba2bc95ee4a000`
- Reproduction package version: `bfcl-eval==2025.12.17`
- Public scoreboard snapshot last updated 2026-04-12
- Download exact source with `fetch.ps1`; it sparsely checks out
  `berkeley-function-call-leaderboard/` into ignored `upstream/`.
- The selected Wrench input is the official non-live file
  `bfcl_eval/data/BFCL_v4_irrelevance.json` (240 cases). Its SHA-256 is recorded
  in `benchmark-manifest.json` after the adapter run is prepared.
- `scoreboard-reference.csv` is the official raw score export downloaded from
  `https://gorilla.cs.berkeley.edu/data_overall.csv`.

## Scoring and comparability

The Wrench projection reports abstention accuracy, false-continue rate, and
input-limit rate across the 240 non-live irrelevance cases. Preserve source
case IDs and the official gold behavior, which is to make no function call.
Wrench abstention means escalation to the stronger model, so report this as a
call-gating component rather than completed user-task success.

The six authorized Wrench actions are `read_file`, `read_lines`,
`literal_search`, `git_read_status`, `health_read`, and `patch_draft`. A scan of
the pinned BFCL V4 data files found no exact function-name matches for these
actions. We therefore do not report BFCL AST tool-call accuracy. The irrelevance
category remains useful as a boundary diagnostic because every case should be
abstained, regardless of the unrelated function schema shown in the prompt.
It is not one of the five scorecards: all 240 selected non-live cases are
no-call examples, and the supplied function names have zero exact matches to
Wrench's allowlist. An always-abstain control scores 100%, while the prior
Wrench head scored 61.7%. This slice cannot distinguish productive tool
routing from a generic no-call policy, so it is not a fair showcase of Wrench.

The official published aggregate Irrelevance Detection scores are 64.47% for
xLAM-2-1B-FC-R, 63.45% for xLAM-2-3B-FC-R, and 84.93% for
Qwen3-4B-Instruct-2507-FC. The public aggregate includes live and non-live
irrelevance cases; these values are reference anchors, not exact matched
comparisons to Wrench's 240-case non-live projection. Do not label a Wrench
adapted result as an official BFCL leaderboard score.

The official page states its reproduction commit and package version and
publishes model responses. See the top-level benchmark slate for the exact
reference values and comparison rules. Keep all downloaded data and outputs
under this phase folder.

## Completed Wrench component run

The frozen Wrench binary gate processed all 240 unique non-live cases at
`runs/wrench-qwen-head-v1/`. The input SHA-256 is
`9c1fa6596922c78b7817aa94e5eb94c14ed18d87a1b564b974fbd113b213121e` and the
prediction SHA-256 is
`eb8b927f4103656e6e650fe40504dd93269ab299e1fe42454feccf1e15c5208e`.

| Metric | Result |
| --- | ---: |
| Abstention accuracy | 61.7% (148/240) |
| False continuation | 38.3% (92/240) |
| Input-limit rate | 0% (0/240) |
| Exact function-name matches to Wrench actions | 0 |
| Model-decision latency p50/p95 | 196/270 ms |

This is a weak component result and should not be presented as evidence of
strong refusal behavior. The official comparison scores cover the combined
live and non-live category; they are reference anchors, not a matched
comparison to this projection. The run used the frozen gate only, generated no
tokens, made no provider calls, and executed no tools. RAM and VRAM samples
remained above the repository's 10% reserve.
