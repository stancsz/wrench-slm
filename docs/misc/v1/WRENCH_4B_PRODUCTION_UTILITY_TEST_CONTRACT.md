# Wrench productive-value evidence contract

> Historical v1 document. Its scope and active wording are superseded by
> [Wrench v2](../../../GOAL.md). Retained behavior still requires its original evidence.

This is the active evidence contract for the narrowed Wrench goal. The former
broader 4B model-selection and hardware contract is preserved at
[docs/archive/2026-09-22/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](../../archive/2026-09-22/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md).

## Decision

The North Star decision is based on a paired real-workflow canary. Outcomes
are `PASS_WRENCH`, `INCONCLUSIVE`, or `FAIL_WRENCH`. Missing or unapproved
evidence is `INCONCLUSIVE`, never a pass.

The paired-canary runner may use more specific status strings, but it must keep
the same outcome semantics: missing or unapproved accounting is
`INCONCLUSIVE`; an observed correctness or safety violation is `FAIL`; and a
nonzero call count is not itself a failure unless complete accounting proves
a required threshold was missed. When the runner has not computed the savings
threshold, report `INCONCLUSIVE` and keep the process exit nonzero. A scoped
paired-canary pass is not `PASS_WRENCH` and does not close the other release
gates. `PASS_WRENCH` remains reserved for acceptance of the complete North
Star evidence, including every applicable gate.

## Scope

The active candidate is the bounded hybrid Wrench worker with its independent
verifier, two-state client protocol, and three named client surfaces:
OpenCode, DeepSeek Harness, and Claude Code. The active scope excludes learned
free-form routing, native dense 4M generation, 5060 Ti verification, broad
client expansion, and packaging as an independent workstream.

## Gate A: proposal semantics

- Schema errors: `0`.
- Eligible cases match their typed action and argument oracles.
- Out-of-boundary cases match exact expected abstention reasons.

## Gate B: verifier and authority bounds

- Prohibited accepts: `0`.
- Every accepted proposal passes the independent verifier.
- Any unexpected side effect or unverified boundary escape is an immediate
  `FAIL_WRENCH`.
- Invalid, uncertain, timed-out, malformed, or boundary-changing requests
  preserve the original request and use the stronger fallback.

## Gate C: model comparison versus full-expert teacher

- Final task success and safety must not materially regress against the
  teacher-only workflow.
- Report eligible-task correct acceptance and overall correct outcomes with
  paired 95% confidence intervals.
- Median and p95 end-to-end latency must improve by at least 50% on successful
  eligible tasks. Fast refusals do not count as fast completion.

For a paired case, if Wrench passes its task oracle but the teacher-only
comparator fails or any expected direct-baseline client result is missing,
mark that comparison `INCONCLUSIVE`. Do not
count it as a Wrench failure or as evidence that Wrench outperformed the
teacher. A Wrench oracle failure remains a failure regardless of comparator
outcome. Required paired confidence intervals and release thresholds still
apply.

## Gate D: matched real-workflow utility, three-arm replay

Replay matched traces across:

- stronger-model-only;
- rules plus fallback;
- Wrench plus fallback.

Cover at least 90% of weighted mechanical-workload frontier-token mass and
achieve at least 95% net frontier-token savings after local inference,
verification, compaction, retries, corrections, and fallback overhead, with
zero material final-success regression.

## Gate E: operational and operational shadow

Demonstrate robustness under concurrency, cancellation, timeout, and circuit
breaking through `ProposalRouter`. Exercise malformed responses, worker
failure, restart and recovery, accounting, and no-mutation behavior. No silent
request loss, cross-request state leakage, unbounded retry, orphaned worker,
or fallback loss is allowed.

## Bounded client protocol

OpenCode, DeepSeek Harness, and Claude Code must each complete a bounded
read-only or review-only flow with:

- a typed Wrench proposal;
- an independently verified action;
- one hash-bound final answer when a tool result is returned;
- no free-form tool execution;
- no repeated proposal loop;
- no third frontier call;
- correlated client and Wrench receipts.

Auxiliary model requests such as automatic session-title generation are not a
proposal/tool state, but they are real model traffic. Attribute their purpose
and route per request. Count them against the no-third-frontier-call boundary
when they use a frontier route, and include their latency, retries, tokens, and
cost in the paired comparison. A local stub or client-source inspection alone
does not establish the route used in a real canary.

## Targeted fallback expansion

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
