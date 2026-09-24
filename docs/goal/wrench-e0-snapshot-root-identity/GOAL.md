# E0 root-object identity in source snapshots

Status: bounded snapshot-v3 identity and continuity increments implemented
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
- Carry the captured root binding across validation, snapshot creation, and
  exact retrieval when a caller needs continuity across intervening work.
- During POSIX root capture, verify the named directory identity before and
  after opening it relative to the pinned parent handle. Reject relative or
  malformed public bindings and report missing dir-fd support as an admission
  error.
- Focused Windows Python 3.11.16 suite for root binding and E0 preparation:
  75 passed, 8 skipped with pytest 8.3.5, including direct bound retrieval
  and byte-identical replacement coverage.
- Independent post-fix source review found no remaining correctness blocker;
  it requested direct retrieval coverage, which was added before final
  verification. See the [continuity evaluation](../../evals/wrench-e0-snapshot-root-identity/root-binding-continuity-review.md)
  for reviewer identity and scope.
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

Callers must retain and pass the `SourceRootBinding` returned by
`bind_source_root` across validation and snapshot creation, then pass that
same binding to `retrieve_exact` when continuity is required. OpenCode callers
can carry `OpenCodeSessionRoot.binding` into both snapshot creation and
`prepare_opencode_e0_context(..., resolved_session_root=...)`. A binding is a
local replacement-detection token, not authenticated session identity, an
atomic multi-file snapshot, or a client dispatch veto.
