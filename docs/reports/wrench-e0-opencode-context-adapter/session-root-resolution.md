# OpenCode session-root resolution slice

Job: `W2-E0-OPENCODE-SESSION-ROOT-20260924`

Expected base: `ee29493`

OpenCode source pin: `v2.0.15`, commit `6f3639d`

Package pin: `@opencode/plugin@2.0.15`

## Result

Added `resolve_opencode_session_root` as a provider-free Wrench boundary. It
accepts an event session ID and a session record, verifies that the record ID
matches, accepts only the session's absolute `location.directory`, rejects
parent path components and any nonempty or null `subpath`, and validates that
the configured root is an existing usable directory. It does not query
OpenCode or infer a root from process state. The result preserves the configured
lexical root so the existing snapshot-v2 identity uses the same path the
session supplied.

The existing snapshot module exposes `validate_source_root` for this bounded
check. On POSIX it opens the directory chain without following symlink
components and closes the handles before returning. On Windows it uses the
existing root preparation checks. Neither function enumerates repository files
or retains source bytes.

## Boundary and limits

The OpenCode v2.0.15 tagged schema has a session `id`, `location.directory`,
and optional `subpath`; tagged plugin types expose semantic context fields but
no typed context-veto result. The resolver is not an OpenCode plugin or hook,
does not establish callback behavior, and cannot prevent a model dispatch. The
selected downstream serializer, provider/model, tokenizer, and final-request
failure contract remain open. No client, provider, model, or tokenizer was
installed or run.

This code slice is offline mechanics only. No participant data was collected,
no corpus was admitted, and no task-utility or E0-acceptance claim is made.
`DATA_SOURCES.md` remains an untracked owner edit and was left untouched. Its
ARB section should be reconciled against the committed benchmark-admission
audit before that source is used; acquisition remains blocked by the audit's
expanded-size, rights, and query-provenance requirements.

## Verification

The source and docs were reviewed against the pinned tag schemas. Independent
code review and `git diff --check` are recorded in the companion evaluation.
No tests were run in this slice.

## Follow-on root-to-preparation seam

Commit `701dd9368556e18d166054fa97dbeada9ede9194` added
`prepare_opencode_e0_context`. It accepts the supplied session record plus the
existing bounded E0 arguments, resolves the session root, and injects that root
as the only `source_root`. Its returned join carries the session ID,
configured-root path, snapshot and root-location hashes, and the preparation
result. The actual preparation path still performs exact retrieval against the
snapshot's root identity. The helper does not query OpenCode or dispatch a
model.

Independent review job `W2-NS-OC-BIND-SUP-20260924` (nonce `OCB-SUP-E812`)
accepted the seam. The review confirmed that the fixture set covers root
forwarding, ID-mismatch short-circuiting, and an actual call through preparation
with a matching session and snapshot root. A wrong-root fixture was suggested
as optional follow-up; a fixture has now been added that points the session at
a different root containing byte-identical source and expects `unknown_snapshot`
with no prompt or selected evidence and without invoking serializer/tokenizer
callbacks. Independent review confirmed the source path supports those
expectations. The test files were not executed, so this is source and fixture
review only.

Reviewed file hashes:

- `src/wrench_harness/opencode_context.py`:
  `11DE4430FEBA5C346717E10B53FFB4295CA91EAA7CB188190E15216280E6336E`
- `tests/test_opencode_context.py`:
  `8E4879AFD2A5EA268A7E3064DD8E071ED901147A356FB8E6D421508D2C106844`

Windows ancestor reparse-point handling and `workspaceID` are not part of the
current join. The resolver must not be treated as a complete hostile-path
boundary until those semantics are reviewed. No client install, runtime test,
provider request, or participant/repository capture occurred.

## Windows ancestor-path review

Read-only audit job `W2-NS-WIN-ROOT-AUDIT-20260924` (nonce `WRA-9C20`)
confirmed a narrower Windows gap. `_prepare_root_path` checks the final root
component and resolves it, while `_windows_read_stable_source` opens the
resolved root by name with `FILE_FLAG_OPEN_REPARSE_POINT`; that flag protects
the final component. Its subsequent child walk is parent-relative, rejects
reparse children, and holds those handles through the read. A replacement or
redirect of an ancestor between root resolution and root-handle open is not
ruled out by the current sequence. This is a source-level threat analysis, not
a demonstrated exploit or runtime test.

Do not solve this by blindly rejecting every lexical ancestor reparse point:
that would reject intentionally redirected directories. A bounded hardening
design is to open the resolved root from its volume/share anchor using
component-relative directory handles, reject reparse points in that resolved
chain, and retain handles through the exact read. Required Windows fixtures
include a normal temp root, a static ancestor junction, and an ancestor swap
between resolution and root opening. UNC roots need separate coverage before
making a support claim. This hardening is not implemented.

## Tagged source failure-path trace

The tagged `v2.0.15` Promise adapter wraps plugin callbacks in an Effect
Promise; the hook trigger does not catch callback rejection. The model request
awaits the context hook before the LLM runner proceeds to the step that calls
`llm.stream`. This source trace supports that a thrown/rejected context callback
prevents dispatch for that attempt. The callback has no explicit typed veto,
and this trace does not establish visible error handling, session settlement,
scheduler retries, or behavior in an installed runtime. No client was run.

The trace follows the tagged [Promise adapter](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/adapter.ts),
[hook trigger](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/hooks.ts),
[model request](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts),
and [LLM runner](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts).
