# Goal: oracle-free selective offload with trusted evidence

Status: active
Updated: 2026-09-11
Owner: repository agent
Related compatibility record: [`goal.md`](../../../goal.md)

## Steward-owned contract

### Outcome

Establish whether a narrow, read-only local completion path can safely handle
a useful fraction of routine developer requests and reduce stronger-model work
after local validation, fallback, latency, and provider accounting are included.
The learned proposal is optional. Rules-only is a valid outcome.

### Source of truth

- `NORTHSTAR.md` owns durable product direction.
- This file owns the active documentation and evidence contract.
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md` owns the
  frozen experiment protocol.
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_RESULT.md` owns the current
  result narrative and must distinguish diagnostics from gate evidence.
- V21 release claims remain owned by `releases/v21/` and its handoff.

### Runtime invariants

- Routing sees only public request/context, declared tools, policy, real tool
  observations, and safe runtime boundary state.
- Runtime code never reads expected answers, fixture gold, hidden task labels,
  or offline scores to select a local route.
- Only an explicit narrow read-only action may execute.
- Writes remain review-only drafts.
- Invalid, uncertain, timed-out, failed, malformed, or boundary-changing cases
  fall back with the original request and relevant observation.
- Provider execution requires explicit attempt and token ceilings and explicit
  operator authorization.

### Acceptance criteria

- [x] M1: callable oracle-free local route, zero provider calls on accepted
  local cases, and explicit fallback tests for invalid, irrelevant, timeout,
  tool-error, verifier-failure, malformed-observation, and mutation cases.
- [x] M2: fresh disjoint evaluation with runtime routing and offline scoring
  recorded separately, nonempty correct local coverage, zero accepted
  prohibited actions, and zero unexpected mutation.
- [ ] M2-data: authorized production-derived traces where available, deterministic
  redaction, provenance-separated synthetic/adversarial strata, frozen hashes,
  and a versioned cloud price ledger.
- [ ] M3: matched cloud-only, rules-plus-fallback, and learned-plus-fallback
  episodes with complete calls, tokens, cost, latency, outcomes, and failures.
- [ ] M4: reproducible operator decision, supported scope, bypass procedure,
  receipt paths, denominators, and an honest enable/rules-only/disable verdict.

### Non-goals and escalation

Do not retrain V21, create a new model tier, deploy production services, grant
arbitrary shell access, or claim production value from authored fixtures. A
missing provider ceiling, missing trusted data, evidence-integrity failure, or
product decision outside this contract is an escalation. Do not relabel it as
ordinary implementation difficulty.

## Builder execution record

### Current approach

Document and verify the existing selective runtime, readiness gate, protocol,
and release boundaries before adding new behavior. Keep the maintained V21
package workflow separate from the experimental pilot workflow.

### Progress

- [x] Repository architecture and product contract documented.
- [x] Code, script, test, and workflow surfaces indexed in
  `docs/reference/CODE_GUIDE.md` and linked from the main documentation paths.
- [x] Current release, data, pilot, and historical boundaries documented.
- [x] Existing trusted-scenario readiness rejection recorded in the active
  result documents.
- [ ] Complete or independently verify M1 through M4.

### Discoveries and decisions

- The current worktree contains a large selective-offload implementation and
  trusted-scenario intake changes. They are user work and are preserved.
- Metadata-only source scans currently do not provide replayable prompt/context
  records, a price ledger, or trustworthy duration units. The readiness gate
  correctly blocks paid M3 on those reasons.
- A release-ready V21 adapter and a production-ready selective route are
  different claims and require different evidence.

### Validation

The production value scorecard is saved in
`docs/PRODUCTION_VALUE_SCORECARD.md`. The readiness gate was rerun against the
current paired receipt and returned `REJECTED` for missing prompt/context,
missing price ledger, unverified duration units, and replay readiness. The
focused safety/readiness suite passed 29 tests and the full active-source suite
passed 212 tests with one warning. A fresh zero-provider preflight verified the
frozen identity for all 600 evaluation tasks and wrote
`artifacts/selective-offload-real-runtime-v2/preflight-20260911/run.json`.
Runtime and matched workflow acceptance remain open.

The authorized-run wrapper was also exercised with the rejected receipt. It
returned exit code 1, printed `Trusted-data readiness rejected`, and created
no runner output, confirming that the paid runner is not started before the
trusted-data gate passes.

### Remaining gap

M3 must remain blocked until an operator supplies an explicit provider attempt
ceiling and cloud-token ceiling and M2-data passes the independent readiness
gate. No frontier-token savings claim is permitted before a matched A/B/C run.

Operator approval was supplied on 2026-09-11. A fresh read-only inventory then
found 92,431 events and 12,226 completed tool records, but still no prompt or
context fields. The adjacent consultation store has message arrays but no
request or trace identifier that can join them to provider usage. The
2026-09-11 synthetic live canary and deterministic audit are valid plumbing
evidence, but Wrench abstained and saved zero provider tokens, so they do not
satisfy M3 or establish production value. The remaining data requirement is
an authorized export that carries public prompt/context, a stable gateway
request ID, and the corresponding usage record.
