# Storage reservation scope review

## Scope

Verify that a previously admitted `included_roots` list remains part of later
aggregate storage status and reserve scans, and that malformed reservation
identity cannot disappear through in-memory replacement.

## Evidence

- Source change: `tools/check_wrench_storage_budget.py` carries validated
  active-root scope into status and reserve scans, writes separate
  `required_roots` and `optional_cache_roots` fields for new records, validates
  reservation filename/job ID identity, and reports duplicate IDs as errors.
- Legacy v1 records contain only flattened `included_roots`. Compatibility
  permits omission only for a missing path matching a current standard optional
  cache candidate. Other missing roots fail closed. New explicit roots remain
  required even if they match a standard cache path.
- Regression coverage in `tests/test_check_wrench_storage_budget.py` includes
  carried-forward present roots, missing and unscannable roots, legacy cache
  omission, explicit-root preservation, persisted scope fields, filename
  identity, duplicate IDs, partial new-scope metadata, and persisted optional
  cache behavior when the current candidate list changes.
- Focused suite: 27/27 passed with Python 3.13 `unittest`. Pytest was not
  installed in the available Python 3.13 or Python 3.11 interpreters.
- Fresh storage status before the final successful suite was `WITHIN_LIMIT`:
  actual 10,043,643,523 bytes, active reservations 36,103,000 bytes, projected
  10,079,746,523 bytes. This includes a 9,379,396,658-byte UV cache root from
  an active job's recorded scope. The local test reservation was 5,000,000
  bytes; other job records were not changed.
- Independent source review job `W2-NS-STORAGE-CACHE-FINAL-REVIEW-20260924`
  (nonce `SCOPE-REV-3C58`) passed after earlier partial-metadata and optional
  cache classification findings were repaired.

## Disposition

The implementation, focused suite, and independent source review pass. This
does not test OS quota enforcement, filesystem write interception, or
physical-volume headroom.
