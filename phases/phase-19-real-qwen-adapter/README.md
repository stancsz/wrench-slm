# Phase 19: real Qwen through the local adapter

This phase exercises the Phase 15 adapter against the actual local FreeToken
server and the Qwen3.6-35B-A3B-NVFP4 FTW checkpoint. FreeToken loaded the
checkpoint with expert offload and served the configured model identity. Qwen
returned a strict JSON read proposal, the adapter validated the returned model,
and the Phase 9 verifier accepted the bounded read observation.

The server was stopped after the request. This proves one real local
model-to-adapter-to-verifier path. It does not establish proposal precision,
task-family success, throughput, pruning, or production readiness.
