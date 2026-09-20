# Phase 191: persistent prefill cache and native-lane boundary

Date: 2026-09-20

## Product boundary

Dense native 2M/4M attention is not a Wrench selling point or release gate.
The supported product path is a model-local endpoint that accepts the raw
monster payload, runs embedded deterministic MapReduce, retrieves bounded
evidence, and gives the small model a compact effective working context.

If a future dense-native lane is enabled, its first model-side layer must be a
fast pruner and cherrypicker that emits a 32K to 64K active context while
preserving newest intent, authority and dependency context, and hash-bound
lookup evidence. This is an optional native-lane architecture target.

## Implementation

The content-addressed `MechanicalPrefillIndex` is now persistent for the life
of a package server. It has a configurable byte ceiling through
`WRENCH_PREFILL_CACHE_BYTES` or `--prefill-cache-bytes`, defaults to 256 MiB,
and exposes entries, bytes, hits, and misses in the dynamic-prefill receipt.
Oversized payloads remain usable for the current request without evicting the
whole cache. A zero ceiling disables retention.

The server's native handoff path is wired to the same index as the worker path.
This prevents repeated requests for the same large reference from rebuilding
the entire index.

## Portable package smoke

Package:
`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v75-server-cache`

- structural validation: `PASS_STRUCTURAL_PACKAGE`;
- package-local `/api/chat` accepted `options.num_ctx=4000000` and returned
  HTTP 200 on the small mechanical smoke, with `prompt_eval_count=7` because
  that request was intentionally small and embedded mechanical;
- repeated large native-handoff request: first receipt `0` cache hits and
  `2` misses, second receipt `2` hits and `2` misses;
- cache accounting: `42,000,078` bytes retained under a `67,108,864` byte cap;
- native upstream response: verified and accepted through the independent
  proposal verifier;
- no file mutation authority was granted.

The 4M raw-intake behavior itself remains covered by the v74 receipt in
`phases/phase-189-v74-ollama-4m`. This phase proves package portability and
cache reuse for the staged native handoff, not dense native attention quality.

## Regression

`pytest -q` passed with `162 passed, 14 warnings`.
