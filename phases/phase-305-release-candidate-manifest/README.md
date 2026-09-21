# Phase 305: v103 release-candidate manifest

The current local v103 package was composed into a single hash-bound candidate
manifest without uploading or changing any Hugging Face repository.

- package file manifest SHA-256: `f1b0ba92db08b958ad2b4e17fb1d7162b6a672dfe85de35a613f03eb0063641c`
- local package structural validation: passed
- local OpenCode, DeepSeek Harness, and Claude Code acceptance: passed
- local Ollama-shaped 4M acceptance: passed
- parameter count remains below the 4.25B ceiling
- `publication_performed`: `false`
- `all_local_checks_pass`: `true`

The receipt status is intentionally `NEEDS_CLEAN_SOURCE_SNAPSHOT` because the
shared source worktree contains pre-existing user changes and untracked phase
artifacts. This prevents the candidate from being presented as a clean,
reproducible release snapshot. It does not invalidate the package-local
runtime evidence.

Receipt: `release-candidate.json`

Before publication or independent 5060Ti promotion, create a clean source
snapshot, re-materialize or re-verify the exact package, and preserve this
manifest hash. No upload was performed in this phase.
