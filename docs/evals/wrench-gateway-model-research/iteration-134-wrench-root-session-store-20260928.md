# Iteration 134: Wrench-root durable OpenCode session store

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-TOOL-SESSION-SQLITE-ADAPTER-ITER134`  
Status: **local store and hook integration checks passed; not enabled for live OpenCode traffic**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Change

Added a Wrench-root session store for the OpenCode tool-profile prototype at [the adapter](../../../examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.mjs). Its default SQLite database is `C:\\wrench-slm-data\\opencode\\tool-profile-state\\session-state.sqlite`. It accepts only the approved storage root and bounded namespace, rejects symlink/reparse-like path components and linked/oversized database files, and validates the database identity, schema, integrity, and foreign keys at open.

`claim(key, maxKeys)` uses a SQLite `BEGIN IMMEDIATE` transaction for the existing-key check, persistent capacity count, and unique insert. `get`/`set` match the profile hook's undefined-on-miss interface. The store caps claims at 256, state records at 128 KiB, and database pages at 48 MiB. It requires the 5 GB physical free-space floor plus the maximum database size before writes. SQLite uses rollback-journal mode and full synchronous commits. The external Wrench storage checker is still the authority for aggregate admission; the adapter cannot create or release a job reservation.

Updated the example README to explain the adapter and its deployment limits. Added direct storage tests and a source-hook integration test using the real adapter.

## Verification

```text
node --test examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.test.mjs examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.integration.test.mjs
28 tests, 28 passed, 0 failed (1.65 s)
```

Evidence includes:

- Existing 24 profile-hook behavior tests still pass.
- A four-process race over 64 distinct keys at capacity 32 admitted exactly 32 and returned `capacity` for the other 32.
- Claimed state survives closing and reopening the SQLite store.
- The profile hook selected once, persisted through the adapter, then restored after constructing a new hook/store without invoking the selector again.
- Invalid root/namespace, insufficient disk floor, malformed DB, unclaimed writes, malformed keys, and oversized JSON fail closed.

Two earlier test runs exposed fixture namespace reuse and the adapter returning `null` where the hook requires `undefined`; both were fixed. A subsequent corruption test exposed a raw SQLite error escaping the adapter; it now maps to a bounded storage error. The final combined run above is green.

## Exact identities and environment

| File | SHA-256 |
|---|---|
| `examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.mjs` | `5450BC62EE68EF4AE7CC784B1D4C900BCB6608BA00C84FB108956715B2722AD1` |
| `examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.test.mjs` | `4AF1E08E6E20B2F5C7C043DAC7EE792EC3F3FA519CF8808E8353BF3DA27048BD` |
| `examples/opencode_v2_subroute_tool_profiles/wrench_root_session_store.integration.test.mjs` | `F47E01ABB67E829879D2FF35F2538B21FA00C3ED3ADB311DDD31BDE8F0B3C558` |
| `examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs` | `19769A4229878C9AC0C42CE93B3F44CDE8864A7121D6FCA94363F3E92EF8B014` |
| `examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs` | `62F19A92B48546CBCDE63D2435A77D560AA60320C43D17EED4D10221BEE4903C` |
| `examples/opencode_v2_subroute_tool_profiles/README.md` | `9E665136C9050EFE617F45DB9CEB6BAE7716102EC196A9B3813E8EC899CCC69B` |

Runtime: Node `v24.19.0`; `opencode --version` reports `v2.0.12`. The official [Node.js SQLite documentation](https://nodejs.org/download/release/latest-v24.x/docs/api/sqlite.html) describes `node:sqlite` as a release candidate in the v24 line. The tests imported the module with Node directly; they did not load this adapter inside the installed OpenCode plugin host.

`git diff --check` passed; Git emitted existing mixed-line-ending warnings for unrelated dirty files. The active goal hash remained unchanged.

## Boundaries and next action

No provider or SubRoute request, credential read, spend, active configuration edit, model inference, or token measurement occurred. These tests do not demonstrate schema-token reduction, frontier-token savings, task quality, all-in cost, crash/power-loss recovery, long-running contention, or all-day coding reliability. The actual tool-profile plugin remains disabled. Before a local opt-in, test the exact installed OpenCode plugin host/runtime, run an interruption/recovery drill, and ensure a retained storage reservation covers the 48 MiB database plus its rollback-journal peak. Any provider traffic remains closed pending an enforced numeric campaign cap.

The full 95/5 completion/routing, 95% success-retention, 95% frontier-token reduction, 95% all-in-cost reduction, and all-day engineering goals remain active and unproven. This iteration only removes one persistence blocker for the mechanical tool-schema path.

## Storage admission

This iteration reserved `125,000,000` bytes under the assignment ID. The last pre-report storage scan returned `WITHIN_LIMIT` at `15,436,260,505` actual bytes plus `131,103,000` active reservations (`15,567,363,505` projected), with all recorded roots present, including Docker's WSL model volume and the hourly automation directory. C: had approximately `139.7 GB` free. Test databases were created beneath the approved data root and removed by the suite cleanup hook.
