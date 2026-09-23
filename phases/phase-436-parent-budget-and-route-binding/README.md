# Phase 436: parent-budget guard and route identity

Date: 2026-09-22

## Decision and scope

Paid canary remains on hold. No request to the port-4000 service or paid
provider was made. The active parent `COLLABORATION_CONTRACT.json` still has
`monetary_budget: 0`. The human's stated $500 ceiling does not silently rewrite
that contract, and there is still no provider-enforced cap reference or
provider-authoritative cost export.

The GPT-6 clarification for the service on port 4000 is recorded. A read-only
`/v1/models` inventory showed aliases, but no Wrench request has been
correlated to a requested alias and provider dispatch. The paid-cost validator
and export templates still expect `minimax-guided`. No model identity was
inferred or changed.

## Finding and change

The configured-baseline child-contract check accepted a positive child spend
cap without reading or enforcing the active parent's Q4 monetary budget. A
synthetic child cap of $0.10 therefore passed even while the active parent
budget was zero. This was a fail-open authorization gap.

The paired-canary preflight now reads and hashes the current parent contract,
checks its identity and finite nonnegative monetary budget, and rejects a
configured baseline when the budget is zero or the child's positive cap
exceeds it. Child contract schema v2 must bind the exact parent contract
SHA-256 as well as its ID, so an approval cannot silently survive edits under
the same ID. The authorization receipt records the parent contract hash and
parent budget alongside the child contract hash and cap. These checks occur
before output-directory creation and before any network activity. The parent
budget was not modified.

Regression coverage verifies zero-budget rejection before output or network,
child-cap-over-parent rejection, parent-hash mismatch rejection, and the exact
approved workload, endpoint, model, repetition, status, and cap requirements.

## Validation and evidence

- Focused canary and paid-cost validator tests: 10 passed.
- Full repository suite: 314 passed with 18 existing Windows asyncio deprecation warnings.
- Ruff check for the changed runner and tests: passed.
- Q4 contract validator: `VALID`.
- At this phase checkpoint, the active parent contract had zero monetary
  budget. Phase 437 records the later Q4 approval for one paired canary with a
  `$500` ceiling; provider-cap, route-alias, and cost-export prerequisites
  remain open.
- No port-4000 completion request, paid canary request, credential access, or
  spend occurred.
- The approved test-only Gate E soak is recorded separately in
  [Phase 435](../phase-435-router-soak/README.md). It did not contact the
  port-4000 service.

Source identities:

- `COLLABORATION_CONTRACT.json`: SHA-256
  `e954023bb077c0507fd9a53fed1d2e3dcb71aa0f2ccceb667d5edf23b6564d71`
- `tools/probe_paired_real_client_canary.py`: SHA-256
  `37b3ea1c3d5ec2609df7744f36c21a7e1c5bb0004cf0c35002ca4e930a34a929`
- `tests/test_paired_client_canary.py`: SHA-256
  `fa2f3241a1d2ccddbaad5fe35931c3dbc93286d6decf70e6f65da579c738e7ed`
- Phase 435 attempt 03 receipt: SHA-256
  `fcccf36643005a9e69aba60e4acb2ea9c14584e1cc1c45d5db13a8679ee3c400`

The Sol advisor escalation packet is retained as
[advisor-packet.txt](advisor-packet.txt). The escalation was invoked, but its
result was not captured in this phase directory. No route-identity change was
made without that advice or direct mapping evidence. The validator therefore
remains closed to a GPT-6 model change until a requested-alias to provider-model
mapping is supported by correlated export evidence.

## Q4 next decision

Recommendation: keep paid canary on hold. Before reconsideration, require an
explicitly updated active parent budget, a verifiable provider-enforced hard
cap within that budget, a provider cost export correlated to the canary request
and provider model identity, and a new exact child approval binding the parent
contract hash, workload, endpoint, requested model alias, repetition, and
maximum spend.

Alternative: defer the paid canary and continue only repository-local or
test-only work. Rollback is local: revert the preflight and regression tests
if they cause a test regression, while preserving receipts and leaving the
parent zero-spend contract intact. No deployment, provider call, or production
routing change is part of this phase.
