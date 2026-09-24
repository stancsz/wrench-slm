# Artifact-store physical-volume headroom guard

Date: 2026-09-24  
Goal: [E0 bounded artifact store](../../goal/wrench-e0-artifact-store/GOAL.md)  
Base: `45162350068eaf6541e15b1eec5dca995b1c0559`  
Job: `W2-NS-STORE-HEADROOM-20260924`  
Nonce: `SPACE-7D2A`  
Status: cooperative per-write guard implemented and focused suite verified

## Change

`ArtifactStore` accepts an optional `free_space_probe(Path) -> int`. The default
uses `shutil.disk_usage(store_root).free`. Immediately before staging each new
object and each atomic manifest replacement, the store requires current free
space to cover the complete staged byte count plus the documented
`5,000,000,000` byte operating reserve. The full byte count is used because the
temporary staged copy coexists with the old destination until replacement.
Probe exceptions and invalid/insufficient values fail closed with a bounded
store limit error.

Read operations do not call the probe. The existing per-store aggregate byte
cap remains a separate limit; this guard measures volume free space and does
not read or change the aggregate admission reservation. Object and manifest
writes each get a fresh check, so a later manifest refusal can leave a newly
written, unreferenced content-addressed object for the existing recovery path
to retain and account for.

## Verification

Storage admission job `W2-NS-STORE-HEADROOM-TEST-20260924` reserved
10,000,000 bytes before the final test run after a fresh `WITHIN_LIMIT`
status. During admission, C: had 184,705,495,040 bytes free. Host RAM was
15,394,574,336 of 34,290,302,976 bytes available; the NVIDIA GeForce RTX 5060
Ti reported 15,211 MiB free of 16,311 MiB.

Windows Python 3.11.16 with the already-cached pytest 8.3.5 dependencies ran:

```text
python -B -m pytest -q -p no:cacheprovider tests/test_artifact_store.py --basetemp C:\wrench-slm-data\cache\W2-NS-STORE-HEADROOM-TEST-20260924\pytest-tmp
33 passed, 3 skipped in 3.33s
```

The skips are existing symlink-creation cases unavailable to this account.
The focused tests include exact reserve boundary admission, refusal before
object/manifest staging, fail-closed invalid/unavailable probes, and a read
that succeeds without probing. The final run included the constructor fallback
adjustment so falsey callables remain injectable. Test scratch remained under
the approved data root. After the test process stopped, status reported
`WITHIN_LIMIT`: 663,523,282 actual bytes, 50,103,000 bytes in active
reservations before this job released its 10,000,000-byte reservation,
713,626,282 projected bytes, and 49,286,373,717 bytes of headroom.
`git diff --check` passed.

The independent review agreed that sequential object and manifest staging
writes recheck enough current free space to cover the next staged copy and
reserve. It classified the change as **NEEDS_CHANGES** if represented as a hard
5 GB guarantee: separate store roots or unrelated writers can race between a
probe and a write, and initial store-directory creation precedes the first
manifest probe. This report and the goal therefore describe the implementation
as a cooperative per-write check. The reviewer made no edits and ran no tests.

## Limits

This is a save-time check, not a reservation or operating-system quota. Another
store or background process can consume space after the probe and before or
during the write. Directory creation during initialization precedes manifest
probing. It checks each bounded staging write independently rather than
reserving a whole logical transaction. It does not establish crash, power-loss,
hardware, multi-process, or production-volume qualification.
