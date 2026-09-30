# Iteration 133: OpenCode tool-profile source behavior verification

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-OPENCODE-TOOL-PROFILES-TEST-ITER133`  
Status: **24/24 source unit tests passed; product utility remains unproven**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Verification

The provider-free Node source suite passed:

```text
node --test examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs
24 tests, 24 passed, 0 failed (369.0603 ms)
```

The cases cover complete-schema hashing and exact profile filtering, immutable snapshots, fail-through on unknown profiles, schema mismatch, timeouts and missing tools, receipt-sink failure restoration, provider-scoped hook registration, session profile reuse and restart restoration, schema drift, bounded expansion, and storage failures. Tests use in-memory mock state stores.

Source identities at verification:

| Source | SHA-256 |
|---|---|
| `examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs` | `62F19A92B48546CBCDE63D2435A77D560AA60320C43D17EED4D10221BEE4903C` |
| `examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs` | `19769A4229878C9AC0C42CE93B3F44CDE8864A7121D6FCA94363F3E92EF8B014` |

No provider call, SubRoute request, credential read, network request, or service/configuration change occurred. The run verifies deterministic prototype logic only. It does not demonstrate target-token savings, generated task success, durable storage, or interaction with the active SubRoute route.

## Limits and next step

The prototype is not enabled for repository engineering. It still lacks a compliant Wrench-root persistent store with process-wide atomic session claims. The in-memory tests do not prove disk persistence or crash recovery. Installed OpenCode v2.0.12 request-boundary behavior and synthetic request-level token measurements are separately recorded in Iterations 099-101; those mock results are not frontier-token savings or task utility. The next production-directed slice is a bounded durable store adapter under `C:\\wrench-slm-data`, with restart/crash and corrupt-state coverage, then integrate it only through an explicit reversible local opt-in.

No figure in this iteration is a Wrench frontier-token reduction result. The active acceptance gates remain unchanged: at least 95% local verified completion, at most 5% frontier-routed episodes, at least 95% success retention, at least 95% full-lifecycle frontier-token savings, at least 95% lower all-in cost, and reliable all-day engineering.

## Resource and storage accounting

The test reservation was `50,000,000` bytes under the assignment ID above. After correcting the automation inventory root to the path already recorded by the reservation, the storage checker reported `WITHIN_LIMIT`: 15,436,234,209 actual bytes plus 56,103,000 bytes of active reservations, 15,492,337,209 projected bytes against the 50,000,000,000-byte limit. The scan included the Docker WSL model volume, Wrench sibling/worker trees, SubRoute checkout, legacy source snapshot, and the existing hourly automation directory. C: had 139,705,847,808 bytes free. No generated model or benchmark artifacts were created.
