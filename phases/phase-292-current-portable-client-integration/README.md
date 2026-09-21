# Phase 292: current portable client integration

At source commit `1f73fd0`, the current v103 NVFP4 model artifact was
materialized into `D:\models\_wrench-current-client-20260921` with hard-linked
weights and the bundled runtime, OpenCode config, DeepSeek Harness patch, and
Claude Code launcher.

The first smoke invocation used port `28971` and exposed a real packaging-test
bug: the package client templates default to `28900`, while the smoke script
allowed a different server port without rewriting the temporary client copies.
OpenCode therefore waited on the wrong endpoint. The package itself was not
modified. `tools/smoke_portable_clients.ps1` now rewrites only its temporary
OpenCode and DeepSeek Harness copies, so alternate-port smoke runs are
isolated and reproducible.

The corrected run used port `28972` and passed both OpenCode and DeepSeek
Harness. A separate run of the same current materialized package used
`run_claude_code.ps1` on port `28973` with a loopback blocker and passed a
read-only `Read README.md` request. The resulting traces show the embedded
mechanical route and settlement route, zero model calls, hash-bound payloads,
and no mutation claim.

This closes current-package client wiring for these local read-only smoke
paths. It does not establish MiniMax parity, native learned-decoder quality,
independent RTX 5060 Ti execution, sustained concurrency, or production
enablement.

Evidence is recorded in `current-client-receipt.json`; raw receipts and traces
remain under the external temporary paths recorded there.
