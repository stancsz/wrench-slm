# Phase 450: isolate Git status from repository FSMonitor hooks

Date: 2026-09-23

## Change

`git_read_status` ran `git status` using the target repository's effective
configuration. Git supports `core.fsmonitor` as an external hook command, so a
repository inside the allowed root could cause a supposedly read-only status
request to execute that command with Wrench's process privileges.

The status invocation now adds the per-command override `core.fsmonitor=` to
disable FSMonitor for this one call. It does not alter repository or user Git
configuration. This reduces one path for configured command execution; it is
not a complete audit of every behavior available through Git configuration.

## Evidence and limits

- Source review confirmed `_git_read_status` passes the override directly as a
  Git command-line configuration argument.
- `git diff --check` passed for the changed source and phase record.
- No tests were added or run. In particular, a repository-local FSMonitor
  sentinel regression check remains needed before claiming the boundary is
  verified.
- No model, provider, credential, training, or large-artifact work occurred.
