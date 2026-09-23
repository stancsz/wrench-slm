# Phase 451: literal-search fallback symlink containment

Date: 2026-09-24

## Change

The Python fallback for `literal_search` previously checked only a candidate's
lexical path. A file symlink beneath the requested search root could therefore
be followed by `stat()` and `read_text()` even when its target was outside the
allowed root.

The fallback now resolves each candidate before checking its file size or
reading content. It skips targets outside either the allowed root or the
requested search root, applies hidden-path checks to the lexical and resolved
paths, and returns that canonical path in matches. The change preserves the
existing ripgrep fast path and whole-request scope.

## Evidence and limits

- Source review confirmed the containment checks precede fallback metadata and
  content reads.
- `git diff --check` is the only verification performed. No tests or runtime
  symlink checks were run.
- This resolve-then-open approach blocks a static symlink escape, but does not
  prove race-resistant containment if the filesystem changes between path
  resolution and reading. Gate B remains open until focused fallback and
  platform-specific regression checks pass.
