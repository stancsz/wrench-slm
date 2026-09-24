# E0 preparation selected-source lineage integration review

**Status:** PASS, independent read-only review.

The focused integration covers the optional selected-source lineage receipt on
`PreparationResult`.

| Check | Result |
| --- | --- |
| Selected source maps to path, snapshot/content hashes, and artifact handle | Covered |
| Selected structural candidate maps to parser-reported inclusive lines | Covered |
| Whole-file source span is labeled and has null line bounds | Covered |
| Receipt contains exactly selected evidence IDs | Covered |
| Unselected source is excluded | Covered |
| Missing summary lineage has a reason | Covered |
| Receipt digest affects preparation aggregate/context receipt digest | Covered |
| Focused suites | 25 passed, Windows Python 3.11.16, pytest 8.4.2 |

Limits: synthetic-only evidence; parser-reported spans do not establish source
truth; summary lineage is unavailable; artifact handle IDs do not prove a live
pin; no downstream request serialization, client dispatch, task outcome,
customer utility, or complete E0 lifecycle is established.

Reviewer job `W2-NS-LINEAGE-INTEGRATION-REVIEW-20260924`, nonce
`W2REV-21E9`, confirmed that selected-only records use validated public
identities, parser spans retain their parser-reported label, the immutable
lineage digest and unavailable reason rows feed the preparation aggregate, and
failure returns no prompt. The reviewer did not run tests or edit files.
