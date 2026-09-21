# Phase 245: compact v97 NVFP4 publication

The BF16 v97 package is about 7.9 GiB on Hugging Face. That is appropriate
for development and compatibility work, but too large for the normal copy and
try path. This phase publishes the same current Wrench runtime and context
gate over the compact NVFP4 W4A16 package.

Published package:

- Repository: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate`
- Revision: `1a43e77e44e25a09459c4d350d8bf7c4527c590b`
- Public HF dry-run: about 3.4 GiB, 2 Safetensors shards

Local validation on the development host:

- structural package validation: pass
- bounded mechanical smoke: pass
- direct model-local 4M probe: HTTP 200, `3,999,995` prompt tokens,
  `170.664 ms`, zero model calls

This is still an experimental compact package. The receipt does not claim
dense native decoder quality, MiniMax parity, or independent RTX 5060 Ti
performance.
