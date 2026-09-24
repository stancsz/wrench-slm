# E3 synthetic model-version lifecycle

Date: 2026-09-24 (America/Edmonton)
Job: `W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924`
Nonce: `E3SYN-ROOT-7C12`
Base HEAD: `f50a70d1f8e1d2a9327a41a3df7549a198102258`

## Result

Implemented a bounded, offline lifecycle state machine for tiny synthetic
opaque payloads. It stores immutable version manifests and file hashes,
validates candidate completeness and compatibility, writes a development
admission receipt bound to the candidate ID, manifest digest, and parent,
atomically transitions active state, and retains factory/prior references.
Rollback and personal reset are supported. Request pins snapshot a manifest
and carry a per-instance HMAC capability; a pin remains bound to its original
version across activation and cannot be used by a reopened store instance.

Writers use an OS-backed lock and verify the on-disk generation before
mutation. Opening verifies state references and artifacts, restores from a
verified backup without overwriting that backup with a damaged pointer, and
fails closed when no usable reference remains. An oversized main pointer can
be replaced from a valid backup only when it is within the store's aggregate
ceiling. Candidate state requires an exact development admission receipt, so
an unadmitted staged candidate or candidate missing its receipt cannot become
the opened active version.

The store enforces a fixed 10,000,000-byte aggregate ceiling, 512-entry ceiling,
32 version and admission counts, per-file limits, and projected growth checks.
It rejects unexpected, orphaned, oversized, and reparse-point entries without
cleaning them up. Emitted manifest and receipt flags are fixed to
`training_eligible=false` and `production_activation=false`.

## Changed implementation paths

- `src/wrench_harness/model_lifecycle.py`
  SHA-256: `38DE8C78107845CFDE306A981D32AEDC9FFD1A72FCB82EE0D145CF339D661A8F`
- `tests/test_model_lifecycle.py`
  SHA-256: `7EB5DFB0F0AF6F491A2D44A48D8AD2BE57149525F67A8C1B4ED28F4FB4B8F826`

The fixtures use only synthetic IDs, metadata, and small byte strings. They do
not load models, call a provider, perform inference, install integrations, or
use customer, participant, or repository-task data.

## Verification

Runtime: Python 3.11.16 with the pre-existing pytest 8.4.2 cache at
`C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages`. No
packages were installed.

Command (with `PYTHONPATH=C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src`):

```powershell
C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe -m pytest -p no:cacheprovider --basetemp=C:\wrench-slm-data\tmp\W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924\impl\pytest-E3ADM-91A3-final tests/test_model_lifecycle.py -q
```

Result: **18 passed, 1 skipped in 24.90s**. The skipped fixture attempted to
create symlinks and was skipped because this Windows host did not grant the
required `os.symlink` privilege. Reparse checks are implemented and reviewed,
but nested-link behavior was not exercised on this host.

`git diff --check` passed. The focused suite covers request pin stability,
candidate completeness/compatibility/admission, corrupt admission, forged and
stale pins, reset and rollback, reopen, promotion failure, pointer corruption,
oversized main recovery, interruption while replacing a parseable invalid
pointer, two-process writer locking and stale-generation rejection, reparse
path checks where supported, and aggregate byte/entry boundaries.

Independent review passed on the hashes above. Review job:
`W2-NS-E3-ADMISSION-FINAL-20260924`, nonce `E3ADMREV-3B80`. The review
confirmed recovery and admission fixes, locking, pin provenance, path checks,
inventory checks, and dev-only flags. It did not run code or tests.

## Storage and host resources

The 10,000,000-byte reservation
`W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924` remained active through tests
and review. The checker included `C:\Users\stanc\AppData\Local\npm-cache`
and reported `WITHIN_LIMIT` before and after the final test run. Post-run
inventory: 2,286,497,667 bytes actual plus 10,103,000 bytes of active
reservations, with 47,703,399,332 bytes remaining under the Wrench ceiling.
C: had 182,687,490,048 bytes free. RAM had 14,480,112 KiB free of 33,486,624
KiB; the RTX 5060 Ti had 15,238 MiB free of 16,311 MiB. Test scratch was under
the approved job directory and removed after the run.

