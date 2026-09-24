# E1 Windows candidate identity verifier

## Objective

Provide a bounded local identity check for a flat model-candidate file
manifest on supported Windows hosts, while keeping candidate selection,
download, training, inference, and activation behind their separate gates.

## Status and evidence

Status: the Windows local-mechanics slice is accepted after a focused synthetic
fixture run and independent source/test review (2026-09-25).

The verifier uses retained, handle-relative no-follow opens, bounded full
directory enumeration, NTFS file identity, streamed hashing, and post-read
identity checks. On the 64-bit Windows NTFS developer host, the focused suite
reported 16 passed and 6 skipped. Both junction rejection cases passed; the
symlink case skipped because the account lacked symlink privilege, and five
POSIX-only seams were skipped. Independent full review returned PASS; that
reviewer did not run tests.

See the [implementation report](../../reports/wrench-e1-candidate-identity/windows-verifier.md)
and [evaluation](../../evals/wrench-e1-candidate-identity/windows-verifier.md).

## Limits and remaining gates

Evidence covers only tiny Wrench-authored synthetic fixtures on the named
Windows host and NTFS volume. The verifier supports only flat manifests rooted
on a drive-letter path with the required native APIs. It does not establish a
filesystem transaction against administrators or out-of-band writers, verify
an actual downloaded model, prove backend compatibility or adapter composition,
measure held-out quality or resources, or authorize promotion.

E1 model selection and download still require complete shard and metadata
inventory, pinned revision and hashes, storage admission, volume headroom, and
host RAM/VRAM reserves. Compatibility, personal-adapter training, held-out
evaluation, atomic activation, and rollback remain open under the v2
architecture and staged experiment.
