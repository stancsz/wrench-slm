# Phase 335: Exact current-head NVFP4 native binding

Status: `PASS_FREETOKEN_MODEL_LOAD_AND_GENERATION`.

The exact current hybrid package
`D:\models\_wrench-release-candidate-bbc680f` was loaded by the bundled
FreeToken ModelOpt NVFP4 backend using the explicit Windows executable path.

## Evidence

- Full NVFP4 weight load: passed.
- Direct native model endpoint: HTTP `200`.
- Minimal native generation: passed, generated text starts with `{"`.
- Configured native KV capacity: `4,000,000` tokens.
- Startup plus minimal generation: `25,882.644 ms`.
- RAM free fraction before/ready/after: `54.959% / 48.351% / 48.305%`.
- VRAM free fraction before/ready/after: `93.075% / 50.893% / 93.504%`.
- Process cleanup returned VRAM use to about `752 MiB`.

This binds native load and generation to the same package identity as the
current 4M hybrid route and client tests. It does not claim dense-native 4M
quality or fast direct 2M/4M prefill. The supported practical path remains
raw 4M model-local intake followed by deterministic reduction to bounded model
work.

Evidence: `phase-335-current-head-freetoken-native.json` and its stdout/stderr
logs.
