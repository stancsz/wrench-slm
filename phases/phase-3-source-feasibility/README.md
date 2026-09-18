# Phase 3: unquantized source feasibility

The official Qwen source is identified, but its unquantized weights are not
present locally. The source metadata receipt records the exact revision,
license, architecture, shard count, and total byte size needed before pruning.

The local NVIDIA NVFP4 package remains an inference artifact and must not be
used as a stand-in for tensor slicing. Downloading the unquantized source is a
separate 71.9 GB acquisition decision. Once it is available, run the Phase 1
inspector against that directory and compare its configuration and shard index
to this receipt before any pruning code is allowed to write output.
