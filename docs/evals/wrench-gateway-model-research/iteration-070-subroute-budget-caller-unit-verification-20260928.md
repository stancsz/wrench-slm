# Iteration 070: verify the SubRoute campaign-budget caller offline

## Scope

Completed the previously pending focused unit run for the campaign-wide
SubRoute caller and durable spend ledger. The user-directed route remains
`http://127.0.0.1:4000`; this run used only mocked transport and did not send
an HTTP request.

Repository HEAD before the run: `af01304824f079a64b6c3902397a2034b843511a`.
The five source/test identities matched the existing Iteration 033 review:

| File | SHA-256 |
| --- | --- |
| `tools/subroute_budget_guard.py` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` |
| `tools/capture_subroute_teacher_traces.py` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` |
| `tools/capture_minimax_teacher_traces.py` | `CA696597753995024650DEC7470379AAF91E2CF5F4EFAB26F19AEF07E361BA47` |
| `tools/provider_budget_guard.py` | `5D48687A5CF0CCB58C8B5D686256AD9FC2ECA713F9F36DA51D445E9BBAE21114` |
| `tests/test_subroute_budget_guard.py` | `62B8C3BFE58A0D46BE2189C766DF1FB348540A9A5B1A6363E64DF5076A8801B9` |

## Result

The system Python 3.13 did not have `pytest`, so that initial command ran zero
tests. Reused the existing project Python 3.11.16 and ran:

```text
python -m unittest discover -s tests -p test_subroute_budget_guard.py -v
```

**8 tests passed in 1.917 seconds.** Coverage includes request reservation
rounding; cumulative and cross-job campaign-cap enforcement; full-reserve
retention on ambiguous calls; refusal after approval identity changes; and
mocked capture settlement plus fail-closed behavior when approval or the
SubRoute key is missing. The capture fixture is synthetic, and the transport
was injected in-process. The missing-key test patches both credential
environment entries to empty; no credential value was read.

RAM was 4,830.1 / 32,701.8 MiB free (14.77%) before the run and 4,844.8 MiB
(14.82%) after it. VRAM was 15,255 / 16,311 MiB free at admission. Storage
reported `WITHIN_LIMIT`, at 10,991,806,268 actual bytes before releasing the
test reservation. Synthetic fixtures and SQLite files were confined to the
repository's temporary test root; Python bytecode caches remained inside the
repository and were included in the storage scan. The prior caller-test reservation
`WRENCH-SUBROUTE-BUDGET-CALLER-20260927-01` was released after the test process
stopped and outputs were accounted. The separate 100,000-byte documentation
reservation is tracked under
`WRENCH-SUBROUTE-BUDGET-UNIT-VERIFICATION-ITER070-20260928`.

## Limits and next gate

This verifies local ledger logic and the mocked receipt path only. It does not
verify that live SubRoute forwards the metadata marker to the OpenRouter
callback, the provider selected for a real request, actual token usage or
billed cost, or the model's task quality. No approval file with a numeric
campaign cap exists; no completion request or provider spend is authorized by
these tests. Keep generation closed until the current caller/control path is
verified and an explicit capped approval is present. No fit, inference,
benchmark, or held-out-data operation ran. Fit 03 remains gated by its 25%
free-RAM start threshold.
