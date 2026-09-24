# Artifact-store migration and recovery regression evidence

Date: 2026-09-24
Goal: [E0 bounded artifact store](../../goal/wrench-e0-artifact-store/GOAL.md)
Base: `a5dba0f`
Job: `W2-NS-ART-RECOVERY-TEST-20260924`
Nonce: `ARTREC-6F20`
Status: focused offline regression tests pass; production recovery qualification remains open

## Coverage added

`tests/test_artifact_store.py` now exercises four gaps identified in the
retention review:

- A valid v1 manifest opens with every legacy record protected and no expiry.
  The existing handle identity remains readable, eviction cannot remove it,
  and a later put writes v2 retention fields while retaining that identity.
- A content-addressed object shared by multiple handles stays ineligible when
  any reference is protected or not yet expired.
- An unreachable byte target returns an empty result while preserving current
  and previous manifest bytes, object bytes, staging entries, and in-memory
  payload state.
- Eviction recovery is checked when execution stops before the second eviction
  generation, between the second generation's previous/current manifest slot
  replacements, and after both replacements but before object deletion.
  Recovery may restore an earlier eligible reference while its object remains
  present; after both slots record eviction, corrupting the current manifest
  must not resurrect the handle from the previous slot.

The interrupted paths are deterministic exception-injection fixtures around
the store's Python calls. They verify logical recovery ordering and do not
simulate power loss, torn filesystem metadata, hardware failure, or directory
entry durability.

## Verification

On Windows, Python 3.11.16 with the already-cached pytest 8.3.5 environment:

```text
python -m pytest -q -p no:cacheprovider tests/test_artifact_store.py --basetemp C:\wrench-slm-data\cache\W2-NS-ART-RECOVERY-TEST-20260924\pytest-tmp
26 passed, 3 skipped in 2.94s
```

The three skips are existing symlink-creation cases unavailable to this
Windows account. The independent test review passed after the final assertions
were revised to include staged-file bytes and the interruption between
manifest-slot replacements. `git diff --check` passed. Pytest temporary files
were directed to the approved cache root under the active 10,000,000-byte
reservation; no package was installed.

## Limits and next work

These are bounded local regression fixtures. They do not validate multi-process
writers, host-crash behavior, failure-independent backup, restoration after
volume loss, real-data retention, or production consent and deletion policy.
The artifact store remains a single-process primitive and the broader E0
request lifecycle remains incomplete.

See the [independent evaluation](../../evals/wrench-e0-artifact-store/recovery-regressions-review.md).
