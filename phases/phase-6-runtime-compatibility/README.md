# Phase 6: runtime compatibility

The current global Python environment has Transformers 4.57.1, which does not
recognize the Qwen3.6 `qwen3_5_moe` architecture. The compatibility check
therefore returns `NOT_READY` without loading weights. An isolated test with
Transformers 5.17.0 can parse the metadata, but that test environment has no
PyTorch and is therefore `METADATA_READY_ONLY`, not inference-ready.

Use a project-specific environment and the requirements in
`requirements/runtime.txt`, then rerun:

```powershell
py -3 tools/check_qwen_runtime.py `
  D:\Users\stanc\.freetoken\models\Qwen3.6-35B-A3B-NVFP4 `
  --output phases/phase-6-runtime-compatibility/runtime-check.json
```

This phase is complete only when the runtime exposes the expected architecture
and the unquantized source has independently passed the Phase 3 identity check.

An isolated environment using Transformers 5.17.0 with the existing system
PyTorch now reports `READY` for architecture and backend availability. This is
still a metadata/runtime prerequisite check only; no model weights were loaded
and no GPU inference claim is made.
