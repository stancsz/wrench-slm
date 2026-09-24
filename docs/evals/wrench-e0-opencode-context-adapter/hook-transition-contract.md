# OpenCode context-hook transition evaluation

Job: `W2-NS-W4-HOOK-TRANSITION-20260924`  
Nonce: `W4HOOK-72C4`  
Implementation review: `W2-NS-W4-HOOK-TRANSITION-REVIEW-20260924`, nonce
`W4HOOKREV-813B`

## Result

Focused verification passed **37 tests** in `tests/test_opencode_hook_projection.py`
on Python 3.11.16. `git diff --check` passed for the owned source, test, and
report paths.

The independent implementation review returned **NEEDS_CHANGES** only because
the report overstated validation of nested upstream schemas. The wording was
narrowed to the pinned top-level field envelope and Wrench's bounded shape
constraints, and explicitly says nested OpenCode message and option schemas
are not fully validated. Targeted read-only re-review job
`W2-NS-W4-HOOK-TRANSITION-REVIEW2-20260924`, nonce `W4HOOKREV2-2C9A`, returned
**PASS** and confirmed the finding was resolved. Reviewers ran no tests. No
code changed after the 37-test run.

## Scope limits

The passing fixtures establish the local transition predicate over synthetic
caller-supplied projections: one expected message can be inserted at one exact
position while protected fields and original messages remain unchanged. They
do not establish that OpenCode emitted those projections, that its hook used
the accepted transition, that any callback failure prevents dispatch, that
later request lowering preserves the projection, or that token counts match
the provider request. This is an offline W4 contract slice, not E0 acceptance
or production evidence.
