# Root-binding continuity review

Goal: [E0 snapshot root-object identity](../../goal/wrench-e0-snapshot-root-identity/GOAL.md)

Revision reviewed: working tree based on `fc758f874f3fdd41d4f18c023f440cc12aba914e`, before commit.

Reviewers: `rootbind_postfix_reviewer` (independent source/test review), `opencode_binding_integration_reviewer` (independent API-flow and documentation review). Neither reviewer edited files. The orchestrator implemented the changes and performed final verification.

## Findings and resolution

The first review confirmed the normal trusted-binding flow and requested an absolute-path check for manually constructed tokens plus normalized failure when POSIX `dir_fd` support is unavailable. Both were added. A subsequent review found a capture-time POSIX name-to-handle race; capture now compares the pre-open `stat`, opened descriptor `fstat`, and post-open `stat` identities. The reviewer found no other correctness blocker and requested direct retrieval-path coverage. Added a test for successful retrieval with the binding and rejection after same-path byte-identical replacement.

The integration review confirmed that callers must carry the exact same `OpenCodeSessionRoot` binding into `create_snapshot` and `prepare_opencode_e0_context`. Goal docs now state the call sequence and clarify replacement detection is not session authentication, transaction isolation, or dispatch enforcement. The returned dataclass field/constructor shape changed to expose `binding`; `.configured_root` remains a read property.

## Verification

Windows, Python 3.11.16, pytest 8.3.5: 75 passed, 8 skipped across snapshot, OpenCode session-root, OpenCode context, and E0 context pipeline tests. `git diff --check` passed. Storage checker reported `WITHIN_LIMIT` at 645,051,724 actual bytes plus 52,531,800 bytes of active reservations before the final focused test run. No client, provider, or model was installed or run.

After commit, Ubuntu 24.04 WSL Python 3.12.3 ran a standard-library-only
smoke for the POSIX path. It rejected a deterministic directory swap during
root handle capture and passed the ordinary bound snapshot/retrieval round
trip. Pytest was absent in that distro, so the POSIX pytest regression itself
was not run there. The smoke script was held briefly in the approved data
root and removed after completion; its 5,000,000-byte reservation was released.

## Remaining limits

Static review and local fixtures do not establish hostile concurrent-writer immunity beyond the tested capture sequence, authenticated session identity, atomic multi-file snapshots, UNC/network filesystem qualification, dispatch veto, final provider serialization/tokenizer parity, lifecycle accounting, production recovery, or E4 task utility. Runtime integration and real-workflow data remain unapproved.
