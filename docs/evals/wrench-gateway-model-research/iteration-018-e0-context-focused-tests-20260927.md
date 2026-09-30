# Iteration 018: deterministic E0 context tests

Date: 2026-09-27 19:24 UTC (America/Edmonton)

Status: **54 FOCUSED TESTS PASSED; MODEL EFFECTIVENESS NOT MEASURED**

## Purpose

Advance the reliable mechanical foundation beneath local context selection,
compaction, and routing. This is a focused regression run of the E0
deterministic context path, not a Wrench LoRA evaluation or a token-savings
experiment. Worktree HEAD was
`af01304824f079a64b6c3902397a2034b843511a`; the source and tests were run as
they existed in the working tree, including the uncommitted
`e0_context_pipeline.py` change.

## Execution and result

The host's default Python 3.13.15 did not have pytest installed. To avoid
altering that interpreter or the pinned model runtime, pytest 9.1.1 was run in
an isolated `uvx` environment whose cache is under
`C:\wrench-slm-data\cache\wrench-e0-pytest-20260927-01`. The selected version
supports Python 3.10 and newer; the official [PyPI release record](https://pypi.org/project/pytest/)
lists the 9.1.1 universal wheel. The cached environment also resolved Pygments
2.21.0, colorama 0.4.6, iniconfig 2.3.0, packaging 26.3, and pluggy 1.6.0.
No project or model environment was changed.

Command, run from the repository root:

```powershell
uvx --isolated --cache-dir C:\wrench-slm-data\cache\wrench-e0-pytest-20260927-01 --python C:\Users\stanc\AppData\Local\Programs\Python\Python313\python.exe --from pytest==9.1.1 --no-progress pytest -p no:cacheprovider --basetemp C:\wrench-slm-data\cache\wrench-e0-test-tmp-20260927-01 -q tests/test_e0_context_pipeline.py tests/test_e0_request_record.py tests/test_e0_request_scope.py tests/test_e0_route_preparation.py tests/test_e0_route_preparation_composition.py tests/test_e0_source_injection_route.py tests/test_selected_segment_sources.py
```

Result: **54 passed in 11.19 seconds**. The selected files exercise exact
source/context assembly, pinned-artifact lifecycle, request and route
preparation, accounting receipts, selected-source references, and the
source-injection boundary. The test temporary directory remained below
`C:\wrench-slm-data`; its measured size was 57,498 bytes.

The executed source/test identities were:

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/e0_context_pipeline.py` | `84D626DBAB14D4C768E63636880F0C7B0A3EB8A5E10DB3B6A63F194C11A3ACD8` |
| `tests/test_e0_context_pipeline.py` | `0029E6F2A683CD0A015E82B96E8F5D25380641B77AC6FCBA7DC53267DE832105` |
| `tests/test_e0_request_record.py` | `62F2C46AE095635CFC3F7A33CDABB752CB5E28D78B3B37161499FAEC2C7093C5` |
| `tests/test_e0_request_scope.py` | `4FFF28BB143217BC8F7B04C33D5DC1172CA7F3C3C1B9F702C6EDC794A28FB8D1` |
| `tests/test_e0_route_preparation.py` | `3AF272082F057C24931DECC2477A9797B66594EC47FB1B1BE7B6FB1AA1C8847C` |
| `tests/test_e0_route_preparation_composition.py` | `56228829D3B9FCBEBBB9C451BAAE83EE1B591877BDAA71ED19F42B8E0634A430` |
| `tests/test_e0_source_injection_route.py` | `1421604D79B848A8E030CFF1DD5635AE3A91217744052B7D1F9A20650BA8458A` |
| `tests/test_selected_segment_sources.py` | `AC1AF50F821BF07557C872CCA86623D61CAD82E1A800F32944A40CC524ED188E` |

## Resource and storage record

Immediately before the tests, the host sample was 3,613 / 32,702 MiB RAM
free (11.05%), and the RTX 5060 Ti had 15,245 / 16,311 MiB VRAM free. After
the tests, RAM was 3,738 / 32,702 MiB free (11.43%) and VRAM was 15,236 /
16,311 MiB free. These are pre/post samples, not continuous telemetry; no
model was loaded and GPU utilization remained at 0%.

The storage admission for the package cache and test outputs reserved
100,000,000 bytes under job
`WRENCH-E0-CONTEXT-PYTEST-20260927-01`. The reservation was held through the
test, report edits, and final storage check, then released. The isolated pytest
cache is retained for future bounded tests and counts as Wrench-owned storage.

## Interpretation and next step

The passing tests strengthen confidence in deterministic context assembly,
lineage, accounting, and routing boundaries. They do not measure semantic
selection quality, coding success, actual downstream token usage, retries or
human rescue on matched work, 95/5 routing, 95% frontier-token savings, or
all-day engineering. The 95% claim remains unproven.

Next, turn the existing real-task study design into a runnable, no-spend
matched local/downstream accounting harness with explicit outcomes and exact
serialized-request token counts. Keep provider generations closed until the
SubRoute caller has a fail-closed aggregate spend cap and auditable receipts.
Recheck RAM before any model load or fit; the current free-RAM buffer remains
too small for fit-03's 25% start gate.
