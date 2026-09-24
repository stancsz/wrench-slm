# E1 Windows candidate identity verifier evaluation

Job: `W2-NS-E1-WINDOWS-IDENTITY-20260925`

Nonce: `E1WIN-SUP-7B31`

Implementation baseline: `d054e4a67024a5c828f114529a458f090964266f`

## Decision

The Windows local mechanics slice is implemented and has a passing focused
synthetic run on the current 64-bit Windows NTFS developer host. Independent
full source and test review returned PASS; the reviewer did not rerun tests.
The result is evidence for the named host and contract only, not broad Windows
filesystem support or E1 milestone acceptance.

## Evidence

- Changed implementation: `src/wrench_harness/candidate_identity.py`.
- Changed tests: `tests/test_candidate_identity.py`.
- Detailed method and limitations: [Windows verifier report](../../reports/wrench-e1-candidate-identity/windows-verifier.md).
- Python 3.11.16 on Windows, cached pytest 8.4.2: **16 passed, 6 skipped**.
- Five skips are POSIX-only race seams. One symlink test skipped because the
  Windows symlink privilege was unavailable.
- Windows-only passing cases included streamed identity verification, exact
  file-set rejection, size and digest mismatch, UNC rejection, Unicode
  filename serialization and lookup, and continuation across bounded
  enumeration batches.
- A Windows junction test passed for both an unexpected child junction and a
  root reached through an ancestor junction. It created junctions only below
  `tmp_path`, removed each junction with `os.rmdir`, and left no junction
  behind. No junction fixture was skipped.
- `git diff --check` passed.

The final test command was run with these values:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=src;C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages
TEMP=C:\wrench-slm-data\tmp
TMP=C:\wrench-slm-data\tmp
Python=C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe
pytest tests/test_candidate_identity.py -q -rs -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\W2-NS-E1-WINDOWS-JUNCTION-REVIEW2-20260925
```

The 16/6 result is bound to implementation SHA-256
`9163a320ec8ddfabe6f230b211f1721d161821df919ba6c9376f49d272b2e63b` and test
SHA-256 `143619bcc45253ff0503cba23b9802dd357f46047786055b0a96a736f6c489c7`.

The tests created only tiny Wrench-authored synthetic files beneath
`C:\wrench-slm-data\tmp`. No candidate model file was accessed. The verifier
requires an absolute drive-letter root, a flat manifest, 64-bit Python, an
NTFS volume, and the required native APIs. It fails closed when these
conditions or API calls are unsupported. The junction fixture exercised
unexpected child and ancestor reparse points. The separate symlink fixture
skipped because Windows symlink privilege was unavailable. No privileged or
out-of-band mutation during hashing was exercised.

The storage checker was `WITHIN_LIMIT` before and after testing. The
The implementation job reserved 5,000,000 bytes, the initial junction run
reserved 1,000,000 bytes, and the review rerun reserved 1,000,000 bytes. All
scans included `C:\Users\stanc\AppData\Local\uv\cache`. After all E1 runs
stopped and their outputs were accounted for, all three E1 reservations were
released. Final status was `WITHIN_LIMIT`: 10,052,660,445 actual bytes,
103,000 bytes in unrelated active reservations, 10,052,763,445 projected
bytes, and 39,947,236,554 bytes headroom. C: had 183,746,764,800 bytes free.
At final status RAM was 41.4% free and the RTX 5060 Ti had 15,214 MiB free of
16,311 MiB. The tests used no GPU.

No commit was made. Fresh full review `W2-NS-E1-WINDOWS-FULL-REVIEW-20260925`
(nonce `E1REV-FULL-61A9`) returned **PASS** on the implementation and junction
test; the reviewer did not run tests. Broader
filesystem compatibility and the full E1 runtime and utility gates remain
open. This implementation and its test do
not authorize model downloads, client or provider runs, real-task data
capture, training, inference, spending, publication, or production use.
