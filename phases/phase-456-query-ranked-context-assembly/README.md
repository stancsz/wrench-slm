# Phase 456: query-ranked context assembly

Date: 2026-09-23

## Change

`ContextLedger.assemble()` now uses its query to rank optional context at the
whole-unit level. Explicitly preserved units and the latest user intent/latest
active tool unit retain priority. Matching hot, warm, and reference units are
ranked ahead of unmatched hot/warm recency fallback. Cold-containing units are
excluded from all automatic paths, including fallback; explicit preservation
remains an intentional override. Mandatory preserved units are preflighted as
a group and fail closed when their combined cost exceeds the active segment
budget.

Selected segments remain atomic by `unit_id` and render in source order. The
ranking uses deterministic lexical scores, not semantic retrieval.

## Verification

- `python -m pytest tests/test_context.py tests/test_context_client.py -q`: 19
  passed.
- `python -m ruff check src/wrench_harness/context.py tests/test_context.py`:
  passed.
- `git diff --check` on the edited tracked files: passed; Git emitted only
  expected LF-to-CRLF conversion notices.
- Added regressions for query-ranked selection, deterministic ties, automatic
  cold exclusion when a unit is mixed-tier (both match and fallback paths),
  and overflow across multiple mandatory preserved units.

## Limits

These are deterministic mechanics checks only. They do not establish semantic
retrieval quality, model success, task completion, production utility, or an
external benchmark result. `selected_token_count` still counts stored segment
costs, not every wrapper, separator, chat-template token, or the complete
outbound prompt. Ranking scores and selection-policy version are not yet
included in the assembly receipt. The paired workflow and release gates remain
open.
