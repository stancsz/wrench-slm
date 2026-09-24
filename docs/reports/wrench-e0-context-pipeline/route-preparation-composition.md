# E0 route-to-preparation multi-file composition fixture

Job: `W2-NS-E0-ROUTE-PREPARATION-COMPOSITION-20260925`
Nonce: `ROUTECOMP-61D4`
Baseline: `e55178489100ff8e75290c23dd619607451db17a`

## Change

The new offline fixture runs a bounded literal search across one authored
source file, one log file, and one test file. It uses the returned
`RuleRouteResult` match paths and content hashes to select preparation inputs
and carries a bounded serialization of that caller-supplied result in a base
message. E0 preparation then exact-reads the selected paths and checks the
source hashes against the route evidence.

The sufficient-budget case requires and preserves all three named paths. It
asserts exact source identity joins, selected required evidence, a ready local
prompt, `route == none`, and the normal incomplete unknown-outcome receipt.
The tight case sets the context budget to one token and asserts no prompt,
`REQUIRED_EVIDENCE_OMITTED`, explicit omitted IDs with
`preserved_unit_exceeds_active_budget`, and an incomplete receipt.

## Verification

Focused Windows pytest used the existing offline cached environment. Temporary
fixture and test output stayed below `C:\\wrench-slm-data\\cache`:

```text
tests/test_e0_route_preparation_composition.py
2 passed
```

The fixture installs tripwires for the worker executor and common process
launch ports. It makes no task-success claim and defines no correctness oracle.
No client, provider, model, network, real data, or training was used.

## Limits

The caller constructs the preparation path list and route-result base message;
this is a structural caller-owned composition fixture, not authenticated
provenance. The local character counter and prompt serializer do not establish
target-runtime parity. The incomplete receipt correctly leaves task outcome
unknown. This slice proves neither customer utility nor E0 acceptance.

Independent review: **PASS**, job
`W2-NS-E0-ROUTE-PREPARATION-COMPOSITION-REVIEW-20260925`, nonce
`ROUTECOMPREV-4A10`. The read-only reviewer confirmed the route result feeds
the preparation paths and base message, the per-file hash join, the sufficient
and insufficient budget assertions, and the stated limits.
