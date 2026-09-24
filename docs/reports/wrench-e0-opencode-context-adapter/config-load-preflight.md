# OpenCode v2.0.15 config-load preflight

Job ID: `W2-NS-OPENCODE-CONFIG-LOAD-20260924`
Nonce: `OCLD-7A31`
Repository commit: `c678e5392aa7f6d0d575a0e0f8e9ed27805f4805`

## Result

The isolated CLI reports `opencode v2.0.15` from the allowed version-only
command. Offline parsing and a static field/value check confirmed the corrected
workspace config at
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\workspace\opencode.json`:

- 404 bytes, SHA-256
  `BF30BF301159C947D3632640962C32ED943356D792E1CE89E5C79F715E121F4D`
- model `wrench-local/current`
- custom provider `wrench-local`, package `@ai-sdk/openai-compatible`
- `options.baseURL` of `http://127.0.0.1:4000/v1`
- model key `current`, display name `Current server model`

The preserved prior-shape backup is
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\workspace\opencode.json.codex-prior-shape.bak`:
415 bytes, SHA-256
`A8698774B7592572A5592372D65E13491C82CEC5F043FFF594D8158D932FF40D`.
Both files parse as JSON. The corrected config has only the expected top-level,
provider, and model fields.

## Runtime-check boundary

The resolved-config command was not run. The installed CLI package exposes a
compiled executable without inspectable command-handler source. The pinned
[v2.0.15 provider docs](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/web/src/content/docs/providers.mdx)
and [config docs](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/web/src/content/docs/config.mdx)
document config fields and locations, not whether `debug config` avoids
provider package loading, installation, or external work. The isolated wrapper
sets `OPENCODE_DISABLE_AUTOUPDATE=1`, but that alone does not establish those
other properties. The safety condition for running config inspection therefore
was not met.

Exact checks performed: `git rev-parse HEAD`; `git status --short`; config and
backup `Get-FileHash -Algorithm SHA256`; offline PowerShell `ConvertFrom-Json`
and field/value assertions; and
`& 'C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\opencode-local.ps1' --version`.
No resolved-config command, OpenCode session, prompt, model call, or provider
request was intentionally issued. Network traffic was not monitored during
`--version`, so implicit startup traffic was not observed or ruled out. Runtime
config loading and actual provider/model selection remain unverified.

Before the bounded verification/report work, storage was `WITHIN_LIMIT` at
1,714,288,116 actual bytes with 103,000 bytes in other active reservations.
A 16,000-byte reservation (`W2-NS-OPENCODE-CONFIG-LOAD-20260924`) covered the
version-only command and report; it was released after final accounting. C:
had 182,493,093,888 bytes free. The host had 39.38% system RAM free and the RTX
5060 Ti reported 15,204 MiB free of 16,311 MiB. Final storage status was
`WITHIN_LIMIT`: 1,714,291,752 actual bytes plus 103,000 bytes in other active
reservations; this job's reservation was released.
