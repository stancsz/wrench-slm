# Phase 257: v103 package-local 4M handoff

The current NVFP4 portable package was rerun after the Hugging Face model-card
refresh. A direct Ollama-shaped `/api/chat` payload estimated at `3,996,267`
raw tokens was accepted by the bundled model-local runtime and reduced to
`1,955` staged working tokens.

Receipt highlights:

- total elapsed: `238.769 ms`
- first-layer context-gate latency: `50.175 ms`
- server staging: `98.032 ms`
- configured working budget: `64,000` tokens
- raw payload hash bound: yes
- model-quality claim: none

The upstream is a local protocol stub. This is direct package intake,
MapReduce reduction, and handoff accounting evidence on the RTX 5070 Ti. It is
not dense-native 4M attention quality, retrieval quality, MiniMax parity,
independent RTX 5060 Ti evidence, or production authorization.
