# Iteration 223: wire the larger E0 ingestion cap into the frozen screen

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-E0-SCREEN-INGEST-WIRE-ITER223-20260930-01`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Heartbeat-declared gateway goal SHA-256: `b847d638b0ca4f9c24041dccec2fb440861f0b27be0441e37e288057f701b027`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59` (mismatch)

## Change

The Iteration 220 tokenizer-only measurement called the Iteration 219 context builder, which still used the default 8,192 source-ingestion limit. As a result, the Iteration 221 core cap and Iteration 222 wrapper wiring did not reach this frozen screen.

`run_diverse_local_pilot_iter219._build_episode_context` now accepts an optional `source_ingestion_token_limit`, defaulting to the existing 8,192 tokens. The Iteration 220 measurement passes `MAX_SOURCE_INGESTION_TOKENS` (65,536) explicitly and records that setting in its receipt. No fixture, oracle, model identity, or final held-out data changed.

## Verification

Focused tests:

```text
.venv\\Scripts\\python.exe -m pytest -q tests/test_diverse_runner_preflight_iter219.py tests/test_iteration220_noise_fixture.py
7 passed in 2.03s
```

The added parameterized unit test verifies both the unchanged 8,192 default and explicit forwarding of 65,536. The first run failed because its fake prepared prompt omitted the test's required oracle quote; the fixture was corrected and the rerun passed. No tokenizer was loaded and no inference was run.

`git diff --check` reported no whitespace errors; only the existing line-ending normalization warnings appeared. Storage was `WITHIN_LIMIT` before and after the test. Before reporting, the checker showed 32,710,929,883 actual bytes plus 86,103,000 bytes reserved (32,797,032,883 projected) under the 50 GB limit. C: had 124,994,576,384 free bytes. RAM was 29.27% free; RTX 5060 Ti had 15,218 / 16,311 MiB free and 0% utilization. No Wrench or model process was found.

## Remaining gate

The frozen Iteration 220 screen was not executed. Its runner still fail-closes because the on-disk goal hash differs from the active heartbeat hash. After the identity is reconciled, rerun the tokenizer-only screen and report the paired token counts, failure/fallback denominator, quote visibility, omissions, latency and resource use. This wiring result establishes no token-saving percentage, task success, frontier saving or cost result.

## Identities

- `examples/gateway_context_mvp/run_diverse_local_pilot_iter219.py`: `0e0cb871bebeeedf43588819c25a62a2f2af046aada359666f037ca59014fd73`
- `examples/gateway_context_mvp/measure_iteration220_context_only.py`: `05f0ebed7e03dc28520e29f693b733454f656697aafe11321ee8f6ace294ba10`
- `tests/test_diverse_runner_preflight_iter219.py`: `8688b3a46a26128a61cccb4bc97112b1075be9fd42a7b507bdf9ac73c76b762a`
- Frozen Iteration 220 manifest: `f80b48ce3269154f45735323d2f97cc8d2110de5b20800f286980f310046d9f4`
