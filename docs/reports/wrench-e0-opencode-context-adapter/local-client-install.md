# OpenCode local CLI install and localhost configuration

Job: `W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925`
Nonce: `OPL-4D91`
Date: 2026-09-24 (America/Edmonton)
Expected repository revision: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`

## Result

OpenCode CLI `v2.0.15` is installed in an isolated job directory under
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925`.
The wrapper
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\opencode-local.ps1`
sets user, XDG, OpenCode, npm cache, log, and temporary paths inside that job
directory, selects its `workspace` directory, and runs the local prefix CLI.
Its only configured provider is `wrench-local`, package
`@opencode/ai/providers/openai-compatible`, base URL
`http://127.0.0.1:4000/v1`, with configured model ID `current` in
`workspace\opencode.json`. No plugin is configured.

Registry metadata for `@opencode/cli@2.0.15` recorded tarball
`https://registry.npmjs.org/@opencode/cli/-/cli-2.0.15.tgz`, 2,419 compressed
bytes, 7,124 unpacked bytes, and integrity
`sha512-Ynxz9HRJiHQBotBrQeEt3T/3TyEpkwdZkMTE7HPxT2nB1IU3WAqFXBYiIpWTYLKifXga4L5UG0sXEDISe/rJxg==`.
The installed x64 native executable is 203,656,232 bytes with SHA-256
`64e18ba60360de85583d898923d29af6b86d448f5531f58feea981302734608d`.
The optional baseline x64 executable is also retained at 203,656,232 bytes,
SHA-256
`986c73f1d8f16d31f5bff6f9651bfcae407b85615a394a80bd002b1944b4a3e5`.
The registry package versions, executable bytes and identities, wrapper, and
configuration should be treated as separate identity evidence. The full
isolated installation directory measured 1,036,471,244 bytes across 609
files. The optional native packages remain included in that footprint.
The installed wrapper SHA-256 is
`3ea4a021c1d2b131992185b3ce75962edabe2d71da2df5d5610bf1f49db65f0f`;
`workspace\\opencode.json` SHA-256 is
`a8698774b7592572a5592372d65e13491c82cec5f043fff594d8158d932ff40d`.
The saved version response hash is
`50f9daa2843d413b37c8f893383c9aa89b9919a88f5dece03c9880ba9405adad` and
the model-list response hash is
`c33d8087b76470e698292d43767fb14308880614711d3efdf065dcb165603a20`.

## Observed checks

- The isolated CLI reported `opencode v2.0.15`; saved help output exposed the
  expected CLI commands and flags.
- `debug paths` and `debug config` resolved user, data, cache, configuration,
  state, database, and log locations under the job root. The saved config
  source report showed the job-local config directory and the provider file.
- A single saved `GET http://127.0.0.1:4000/v1/models` response returned HTTP
  200 and included model ID `current`. That server also advertises other IDs,
  so the response establishes availability only, not destination routing for
  a future task.
- No OpenCode prompt, task, chat, model inference, repository read by the
  client, or provider request was made. No external provider was contacted.

## Limits and handoff

This proves the isolated CLI setup and one model-list connectivity check. It
does not prove that a model request routes to the configured localhost URL,
that final request serialization matches the Wrench projection, or that an
OpenCode context hook is registered or enforced. In particular, the selected
OpenAI-compatible configuration differs from the E0 research pin for the
OpenAI Responses route and `gpt-4.1-2025-04-14`; a runtime test must declare
which configuration it is characterizing before any request.

The isolated service state contains generated local service data and is not
published here. No credential value is included in this report. Install
footprint is retained under the approved root and was included in the final
storage inventory. See the [installation evaluation](../../evals/wrench-e0-opencode-context-adapter/local-client-install.md)
and the [runtime mock preflight](mock-runtime-preflight.md).
