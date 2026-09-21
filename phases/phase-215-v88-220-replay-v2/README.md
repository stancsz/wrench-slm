# Phase 215: v88 full 220-case package replay

Date: 2026-09-20

The v88 portable package was replayed through its own `wrench_runtime` HTTP
server with client-side mechanical shortcut disabled and an isolated loopback
health fixture. The teacher capture matched the v2 cases by input SHA-256.

Results:

- 220/220 traces completed;
- weighted mechanical frontier-token coverage: `94.5411%`;
- net frontier-token savings: `95.5310%`;
- Wrench plus identical MiniMax fallback weighted final success: `99.6503%`;
- MiniMax teacher-only weighted final success: `78.9959%`;
- Wrench verifier success: `100%`;
- Wrench median / p95 latency: `183.314 ms` / `337.174 ms`;
- Wrench frontier tokens: `2,879`, teacher frontier tokens: `64,422`;
- fallbacks: `5`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

The diagnostic gates pass. This remains historical workflow evidence pending
the frozen family-disjoint MiniMax-worker trace set, independent 5060Ti
verification, and human release authorization. It is not dense-native 4M
attention quality evidence.

Receipts: `evaluation.json` and `trace-manifest.json` in this directory.
