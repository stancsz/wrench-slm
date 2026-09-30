# Iteration 095: bounded execution-state persistence and restart recovery

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-STATE-PERSISTENCE-095-20260928`  
Status: **standalone persistence primitive implemented and focused mechanics verified; not integrated or evaluated as a model**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway research goal SHA-256 preserved:  
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Change

Added [execution_state_store.py](../../../src/wrench_harness/execution_state_store.py), a host-controlled, bounded append-only event store for the evidence-backed patch primitive from Iteration 094. Each event pins session, task identity, field schema, revision, predecessor event hash, normalized patch, evidence hashes, and resulting state hash. A caller must provide the current evidence manifest on every load; if a live fact's source hash is missing or changed, replay fails closed.

Writes use a bounded staging file, flush the event file, and atomically rename it into the revision log. On restart, one complete and valid next-revision staging file can be recovered. Partial or invalid staging files are retained and reported as ignored. Multiple valid staged successors are rejected as ambiguous. Replay checks the entire hash chain and state transitions. The store also enforces file/event limits, rejects unexpected files and reparse points, serializes access across threads/processes, rejects parent traversal in its configured root, and applies the configured event-count limit during recovery as well as commit.

This provides process-interruption recovery. It does not claim power-loss durability. The host, not the model, chooses the storage path, evidence manifest, schemas, and resource reservation.

| File | SHA-256 |
|---|---|
| `src/wrench_harness/execution_state.py` | `61C913D131E64E763E86A9C40ED0DDC60F7D2995EA40993068BD208974E00533` |
| `src/wrench_harness/execution_state_store.py` | `54671CC1344FF8BEC009B72AAAEDC87821CA1D599F4554C31B3B9792AAD86702` |
| `tests/test_execution_state.py` | `83A8DCA3E2BBF9818E607B8A185BE08B9CF14A74917B95F5C2F1FD576C0C2815` |
| `tests/test_execution_state_store.py` | `FE134DAEF675ECCC049F661646C1230DF3BB1B08ECBBD611E856156322AF71B7` |

## Verification and limits

All 11 persistence tests passed with Python 3.11 `unittest`. They cover commit and restart replay, stale-write rejection, recovery of a complete staged event after an interrupted publish, preservation of partial staging files, corruption detection, current evidence checks, schema/task identity binding, stale competing writers, ambiguous staging, configured recovery caps, and parent-traversal rejection. All 12 focused patch-validator functions also passed using a small standard-library harness for the `pytest.raises` context manager. `git diff --check` completed with no whitespace errors. The repository's regular pytest suite was not run because pytest is absent from the available Python installations.

The primitive is still not connected to `ContextLedger`, pinned source snapshots, request compilation, OpenCode, or SubRoute. No paired transcript-versus-stateful coding episodes ran. It has not demonstrated context-token reduction, frontier-token savings, task success parity, all-in cost savings, or reliable all-day engineering. It stores host-validated state only; a downstream prompt must still mark state values as untrusted. These results do not establish that a LoRA is useful or that a small model can perform the coding work.

The GET-only SubRoute check at `127.0.0.1:4000` returned HTTP 200 for `/health/liveliness`, `/models`, and `/api/active-model`. The active route remains `openrouter`, mode `force`, policy version 4. No completion request, provider call, credential read, route change, or held-out data access occurred; the campaign-wide numeric spend cap is still absent.

At the final host sample, 4.69% system RAM and 15,226/16,311 MiB VRAM were free. RAM was below the 10% floor throughout this source/test iteration; no model load, training, inference, benchmark, packaging, or delegation ran. The storage check included the hourly automation and the Docker model volume at `\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\local-ai-models\_data`. Before reservation release, aggregate actual storage was 15,418,893,030 bytes and projected use including active reservations was 15,425,146,030 bytes, within the 50,000,000,000-byte ceiling. This iteration reserved 150,000 bytes under `WRENCH-GW-STATE-PERSISTENCE-095-20260928`; the reservation is released after report and source files are accounted for.

## Next implementation step

Bind store evidence to a pinned `ContextLedger` or source-snapshot identity and integrate replay into the deterministic request compiler. Then compare transcript and stateful arms on identical, representative coding episodes, accounting for retrieval, compaction, recovery, retries, verification, and all tokens. Keep the LoRA as a bounded patch proposer behind deterministic validation; train only after the control path and approved train/dev provenance are established. Keep the 95% success, 95% token/cost, and sustained-engineering claims explicitly unproven until measured.