# E3 synthetic model-version lifecycle evaluation

Date: 2026-09-24 (America/Edmonton)
Result: **PASS for the bounded synthetic development primitive**
Implementation report SHA-256: `2C312D107D8550C12DA39E1F309778F103ACB14E42021B1C7B2F8A93CE51726C`

## Evidence

- Focused suite: **18 passed, 1 skipped in 24.90s** using Python 3.11.16 and
  the existing pytest 8.4.2 cache. The Windows host denied symlink creation,
  so the symlink fixture skipped. No dependencies were installed.
- `git diff --check`: passed.
- Independent static review: **PASS**, job
  `W2-NS-E3-ADMISSION-FINAL-20260924`, nonce `E3ADMREV-3B80`; source and test
  hashes match those in the report.
- Storage admission stayed `WITHIN_LIMIT`, with npm-cache included; the
  reserved job scope remained active through verification and review. Host
  RAM and VRAM remained above the required 10% free reserve.

## Acceptance within this slice

| Criterion | Result | Evidence scope |
|---|---|---|
| Immutable hash-bound synthetic versions | Pass | Focused file-backed fixtures |
| Candidate completeness, compatibility, and explicit admission | Pass | Rejects missing/corrupt/incompatible candidates and corrupt/missing receipts |
| Atomic development activation and prior/factory retention | Pass | Failure injection, reopen, rollback, and reset fixtures |
| Request-scoped version pins | Pass | In-flight pin stability, stale instance refresh, forged/reopened pin rejection |
| Startup recovery | Pass with limits | Corrupt, oversized, parseable-invalid, and interrupted pointer fixtures preserve a verified backup |
| Writer serialization and stale generation detection | Pass in local fixtures | OS-backed lock and two-process contention/stale-write check |
| Store bounds and unsafe path rejection | Pass with platform skip | 10 MB, 512-entry, version/admission counts, projected writes, orphan/oversized entries; symlink fixture skipped |
| Training and production use | Disabled | Emitted flags are hard-coded false |

## Decision and limits

Accept this as an offline E3 state-machine/storage primitive only. It is not
E3 production acceptance and supplies no evidence about model identity,
runtime compatibility, training, task utility, or serving behavior. The
symlink/reparse fixture needs a host that permits link creation for dynamic
verification. Same-volume state backups and unit fixtures do not establish
power-loss, volume-loss, or non-cooperating filesystem-writer recovery.

No human-only authority was exercised. The shared goal index and commit are
root-owned; this task made no commit.

## Repair follow-up evaluation

Date: 2026-09-24 (America/Edmonton)
Result: **PASS for the bounded synthetic repair**
Base HEAD: `cbd819d324bcc571af5116c6a40b3f58519d375d`
Report: [repair follow-up](../../reports/wrench-e3-synthetic-version-lifecycle/implementation.md#repair-follow-up)

The final source SHA-256 is
`6A5C586981B26646223815BD161FA1191CB2FA0AA75CC8CAE3E2D44407680E56`; the
test SHA-256 is
`B200F7428368019BEA3BBBAA02CB3AE53A12BED85EFAD140615BEC7F182D154B`.
The focused lifecycle suite reported **26 passed, 1 skipped in 35.08s**.
`git diff --check` passed. The existing symlink case skipped because this
Windows host denied symlink creation.

Independent read-only review passed under job
`E3-LIFECYCLE-FIX-REVIEW-20260924`, nonce `E3FIXREV-91B2`, on those exact
hashes. It confirmed canonical-byte receipt validation rejects numeric
false flags and duplicate keys; active candidate receipt failure recovers to a
verified prior version; admission and activation verify the active manifest
digest and payloads; and a stale reset instance cannot overwrite the state
after activation. The reset writer lock was already present at the base HEAD;
the change adds direct regression coverage rather than duplicating the lock.

Storage remained `WITHIN_LIMIT`: post-check actual use was 1,714,707,890 bytes
with 1,151,576 bytes of active reservations. RAM was 52.7% free and VRAM was
15,459 MiB free of 16,311 MiB. The fix reservation remains active for root's
integration and commit. No model, client, endpoint, provider, download, or real
task data was used. This remains synthetic control-plane evidence; production
recovery, power-loss durability, runtime compatibility, and model utility are
not established.

## Reset serialization regression evaluation

Date: 2026-09-24 (America/Edmonton)
Result: **PASS for the bounded concurrency regression**
Base HEAD: `3982b0fd1ca984da44e1adfb1100cb7b69d7c7c8`
Report: [reset serialization follow-up](../../reports/wrench-e3-synthetic-version-lifecycle/implementation.md#reset-serialization-regression-follow-up)

At the assigned base, `reset_personal` already had the serialized-writer
decorator; the earlier missing-decorator finding did not apply to this
revision. The new cross-process regression,
`test_reset_serializes_against_stale_process_activation`, pauses reset while
the OS lock is held and verifies a competing process cannot acquire it before
reset commits. The stale activation then fails, and the test checks generation,
active/prior IDs and their manifest digests, plus the preserved factory ID and
digest. The focused test passed **1/1 in 5.48 seconds**; `git diff --check`
passed. Test SHA-256:
`008B8738D7C0BD493092CAC55F797CFD8F6913678122F38F6B5A472A20461CB3`.

Storage remained within the 50 GB limit, C: retained over 5 GB free, and RAM
and VRAM remained above 10% free. The full lifecycle suite was not rerun for
this test-only follow-up. Independent static review passed on the exact source
and test hashes in the [report](../../reports/wrench-e3-synthetic-version-lifecycle/implementation.md#reset-serialization-regression-follow-up).
Production E3 and power-loss recovery remain open.
