# OpenCode localhost setup follow-up

Job ID: `W2-NS-OPENCODE-SETUP-20260925`
Nonce: `OCSETUP-8D41`
Checked: 2026-09-24 (local host, Windows)

## Verified setup

OpenCode was already installed in its isolated Wrench data directory, so this
follow-up made no package installation or client configuration changes. The
isolated PowerShell entry point is
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\opencode-local.ps1`.
It scopes user, XDG, npm, temporary, database, and config paths beneath that
job root and starts in the associated `workspace` directory.

The entry point reported `opencode v2.0.15`. Its configured file is
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\workspace\opencode.json`.
That config selects `wrench-local/current`, uses the OpenAI-compatible provider
package `@opencode/ai/providers/openai-compatible`, and sets the base URL to
`http://127.0.0.1:4000/v1`; the model ID is `current`, and the plugin list is
empty.

SHA-256 identities:

- `opencode-local.ps1`: `3EA4A021C1D2B131992185B3CE75962EDABE2D71DA2DF5D5610BF1F49DB65F0F`
- `workspace/opencode.json`: `A8698774B7592572A5592372D65E13491C82CEC5F043FFF594D8158D932FF40D`

## Checks and limits

Read the wrapper and JSON config with PowerShell `Get-Content`; ran the
isolated wrapper with `--version`; computed both hashes with
`Get-FileHash -Algorithm SHA256`; and checked repository status. The only
reported repository item was the pre-existing untracked `uv.lock`.

No connection was made to port 4000. No prompt, model request, inference,
provider spend, plugin install, credential setup, or client session was run.
The local CLI and config therefore establish client-side setup only; they do
not establish that the gateway is reachable or that a request will use a
particular upstream model or tokenizer.

The storage checker reported `WITHIN_LIMIT`: 1,710,355,457 bytes used and
103,000 bytes of other active reservations before this report. A 16,000-byte
reservation for this documentation update was made and released after the
report was accounted for. `Get-Volume -DriveLetter C` reported 182,617,497,600
bytes free at verification time.
