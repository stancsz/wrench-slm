# Phase 178: prompt-complete MiniMax teacher capture

Date: 2026-09-20

## Purpose

Capture a live MiniMax endpoint proposal baseline over the same 220-case
prompt-complete contract. The capture is proposal-only. It does not execute
tool calls, mutate a workspace, or establish teacher workflow quality.

## Captures

The first run used `max_tokens=256`. It completed 220 requests with zero
transport failures, but 88 responses were unusable because reasoning and JSON
output competed for the small completion budget. It is retained as a failure
diagnostic.

The second run used `max_tokens=1024`:

- 220 requests.
- 0 transport failures.
- Capture metadata reports 4 invalid responses, all in `patch_draft` rows.
- 19 additional rows contain incomplete raw JSON and therefore have no
  normalized proposal. They are not treated as successful teacher proposals.
- 216 rows returned a provider response with model id `minimax`.
- Finish reasons: 215 `stop`, 1 `length`, 4 missing because no usable provider
  response was recorded.
- Median request latency: 1,997.283 ms.
- p95 request latency: 7,716.028 ms.
- Prompt tokens: 84,882.
- Completion tokens: 61,728.
- Total provider-reported tokens: 146,610.
- Provider-reported upstream inference cost: `$0.08236908`.

The raw receipt is
`teacher-220-max1024.json` with SHA-256
`62f8beff20a16e2a457bbfc939d09670bcb834619d4ad42f99b263d4cb0b3473`.

## Wrench comparison boundary

The current v73 package-local prompt-complete replay accepted all 220 expected
outcomes, produced 120/120 exact eligible proposals, made zero model calls,
and measured 24.011 ms median and 81.938 ms p95. Its receipt recorded 23,409
raw input tokens and all 23,409 as input tokens not sent to a model.

These are different measurements. The MiniMax capture is a teacher proposal
baseline with no verifier-executed workflow. The Wrench receipt is a bounded
mechanical package replay with embedded verifier and TTC gates. A real
MiniMax-versus-Wrench production claim still requires matched three-arm replay
with final success, safety, fallback, local inference, retry, correction,
latency, and cost accounting.

## North-star interpretation

This capture strengthens the product thesis without closing the final gates:
the teacher spends frontier tokens and milliseconds deciding routine actions,
while Wrench can accept a 4M-token raw payload, reduce it mechanically, and
complete an eligible bounded task without model prefill. The value is high
throughput and low frontier-token spend for repetitive work. It is not a claim
that every 4M-token task is safely solvable by deterministic reduction, nor a
claim of dense native 4M attention.

