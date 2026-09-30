# Iteration 038: OpenCode no-provider hook registration seam (2026-09-27)

## Objective

Move the existing provider-free `http.request` observer closer to the actual
OpenCode plugin boundary, without contacting SubRoute or a provider.

## Change

Extracted plugin setup into
`examples/opencode_v2_subroute_capture/plugin_setup.mjs`. The SDK-facing
`plugin.mjs` now binds the real `Plugin.define`, observer, bounded sink, and
no-provider callback to that setup factory. The factory refuses missing hook
registration, requires a disposer, remains inert when disabled, and disposes
at most once. Added `plugin_setup.test.mjs` to cover disabled setup,
`http.request` registration, the synthetic callback's fail-closed ordering,
content-free receipt handling, idempotent disposal, and missing-hook refusal.

The installed CLI reports OpenCode `v2.0.12`. Pinned upstream source at that
version constructs the Web `Request`, awaits the `http.request` hook, rebuilds
the provider request, and only then invokes the HTTP handler. The hook registry
awaits callbacks in registration order and does not swallow callback failures.
This is source-contract evidence that a thrown hook should stop before the
handler. It does not prove the installed runtime loaded this plugin, propagates
the exception as expected, or exposes all retries through this hook.

## Verification and limits

No test or OpenCode runtime preflight was run. A fresh host sample showed
2,765.3/32,701.8 MiB RAM free (8.45%), below the 10% runtime reserve; VRAM was
15,103/16,311 MiB free. No Wrench inference, training, benchmark, or provider
request occurred. The added tests remain unverified until RAM and VRAM both
meet the runtime floor. Training remains higher priority when the fit-03 25%
RAM start gate and every exact run gate pass.

Even after the focused test passes, this remains fixture/helper-level
integration evidence. The separate next step is an isolated OpenCode runtime
preflight against a loopback-only mock, proving plugin loading and handler
non-invocation without contacting `127.0.0.1:4000`. Full-request token counts,
paired frontier usage, task success, cost, and all-day engineering remain
unmeasured.

## Sources

- [OpenCode v2.0.12 request path](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/core/src/session/model-request.ts#L1497-L1518)
- [OpenCode v2.0.12 hook registry](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/core/src/plugin/hooks.ts#L556-L568)
- [OpenCode v2.0.12 plugin API](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/plugin/src/promise/session.ts#L649-L661)
