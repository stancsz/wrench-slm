# Phase 443: paid-canary parent route binding

Date: 2026-09-22

## Finding

The active Q4 parent scope binds the one paid paired canary to GPT-6 at
`http://localhost:4000/v1`, with one repetition and a `$500` maximum. The
exact GPT-6 alias remains unselected. The child validator binds a child to the
parent ID, hash, and budget, and verifies the child's requested alias against
the run arguments. It does not verify that the child alias and expected
provider model remain within the parent-authorized route.

A synthetic in-process child using alias `openrouter` and expected provider
model `openrouter/minimax/minimax-m3` passed `_validate_paid_baseline_child_contract`
against the actual active GPT-6 parent hash, with a synthetic `$0.01` cap and
the approved workload hash. The child contained synthetic approval markers.
No output directory, network request, or model call was made. This demonstrates
validator behavior only, not approval or permission to run the child.

## Advisor review

Sol assessed this as a fail-open route-authorization defect. Recommendation:
require a structured, hash-bound parent route allowance and reject any child
whose alias or resolved provider model falls outside it. Missing allowance
must block child creation and execution. Stop all paid-canary child creation
and runs until a human binds the route; do not choose the GPT-6 variant.

Consultation: `codex-sol-advisor`, request
`chatcmpl-codex-advisor-5c2c066d77fb`; 504 prompt tokens, 239 completion
tokens, 743 total; packet length 1,793 characters; `decision_changed: true`.
The advice changed the next action from treating the issue as route-choice-only
to proposing a structured parent-child scope guard before any child can be
issued. The advisor result is a recommendation, not authorization or proof of
a repair.

## Q4 decision at handoff

Recommended option: authorize a local schema and validator change requiring a
machine-readable parent route allowance. A missing allowance or child alias /
expected-model mismatch would fail closed. Do not populate or broaden that
allowance until the human resolves the separate route choice. The current
parent would therefore continue to block every paid child until explicitly
updated.

Alternative: defer the guard change and keep the canary stopped. This leaves
the mismatch behavior reproducible if a future operator supplies a child
contract inconsistent with the parent's GPT-6 scope.

The change would alter the machine-readable Q4 parent shape and canary
preflight, but would not select a provider, create a child, make a provider
request, or change the `$500` ceiling. If tests or compatibility checks fail,
rollback only the new guard and its tests, preserve the active parent contract
and all receipts, and keep paid execution disabled. No reply means defer and
leave the current scope and code unchanged.

## Subsequent human decision

On 2026-09-22, the human approved the local fail-closed route guard and then
selected MiniMax as the comparison route. The exact route is the existing
loopback gateway alias `openrouter`, which Phase 442's read-only metadata
mapped to `openrouter/minimax/minimax-m3`. Phase 444 records the amended Q4
parent allowance and local validator change. This route selection does not
waive the provider hard-cap, authoritative cost-export, or child-contract
prerequisites, and no provider request has been made.

## Source identities at handoff

- `COLLABORATION_CONTRACT.json`: SHA-256
  `CF255E5C73AE9DF58C5FD29D879BD7AAA9A2972245EFB61A3C4C597F65D9B4B5`
- `tools/probe_paired_real_client_canary.py`: SHA-256
  `62851F07A559FFF3DE2FCFDC9B8C56878BC1D6DD7013821C081EAA1F1830F7D5`
- `tools/validate_paid_cost_receipt.py`: SHA-256
  `874CE89454EC7F1609F04832431A4752A26534EE553753A90141000305553F74`
- `tests/test_paired_client_canary.py`: SHA-256
  `A551DF009A7DB737A62977648EB9E742C0B194B73900CF9D15EA711B76C92415`
