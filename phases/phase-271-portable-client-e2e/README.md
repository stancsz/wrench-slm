# Phase 271: portable OpenCode and DeepSeek Harness end-to-end smoke

Status: `PORTABLE_CLIENT_SMOKE_PASSED`.

The repository's repeatable `tools/smoke_portable_clients.ps1` runner was
executed against a freshly materialized portable package containing the
bundled OpenCode and DeepSeek Harness configuration files. The runner created
an isolated client workspace, started the package-local Wrench server in
mechanical-only mode, and ran one read-only task through both clients.

Observed result:

- OpenCode exit code: `0`;
- DeepSeek Harness exit code: `0`;
- structured `read` tool observed in the Wrench trace;
- three OpenAI-compatible trace rows including proposal and settlement;
- backends: `embedded-mechanical` and
  `embedded-mechanical-settlement`;
- total model calls: `0`;
- mutation claim: `false`.

This proves the downloaded package's client configuration is usable for the
two OpenAI-compatible clients on the development host. It does not prove
independent RTX 5060 Ti execution, learned MiniMax parity, dense-native 4M
decoder quality, or production readiness.

Evidence:

- package: `D:\models\_wrench-client-config-materializer-check-v4`;
- runner receipt: `D:\models\_wrench-client-e2e-v3\receipt.json`;
- Wrench trace: `D:\models\_wrench-client-e2e-v3\wrench-client.trace.jsonl`.
