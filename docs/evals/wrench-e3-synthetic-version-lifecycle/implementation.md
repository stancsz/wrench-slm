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
