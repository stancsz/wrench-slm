# Phase 363: Claude Code local client smoke

Date: 2026-09-21

Status: `PASSED_LOCAL_CLIENT_SLICE`

Claude Code completed a real read-only `Read README.md` operation through the
package's local Anthropic Messages-compatible endpoint.

- Client exit code: 0.
- Returned result: `# Wrench SLM` as the first heading.
- Trace protocol: `anthropic-messages`.
- Accepted request: `embedded-mechanical`, 2.989 ms, 0 model calls.
- Tool settlement: `embedded-mechanical-settlement`, 0.019 ms, 0 model calls.
- The trace is hash-bound and records the first-layer pruner/cherrypicker with
  a 64K working-context budget.

Claude Code emitted a non-fatal `unrecognized_model` diagnostic for
`MiniMax-M2.7`. This is retained as a warning. The local trace proves the
request stayed on the Wrench route and did not fall through to a provider.

This proves a real local Claude Code integration slice. It does not prove
independent RTX 5060 Ti execution, learned MiniMax parity, dense-native 4M
decoder quality, or production readiness.
