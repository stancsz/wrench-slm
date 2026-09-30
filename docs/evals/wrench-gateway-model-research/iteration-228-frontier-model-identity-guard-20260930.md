# Iteration 228: reject mixed upstream models in paired usage

Date: 2026-09-30 (America/Edmonton)
Job ID: `WRENCH-ITER228-FRONTIER-MODEL-IDENTITY-GUARD-20260930-01`
Scope: local accounting code and synthetic unit test only.

## Change

`aggregate_paired_frontier_usage()` now requires every captured response in the paired dataset to report the same upstream model. If one route alias serves different upstream models across either arm or retry, aggregation fails with `response_model_mixed_or_missing` instead of emitting a pooled token-reduction ratio. The returned summary now includes that verified single response-model string.

The regression fixture uses the same synthetic route alias with different response model names across the baseline and Wrench arms and asserts fail-closed behavior. It does not contact a provider.

## Verification

Focused command:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_frontier_usage.py
7 passed, 3 subtests passed in 0.59s
```

Python compilation also succeeded for `src/wrench_harness/frontier_usage.py`. No model, tokenizer, SubRoute, provider, credential, or sealed data was accessed. The route and budget guard were not changed.

## Artifact identities

- `src/wrench_harness/frontier_usage.py`: `E4A6A3B94310458058AB51057F710EF7D946AD0CAB4D3FBBD1602D6B251040FE`
- `tests/test_frontier_usage.py`: `9DA8FC4864464DA364E56E583F2F50D5C40CBB791EF291456BA4A45B55007D54`

This hardens upstream identity comparability; it does not verify provider billing. `response_usage_is_billing_verified` remains false. Audited all-in cost, representative task success, gateway model selection, and the full 95/5/95 thresholds remain unproven.

The on-disk gateway goal SHA-256 remains `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`, which differs from the active heartbeat value `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`. Frozen model/tokenizer screens remain fail-closed on that mismatch.
