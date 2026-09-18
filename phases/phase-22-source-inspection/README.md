# Phase 22: Official Unquantized Source Acquired and Validated

Status: PASS for source acquisition and metadata eligibility only.

The explicitly authorized acquisition command downloaded the official
`Qwen/Qwen3.6-35B-A3B` snapshot at revision
`995ad96eacd98c81ed38be0c5b274b04031597b0` to
`D:\models\Qwen3.6-35B-A3B`.

Evidence:

- `checkpoint-facts.json` records 38 local files, the Apache-2.0 license, the
  `Qwen3_5MoeForConditionalGeneration` architecture, 40 layers, 256 routed
  experts, top-8 routing, 2,048 hidden size, and zero quantized layers.
- `pruning-source-validation.json` reports `eligible: true`, 26 safetensors
  shards, 1,045 mapped tensors, no missing shards, and no rejection reasons.
- The official index total is exactly 71,903,645,408 bytes. The acquisition
  command returned `status: PASS` after fetching all 38 requested files.

This phase does not claim that pruning, router profiling, model loading,
calibration, quality, throughput, or production value has been proven. The
checkpoint remains outside Git and is not modified. Structural pruning is now
permitted to proceed to an architecture-aware profiling design, subject to the
approved task portfolio and remaining evidence gates.
