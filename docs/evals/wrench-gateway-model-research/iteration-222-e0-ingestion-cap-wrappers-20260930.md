# Iteration 222: expose bounded E0 ingestion limit through wrappers

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-E0-WRAPPER-INGEST-CAP-ITER222-20260930-01`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Heartbeat-declared gateway goal SHA-256: `b847d638b0ca4f9c24041dccec2fb440861f0b27be0441e37e288057f701b027`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59` (mismatch)

## Change

Iteration 221 added a separately bounded source-ingestion limit to `prepare_e0_context`, leaving the selected-context and prompt budgets capped at 8,192 tokens. This iteration exposes `source_ingestion_token_limit` through both `route_and_prepare_e0_context` and `prepare_opencode_e0_context`. Both wrappers default to the historical 8,192-token ingestion limit and forward explicit values to the core function. The core validation still owns the 65,536-token maximum and checks the ingestion limit against the selected-context budget.

No model, provider, or sealed data was used. No route, permission, installed adapter, or foundation behavior was changed by this wrapper wiring.

## Verification

Ran:

```text
.venv\\Scripts\\python.exe -m pytest -q tests/test_e0_route_preparation.py tests/test_opencode_context.py tests/test_e0_context_pipeline.py
61 passed in 8.30s
```

New wrapper tests assert that a 16,384-token ingestion limit reaches core E0 through the route-preparation wrapper and the OpenCode wrapper. Existing core tests cover default rejection, successful larger bounded ingestion with a smaller selected-context budget, invalid settings, and fail-closed behavior above the hard cap.

`git diff --check` reported no whitespace errors. Git emitted line-ending normalization warnings on existing dirty files. The broader integration command from Iteration 221 still excludes one baseline OpenCode 2.0.12 projection/observation test because the E0 pipeline currently accepts only `generic` and `opencode-2.0.15`; this narrow 61-test run does not resolve or claim that separate compatibility gap.

The storage checker reported `WITHIN_LIMIT`: 32,710,818,051 bytes actual and 136,103,000 bytes reserved, for 32,846,921,051 projected bytes under the 50,000,000,000-byte cap. At final verification, system RAM free was 29.45% and GPU 0 had 15,196 / 16,311 MiB free with 0% utilization. These resource readings were not used to admit inference; no inference was started.

## Remaining gates

The active-goal hash mismatch remains unresolved. Therefore the frozen Iteration 220 tokenizer screen was not rerun, and no exact token-saving claim follows from this wrapper change. Once the goal identity is reconciled, rerun the frozen screen with an explicit ingestion limit and report token counts, failures, omissions, latency, and resources before considering any model runtime.

## Identities

- `src/wrench_harness/e0_context_pipeline.py`: `7dbf627cec54c1f3fc8812ac2fd9e0893aa0c39dcfdbe5d531011f3796e666a2`
- `src/wrench_harness/e0_route_preparation.py`: `93531614ae4b18157cc04303f1619358ca5f6130bf5b915ab274564b6436a275`
- `src/wrench_harness/opencode_context.py`: `05eb93591d943ace6d964e222b8c1de6e2c0197ecb63e6824798171a7366a886`
- `tests/test_e0_context_pipeline.py`: `d9c6bd85b25515c25dbfc190bee1667379f0fbf13ec0179a846b4e179302b846`
- `tests/test_e0_route_preparation.py`: `4d6901b6872b9abafd15325a5d97de84c75381f996453d253bfc3b38559748a4`
- `tests/test_opencode_context.py`: `abebe3740034b9afc6d0b73fe9763d68783d360922c90bce69ab8bcf5c25423c`
- Iteration 221 report: `507779ed79d7b35868ca777f0fb2f63b66914af271cd6921855bc4f87c71ee27`
