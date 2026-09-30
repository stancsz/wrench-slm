# Iteration 030: explicit provider-cost accounting

Date: 2026-09-27 (America/Edmonton)

Status: **COST DEFAULT CLOSED; FOCUSED TESTS PASSED; NO PROVIDER REQUEST**

## Finding and change

The teacher request path remains disabled, and captured teacher responses keep
missing costs as `null`. However, `_arm_record` still defaulted an omitted
`cost_usd` argument to `0.0`. A future paid call site could therefore serialize
an unreported provider charge as zero if it forgot to pass the cost.

Changed `tools/run_diagnostic_worker_arms.py` so `_arm_record` requires every
caller to provide a cost value explicitly. The no-provider Wrench diagnostic
now passes `0.0` explicitly for frontier cost. An actual provider request can
still pass `None`, which remains null in the emitted record. Added a regression
test that omission raises `TypeError` and missing provider cost remains null.

## Verification

Ran the focused offline test command using the already populated pytest cache:

```powershell
uvx --offline --isolated --cache-dir C:\wrench-slm-data\cache\wrench-teacher-budget-test-20260927-01 --python C:\Users\stanc\AppData\Local\Programs\Python\Python313\python.exe --from pytest==9.1.1 --no-progress pytest -p no:cacheprovider --basetemp C:\wrench-slm-data\cache\wrench-explicit-cost-test-tmp-20260927-01 -q tests/test_diagnostic_worker_arms.py
```

Result: **13 passed in 1.34 seconds**. `git diff --check` reported no
whitespace errors; Git printed line-ending normalization notices for existing
modified files. HEAD was `af01304824f079a64b6c3902397a2034b843511a`.

| File | SHA-256 |
| --- | --- |
| `tools/run_diagnostic_worker_arms.py` | `91C028A6C10C921973DC4734B75D0ADD90EC4AEF15340D3F963627935336EBE1` |
| `tests/test_diagnostic_worker_arms.py` | `9E5F597E25D857CA434C77E8C5533E3643D17CA2824733E73253062EA8B81991` |

## Limits and next action

Live teacher calls remain disabled. This change prevents one future accounting
mistake; it does not implement an aggregate spend ledger, provider-side hard
cap, durable billing validation, or all-in cost calculation. No SubRoute
request, inference, or training occurred.

The post-test sample was 3,734.2 / 32,701.8 MiB free RAM (**11.42%**) and
15,224 / 16,311 MiB VRAM free on the RTX 5060 Ti. This is below fit-03's 25%
free-RAM start gate. The storage checker was `WITHIN_LIMIT`: 10,989,639,220
actual bytes plus 6,403,000 reserved bytes, projected 10,996,042,220 under the
50,000,000,000-byte ceiling. C: had 141,300,023,296 bytes free. The 300,000-byte
reservation `WRENCH-EXPLICIT-COST-RECEIPT-20260927-01` covered this bounded
source/test/report change and was released after final accounting. The final
checker status remained `WITHIN_LIMIT` at 10,989,641,483 actual bytes plus
6,103,000 bytes reserved.

The Wrench 95% local completion, 5% frontier escalation, 95% frontier-token
reduction, all-in cost, and sustained engineering targets remain active and
unproven. The hourly heartbeat remains the execution path for the next
candidate-admitted local experiment.
