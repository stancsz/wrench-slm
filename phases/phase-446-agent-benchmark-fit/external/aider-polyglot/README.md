# Aider Polyglot adapter plan

## Why it is selected

Aider Polyglot tests the bounded `patch_draft` action directly. Its tests check
whether a proposed source edit solves a real programming exercise, rather than
whether a patch merely parses. The Wrench model only drafts the diff. An
isolated harness applies the proposal and runs the supplied tests; Wrench gets
no write or shell authority.

## Pinned upstream

- Dataset repository: `https://github.com/Aider-AI/polyglot-benchmark`
- Dataset revision: `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`
- Languages: C++, Go, Java, JavaScript, Python, and Rust
- Expected benchmark size: 225 exercises
- Run `fetch.ps1` to place the pinned source under ignored `upstream/`.
- Fetch completed on 2026-09-22: commit
  `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`, 225 exercises across all six
  languages. The fetched Aider harness source is included at
  `upstream/aider-source/benchmark/` for protocol inspection.
- Aider's published GPT-5 high result used 225 tasks, Aider commit
  `32faf82`, pass@1 52.0%, pass@2 88.0%, and 91.6% well-formed edits.
  GPT-5 medium reported pass@1 49.8% and pass@2 86.7%.

## Scoring and comparability

Primary Wrench metric: pass@1 with one proposal and no test-feedback retry.
Also report valid unified-diff rate, apply rate, test pass rate, and per-language
results. Only publish pass@2 after implementing the same retry count and
ground-truth test feedback as the matching leaderboard protocol.

Keep source data and candidate edits in disposable per-case checkouts. Execute
the benchmark tests inside a disposable container because the published
harness runs generated code. The adapted Wrench metric is not the official
Aider leaderboard score. Compare only to published models as a reference unless
those models run through the same adapter, task revision, and test container.

Before a full run, verify the pinned exercise count, test availability for all
languages, and whether Wrench can construct one bounded proposal from the
provided files. Preserve every refusal, malformed edit, timeout, and test
failure in the denominator.

## Execution boundary

The upstream Docker launcher mounts its full checkout and forwards
`OPENAI_API_KEY`. The Wrench run must instead use a disposable per-exercise
workspace with only that exercise's source and tests mounted. Apply the
review-only patch outside the Wrench worker, then execute tests in a container
with no credentials and no network. Record dependency or platform setup errors
separately from model failures. No Aider benchmark tests have been run yet.
