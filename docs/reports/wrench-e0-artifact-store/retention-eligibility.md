# Artifact-store retention eligibility

Date: 2026-09-24
Goal: [E0 bounded artifact store](../../goal/wrench-e0-artifact-store/GOAL.md)
Implementation commit: `680cc6ec7635bed4b6101756cf541e8ff836b551`
Status: bounded eligibility gate implemented; no real-data retention policy or
scheduler is authorized or implemented

## Change

Manifest v2 adds a protected/disposable disposition and optional UTC Unix
expiry to each artifact reference. New source records default to protected
with no expiry. Legacy v1 records decode as protected, and their handles and
receipt identities do not change. A disposable record must carry an explicit
expiry. Re-putting an existing identity cannot change its disposable expiry;
it can only promote the record to protected. The promotion returns only after
both manifest slots contain the protected generation.

`evict` now requires an explicit UTC epoch cutoff. A content blob is eligible
only when every manifest handle that references it is disposable, expired at
or before that cutoff, and unpinned. Candidate groups are ordered by expiry,
generation, handle identity, and digest. If the eligible groups cannot reclaim
the requested byte target, eviction returns without changing manifests.
Only selected eligible object hashes are deleted, and only after both manifest
slots no longer reference them. Pre-existing unreferenced blobs remain for
separate recovery review.

The existing source-writing call sites omit retention arguments and therefore
remain protected indefinitely. No automatic cleanup, retention window, consent
decision, or deletion right is inferred from age, source staleness, or request
completion. If only protected records remain, the bounded store may reject new
data rather than remove them.

## Review and checks

Three independent read-only reviews informed the schema, migration, eviction,
and source-protection design. Their key boundary was consistent: old and new
source records remain protected unless a caller explicitly assigns a reviewed
expiry. A later source review caught a promotion rollback issue; promotion now
commits its protected state to both manifest slots before returning. One
reported malformed-payload concern was checked against the implementation: a
non-dictionary payload is already rejected before schema access.

Existing eviction fixtures were updated to opt into disposable expiry. Context
and OpenCode preparation fixtures continue to treat source artifacts as
protected after request scopes close. No new test cases were added, and tests
were not run. `git diff --check` and Python AST parsing passed. These checks and
read-only review do not replace the focused migration, shared-blob, expiry,
promotion-recovery, or interruption tests.

## Remaining limits

This is manual eviction eligibility, not a retention schedule or automatic
deletion workflow. Expiry values are caller supplied and are not authenticated
or tied to consent, permitted use, repository origin, or deletion rights.
Current real-data capture remains unauthorized; authored fixtures remain the
only permitted corpus. The store still uses process-local pins and one
instance per root, and its manifests share a volume. Failure-independent
backup and restore, power-loss qualification, multi-process locking, and the
complete E0 lifecycle remain open.

The [artifact-store evaluation](../../evals/wrench-e0-artifact-store/review.md)
records the original bounded-store evidence. A focused review for this
retention increment is tracked separately in the lifecycle evaluation.

## Follow-up regression evidence

The report above records the state when the retention increment was first
reviewed. Focused tests were subsequently added for valid v1-to-protected
normalization, mixed shared-content eligibility, unreachable eviction targets,
and interruption around the two eviction manifest generations. The suite
passed **26 tests with 3 symlink-related skips** on Windows Python 3.11.16.
Details and independent review are recorded in the [recovery regression
report](recovery-regressions.md) and
[evaluation](../../evals/wrench-e0-artifact-store/recovery-regressions-review.md).
