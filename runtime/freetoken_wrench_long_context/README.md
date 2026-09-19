# Wrench FreeToken long-context overlay

This is an opt-in runtime overlay for the local FreeToken engine. It keeps the
complete request payload intact, retains selected Qwen3.5 full-attention layers
as global memory, and changes the remaining Qwen full-attention layers to a
bounded sliding-window KV pool.

Example environment:

```powershell
$env:PYTHONPATH = 'C:\Users\stanc\github\portfolio\wrench-slm\runtime\freetoken_wrench_long_context'
$env:WRENCH_LONG_CONTEXT_OVERLAY = '1'
$env:WRENCH_GLOBAL_FULL_LAYERS = '39'
$env:WRENCH_SWA_WINDOW = '65536'
```

This does not change the Safetensors weights. It is a serving architecture
experiment and must be followed by long-context distillation or fine-tuning
before quality is considered release-ready.

The design target is a native 4M request with memory roughly proportional to:

```text
global_full_layers * full_KV(input_length)
  + bounded_window_layers * full_KV(window)
  + linear-attention state
```

The endpoint must still report the complete model-side `prompt_tokens`. A
gateway, context ledger, AST, or retrieval preselector cannot substitute for
that evidence.

The local Wrench serving experiment also applies a deterministic map-reduce
before `TokenizeMsg`: raw context is accepted by the 4M-configured endpoint,
then reduced to a 64K effective working context with a 48K hot budget and a
16K reference-card budget. This is a runtime toolbelt, not a new learned layer
inside the Safetensors. It reports raw-input estimate, exact staged prompt
tokens, cold ingest, and hot selection separately. The integration receipt is
`phases/phase-70-mechanical-map-reduce/runtime-4m-64k.json`.
