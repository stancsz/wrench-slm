# OpenCode local CLI install evaluation

Job: `W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925`, nonce `OPL-4D91`  
Reviewed revision: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`  
Reviewer: goal supervisor, with independent install handoff evidence

## Finding

The local OpenCode v2.0.15 CLI setup is present at the recorded isolated path.
Its wrapper and `debug paths`/`debug config` evidence support the claim that
configuration and runtime state were kept inside the Wrench approved root.
The saved model-list response supports only `GET /v1/models` connectivity to
`127.0.0.1:4000` and availability of model ID `current`. This is not a client
request or route test.

The install report records npm package integrity metadata, native executable
SHA-256 identities and the measured 1,036,471,244-byte installation directory.
`service.json` content is intentionally excluded. No task, prompt, chat,
inference, external provider call, or installed plugin is evidenced. The
unrelated repository `uv.lock` was preserved.

## Acceptance

- CLI version: `v2.0.15` in saved version output.
- Isolated paths: under
  `C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925`.
- Local endpoint evidence: saved GET to `/v1/models` returned 200; no POST
  request or generation result is claimed.
- Current aggregate storage status with npm cache included:
  `WITHIN_LIMIT`, actual `2,280,564,978` bytes, reservations `15,103,000`
  bytes, projected `2,295,667,978` bytes, headroom `47,704,332,021` bytes.
- No prompt, task, chat, inference, credentials, or external provider use.

## Limits

This is an installation/configuration evaluation only. OpenCode runtime
validation, the client hook boundary, model dispatch behavior, request body,
provider transport, tokenizer parity, and any utility outcome remain
unverified. The install config chooses the generic OpenAI-compatible chat
route for `wrench-local/current`; the separate E0 Responses route/model
research pin must not be reported as tested by this setup. See the
[installation report](../../reports/wrench-e0-opencode-context-adapter/local-client-install.md)
and [mock runtime preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md).
