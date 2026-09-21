# Phase 240: dense-native first-layer gate

This phase makes the conditional dense-native target executable in the bundled
FreeToken overlay. When `WRENCH_DENSE_NATIVE_GATE=1`, the raw request has
already arrived at the model-local native endpoint, then the overlay invokes
the same deterministic `FirstLayerContextGate` used by the Wrench worker before
the expensive native decoder layers. The gate is bounded to 32K through 64K
working tokens and fails closed on invalid bounds or raw input above 4M token
equivalents.

The launcher exposes this as a model-local mode. `-NativeDirectInput` enables
the first-layer gate automatically, while `-DenseNativeGate` is accepted as an
explicit equivalent:

```powershell
.\serve_freetoken.ps1 -OllamaApi -NativeDirectInput -DenseNativeGate
```

`-BypassDenseNativeGate` is reserved for capacity probes. It cannot be
combined with either dense-native mode switch.

## Local gate-only receipt

The current source overlay was executed against a synthetic raw payload of
`3,990,568` estimated tokens. It produced `35` tokens of dense-attention input
in `137.329 ms`, with a raw payload SHA-256 and the stage
`first_model_side_pruner_cherrypicker` in the receipt.

This is a current-host deterministic gate measurement. It proves model-package
staging behavior and receipt binding, not native decoder quality, MiniMax
parity, 5060 Ti performance, or production release readiness.

The v95 portable package was then imported independently from its own
`wrench_runtime/sitecustomize.py` with no repository `PYTHONPATH`. It produced
the same raw payload hash and the same 35-token working set in `114.284 ms`.
Structural package validation passed with nine Safetensors shards and no
reported errors.

After fixing the generated README's stale `Set-Location` directory, v96 was
materialized and structurally validated. Its package-local `/api/chat` 4M
handoff then passed with `3,995,842` raw estimated tokens, `1,955` staged
tokens, `106.276 ms` server staging, and `252.351 ms`
complete local round trip. The upstream was a local protocol stub, so this is
package intake and reduction evidence, not native decoder quality.

The v97 package carries the same fix plus the safer launcher default. Structural
validation passed with nine Safetensors shards. Its package-local `/api/chat`
4M handoff passed with `3,995,842` raw estimated tokens, `1,955` staged tokens,
`87.807 ms` server staging, and `243.24 ms` complete local round trip. The
receipt records `first_model_side_pruner_cherrypicker`, a `34.186 ms` gate
latency, and the raw payload hash binding. This is stronger package handoff
evidence, but the upstream remains a local protocol stub, so it still does not
prove dense decoder quality, retrieval quality, or 5060 Ti performance.
