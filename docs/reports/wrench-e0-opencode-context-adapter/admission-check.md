# E0 OpenCode preparation admission check

Date: 2026-09-24 (America/Edmonton)
Code commits: `b141ea7` (`feat: add OpenCode preparation admission check`) and
`fdecaff` (`fix: validate OpenCode preparation receipt`)

## Change

Added `check_opencode_preparation_admission(event_session_id, join)` as an
inert local classifier over the existing `OpenCodePreparationJoin`. It returns
READY only when the event and join session IDs match, the preparation has the
typed READY status and `none` route, the prompt is nonempty, the prompt-gate
receipt is typed and READY, retrieval misses are an empty tuple, and the
preparation's canonical outcome receipt validates as the expected INCOMPLETE
preparation receipt. The receipt must bind the join's snapshot and preparation
hashes, retain an unknown outcome, and have only `outcome` listed as missing.
Every rejection result omits the join; READY carries the original join for
inspection.

The check has no client hook, dispatch callback, provider, persistence, or
authority to force a caller to honor its result. The session record, serializer,
tokenizer and outcome receipt remain caller supplied. It does not prove that
the OpenCode request contains every runtime field, that the prompt matches the
client's final serialized request, or that callback identifiers are authentic.

## Verification

- Command: `python -m pytest tests/test_opencode_context.py tests/test_e0_context_pipeline.py -q -p no:cacheprovider --basetemp C:\\wrench-slm-data\\tmp\\pytest-opencode-admission-20260924`
- Runtime: Windows Python 3.11.16 with the cached pytest dependency path.
- Initial result: **21 passed in 2.21s**.
- Coverage includes READY acceptance and rejection for session mismatch,
  non-READY preparation, unexpected route, absent prompt, absent or rejected
  prompt gate, malformed/missing/incorrect preparation receipts, and retrieval
  misses. An independent review found that `ReceiptStatus.VALID` with a missing
  serialized receipt could otherwise be accepted. The predicate now requires
  the correct INCOMPLETE preparation receipt, revalidates its digest and
  canonical form, and checks its identity fields.
- After that correction, the same focused suite passed: **23 passed in 1.52s**.
- Independent review job `W2-NS-OPENCODE-ADMISSION-REVIEW-20260924`, nonce
  `OAR-20260924-7C3A`, verified expected HEAD `d120afb` and reported the single
  malformed-receipt issue above. The fix is in `fdecaff`.
- Final review job `W2-NS-OPENCODE-E0-FINAL-REVIEW-20260924`, nonce
  `OFR-20260924-21BD`, found no code blocker but noted the tests did not yet
  substantiate the report's wrong-identity coverage claim. Commit `7bc27fd`
  adds valid-but-misbound snapshot and preparation-hash fixtures. The focused
  suite then passed: **25 passed in 1.57s**.
- `git diff --check` passed before commit. The exact test scratch directory was
  removed after the run and the 20 MB storage reservation was released.
- Storage checker remained `WITHIN_LIMIT`; actual usage after the run was
  approximately 614 MB, with the pre-existing 100 KB source-recon reservation.
- The related session-bound post-run finalizer is covered in the
  [session-bound outcome report](session-outcome-binding.md).

## Remaining E0 gates

This increment does not complete E0. Runtime hook projection and failure
behavior, a verified dispatch veto, final serializer/tokenizer parity,
complete lifecycle accounting, authenticated outcomes, and end-to-end client
recovery remain open. OpenCode has not been installed or run. No model or
provider call was made. E1 through E4 are not accepted by this evidence.
