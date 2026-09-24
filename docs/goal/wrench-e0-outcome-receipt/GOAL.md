# E0 bounded outcome receipt

Status: accepted bounded contract slice; not an E0 completion claim  
Job: `W2-E0-OUTCOME-RECEIPT-20260924`  
Nonce: `OREC-a28c14`  
Baseline: `58aec9f1439b9440d89fc442f8fc49cf5d7b9464`

## Objective

Define a deterministic local receipt contract for task/run identity, source and
context receipt digests, evidence selection and omission, retrieval misses,
actual routing and attempts, verifier evidence, separately-provenanced task
outcomes, correction references, and reconciled accounting. The receipt keeps
references and hashes only. It does not persist prompts, source content, or
hidden reasoning and does not claim that an outcome is true.

## Acceptance

- A pure builder and validator return typed valid, incomplete, or invalid
  results with structured errors and no partial receipt on invalid input.
- Canonical serialized receipt is at most 64 KiB. Attempts are capped at 64;
  evidence, event, and work-call references are bounded at 256; IDs at 256
  characters. Strict schemas reject unsupported fields and raw-content keys.
- Selected and omitted evidence are unique and disjoint. Retrieval misses link
  to omitted evidence. Verifier and outcome evidence link to selected IDs.
- User-reported and independently-verified outcomes remain distinct.
  Independently-verified outcomes require verifier identity and linked
  evidence, with a fixed mapping: passed to completed, failed to failed, and
  inconclusive to partial.
- Bounded attempt and verifier/tool work records reconcile actual route, calls,
  retries, fallback counts, separate local/frontier token totals, token counter
  identities per route, and costs. No-call attempts cannot claim positive
  exact/estimated use; retry targets must be prior actual calls; fallback
  totals count actual calls only. Non-model work costs must be explicit zero
  or unknown. Unknown stays null and distinct from
  not-applicable or explicit zero. The completeness status names missing fields.
- Focused tests cover hash binding, stale misses, route/verifier failures,
  outcome provenance, timeouts, retries, no-model accounting, tokenizer
  mismatch, duplicate/oversized values, and forbidden content keys.

## Limits and trust boundary

The receipt is local metadata supplied by its caller. Hashes bind bytes only;
they do not prove provenance, authorization, verifier independence, user
consent, or task success. A caller must establish those facts before admission.
This slice has no persistence, review workflow, transport, model/provider
integration, or production-learning admission.

## Post-run join follow-up

The v2 follow-up in [the post-run join report](../../reports/wrench-e0-outcome-receipt/postrun-join-v2.md)
joins a ready E0 preparation to caller-supplied post-task evidence references
and the preparation-accounting digest. V2 verifier and outcome references use
the post-task evidence namespace, and task/run/session/verifier/post-task IDs
are constrained to compact opaque syntax. A missing session makes the receipt
incomplete. Six focused fixture functions passed by direct invocation under
Python 3.11.16; `pytest` is unavailable in the local runtimes.

This follow-up is an unpersisted, unauthenticated local join. It does not
capture a client lifecycle or prove verifier independence, consent, task truth,
or E0 completion. See the [evaluation record](../../evals/wrench-e0-outcome-receipt/postrun-join-v2.md)
for the bounded verification result and remaining gates.

Serialization first copies nested built-in dictionaries, lists, tuples, and
strings into a bounded owned tree. The exact output size and encoding are then
computed from that copy, so later caller mutations cannot change the measured
object.

## Independent review

Review job `W2-E0-OUTCOME-RECEIPT-REVIEW3-20260924`, nonce `ORR3-ff315a`,
accepted the final contract. The review verified route-specific usage,
retry/fallback reconciliation, outcome/verifier mapping, owned bounded
serialization, separate local/frontier token-counter identities, non-model
work cost handling, and typed failure on concurrent dictionary resizing.
Focused verification passed 28 tests. This acceptance covers the receipt
contract only; integrated E0 utility and authority evidence remains open.
