# Evaluation: E0 route-to-preparation multi-file composition

Job: `W2-NS-E0-ROUTE-PREPARATION-COMPOSITION-20260925`
Nonce: `ROUTECOMP-61D4`

## Result

Both focused fixtures pass. A bounded `literal_search` route result finds a
synthetic marker in `src/service.py`, `logs/session.log`, and
`tests/test_service.py`. The fixture uses the matched paths and caller-owned
route-result reference to prepare exact source context from the same snapshot.

With a 256-token local context budget, all three required and preserved source
IDs are selected; their content hashes match the route's exact-read evidence.
The prompt is gate-ready locally, the route remains `none`, and the outcome
receipt remains incomplete because no task outcome is supplied.

With a one-token context budget, all three required/preserved IDs are omitted
with `preserved_unit_exceeds_active_budget`. The facade returns
`REQUIRED_EVIDENCE_OMITTED`, no prompt, and an incomplete outcome receipt.

## Evidence and disposition

- Focused Windows pytest: **2 passed**.
- Route-to-preparation source identity: exact per-path content hash equality.
- Worker executor and process launch tripwires: not called.
- Client, provider, model, network, real data, and training: not used.
- Task truth, downstream tokenization, dispatch enforcement, and utility: not
  evaluated.
- Independent review: **PASS**, job
  `W2-NS-E0-ROUTE-PREPARATION-COMPOSITION-REVIEW-20260925`, nonce
  `ROUTECOMPREV-4A10`.

This is evidence of bounded local composition and required-evidence overflow
accounting only. The route result and selected path list remain caller supplied
and unauthenticated. The test does not close E0 acceptance.
