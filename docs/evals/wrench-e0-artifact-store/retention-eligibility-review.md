# Artifact-store retention eligibility review

Date: 2026-09-24  
Revision inspected: `680cc6ec7635bed4b6101756cf541e8ff836b551`  
Implementation: `src/wrench_harness/artifact_store.py`  
Report: [retention eligibility](../../reports/wrench-e0-artifact-store/retention-eligibility.md)

## Independent review

Reviewer `/root/retention_migration_critic`, job
`W2-ART-LIFECYCLE-REVIEW-04-20260924`, nonce `RET-MIG-FIX-216D`, verified the
implementation SHA-256 as
`CB8D9F1F36DFFC963109CEB621FA5207247600CD31F309E04FDE847497792215` and found
no blocking issues in the reviewed migration and promotion scope. The initial
finding that schema access preceded the non-object payload guard was disproved
by direct inspection; the guard is present.

The review confirmed that v1 entries normalize to protected with no expiry;
v1/v2 current and previous manifests can be decoded into one normalized shape;
recovery selects a valid current manifest and falls back only when current is
invalid; non-object JSON payloads are rejected before schema access; and a
disposable-to-protected promotion returns only after two commits place the
protected generation in both manifest slots.

The earlier malformed-payload concern was not a defect: the implementation
already validates `payload` as a dictionary before calling `.get`. The
promotion concern was valid and was repaired with the second manifest commit.

Reviewer `/root/retention_eviction_critic`, job
`W2-ART-LIFECYCLE-REVIEW-05-20260924`, nonce `RET-ORPHAN-71C2`, then verified
the final implementation SHA-256 as
`CE709534166B9253470B207F5DA790D05BE961D17EA4F8D3F153B6197ED2F052`. The
review confirmed content-digest groups are removed only if every reference is
expired, disposable, and unpinned; insufficient reclaim is a no-op; and
deletion is restricted to selected digests after both manifests drop their
references. Pre-existing unreferenced blobs are left untouched. No blocking
data-loss issue was found in the static review.

## Evidence and limits

`git diff --check` and Python AST parsing passed. Tests were not run. Existing
test fixtures were adjusted for explicit expiry or protected source retention;
no new test cases were added. The reviewer identified missing direct regression
coverage for legacy migration, mixed-schema recovery, malformed-payload
fallback with a valid previous manifest, and promotion followed by current
manifest corruption. Shared-blob, insufficient-target, and preservation of
pre-existing orphan blobs were reviewed statically but also lack direct
regression coverage.

This evaluation does not establish a real-data retention schedule, automatic
cleanup, consent/deletion authority, power-loss durability, or production
recovery. Those remain open in the [artifact-store goal](../../goal/wrench-e0-artifact-store/GOAL.md).
