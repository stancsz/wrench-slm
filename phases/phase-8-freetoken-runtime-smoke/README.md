# Phase 8: FreeToken FTW runtime smoke

This phase verifies the real local serving path for the existing Qwen3.6
NVFP4 package. The package uses FreeToken's `.ftw` checkpoint format, so the
default vLLM loader is not the applicable loader for this artifact.

FreeToken loaded the four-shard checkpoint, initialized the Qwen3.6 MoE
runtime on the RTX 5070 Ti with expert offload, completed CUDA-graph and
prefill warmup, and served the OpenAI-compatible API on `127.0.0.1:8000`.
The bounded request returned exactly `WRENCH_RUNTIME_OK` with a stop finish
reason. This proves checkpoint loading and one local generation path only. It
does not prove pruning, task quality, throughput, stability, or release
readiness.

The reproducible receipt is `runtime-smoke.json`. The server was started with
the local FreeToken Python environment and the options recorded in that
receipt; no external provider or large download was used.
