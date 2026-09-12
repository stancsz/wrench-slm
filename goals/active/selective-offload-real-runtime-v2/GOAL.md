# Goal: earn a production deployment

Status: active
Updated: 2026-09-12
Owner: repository agent

## Steward-owned contract

### Outcome

Determine whether Wrench-SLM should be disabled, used as deterministic rules
with fallback, or used as a learned selective route. Progress from a bounded
prototype to production only through observed, reproducible evidence.

### Why

A small local model is useful only if it completes real work without increasing
wrong outcomes, boundary risk, total latency, or fully accounted provider cost.
Low but reliable coverage is acceptable. Rules-only and disable are valid
product outcomes.

### Sources of truth

- `NORTHSTAR.md` owns product direction.
- `ARCHITECTURE.md` owns the Wrench and LeanRouter boundary.
- This file is the only active execution contract.
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md` owns the frozen experiment.
- `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_RESULT.md` owns the result narrative.
- `docs/PRODUCTION_VALUE_SCORECARD.md` owns the readiness evidence map.
- `releases/v21/` owns V21 release claims.

### Invariants

- Routing uses only public request/context, declared tools, policy, real tool observations, and safe boundary state. Gold and offline scores are evaluation inputs only.
- Local execution is explicit, narrow, and read-only. Writes remain review drafts. Uncertainty, timeout, malformed output, tool failure, or unexpected mutation always falls back with the original request intact.
- Provider execution requires explicit attempt and token ceilings.
- Authored fixtures, simulations, local tests, and preflight receipts never become production, adoption, or savings claims.

### Milestones

| Stage | Outcome | Exit evidence | State |
| --- | --- | --- | --- |
| M0: Toy | Show the concept on authored examples. | Deterministic fixtures produce valid proposals and abstentions. | Done |
| M1: Safe prototype | Complete one useful read-only shape without an oracle. | Gold-free zero-provider success plus declared negative-path tests. | Done |
| M2: Reproducible candidate | Make the narrow capability independently inspectable. | Frozen identity, disjoint held-out rows, denominators, clean-clone verification, supported scope, bypass, and fail-closed operator receipt. | Done, locally bounded |
| M3: Useful pilot | Decide whether local execution creates end-to-end value. | Authorized redacted replay data passes intake; matched A/B/C episodes record all calls, tokens, cost, latency, corrections, failures, and outcomes; paired uncertainty supports an explicit decision. | Blocked |
| M4: Production candidate | Make the chosen path ordinary and operable. | Installable package, distribution contract, full CI, security checks, safe service boundary, health/metrics/logs, load and failure tests, restart/recovery, rollback, and a bounded shadow canary. | Not started |
| M5: Production proven | Demonstrate sustained real-world safety and value. | A time-bounded production window meets declared availability, error, latency, quality, cost, and rollback SLOs with complete denominators. | Not started |

### Current acceptance gate

- [x] M1 has no runtime dependency on expected answers, hidden labels, or offline scores.
- [x] M1 returns a local result with zero provider calls and fails closed on every declared negative path.
- [x] M2 freezes selector, verifier, policy, data, package, and receipt identities before final evaluation.
- [x] M2 records 90/600 accepted authored held-out cases, 90/90 successful accepted completions, zero accepted prohibited actions, and zero unexpected mutations.
- [x] M2 ships a clean-clone verifier and a fail-closed `DISABLE` operator decision.
- [ ] M3 trusted input includes authorized, deterministically redacted, joinable request/context and exact usage records, separated from synthetic and adversarial data.
- [ ] M3 uses a versioned price ledger, verified duration units, explicit provider ceilings, fixed endpoint/model identity, and complete accounting.
- [ ] M3 compares cloud-only, rules-plus-fallback, and learned-plus-fallback on identical tasks and executor behavior.
- [ ] M3 reports final outcomes and family-paired uncertainty, with zero observed local-caused wrong result or boundary violation.
- [ ] M4 operational gates are encoded in CI and demonstrated in a clean package and bounded canary.
- [ ] M5 SLOs and rollback are demonstrated on authorized production traffic.

### Decision rule

Enable the learned route only if it improves on rules-plus-fallback with complete accounting and no worse final outcomes than cloud-only. Choose rules-plus-fallback if rules create value and learning adds none. Otherwise disable local completion. An uncertainty interval crossing no benefit makes the result exploratory, not production proof.

### Non-goals and escalation

Do not retrain V21, broaden tool autonomy, deploy a production service, or make provider calls as part of this documentation goal. M3 requires both a passing trusted-data receipt and an explicit finite provider budget. Missing either is a genuine escalation condition, not permission to substitute synthetic data.

## Builder-owned execution record

### Current position

M1, M2, and the fail-closed operator package are implemented and locally verified. The learned route remains disabled. M3 cannot start because the inspected event inventory does not contain joinable prompt/context and usage records, and no paid-run ceilings are recorded.

### Evidence snapshot

- `releases/v21/evidence/selective-local-quality-v21.json` binds the maintained 600-row local-quality gate. Row-level runtime artifacts are not shipped, so this is archival identity verification rather than an independent replay.
- `releases/v21/evidence/operator-decision-v21.json` records `VALID_FAIL_CLOSED` and `DISABLE` because trusted readiness is rejected and no M3 receipt exists.
- `scripts/verify_trusted_readiness.py` rejects partial prompt/context, missing or duplicate IDs, estimated-only tokens, incomplete costs, unverified time units, and source read errors.
- `scripts/verify_public_claims.py` keeps public distribution and production-value language aligned with release and operator receipts.

### Immediate next action

1. Obtain an authorized export with public prompt/context, a stable gateway request ID, the matching provider usage record, verified time units, and a versioned price ledger.
2. Freeze the provenance-separated replay manifest and pass `python scripts/verify_trusted_readiness.py`.
3. Record finite attempt and cloud-token ceilings for the fixed M3 endpoint and model.
4. Run the frozen A/B/C workflow, analyze every episode, and apply the decision rule without tuning against final rows.
5. Only after M3 passes, materialize M4 implementation work.

### Validation to rerun before changing state

```powershell
py -3 -m pytest -q tests/test_selective_offload.py tests/test_policy.py tests/test_pilot_workflow.py tests/test_release_boundaries.py
```

Record fresh output and receipt paths here before marking a milestone done. The
full suite currently needs ignored local receipts and model manifests. Stronger
receipt verifiers and their inputs must be committed before they can become a
zero-preparation clean-clone acceptance command. Do not reuse historical test
counts as current proof.

### Remaining gap

The next missing artifact is not more authored fixtures. It is an authorized, redacted, joinable replay package plus a finite provider budget. Until both exist and M3 passes, production value is unverified and the safe default is `DISABLE`.
