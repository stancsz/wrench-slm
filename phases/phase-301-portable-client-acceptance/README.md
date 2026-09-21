# Phase 301: downloaded-package client acceptance

## Result

The current materialized package was started directly from its download
directory and connected to all three target coding clients:

- OpenCode: OpenAI-compatible route, read-only `read` work observed, exit 0
- DeepSeek Harness: OpenAI-compatible route, read-only `read` work observed, exit 0
- Claude Code: Anthropic Messages route, native `Read` work observed, exit 0
- all client traces recorded zero model calls and no mutation claim
- the package-local server supplied the endpoint; no external provider was used

The combined receipt is `portable-client-acceptance.json`. Detailed source
traces are `wrench-client.trace.jsonl` and `claude.trace.jsonl`.

## Fix included

The first attempt exposed a real portability issue in
`tools/smoke_portable_clients.ps1`: a relative output directory was passed to
the package child process, whose different working directory made the allowed
workspace path invalid. The script now resolves `OutputDir` to an absolute path
before constructing the workspace. The rerun passed on port 28984.

## Boundary

This is a client integration and no-mutation smoke, not MiniMax parity,
independent RTX 5060 Ti verification, dense-native 4M quality, or production
authorization.
