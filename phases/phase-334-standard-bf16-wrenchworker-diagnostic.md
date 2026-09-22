# Phase 334: Standard BF16 WrenchWorker diagnostic

Status: `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`.

The standard BF16 package was loaded through the package-local
`wrench_runtime.worker.WrenchWorker` in the isolated Transformers `5.17.0`
runtime with `WRENCH_MODEL_DEVICE=cuda`. The mechanical route was explicitly
disabled so this tested the embedded model path rather than the deterministic
toolbelt.

The model loaded on the RTX 5070 Ti in `12,858.085 ms`, then received a
bounded ambiguous proposal request with `max_tokens=64`. The worker performed
two model passes, including its bounded repair pass, but the final generated
text was not valid Wrench JSON:

```text
> Ċ 1 9 9 9 9 9 9 9 9 9 9 9 ...
```

The worker correctly failed closed with `model_output_invalid_json`.

## Decision

This confirms the standard BF16 package is a real HF load and generation
artifact, but its learned proposal lane is not a MiniMax-parity worker. The
production-shaped route remains the embedded mechanical path, which bypasses
this weak decoder for eligible mechanical work and retains the independent
verifier and fallback boundary.

This does not authorize a quality claim, learned routing, or production
enablement. Existing LoRA probes remain rejected when they introduce
prohibited accepts or unsafe malformed proposals.
