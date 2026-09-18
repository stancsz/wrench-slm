# Phase 1: checkpoint facts

This phase establishes what is actually available locally before any training,
pruning, or serving decision.

The current local artifact is the NVIDIA ModelOpt NVFP4 package derived from
`Qwen/Qwen3.6-35B-A3B`. Its metadata reports a hybrid multimodal model with a
40-layer text configuration, 256 routed experts, top-8 routing, 2,048 hidden
size, and a 248,320-token vocabulary. The package uses FP8 and W4A16_NVFP4
quantized modules.

The receipt intentionally does not claim that the package can be structurally
pruned. Packed quantized weights are an inference artifact. A verified
unquantized checkpoint with matching architecture and license is required for
tensor slicing and router restructuring.

Generate or refresh the receipt with:

```powershell
py -3 tools/inspect_qwen_checkpoint.py `
  D:\Users\stanc\.freetoken\models\Qwen3.6-35B-A3B-NVFP4 `
  --output phases/phase-1-checkpoint-facts/checkpoint-facts.json
```

Add `--hash-weights` when a full 21 GB weight identity receipt is required.
