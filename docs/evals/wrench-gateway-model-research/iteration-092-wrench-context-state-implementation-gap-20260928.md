# Iteration 092: Wrench context-state implementation gap

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-EVAL-ITER092-CONTEXT-STATE-GAP-ASSESSMENT-20260928`

Status: **useful context primitives exist; long-horizon state compression is not integrated or measured**

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`

Gateway research goal SHA-256 preserved:
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Source findings

- `ContextLedger` stores bounded immutable segments in memory, groups tool
  calls/results into atomic units, supports summaries linked to source segment
  IDs, performs BM25 retrieval, preserves hot segments first, and packs a
  bounded active context. It can retain originals and expose retrieval pages.
  Its default token counter is a word estimate; callers must supply the target
  tokenizer or explicit counts for exact token evidence.
- E0 prepares a pinned source snapshot, selects evidence, compiles a bounded
  prompt, and returns accounting receipts. `prepare_opencode_e0_context`
  binds preparation to a validated session root and snapshot, but it does not
  maintain cross-turn execution state or invoke a model.
- The OpenCode hook projection is an ephemeral, content-bound projection. Its
  source explicitly says it does not persist, log, dispatch, authorize tools,
  or establish final provider serialization parity. The prepared-context and
  lifecycle modules join local preparation observations; they are not proof of
  a live, request-intercepting context runtime.
- The request-capture receipt counts message and tool-schema fields and stores
  request digests without prompt content. It explicitly leaves `input_tokens`,
  task success, and cost unavailable. Its module describes a future observation
  point; it is not wired to the live OpenCode/SubRoute boundary.
- `handoff.py` makes a bounded handoff packet by clipping and selecting message
  history with an estimated token counter. It is a one-time advisor handoff,
  not a persistent execution-state transition loop.

Thus Wrench has valuable deterministic retrieval, prompt budgeting, summaries,
atomic tool-message grouping, and source provenance. It does **not** yet show
that each live coding turn sends only a validated current-state record plus the
latest observation and exact evidence references. No paired actual request
tokens, provider usage, or end-to-end coding outcomes are measured by these
modules.

## Next implementation/evaluation seam

Build on `ContextLedger` rather than duplicating its source-evidence packing.
Add a versioned, bounded execution-state record whose model-proposed patches
are schema-validated and deterministically merged. Keep an append-only event
log and exact source/tool observations outside the prompt; state fields point
to IDs and hashes so the runtime can fetch omitted details. On each turn,
compile the fixed instructions, current state, latest observation, and only the
required pinned evidence. Reject or roll back incomplete, stale, conflicting,
or malformed state patches. Preserve full interaction history for audit and
recovery, but do not resend it by default.

Compare the current ledger path with a stateful path and the transcript
baseline on the same seeded, multi-step repository episodes. A useful coding
episode must include real file edits and tests, interrupted sessions, CI/test
failures, external repository changes, recovery, and explicit asks to explain
prior decisions. Use the exact target tokenizer after chat serialization and
reconcile it against SubRoute response usage. Report request tokens, task
success, exact-evidence recovery, state-update retries, compute/latency, and
training amortization separately. The 95% threshold must hold over the frozen
workload mix, not only on long simulated episodes.

Train the personal LoRA only after the deterministic state schema and evaluator
are frozen. Train it to propose bounded state patches, evidence IDs, and
retrieve/abstain choices using synthetic train/dev trajectories; keep held-out
trajectories sealed. A passing compactor alone would not satisfy the user's
LoRA or all-day engineering requirements.

## Reviewed source identities

These are the SHA-256 identities inspected for this static assessment:

| File | SHA-256 |
|---|---|
| `src/wrench_harness/context.py` | `F1BA227DA538318AC14D6F4034E0B588FDAE6DBFD2EA923F6B2D3FEE208C4EB8` |
| `src/wrench_harness/handoff.py` | `A7531A27700A8210153865ABFB0FB24B0E4FABC5FE81D56248F5A850AAC20CF1` |
| `src/wrench_harness/e0_context_pipeline.py` | `84D626DBAB14D4C768E63636880F0C7B0A3EB8A5E10DB3B6A63F194C11A3ACD8` |
| `src/wrench_harness/e0_lifecycle_accounting.py` | `7466F9AD9947CBDF1444A9C12CD731636AAA5C407532EDFE87C1CCAF0BC2F3A3` |
| `src/wrench_harness/opencode_context.py` | `F94E6C6A34C6204C35DCB72B5CC8FE3F4BC486D8FB27AFFD80E010BB333EC47A` |
| `src/wrench_harness/opencode_hook_projection.py` | `914462BD8EDCCE4805DCA6C6A96CC651C1155536D50F4BE77AB99DDC4F890D06` |
| `src/wrench_harness/opencode_prepared_context.py` | `C0668C285972A1DBDA53F40740C09AD0AC536ADEF9D2F3AC52A48ACD4F166989` |
| `src/wrench_harness/prompt_compiler.py` | `2930238C48D4162A88944D9A6CC82FC5398C11A1503EAE9B12AC5AE2F9381DDF` |
| `src/wrench_harness/opencode_request_capture.py` | `5ADD10269DE39CB615656093ED13CDF4B61098736F89E6E6D76D189B9629928F` |

The assessment was static and did not change source or run tests. No provider
call, model load, benchmark, or delegation occurred. The latest host sample was
8.85% free RAM, below the required 10% runtime reserve; storage remained within
the aggregate 50 GB limit. The current SubRoute forced route and missing spend
cap remain separate gates for any live teacher comparison.
