# Phase 321: native backend resource-safe rerun

Phase 320 found that a Windows FreeToken parent could exit before its CUDA
worker children, leaving orphan workers behind. The exact orphan PIDs from that
run were cleaned up, and the verifier was changed to call `taskkill /T /F` on
the exact backend parent before waiting.

The rematerialized candidate was then tested again with the repaired verifier.

## Result

Status: `PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION`

- Candidate: `D:\models\_wrench-release-candidate-0be4751`
- Backend: FreeToken ModelOpt NVFP4
- Direct completion: `200 OK`
- 4M KV capacity: configured and logged
- Minimal generation: `{"`
- Load and generation elapsed time: `23871.1 ms`
- RAM free fraction: `49.2875%` before, `42.7503%` while ready, `42.7338%`
  after cleanup
- VRAM free fraction: `93.5043%` before, `50.9170%` while ready, `93.5411%`
  after cleanup
- No candidate worker processes remained after the verifier exited.

This is the stronger current-candidate native backend receipt. It proves
ModelOpt/NVFP4 loading, 4M capacity configuration, minimal generation, and
resource-safe cleanup. It does not prove dense-native 4M retrieval quality,
MiniMax parity, or independent RTX 5060 Ti verification.

Evidence:

- `phases/phase-321-current-head-freetoken-native-cleanup.json`
- `phases/phase-321-current-head-freetoken-native-cleanup.stderr.log`
