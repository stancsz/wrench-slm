# Root-binding continuity

Goal: [E0 snapshot root-object identity](../../goal/wrench-e0-snapshot-root-identity/GOAL.md)

Task: Carry validated source-root identity from admission through snapshot creation and exact retrieval.

Worker: primary orchestrator; review by `rootbind_postfix_reviewer` and `opencode_binding_integration_reviewer`.

Status: implemented and focused verification passed. Date: 2026-09-24 (America/Edmonton).

## Work

Added `SourceRootBinding`, captured before caller-controlled path iteration, and propagated it through snapshot creation, exact retrieval, and the OpenCode session-root preparation seam. POSIX capture now compares the directory entry with the opened handle and confirms the entry still names that handle. Malformed relative bindings and unavailable POSIX dir-fd support fail as `SnapshotAdmissionError`.

The OpenCode flow for preserving continuity is: resolve the session record, pass `resolved.binding` to `create_snapshot`, and pass the same `resolved` value as `resolved_session_root` to `prepare_opencode_e0_context`. No client is installed or run.

## Evidence

On Windows, Python 3.11.16 and pytest 8.3.5:

```text
uv run --no-project --python 3.11.16 --with pytest==8.3.5 pytest tests/test_snapshot.py tests/test_opencode_session_root.py tests/test_opencode_context.py tests/test_e0_context_pipeline.py -q
75 passed, 8 skipped in 4.15s
```

`git diff --check` passed. Coverage includes root replacement during path iteration and initial POSIX handle capture, normal bound retrieval, byte-identical replacement before retrieval, relative malformed binding, unavailable dir-fd capability, and OpenCode resolve-to-prepare mismatch.

The Windows run skips POSIX-only tests. To verify the changed POSIX capture
path without installing pytest in WSL, Ubuntu 24.04 WSL Python 3.12.3 ran a
bounded standard-library smoke script from the approved data root. It
deterministically replaced the selected directory between name stat and
relative open; capture rejected it with `root_directory_binding_changed`.
A normal bound snapshot/exact-retrieval round trip also passed. The temporary
script was removed, and no WSL package was installed.

## Limits and next action

The binding is a replacement-detection token, not authentication or an atomic multi-file filesystem snapshot. Filesystem identity reuse, Windows UNC/network behavior, runtime prompt/token equivalence, OpenCode dispatch veto, complete request accounting, and E4 utility remain open. Only authored synthetic fixtures are authorized today. See the [independent evaluation](../../evals/wrench-e0-snapshot-root-identity/root-binding-continuity-review.md).
