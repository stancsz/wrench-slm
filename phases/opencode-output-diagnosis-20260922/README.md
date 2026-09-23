# OpenCode output completion diagnosis

The installed OpenCode is 1.15.10. The local provider receives the request,
OpenCode stores the correct assistant text with a completed end timestamp,
and the CLI exits zero without printing it. This reproduces with an isolated
home, `--pure`, a local-only provider, and no paid calls. The saved session
export is diagnostic evidence only; it is not substituted for stdout success.

Evidence: `local-run-export/receipt.json` and `local-run-export/stdout.jsonl`.

The upstream 1.15.10 CLI starts `loop(client, events)` without awaiting it,
then returns when the prompt completes. Teardown can interrupt the event
consumer before the final text is printed. The matching 1.18.32 source retains
the loop promise and awaits completion before returning from a local run:

- [1.15.10 source](https://github.com/anomalyco/opencode/blob/v1.15.10/packages/opencode/src/cli/cmd/run.ts)
- [1.18.32 completion handling](https://github.com/anomalyco/opencode/blob/v1.18.32/packages/opencode/src/cli/cmd/run.ts#L835-L877)

## Verified repair

An isolated official 1.18.32 Windows executable was downloaded into the ignored
`artifacts/tools/opencode-v1.18.32/` directory. Global OpenCode and user config
were left unchanged. The release zip SHA-256 matched the GitHub release digest:
`1483c72d5adced825590a0ecf8cc18b3e87e535960a125dbf539d33bce135d0f`.
Executable SHA-256:
`cf664aa1da32b788f9b2699b84a9bb9be30b7e025693b90f9b85829d5fe4e252`.

Against the same local fixture the new CLI emitted `step_start`, `text`, and
`step_finish`, including the expected answer. See `fixed-client/receipt.json`.

The paired runner accepts `--opencode-executable` and passes the same explicit
binary to the baseline and the hybrid PowerShell launcher. The smoke receipt
records its path and version. A regression checks propagation through both arms.

The integrated local rerun returned the expected baseline answers and all
three hybrid client answers, including OpenCode. See `fixed-canary.json` and
`fixed-canary-hybrid/opencode.stdout.txt`. Status is correctly
`FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE`. Stub token counts
are synthetic. This resolves output compatibility, not productive value.

Reproduce using the isolated binary:

```powershell
python tools/probe_paired_real_client_canary.py `
  --package-dir D:\models\_wrench-release-candidate-settlement5-20260922 `
  --output phases/opencode-output-diagnosis-20260922/fixed-canary.json `
  --port 29470 `
  --opencode-executable artifacts/tools/opencode-v1.18.32/opencode.exe
```

Full regression: `240 passed, 18 warnings in 21.28s`. RAM and VRAM reserves
remained above 10 percent. No model training, paid provider calls, global client
upgrade, commit, or production enablement was performed.
