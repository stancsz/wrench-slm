# Windows E1 candidate identity verifier

Job: `W2-NS-E1-WINDOWS-IDENTITY-20260925`

Nonce: `E1WIN-SUP-7B31`

Baseline: `d054e4a67024a5c828f114529a458f090964266f`

## Result

Implemented and exercised a bounded Windows verifier for tiny Wrench-authored
synthetic fixtures. The change supports a flat manifest rooted below an
absolute drive-letter path on 64-bit Python and an NTFS volume. The manifest
and receipt retain the existing schema. It does not access the pinned model
candidate files.

The implementation uses `CreateFileW` for the drive root, then opens each
directory component from its retained parent handle with `NtCreateFile` and
`RootDirectory`. Each relative open uses `FILE_OPEN_REPARSE_POINT`; opened
handles are checked with `FileAttributeTagInfo`, and any reparse point is
rejected. The root and every directory handle remain open through enumeration
and hashing. Opens request read sharing only, which denies ordinary concurrent
write, rename, and delete opens while the verification handles remain open.
The file handle remains open across streamed reads and the final path re-open.

The verifier enumerates directly from the pinned root handle with repeated
`GetFileInformationByHandleEx(FileIdBothDirectoryInfo)` calls. It stops only
when Windows reports `ERROR_NO_MORE_FILES`; any other enumeration error fails
closed. Each returned buffer is bounded to 1 MiB, parsed with bounds checks,
and the total accepted tree is capped at 256 entries. The exact names and
file-set are matched before hashing. Unicode names are decoded from the
length-delimited UTF-16 fields. At present, nested manifest paths, UNC paths,
non-NTFS filesystems, 32-bit Python, unsupported Windows APIs, and malformed
or oversized enumeration results fail closed. There is no path-based or
POSIX-style fallback on Windows.

For identity binding, the legacy 64-bit ID from directory enumeration is
compared with the file index and volume serial returned for the opened handle
by `GetFileInformationByHandle`. The same legacy file index and volume serial
are checked after streaming and after reopening the path. The verifier
requires the NTFS filesystem. It checks the file size and type before
streaming, reads at most
64 KiB per block, compares size, change/write times and file identity after
the read, and reopens the name relative to the pinned root with no-follow
semantics to compare the same identity again. NTFS file IDs remain stable
until deletion; the retained handles omit delete sharing during this check.
Directory and file handles are closed in `finally` blocks, including the
descriptor ownership transfer used for streaming.

## Why this duplicates a small part of snapshot handling

`snapshot._windows_read_stable_source` already provides a tested Windows
`NtCreateFile` parent-relative walk, but it returns a complete in-memory byte
string for one source file and closes its handles before returning. Its
`MAX_SOURCE_BYTES` bound is 256 KiB. Candidate identity accepts up to 4 GB in
aggregate and needs to stream each file while the pinned root and file handles
stay open. The helper also does not enumerate the complete directory from the
pinned root or bind each enumeration row to the opened file ID. Reusing it
would either reject legitimate candidate files above 256 KiB or weaken the
current streaming, exact-file-set and race checks. The existing API is private
and its ctypes declarations are local to the function, so there is no narrow
handle object that this verifier can safely reuse without changing
`snapshot.py` outside this task's write scope.

This duplication is intentionally limited to the candidate identity module.
It is not a general filesystem abstraction. A later shared Windows handle
module could remove the duplication once both consumers can use the same
streaming and enumeration contract.

## Verification

The final focused run used Python 3.11.16 from the existing local Astral
runtime and cached pytest 8.4.2 at
`C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages`.
Exact PowerShell command and environment:

```text
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src;C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
$env:TEMP='C:\wrench-slm-data\tmp'
$env:TMP='C:\wrench-slm-data\tmp'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -m pytest tests/test_candidate_identity.py -q -rs -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\W2-NS-E1-WINDOWS-JUNCTION-REVIEW2-20260925
16 passed, 6 skipped
```

The passing Windows cases include verification of the two-file fixture,
wrong-size and changed-content rejection, missing and unexpected file-set
rejection, metadata bounds, drive-root policy, a Unicode filename round trip,
and exact inventory across multiple bounded enumeration calls. A Windows
junction fixture verified that both an unexpected child junction and a root
reached through an ancestor junction are rejected. The test creates only
temporary junctions under `tmp_path` and removes the junctions themselves
with `os.rmdir`; no junction remained. The single Windows skip is the
symlink-specific fixture: Windows symlink creation was unavailable due to
the account's symlink privilege. The other five skips are POSIX-only handle race
seams; POSIX evidence is recorded in the
[initial verifier report](identity-verifier.md). `git diff --check` passed.

The final test result is bound to these working-tree file hashes:

- `src/wrench_harness/candidate_identity.py` SHA-256:
  `9163a320ec8ddfabe6f230b211f1721d161821df919ba6c9376f49d272b2e63b`
- `tests/test_candidate_identity.py` SHA-256:
  `143619bcc45253ff0503cba23b9802dd357f46047786055b0a96a736f6c489c7`

The focused Windows run executed only synthetic fixture bytes. No network,
client, provider, model, training, inference, benchmark, package, or real-task
operation occurred. A successful receipt still proves only a point-in-time
local byte identity match. Run against a locally controlled, immutable
snapshot; filesystem administrators and out-of-band writers are outside the
ordinary sharing-mode protection described here.

## API references

- [NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile) documents `RootDirectory`-relative names and `FILE_OPEN_REPARSE_POINT`.
- [FILE_ID_BOTH_DIR_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_both_dir_info) documents handle-based directory enumeration and continuation across calls.
- [BY_HANDLE_FILE_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/ns-fileapi-by_handle_file_information) documents the legacy file index and volume serial. Windows NTFS is required because its file IDs remain stable until deletion.
- [GetFileInformationByHandleEx](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex) documents the directory-entry information class used for handle-based enumeration.
- [GetVolumeInformationByHandleW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumeinformationbyhandlew) binds the NTFS check to the opened root handle.
- [Python `os` support for `dir_fd`](https://docs.python.org/3/library/os.html#os.supports_dir_fd) notes that `dir_fd` currently works only on Unix, which is why Python's POSIX traversal cannot serve this Windows path.

The native `NtCreateFile` call is made through ctypes and has no Python-level
fallback. If the API entry points, structure layouts, file identity queries,
NTFS check, or enumeration behavior are unavailable, verification raises a
bounded error. The current run establishes behavior on this 64-bit Windows
developer host and its NTFS volume only. Initial independent source review
found no blocking defect. Fresh full review `W2-NS-E1-WINDOWS-FULL-REVIEW-20260925`
(nonce `E1REV-FULL-61A9`) returned **PASS** against the source and test hashes
above; the reviewer did not run tests. The junction helper skips only for
captured, recognized privilege or platform-support failures and fails for
other `mklink` errors.

After the run stopped and outputs were accounted for, all three E1
reservations (`W2-NS-E1-WINDOWS-IDENTITY-20260925`,
`W2-NS-E1-WINDOWS-JUNCTION-20260925`, and
`W2-NS-E1-WINDOWS-JUNCTION-REVIEW2-20260925`) were released. Final storage
status with the uv cache included was `WITHIN_LIMIT`: 10,052,660,445 actual
bytes, 103,000 bytes in unrelated active reservations, 10,052,763,445
projected bytes, and 39,947,236,554 bytes headroom. C: had 183,746,764,800
bytes free. At this final check, RAM was 41.4% free and the RTX 5060 Ti had
15,214 MiB free of 16,311 MiB. No GPU was used by the tests.
