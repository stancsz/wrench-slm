# Phase 320: current-head FreeToken ModelOpt native backend

The standard Transformers full-weight probe in phase 319 failed because the
candidate stores ModelOpt NVFP4 packed tensors. This phase tested the backend
that owns that format instead of treating the packed tensors as dense BF16.

## Result

Status: `PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION`

- The current candidate's two safetensor shards loaded through the FreeToken
  ModelOpt/NVFP4 path.
- The direct model endpoint reached `200 OK` for a real chat completion.
- The backend configured a `4,000,000` token KV capacity and logged
  `Allocating 4000000 tokens for KV cache`.
- The minimal generation returned `{"` and completed in `26828.449 ms`.
- GPU free fraction remained above the 10% reserve, with approximately 50.9%
  free after initialization. The first run's receipt did not yet include the
  Windows RAM probe, so the verifier was then upgraded to use
  `GlobalMemoryStatusEx` for both RAM and VRAM checks.
- `dense_native_quality_verified` remains `false`. This is a backend load,
  capacity, and minimal generation pass, not a 4M retrieval-quality pass.

The new `verify_freetoken_backend.py` is now bundled into future portable
packages, and the materializer and structural validator require it. The
package documentation now states the honest boundary: Transformers verifies
metadata and tokenizer, while FreeToken ModelOpt is required for these packed
weights.

Evidence:

- `phases/phase-320-current-head-freetoken-native.json`
- `phases/phase-320-current-head-freetoken-native.stderr.log`
- `phases/phase-320-current-head-package-validation.json`
- `phases/phase-320-current-head-package-smoke.json`
- `phases/phase-320-current-head-weight-equivalence.json`
