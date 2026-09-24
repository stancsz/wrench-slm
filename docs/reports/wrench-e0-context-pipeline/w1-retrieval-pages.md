# Bounded W1 retrieval pages

Job: `W2-NS-W1-PAGING-20260924`  
Nonce: `W1PAGE-2C17`  
Base inspected: `bb92c9f825e5de63aa9792734662ff393edf2751`

## Slice

`ContextLedger.retrieve_page` in `src/wrench_harness/context.py` exposes an
explicit caller decision, `ENOUGH` or `RETRIEVE_MORE`. It returns only ranked
segment IDs already present in the in-memory ledger. The caller may request a
first page of at most 32 IDs and one continuation page, for at most 64 IDs
total. A continuation cursor binds the ledger session digest and query digest;
it becomes invalid if either changes. Its checksum detects accidental
corruption and is not authentication.
Replaying a cursor or starting a new first page can repeat results; this caps
each continuation chain, not a caller's total invocations.

`ENOUGH` stops immediately without searching. Retrieval reports `MORE_AVAILABLE`,
`EXHAUSTED`, `CANDIDATE_LIMIT`, `WORK_LIMIT`, or `INVALID_CURSOR` explicitly.
If BM25 posting work is clipped, the method returns no IDs. The candidate cap
uses one extra ranked result to distinguish exhaustion from the cap. The
method does not read sources, alter `assemble`, or change the default E0
facade selection.

## Scope

This is an in-memory deterministic mechanism with authored synthetic ledger
fixtures. It does not implement a learned controller, graph expansion,
client/provider integration, durable cursor state, outcome-backed utility,
or E0 acceptance. The caller owns each decision and must use the returned
known IDs within its own context-selection policy. The cursor is not a
permission or identity boundary.

## Verification

Focused scope: `tests/test_context.py`. Results and independent review are
recorded in the paired [evaluation](../../evals/wrench-e0-context-pipeline/w1-retrieval-pages.md).
