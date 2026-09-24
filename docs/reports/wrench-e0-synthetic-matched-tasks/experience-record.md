# Synthetic regression experience record

Job: `W2-NS-W5-SYNTHETIC-RECORD-20260924`

Nonce: `W5REC-01AD`

Base HEAD: `405f72e36fa53648e02ac5146dd952cb30eb0464`

## Scope

Added `src/wrench_harness/synthetic_experience_record.py`, an in-memory
reference-only record for comparing one caller-supplied candidate with the
frozen expected answer for one case in the sole admitted Wrench-authored
synthetic matched-task manifest. Building a record first calls the existing
manifest admission validator and accepts only the fixed open-development use.
It binds the case, case group, oracle kind, manifest digest, review digest, and
hashes of the frozen oracle and candidate. The only comparison states are
`match`, `mismatch`, and `unknown`.

The candidate is explicitly marked caller-supplied and untrusted. Candidate
answers, prompts, paths, source bytes, and observations are not serialized;
only their canonical digest is retained where supplied. The output is a
bounded canonical JSON string plus SHA-256. Its split and scope are fixed to
open development fixture regression, consent is marked not applicable for
authored synthetic material, and `training_eligible` is hard-coded false.
There is no usage override, persistence, corpus interface, or training call.

Validation checks the record digest and canonical encoding, exact field set,
fixed policy metadata, manifest admission, known case and oracle references,
and that comparison status agrees with candidate and oracle digests. It does
not authenticate the caller or execution that produced the candidate.

## Verification

Storage status before tests was `WITHIN_LIMIT`. The job reserved 10,000,000
bytes and included the Python 3.13 runtime root. C: had about 184 GB free;
observed free system RAM was above the 10% reserve. The default Python 3.13
environment had no pytest, so the already-cached Python 3.11 runtime under
`C:\wrench-slm-data\cache` was used offline. Pytest temporary output was
placed under `C:\wrench-slm-data\tmp\w5-synthetic-record-20260924`.

Focused command:

```powershell
& 'C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe' -m pytest tests/test_synthetic_experience_record.py tests/test_e0_synthetic_matched_tasks.py -q -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\w5-synthetic-record-20260924
```

Result: **14 passed**. `git diff --check` passed. An independent read-only
review by `synthetic_record_review1` returned **PASS** with no findings; the
reviewer did not run tests.

## Limits

`match` means canonical candidate JSON matched the pinned fixture's expected
JSON. The candidate is caller-controlled, so this record does not prove that
the route executed or produced those bytes. The fixture oracle and mechanics
review are synthetic regression material only. This record is not an outcome
receipt, trusted learning label, rights or consent finding, real-data
admission, training authorization, task-completion claim, utility evidence, or
E0/E2/E4 acceptance.
