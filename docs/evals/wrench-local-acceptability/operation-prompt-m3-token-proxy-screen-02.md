# Explicit-operation synthetic M3 input-token proxy screen 02

Date: 2026-09-25 (America/Edmonton)

## Review result

The protocol 02 measurement was stopped before tokenizer load or case
execution. Independent read-only reviews found validity gaps in the
eligibility gate. The operation-prompt M3 input-token result is unavailable;
protocols 01 and 02 produced no measured cases.

## Findings

- The decoded context payload was searched globally. Its opaque evidence IDs
  were not bound back to exact `path` and source hash identities. A matching
  quote elsewhere in the context would not establish that the expected file
  was present.
- A positive literal-search result checked the returned match lines without
  requiring exact visibility of every file in the bounded search scope. That
  cannot prove an untruncated result when other scoped files are absent.
- A route outcome mismatch could become an excluded case because the runner
  returned before comparing it with the frozen operation observation.
- The saved fetch receipt's status and selected-file metadata were not all
  checked explicitly, despite the protocol requiring receipt verification.

These are measurement-gate defects, not evidence of a tokenizer or product
failure. No actual counts exist and no cases are included in any metric.

## Decision

Prompt-size proxy work is secondary to determining which local work Wrench can
acceptably complete. The current local-task boundary and next measurement are
recorded in the [local task acceptance envelope](../../reports/wrench-local-acceptability/local-acceptance-envelope-20260925.md).
Do not use the unfinished runner for a prompt-size claim. If that diagnostic
is resumed, create a fresh protocol that binds each visible section to its
path, source hash and route evidence; requires complete path-bound search
scope; aborts on every unexpected route outcome; and verifies the full fetch
receipt before loading the tokenizer.

## Review scope

Three independent reviewers checked source/evidence binding, route-oracle
handling, tokenizer/runtime identity and protocol scope. All reviews were
read-only. No tests, tokenizer operations, model inference, client activity,
network access or provider calls occurred.
