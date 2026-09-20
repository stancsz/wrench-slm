# Phase 126: v42 text-only portable package

This phase verifies the next portable package shape after fixing two release
path issues: text-only metadata no longer declares a vision tower, and the
embedded mechanical route imports from the files that are actually bundled in
the package.

## Verified

- v42 config SHA256 is `A00F1694B8B49380D448ABAA06C25D280D5B794444230E34689001AB195F0422`.
- The config has no `vision_config`, image-token, video-token, or vision-boundary
  fields.
- FreeToken loaded the v42 NVFP4 package, allocated the configured 4,000,000
  token KV capacity, and completed a short model request.
- The embedded route handled all 220 historical prompts as mechanical fast
  paths with zero model calls and zero prohibited accepts. The receipt reports
  200/220 outcome matches and 82/120 exact eligible proposals because the 20
  accepted patch-draft prompts in this historical fixture omit their actual
  diff. The fail-closed `patch_content_missing` result is intentional.
- An isolated Ollama `0.34.2` MLX runtime loaded the corresponding no-vision
  manifest and reported a 4,000,000-token context length. A short completion
  reached HTTP 200 after a local cuDNN path workaround.

## Boundary

The Ollama completion used an isolated patched MLX DLL because the official
Windows bundle still points at a machine-level cuDNN directory. This proves a
portable runtime repair direction, not a stock Ollama one-click release. The
public Hugging Face package remains experimental until the exact runtime
dependency is packaged without patching third-party binaries.
