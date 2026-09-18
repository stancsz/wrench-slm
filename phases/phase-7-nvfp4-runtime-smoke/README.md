# Phase 7: local NVFP4 runtime smoke

This phase tests the existing local NVFP4 package through the available
containerized CUDA path. It is a runtime diagnostic, not a quality or release
test.

The container reached vLLM 0.29.0, CUDA on the RTX 5070 Ti, the Qwen3.6 model
architecture, and ModelOpt FP8/NVFP4 checkpoint detection. Engine startup then
failed before weight loading because vLLM's V1 engine requested UVA, which is
not available in this Docker/WSL environment. No HTTP request or generated
token was produced. The stopped test container was removed after capture.