## Limits and remaining authority

This verifies a local synthetic control-plane primitive only. It does not
establish compatibility with a model runtime, a serializer/tokenizer, the
OpenCode client, E1 identity, E2 consented experience lineage, training,
utility, production activation, or production recovery. The backup is on the
same store and volume; review and fixtures do not establish power-loss or
volume-loss recovery. Filesystem check/use races against non-cooperating
external writers are not eliminated. The symlink fixture was skipped on this
host.

No human-only authority was used or granted. Model acquisition/loading,
training or inference, real task data, integration installation/use, and
production activation remain separate decisions. Root owns the shared goal
index and commit. No files were committed by this task.

## Repair follow-up

Date: 2026-09-24 (America/Edmonton)
Job: `W2-NS-E3-LIFECYCLE-FIX-20260924`
Nonce: `E3FIX-ROOT-91B2`
Base HEAD: `cbd819d324bcc571af5116c6a40b3f58519d375d`

The root-authorized repair checked receipts as exact canonical bytes during
activation and active-candidate verification. This rejects numeric `0` in
place of JSON `false` and duplicate keys. Inventory still rejects orphaned
receipt files, while deferring receipt-content validation until the candidate
is activated or referenced as active. This lets startup recover to the prior
version when an active candidate receipt is malformed. Admission and activation
now verify the current active manifest digest and all parent payload hashes
before candidate compatibility checks.

The stale-reset audit finding did not reproduce against the assigned base:
`reset_personal` already had `@_serialized_writer` at HEAD. A regression test
now confirms that a stale store instance cannot reset over another instance's
activation and that the committed state identities remain unchanged.

Changed file hashes:

- `src/wrench_harness/model_lifecycle.py` SHA-256:
  `6A5C586981B26646223815BD161FA1191CB2FA0AA75CC8CAE3E2D44407680E56`
- `tests/test_model_lifecycle.py` SHA-256:
  `B200F7428368019BEA3BBBAA02CB3AE53A12BED85EFAD140615BEC7F182D154B`

Verification used the existing Python 3.11.16 runtime and pytest cache, with
synthetic temporary stores only:

```powershell
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -m pytest -p no:cacheprovider --basetemp='C:\wrench-slm-data\tmp\W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924\impl\pytest-E3FIX2-20260924' tests/test_model_lifecycle.py -q
```

Result: **26 passed, 1 skipped in 35.08s**. The symlink fixture was skipped
because the Windows host did not grant link creation. `git diff --check`
passed. The new regressions cover numeric flags and duplicate keys on
activation and open, stale reset after activation from another instance, and
corrupt active-parent manifest/payload rejection before promotion. Open-time
receipt rejection recovers to factory through the retained prior pointer.

Before verification, storage was `WITHIN_LIMIT`: 1,714,704,683 bytes actual
plus 1,151,576 bytes reserved, leaving 48,284,143,740 bytes under the limit.
RAM was 52.8% free and the RTX 5060 Ti had 15,462 MiB free of 16,311 MiB.
After verification, storage remained within the limit at 1,714,707,890 bytes
actual plus 1,151,576 reserved; RAM was 52.7% free and VRAM was 15,459 MiB
free. The E3 fix reservation remains active for root's integration and review.

Independent read-only review returned **PASS**, job
`E3-LIFECYCLE-FIX-REVIEW-20260924`, nonce `E3FIXREV-91B2`, against the exact
source and test hashes above. The reviewer confirmed parent verification,
canonical receipt checks, fallback recovery for a malformed active receipt,
and the stale-reset regression. No client, endpoint, provider, model, download,
or real task data was used. Power-loss, volume-loss, and non-cooperating
filesystem-writer recovery remain unproven.
