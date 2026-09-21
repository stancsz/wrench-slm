# Phase 254: v102 package-local 4M handoff

The bundled package accepted a direct Ollama-shaped `/api/chat` request at the
model-local server and staged it through the deterministic MapReduce context
gate before a local protocol-stub upstream. This is hybrid raw intake and
handoff evidence, not dense-native attention quality.

## Receipt

- Package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v102-ollama-cli`
- Requested logical context: `4,000,000` tokens
- Raw estimated tokens: `3,996,267`
- Request bytes: `35,163,527`
- Effective model prefill: `1,955` tokens
- Compression ratio: `0.000489`
- MapReduce context-gate latency: `31.663 ms`
- Server staging latency: `84.072 ms`
- End-to-end request latency: `238.189 ms`
- Model calls: `1` to the local protocol stub
- Raw payload hash: `e0504b9d859621f9bad62045a0c8def6a79656eaac843f9849a8518461e13b84`

The receipt is hash-bound and records the selected reference card, omitted
spans, working-context budget, and cache state. The upstream is a deterministic
test stub, so this does not prove native dense 4M decoder quality, retrieval
quality on real tasks, or production enablement.

Evidence: `phase-254-v102-package-4m-handoff.json`.
