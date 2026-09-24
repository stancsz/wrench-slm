# W1 retrieval pages evaluation

Job: `W2-NS-W1-PAGING-20260924`  
Nonce: `W1PAGE-2C17`  
Implementation baseline: `bb92c9f825e5de63aa9792734662ff393edf2751`

## Acceptance scope

This check covers typed `ENOUGH` / `RETRIEVE_MORE`, stable ranked IDs,
32-candidate page and 64-candidate total bounds, session/query cursor binding,
early stop, exhaustion, candidate-cap signaling, posting-work fail-closed
behavior, and rejection of untyped decisions. It uses only authored in-memory
synthetic segments. It does not measure retrieval utility, ranking quality on
real tasks, exact token savings, client interception, or outcome attribution.

## Verification

Status: implementation verification passed; independent review passed.

Focused command, using the pre-existing Python 3.11.16 / pytest 8.3.5
environment under the approved Wrench data root, with bytecode and pytest
cache disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& 'C:\wrench-slm-data\cache\w2-root-route-uv\archive-v0\0kHEETakwp9Ic6HO\Scripts\python.exe' -m pytest -p no:cacheprovider tests/test_context.py
```

Result: **27 passed**. An initial system-Python probe found no pytest, and an
offline uv probe confirmed the requested pytest package was not in that cache;
no network or download was used. The existing approved-root Python/pytest
environment was then used directly. After review and releasing this job's
50,000,000-byte reservation, storage status was `WITHIN_LIMIT`:
10,301,198,066 actual bytes, 25,103,000 bytes active reservations, and
39,673,698,933 bytes projected headroom.

Host check during the bounded CPU test: 14,701,182,976 / 34,290,302,976 RAM
bytes free (42.87%); 15,221 / 16,311 MiB VRAM free. `git diff --check` passed.
No model, provider, client, network, or artifact-producing fixture was used.

Cursor replay and fresh first-page requests can repeat results; the two-page
limit applies per continuation chain, not across all caller invocations.

Independent read-only review: **PASS**, follow-up job
`W2-NS-W1-PAGING-REVIEW2-20260924`, nonce `W1REV2-C83D`; observed shared HEAD
`ff00c9fda3171ab69571329f80a394483f993219`. The reviewer confirmed the cursor
checksum test, replay disclosure, cursor binding, candidate/page caps,
clipping behavior, and scope docs. The initial review also passed under job
`W2-NS-W1-PAGING-REVIEW-20260924`, nonce `W1REV-71A4`, at an earlier shared
HEAD. Reviews were read-only; neither ran tests. The cursor checksum detects
accidental edits and is not authentication.
