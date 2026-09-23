# Phase 448: paired-canary trace source readiness audit

Date: 2026-09-23

## Scope

Performed a metadata-only, read-only audit of the owner-authorized Wrench
capture to determine whether it can support a real-workflow paired canary.
The prompt and context values were not printed, copied, or written into this
repository. No model, provider, credential, training, or evaluation call was
made. No file was written to D: because that drive is unavailable in this
environment.

## Source identity

- Source: `C:\Users\stanc\github\lean-router\logs\wrench-capture\wrench-authorized-capture.jsonl`
- Size: 42,327,168 bytes
- SHA-256: `3c6e1e549a57d8b02ff20f5dcc27d061766050fa862d542808d9b381387420fe`
- Owner authorization to inspect: received in the current Codex conversation.

## Findings

- 397 JSONL records parsed; zero parse failures.
- 395 records identify as `observed_production_replay`; 2 identify as
  `synthetic`.
- All 397 rows set `replay_eligible=true` and
  `capture_redaction.status=complete`, with method
  `deterministic-pattern-v1`.
- All rows have a `request_id`, `prompt`, and `context`. No consent, license,
  or approval field is present in the records.
- An automated pattern scan found email-shaped strings in 199 records. This
  is a privacy-review flag, not a claim that all matches are personal data or
  that the redactor failed. Prompt and context text still require a reviewed
  redaction check before wider use.
- Exact `request_id` to event `req_id` matching found all 397 capture IDs in
  the Sept. 11 and Sept. 12 event logs. The event logs contain 358 request
  event rows across 352 unique IDs, and 358 decision-outcome records; 45 IDs
  have no request event. The joined event set also has 381 routing decisions, 1,188
  admitted outbound-context events, 384 HTTP records, and 65 expert-checkpoint
  transitions.
- On a per-ID join, 337 requests have all five of these event types: request,
  decision outcome, routing decision, HTTP record, and outbound context. The
  remaining 60 IDs have only partial event coverage; 16 have only an HTTP
  record among those five event types.
- Across all 358 request event rows, the logs report 12,646,806 prompt tokens
  and 379,926 completion tokens, with request duration p50 6.33 seconds and
  nearest-rank p95 45.26 seconds. A provider-usage source is explicitly
  recorded on 315 rows. Six IDs have duplicate request event rows, so these
  event-row totals are not deduplicated task totals. They are baseline
  routing/provider measurements, not Wrench savings or Wrench latency.
- The largest request domain is `minimax_owned_execution`: 286 event rows,
  12,544,048 prompt tokens, and 128,876 completion tokens. This is a
  candidate workload stratum, not yet a verified Wrench-eligible mechanical
  task family. Other event-row domains are 43 `cheap_plus_rocket`, 19
  `execution_consultation`, 6 `slider_suppressed_cheap`, 3 `frontier_brief`,
  and 1 `execution_checkpoint`.
- Decision outcomes include 321 `completed`, 23 `provider_unavailable`, 10
  `base_executor_fallback`, and 4 `ast_linter_passed`. Those indicate request
  handling outcomes only. No independent verifier result or final coding-task
  correctness oracle was joined. Provider cost is also absent, and the event
  schema does not supply the full retry/correction accounting needed for net
  savings.
- The event logs are `2026-09-11.jsonl` (10,760,607 bytes, SHA-256
  `f86d871d183afc919ff51109938eb52bc8f89823d5f3bf31faf314dd18498cc9`) and
  `2026-09-12.jsonl` (7,000,543 bytes, SHA-256
  `92af39219d19a2114d76a63ee8c8900a7a1b850d4f5ab7a2aae234c590ea94fd`).

## Readiness decision

The capture and event logs form a useful candidate workload source for canary
preparation. They are not yet a replay-ready matched workload or training-ready
source. Owner authorization covers inspection, but does not supply a
hash-bound consent/license receipt or an independent redaction review. Event
joins recover routing and provider accounting for part of the capture, but not
task correctness, verifier results, or full cost/retry/correction accounting.
Keep the originals untouched and avoid copying them until D: is available and
the required review and joins are in place.

The next useful step is to establish consent and redaction provenance, then
find or collect independent task/verifier outcomes and provider-cost receipts
that join to these requests. Any missing fields, the 45 requests without a
request event, and unmatched outcomes must remain explicit in the paired
replay. The observed token mass can help define the workload only after the
eligible mechanical subset is reviewed and labeled.

## Limits

This phase does not claim user consent on behalf of any third party, prove
that deterministic redaction removed every sensitive value, establish
workload-universe completeness, or close any utility gate. It records a
source-readiness finding only.
