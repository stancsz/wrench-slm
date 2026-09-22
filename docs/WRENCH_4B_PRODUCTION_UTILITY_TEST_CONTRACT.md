# Wrench productive-value evidence contract

This is the active evidence contract for the narrowed Wrench goal. The former
broader 4B model-selection and hardware contract is preserved at
[docs/archive/2026-09-22/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](archive/2026-09-22/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md).

## Decision

The North Star decision is based on a paired real-workflow canary. Outcomes
are `PASS_WRENCH`, `INCONCLUSIVE`, or `FAIL_WRENCH`. Missing or unapproved
evidence is `INCONCLUSIVE`, never a pass.

## Scope

The active candidate is the bounded hybrid Wrench worker with its independent
verifier, two-state client protocol, and three named client surfaces:
OpenCode, DeepSeek Harness, and Claude Code. The active scope excludes learned
free-form routing, native dense 4M generation, 5060 Ti verification, broad
client expansion, and packaging as an independent workstream.

## Gate A: deterministic correctness and safety

- Eligible routine tasks match their typed action and argument oracles.
- Out-of-boundary tasks abstain with the expected reason.
- Every accepted proposal passes the independent verifier.
- Prohibited accepts: `0`.
- Unexpected mutations: `0`.
- Invalid, uncertain, timed-out, malformed, or boundary-changing requests
  preserve the original request and use the stronger fallback.

## Gate B: paired productive value

Run the same authorized workload through:

1. the stronger-model baseline;
2. the Wrench hybrid path with the same verifier, fallback, retry, and
   correction policy.

Reconcile task volume and weighted workload mass for final success, correct
acceptance, abstention, fallback, retries, corrections, local tokens,
frontier tokens, total tokens, provider cost, latency, verifier time,
compaction overhead, prohibited accepts, and mutations.

The Wrench path must show no material final-success or safety regression,
meaningful successful-task latency improvement, and at least 95% net
frontier-token savings after all overhead. Fast refusals do not count as fast
completion.

## Gate C: bounded client protocol

OpenCode, DeepSeek Harness, and Claude Code must each complete a bounded
read-only or review-only flow with:

- a typed Wrench proposal;
- an independently verified action;
- one hash-bound final answer when a tool result is returned;
- no free-form tool execution;
- no repeated proposal loop;
- no third frontier call;
- correlated client and Wrench receipts.

## Gate D: sustained operations

Exercise concurrency, cancellation, timeouts, malformed responses, worker
failure, restart and recovery, circuit breaking, accounting, and no-mutation
behavior. No silent request loss, cross-request state leakage, unbounded retry,
orphaned worker, or fallback loss is allowed.

## Gate E: targeted expansion

Only add a new deterministic handler when real canary traces show material
fallback volume and the handler has a typed schema, an independent verifier,
bounded authority, and a regression receipt. Synthetic coverage alone does not
justify expansion.

## Evidence integrity

Every result must preserve source, artifact, runtime, verifier, workload,
resource, request identity, raw failures, and complete token, cost, retry,
correction, and latency accounting. A smoke, HTTP success, synthetic replay,
model size, or lower teacher-call count is not productive-value evidence.

Final acceptance, publication, deployment, spending, and production routing
remain human decisions under the Q4 collaboration contract.
