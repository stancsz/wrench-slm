# Wrench FreeToken long-context overlay

This is an opt-in runtime overlay for the local FreeToken engine. It keeps the
complete request payload intact and changes the Qwen3.5 full-attention layers
to a bounded sliding-window KV pool. A selected global-full policy is still
available, but the 4M capacity profile uses `none`: the pool keeps a zero-layer
full-token bookkeeping slab and stores only the bounded SWA window on GPU.

Example environment:

```powershell
$env:PYTHONPATH = 'C:\Users\stanc\github\portfolio\wrench-slm\runtime\freetoken_wrench_long_context'
$env:WRENCH_LONG_CONTEXT_OVERLAY = '1'
$env:WRENCH_GLOBAL_FULL_LAYERS = 'none'
$env:WRENCH_SWA_WINDOW = '8192'
$env:WRENCH_SWA_POOL_TOKENS = '8192'
$env:WRENCH_ROPE_MAX_POSITION = '4000000'
```

For an opt-in model-side speed experiment, set
`WRENCH_HISTORY_SKIP_MLP_BEFORE` to an absolute token position. Prefill chunks
ending before that position update the linear/SWA state but skip the expensive
MoE MLP; the recent suffix remains on the normal full path. The complete raw
request still reaches the model endpoint. This is a diagnostic fast-history
policy and has no quality or release claim until matched retrieval and worker
tests pass.

For a more aggressive reference-only history experiment, set
`WRENCH_HISTORY_SKIP_LAYERS_BEFORE` to an absolute token position. Prefill
chunks ending before that position preserve the residual stream but skip both
attention and MLP; the recent suffix remains on the normal full path. The raw
payload still reaches the model endpoint, but historical model integration is
reduced by design. This is diagnostic only and must pass retrieval and worker
quality checks before it can be considered for a default profile.

When using that policy, `WRENCH_HISTORY_CONTROL_PREFIX_TOKENS` can reserve the
leading system/developer/authority prefix. Chunks before that prefix stay on
the full path; only the middle historical region is eligible for skipping.
This should be set for quality experiments so the newest intent retains its
control contract.

`WRENCH_HISTORY_CONTROL_SUFFIX=1` enables the corresponding deterministic
recent-control suffix in the serving hook. It repeats only a bounded tail of
the newest user message, not the full payload, so the model-side fast path can
recover the active intent and output contract after skipping stale middle
chunks. Tune the tail with `WRENCH_HISTORY_CONTROL_SUFFIX_CHARS`.

This does not change the Safetensors weights. It is a serving architecture
experiment and must be followed by long-context distillation or fine-tuning
before quality is considered release-ready.

The capacity design target is a native 4M request with memory roughly
proportional to:

```text
  global_full_layers * full_KV(input_length)
  + bounded_window_layers * full_KV(window)
  + linear-attention state
```

With `WRENCH_GLOBAL_FULL_LAYERS=none`, the first term is zero. This makes the
4M address space cheap, but it is not equivalent to full 4M attention. Old
tokens are reference-addressable through the runtime policy, while the model's
attention computation is bounded to the recent SWA window. `WRENCH_ROPE_MAX_POSITION`
extends the runtime rotary table for a capacity probe. It does not add 4M
training data or establish long-context retrieval quality.

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
