# E0 query-ranked context assembly review

Status: accepted for this bounded increment
Reviewed: 2026-09-23 (America/Edmonton)
Goal: [E0 deterministic context runtime](../../goal/wrench-e0-context-runtime/GOAL.md)
Baseline: `b096cc3beefb053b7b77587637c74d28ae20c30f`

## Delivered behavior

`ContextLedger.assemble()` now puts explicitly preserved units first, then hot
context, BM25-ranked candidates, and remaining warm context by recency. Matching
reference/cold evidence can enter the bounded prompt without explicit IDs.
Receipts identify candidate IDs, the search limit, and whether deterministic
retrieval work was truncated. The receipt schema is now
`wrench.context-assembly.v2` because selection semantics and receipt fields
changed.

Admission and search have hard limits: 10,000 segments, 4 MiB total text,
256 KiB per segment, 16 MiB auxiliary identity/metadata/reference bytes,
64 metadata fields and 1 KiB per segment, 256 summary references, 4,096 query
characters, 256 distinct query terms, and 100,000 term-document checks. Search
traversal follows descending `source_order`, including when ingest order
differs. Metadata returned in segments is read-only.

## Verification

| Check | Result |
| --- | --- |
| `tests/test_context.py` and `tests/test_context_client.py` | 20 passed on Python 3.11.16 / pytest 8.4.2 |
| `git diff --check` | Passed |
| Wrench storage status | Within limit; 589,282,696 bytes observed plus a 20,000,000-byte active reservation at the final pre-commit scan |
| Device/model work | None; no download, inference, training, provider call, or benchmark |

The system Python 3.13 environment did not have pytest. Verification used the
already cached pytest dependencies under `C:\wrench-slm-data\cache`; no package
installation was performed. The initial missing-pytest attempt produced no
repository output.

## Independent review

Read-only reviewer `e0_supervisor` inspected the implementation, goal and
focused tests. It raised three P2 issues during iteration: posting traversal
was not bounded by the result limit; query tokenization and recency under
truncation were insufficiently bounded/deterministic; and auxiliary metadata
could bypass admission limits through mutation. Repairs added deterministic
work and input caps, source-order traversal, immutable metadata, and regression
tests. The final review found no remaining correctness issue in those areas
and recommended accepting this bounded slice. The reviewer did not run tests;
the root agent ran the checks above. Review was independent of implementation
but used the same supervisor who performed the initial E0 source audit.

## Limits and next step

This is not full E0 or production evidence. The runtime still needs durable
snapshot/source identity, a reversible bounded artifact store, namespace
discovery, exact final serialized-prompt accounting, and verified outcome
receipts. No downstream external consumer compatibility audit was performed;
the scoped repository has no strict key-set consumer for this receipt. Consumers
that require `metadata` to be a concrete `dict` may need to accept a read-only
mapping.

Next: implement a bounded snapshot identity and exact-source retrieval slice,
with explicit stale/missing behavior, before extending the E0 storage layer.
