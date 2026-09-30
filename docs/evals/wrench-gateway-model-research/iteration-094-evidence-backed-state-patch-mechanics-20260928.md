# Iteration 094: evidence-backed state-patch mechanics

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-STATEPATCH-MECHANICS-20260928`  
Status: **bounded deterministic primitive implemented; not integrated or evaluated as a model**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway research goal SHA-256 preserved:  
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Change

Added [execution_state.py](../../../src/wrench_harness/execution_state.py), a
pure host-side validator for bounded controller-proposed state changes. The
host supplies the allowed fact schema and current evidence-ID-to-hash
manifest. The validator binds a patch to the session and exact state revision,
checks value types, rejects duplicate or stale changes, requires evidence for
each change, and stores exact evidence hashes with each fact. State proposals
cannot add routing, permission, tool, command, credential, policy, spend, or
other authority-like fields. Patches are limited to 16 KiB; the resulting
state is limited to 64 KiB. New state is immutable and receives a stable digest.

Added focused cases in [test_execution_state.py](../../../tests/test_execution_state.py).
They cover valid application, evidence binding, immutability, stale revisions,
session mismatch, forbidden fields, missing/stale evidence, type confusion,
required-field deletion, duplicate fields, malformed shapes, and per-patch and
cumulative state size limits.

| File | SHA-256 |
|---|---|
| `src/wrench_harness/execution_state.py` | `E0A52971F79AC7BC0239BFC91D597DD7DE949FA5FBC8ED8CF2F45CAAB2667B2A` |
| `tests/test_execution_state.py` | `83A8DCA3E2BBF9818E607B8A185BE08B9CF14A74917B95F5C2F1FD576C0C2815` |

## Verification and limits

All 12 test functions passed with a lightweight standard-library harness that
implements the `pytest.raises` behavior used by this file. The normal focused
pytest command could not start: pytest is absent from both the default Python
3.13 install and the repository Python 3.11 `.venv`. No packages were
installed. This is focused mechanics evidence, not the repository pytest
suite, a model evaluation, or a product acceptance result.

The helper is not connected to `ContextLedger`, a persistent event log, a
request compiler, OpenCode, or SubRoute. It does not retrieve evidence, write
state to disk, recover after interruption, or decide routes. Those integration
and recovery gaps are still required before using the state on live coding
episodes. The proposal values are task state and must remain marked untrusted
when a downstream model sees them.

The host sample after the focused run showed 8.16% free RAM and
15,199/16,311 MiB free VRAM. RAM remains below the 10% operating floor, so no
model load, training, inference, benchmark, package job, or delegation ran.
The GET-only SubRoute check to `127.0.0.1:4000` returned HTTP 200 from
`/health/liveliness`, `/models`, and `/api/active-model`. The active model was
`openrouter`, mode `force`, policy version 4. No completion/generation request,
provider call, credential read, or held-out data access occurred; the
campaign-wide numeric spend cap is still absent.

The initial code/test/report work reserved 120,000 bytes under
`WRENCH-GW-STATEPATCH-MECHANICS-20260928`. The cumulative-size amendment used
a fresh 50,000-byte reservation under
`WRENCH-GW-STATEPATCH-STATEBOUND-20260928`. Both storage scans included the
hourly automation and the 4,426,054,848-byte Docker model volume. Each
reservation was released after its outputs were accounted for. The read-only
SubRoute receipt update used a fresh 15,000-byte reservation under
`WRENCH-GW-ITER094-SUBROUTE-READONLY-RECEIPT-20260928`. It is released after
this report update; final aggregate status remains `WITHIN_LIMIT`.

## Next implementation step

Add bounded append-only persistence and restart recovery for validated state
transitions. Reconcile every evidence reference against a pinned
`ContextLedger` or source-snapshot identity, then compile fixed instructions,
current state, latest observation, and exact retrieved evidence for paired
transcript-versus-stateful episode measurements. Keep that deterministic path
as the baseline before training the LoRA to propose these bounded patches.
