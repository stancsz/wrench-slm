# Phase 95: public package 4M latest-intent route

This phase fixes a real failure in the downloaded package route. A monolithic
4M-token message contained stale reference text with the words `status
observed`, followed by a newer read request. The old route inspected the whole
suffix and incorrectly proposed `git_read_status`.

The worker now isolates an explicit newest-intent control block before running
the deterministic mechanical router. The full payload remains available to
the reference lookup path, so old evidence can still be used without allowing
stale text to override the current action.

## Evidence

- `v22-validation.json`: structural package validation passed.
- `probe-v22.json`: a materialized package accepted a 4,000,000-token
  estimated payload, returned `read_file` for the current intent, used the
  embedded mechanical backend, made zero model calls, and completed in
  `10.948 ms` on the local development machine.
- Repository regression suite: `109 passed`, with 8 existing deprecation
  warnings.

The probe is package-worker evidence. It does not claim dense native attention
quality over all 4M tokens, MiniMax parity, or production readiness.
