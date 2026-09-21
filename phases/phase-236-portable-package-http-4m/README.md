# Phase 236: portable package direct 4M intake

This phase verifies the downloaded package boundary, not the source harness.
The package's own `wrench_server.py` was started from
`D:/models/Wrench-Qwen3.6-8expert-BF16-hybrid-v93` and loaded the full BF16
Safetensors model before the probe was sent.

The direct OpenAI-compatible request used the package endpoint
`/v1/chat/completions` and the probe was invoked with `--target-tokens
4000000`. The fixture builder leaves a 300-token estimate margin so the
nominal 4M envelope does not cross the server's hard 4,000,000-token limit
because of the active-intent suffix. The server measured `3,999,963` raw
input tokens and returned HTTP 200.

Observed receipt facts:

- package-local endpoint, no external gateway;
- request size: `32,497,800` bytes;
- first-layer mechanical pruner/cherrypicker: `23.576 ms`;
- effective working context: `9` tokens for this latest-intent case;
- model calls: `0`;
- exact bounded `read_file` proposal and verifier pass;
- raw payload hash present in the context-gate receipt.

This is a direct model-local hybrid raw-intake milestone. It proves that a
copy-pasted package can receive a monster payload and reduce it before model
attention. It does not prove dense native 4M attention, learned generation
quality, retrieval recall across the full 220-case evaluation, or MiniMax
parity. The conditional dense-native target remains: if dense native is
enabled, the first model-side stage must compact the full input to a bounded
32K to 64K context before expensive attention.

Receipt: `receipt.json`.
