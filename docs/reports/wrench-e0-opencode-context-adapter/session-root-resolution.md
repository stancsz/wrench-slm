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
