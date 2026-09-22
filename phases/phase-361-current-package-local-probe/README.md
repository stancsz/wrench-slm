# Phase 361: Current local package 2M/4M intake probe

Date: 2026-09-21

Status: `PASS_PACKAGE_LOCAL_HYBRID_DIAGNOSTIC`

The locally available Wrench release candidate at
`D:\models\_wrench-release-candidate-8d9ea2c` accepted a direct 4,000,000-token
request through its model-local server and completed the deterministic
retrieval probe at 2M and 4M.

- Direct 4M: HTTP 200, 3,999,995 estimated raw input tokens, 172.585 ms total,
  42.567 ms embedded mechanical route, 23.772 ms context-gate time, 0 model
  calls, and a 64K working-context budget.
- Retrieval: 6/6 cases passed, with needles at 1%, 50%, and 99% of both 2M and
  4M payloads. All cases used the embedded mechanical route with 0 model calls.
- The first layer reported `mechanical_fast_pruner_cherrypicker`, exact lookup
  routing, raw-payload hash binding, and bounded working context.

This is direct package-local intake and retrieval evidence. It proves the
hybrid model-local path, not dense-native 4M attention, learned MiniMax parity,
or independent RTX 5060 Ti execution. The raw receipts are kept beside this
README.
