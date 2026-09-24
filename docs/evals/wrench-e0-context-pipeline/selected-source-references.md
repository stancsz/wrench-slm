# Selected source reference review

**Status:** PASS, independent read-only review.

This fixture-only evaluation covers the additive source-reference builder in
`src/wrench_harness/selected_segment_sources.py`.

| Check | Result |
| --- | --- |
| Selected whole-file source resolves to path, content hash, and artifact handle | Covered |
| Whole-file span uses explicit status and null line bounds | Covered |
| Exact symbol span appears only with a matching supplied candidate | Covered |
| Missing candidate leaves symbol span unavailable | Covered |
| Candidate snapshot mismatch is rejected | Covered |
| Receipt rows cannot be mutated after digesting | Covered |
| Oversized source path is rejected before receipt construction | Covered |
| Oversized and wrong-type candidate parser metadata are rejected | Covered |
| Duplicate selected IDs are rejected | Covered |
| Focused tests | 9 passed, Windows Python 3.11.16, pytest 8.4.2 |

Limits: synthetic fixture only; no integration into the preparation return
value; no automatic candidate retention; no summary lineage; no full-prompt,
tokenizer, OpenCode, dispatch, task-utility, or end-to-end lifecycle claim.

Reviewer job `W2-NS-REFS-IMMUTABLE-REVIEW-20260924`, nonce
`REFS-IMM-1E0A`, confirmed bounded fields and canonical hashing, immutable
receipt rows, source and symbol identity joins, and alignment between the
implementation and its limitations. The reviewer did not run tests.
