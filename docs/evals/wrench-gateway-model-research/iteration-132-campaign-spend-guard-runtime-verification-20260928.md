# Iteration 132: campaign spend guard runtime verification

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-SUBROUTE-SPEND-GUARD-VERIFY-ITER132`  
Status: **complete; 8/8 focused local unit tests passed**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Verification

The final campaign-wide caller/ledger unit suite that Iteration 033 had left
unrun now passes in the pinned local Python environment:

```text
python -m unittest tests/test_subroute_budget_guard.py -v
Ran 8 tests in 2.143s
OK
```

Coverage includes shared campaign caps across approvals, cumulative exposure
limits, ledger identity changes, actual-cost settlement and unknown-cost
reserves, rounding, fail-closed missing approval, fail-closed missing
credentials, and a mocked provider capture that checks route controls and
does not persist prompts or raw model output. The credential-path test patches
both relevant environment values to empty strings. The mock capture uses an
in-process transport and did not contact SubRoute or a provider.

This raises confidence in the local caller ledger and mock receipt handling.
It does **not** verify that the running SubRoute service enforces the request
controls, that callback loading is active, that the OpenRouter wire body is
correct through real service configuration, or that provider billing matches
the ledger. No HTTP request, key value, provider call, or spend was used.
Live generation remains closed until there is an explicit numeric campaign
cap and the service-side ingress/wire-path findings are resolved.

## Exact source identities

- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.
- `tools/subroute_budget_guard.py`:
  `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B`.
- `tools/capture_subroute_teacher_traces.py`:
  `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6`.
- `tools/capture_minimax_teacher_traces.py`:
  `CA696597753995024650DEC7470379AAF91E2CF5F4EFAB26F19AEF07E361BA47`.
- `tools/provider_budget_guard.py`:
  `5D48687A5CF0CCB58C8B5D686256AD9FC2ECA713F9F36DA51D445E9BBAE21114`.
- `tests/test_subroute_budget_guard.py`:
  `62B8C3BFE58A0D46BE2189C766DF1FB348540A9A5B1A6363E64DF5076A8801B9`.

## Resource and storage

The checked host samples remained above the required runtime floor, at about
20% free RAM and 93% free VRAM. Storage admission and post-run status were
`WITHIN_LIMIT`; the latter counted 15,434,133,889 actual bytes, including
the Docker WSL model volume and hourly automation directory, plus the active
50,000,000-byte test reservation. The reservation is released after this
report is counted. C: had more than 139 GB free before the run.

## Next work

Keep this test result as caller-side evidence only. Next close the
service-side mocked ASGI ingress/body-shape gap without sending provider
traffic, then resume the representative local code-task and model-size
comparisons. The 95/5 outcome split, retained task success, frontier-token
savings, all-in cost, and all-day engineering remain unproven.
