# E0 root-object identity in source snapshots

Status: bounded snapshot-v3 increment implemented and independently reviewed
Updated: 2026-09-24 (America/Edmonton)

## Outcome

Bind a source snapshot to both the normalized configured root path and the
filesystem identity read from the retained root directory handle. Include the
tagged object identity in the canonical snapshot digest. Detect replacement
of an ordinary directory at the same configured path even when selected source
bytes are identical. Require the same root identity for every file admitted
to one snapshot and during each later exact retrieval.

## Acceptance evidence

- Emit `wrench.source-snapshot.v3`; validate the required platform-tagged root
  identity before accepting a manifest. V2 manifests fail closed.
- Read POSIX device/inode identity from the root descriptor and Windows volume
  serial/file ID from the retained root handle used for the read.
- Bind the identity into `snapshot_sha256`, preserve lexical-root binding, and
  expose the identity through the OpenCode preparation join.
- Reject byte-identical directory replacement at the same path and root
  replacement between selected file reads.
- Focused Windows Python 3.11.16 verification: 127 passed, 9 skipped. Focused
  Ubuntu 24.04 WSL Python 3.12.3 verification: 132 passed, 4 skipped.
- Independent code review `W2-NS-ROOT-IDENTITY-V3-REVIEW-20260924`, nonce
  `RIV3-1B6F`, found no blocking issues.

## Limits

Filesystem object IDs are replacement-detection signals. They can eventually
be reused and do not authenticate the snapshot author or make an atomic
multi-file filesystem snapshot. Each source is checked during its own read;
selected files are not observed under a filesystem-wide transaction.
Windows UNC/network filesystem identity behavior is unqualified. Filesystems
that cannot provide a usable Windows file ID fail closed. The schema bump
changes snapshot hashes and all identities derived from those hashes; existing
v2 snapshot values are not migrated or accepted by v3 validation.

Windows API references: [GetFileInformationByHandleEx](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getfileinformationbyhandleex)
defines `FileIdInfo` as information class `0x12`; [FILE_ID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_id_info)
defines its volume serial and 128-bit file identifier.

This remains a local E0 component. It does not qualify the installed OpenCode
runtime, provider serializer/tokenizer parity, request-lifecycle accounting,
outcome authority, or E4 task utility.
