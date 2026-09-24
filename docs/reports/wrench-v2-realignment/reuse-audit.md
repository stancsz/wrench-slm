# V1 evidence and reuse audit

Status: read-only audit complete, 2026-09-23 (America/Edmonton)
Author: independent worker `v1_evidence_audit`; persisted by root without changing findings
Goal: [v2 realignment](../../goal/wrench-v2-realignment/GOAL.md)
Job: `W2-AUDIT-20260923`; nonce: `W2-AUDIT-b3c1c9`
Observed source HEAD: `87909b958ac252b0b3b2cc720a300babb26b733d`, with pre-existing edits

## Evidence and limits

The owner reports filesystem corruption and lost data. The
[dataset audit](../wrench-25k-data/dataset-state-audit.md), especially its
finding, disk-state and count sections, establishes missing historical D:
payloads and no admitted new corpus at that audit. It does not establish the
physical corruption cause. [Phase 447](../../../phases/phase-447-wrench-training-data-corpus/README.md)
records 402 drafts and unresolved final exposure. These are not recoverable,
quality-admitted training rows. Older model fits and the later corpus effort
are separate events.

The audit also records a validator crash and passing-receipt/source hash
mismatch. Historical success cannot validate a changed executable or missing
payload. Preserve failed checks, provenance and uncertain final exposure.

## Source inventory

Line references below describe the inspected source at the stated revision.

| Module | Reusable source | Gap relevant to v2 |
| --- | --- | --- |
| [context.py](../../../src/wrench_harness/context.py), lines 46, 80, 224, 262, 310 | Immutable segments, hashes, summary provenance, lexical BM25 retrieval, tiers and whole-unit assembly | In-memory state, no durable reversible store or semantic graph/embedding retrieval in this module |
| context.py, lines 337-383 | Preserved explicit units then recent hot/warm selection | `assemble(query, search_limit)` does not itself call search; no automatic query-driven packer claim |
| context.py, lines 83, 385 | Supplied token counter/counts | Default estimates and later wrappers do not prove final serialized prompt budget |
| [toolbelt.py](../../../src/wrench_harness/toolbelt.py), lines 49, 88, 101 | Python AST, symbol index and conservative dependency evidence | Non-Python lexical fallback; no Tree-sitter/LSP/SCIP implementation |
| toolbelt.py, lines 162, 192, 212, 229 | Repo map, test candidates, failure fingerprints and recent intent | No complete persistent graph, deferred schema registry or learning pipeline |
| [core.py](../../../src/wrench_harness/core.py), lines 122, 140, 327, 384, 446, 491 | Six bounded actions, confinement, reads/search, local health and unapplied patch proposals | Preserve independent authority boundary while specifying new bounded context decisions |
| toolbelt.py, line 279 | Structural/authority/evidence/consistency post-verifier | Supplied evidence checks do not prove task success or comprehensive credential-intent detection |
| [mechanical.py](../../../src/wrench_harness/mechanical.py), line 599 | Deterministic proposal routing | Useful baseline, not outcome-trained context/model routing |
| [router.py](../../../src/wrench_harness/router.py), lines 31, 67 | Attempts, cooperative cancellation, circuit opening and bypass | Synchronous invocation; checks cannot preempt a running callback |
| [state.py](../../../src/wrench_harness/state.py), lines 15, 27 | Atomic router-state replacement and config-hash validation | Router counters only, no learned adapter lifecycle or crash-recovery proof |

The requested base/core/personal stack still needs composition, replay,
consolidation, evaluation, promotion and rollback. This scoped audit does not
claim the entire historical repository has no LoRA experimentation code.

## Cleanup hazards and disposition

- Relocated docs are embedded in current fixture generators. Update both
  targets and prompts. Preserve frozen rows/receipts; never replace strings
  across historical JSONL/JSON evidence.
- The legacy canary reads the root parent contract and binds its hash. Retain
  exact old contract bytes; current v2 authority must not inherit paid v1
  allowances or silently rebind old child approvals.
- Old binary-only goals and adapter prohibitions conflict with v2 and need
  supersession. Missing data is not disposable data.
- Root's live device query identifies a 5060 Ti. The notes' 5070 Ti assumption
  and old hardware receipts cannot identify current hardware.

## Method and handoff

Worker used `git rev-parse HEAD`, narrowly scoped `rg` and `Get-Content` over
the supplied notes, named audits and six source modules. No files changed,
sealed datasets opened, tests run, inference/training started or external
calls made. One invalid shell search was corrected with explicit paths.
No disk-health diagnostics or historical original weights were inspected.

Root must integrate the findings, retain original records and verify the
completed navigation/experiment. This report is a source audit, not model,
hardware, parity or release evidence.
