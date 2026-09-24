# OpenCode snapshot-to-hook boundary review

Job: `W2-NS-OPENCODE-HOOK-BOUNDARY-20260924`  
Nonce: `OHB-0C73`  
Reviewed HEAD: `3982b0fd1ca984da44e1adfb1100cb7b69d7c7c8`

## Finding

The enrolled snapshot API closes the source-root and selected-path authority
gap at the Python layer. The OpenCode context event supplies `sessionID`,
`system`, `messages`, `agent`, `model`, `tools`, and `options`; it does not
supply an authoritative repository root. A future adapter must fetch the
session record for the exact `event.sessionID` and pass its `.data` record to
`prepare_opencode_project_snapshot`. It must not use the plugin working
directory, process working directory, model text, repository configuration,
or hook-provided paths as root authority.

The enrolled registry binds the event ID to the session record ID, requires a
unique enrolled root and matching root identity, and provides the finite
source-path allowlist. The snapshot API validates the entire explicit
selection against that list before reading. It does not walk the repository.
The resulting `SourceSnapshot` carries path, size, and digest metadata; later
exact retrieval reopens and verifies selected source. These checks do not
provide transaction isolation against concurrent filesystem replacement.

## Integration decision

There is no current IPC entry point from an OpenCode plugin to the Python
snapshot function. A one-shot, fixed `shell:false` process with a bounded,
versioned JSON stdio protocol could characterize the snapshot boundary, but a
plugin that snapshots and discards the result does not add user-visible E0
context. The existing context preparation and materialization path also needs
a Wrench-owned store lifecycle, context policy, and pinned serializer and
tokenizer identities. The snapshot result intentionally marks the exact-token
gate `UNAVAILABLE`, while materialization requires a prepared `READY` gate.

**Recommendation:** do not add an insertion-capable OpenCode plugin until the
Python-side preparation contract covers the store lifecycle and a downstream
serializer/tokenizer identity is pinned. If a snapshot-only bridge is built
before then, keep it as synthetic characterization and describe it as input
handling only. Do not claim context integration, dispatch denial, or exact
token parity.

## Evidence boundary

Synthetic tests can validate the event/session join, bounded protocol fields,
registry resolution, selected-path caps, error handling, and absence of root
paths or source bytes from responses. They cannot establish that the real
OpenCode runtime loads or invokes the plugin, that the live session record
matches the documented shape, that real source use has consent, that dispatch
is denied or settled correctly, or that final provider serialization and
tokenization match the configured route. No client, plugin, local endpoint,
provider, or real project source was touched by this review.

The E0 exact-token gate and broader E0/E4 acceptance remain open. See the
[v2 experiment criteria](../../northstar/V2_EXPERIMENT.md), the
[request-lowering source audit](request-lowering-source-audit.md), and the
[enrolled-project snapshot report](enrolled-project-snapshot.md).
