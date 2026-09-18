# Phase 24: Provisional 8-Expert Structural Candidate

Status: PASS for structural slicing and CUDA load/forward smoke only.

`tools/prune_qwen_experts.py` streamed the verified BF16 source into
`D:\models\Wrench-Qwen3.6-8expert-BF16`, retaining expert indices 0 through 7
in every routed expert bank and the matching router rows. The source was not
modified.

Evidence:

- `prune-receipt.json` records 82 sliced expert tensors plus 41 router tensors
  and marks the result `EXPERIMENTAL_UNCALIBRATED`.
- `checkpoint-facts.json` records the new 8-expert configuration and an
  unquantized safetensors checkpoint with 9 shards.
- `post-prune-size.json` confirms the structural estimate.
- `runtime-smoke.json` loads the candidate with Transformers 5.16.1 and
  PyTorch 2.11.0+cu130 on `cuda:0`. It reports 3,881,244,016 actual model
  parameters and completes an 8-token deterministic generation.

The generated text is not a quality pass. This candidate uses provisional
indices, not router-profiled Wrench experts, and no calibration or held-out
evaluation has been performed. The next phase must profile routing and replace
the provisional selection before any quantized artifact is considered a Wrench
candidate.
