# OpenCode v2.0.15 configuration schema reconciliation

Job ID: `W2-NS-OPENCODE-CONFIG-V2015-REPAIR-20260925`  
Nonce: `OCFIX15-8D3B`  
Base commit: `dcc476b9c6e8720d828789dcb0d29cb6f6662016`

## Result

The isolated profile's workspace config was rewritten to match the custom
provider structure in the exact OpenCode `v2.0.15` release-tag documentation.
The old config is preserved beside it with a suffix OpenCode does not load as
a config file. The original
[localhost install follow-up](localhost-install-followup.md) remains unchanged
as the record of the prior setup state.

Current config path:
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\workspace\opencode.json`

Current config identity: 404 bytes, SHA-256
`BF30BF301159C947D3632640962C32ED943356D792E1CE89E5C79F715E121F4D`.

The config selects `wrench-local/current`, defines custom provider
`wrench-local` with `npm: @ai-sdk/openai-compatible`, sets
`options.baseURL` to `http://127.0.0.1:4000/v1`, and declares model `current`
with a display name. It has no API key and no plugin entry.

The prior config was 415 bytes with SHA-256
`A8698774B7592572A5592372D65E13491C82CEC5F043FFF594D8158D932FF40D`.
Its exact bytes are preserved at
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\workspace\opencode.json.codex-prior-shape.bak`
with the same length and hash.

## Pinned documentation

The [OpenCode v2.0.15 provider docs](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/web/src/content/docs/providers.mdx)
show a custom OpenAI-compatible provider using the singular `provider` key,
`npm: @ai-sdk/openai-compatible`, `name`, `options.baseURL`, and a `models`
map whose model entries have a `name`. The [v2.0.15 config docs](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/web/src/content/docs/config.mdx)
describe the supported `opencode.json` configuration file locations. The new
file uses those documented field names and keeps the prior loopback endpoint
and model alias.

The previous config instead used `providers`, `package`, `settings.baseURL`,
`modelID`, and `plugins`. Those fields did not match the exact release-tag
examples and are retained only in the hash-bound backup.

## Verification and limits

Both the new config and preserved backup were parsed offline. A static
allowlist assertion confirmed the expected top-level, provider, and model
keys and values. The config was not passed to the OpenCode CLI, so this does
not prove runtime loading or request behavior. No OpenCode process/session was
launched, no connection was made to port 4000, and no model request, credential
access, install, package update, or plugin action occurred.

Admission used a 100,000-byte reservation. Before writing, storage status was
`WITHIN_LIMIT`; C: had 182,543,376,384 bytes free, system RAM was 40.88% free,
and the RTX 5060 Ti reported 15,204 MiB free of 16,311 MiB. The reservation was
released after config and documentation accounting. Final storage status and
independent review are reported with this task completion.
