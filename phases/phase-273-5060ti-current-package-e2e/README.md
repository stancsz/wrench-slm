# Phase 273: RTX 5060 Ti current-package end-to-end receipts

Date: 2026-09-21. Host GPU: NVIDIA GeForce RTX 5060 Ti.

This phase ran against the already verified local NVFP4 Experimental Preview
package. No provider calls, commits, pushes, or repository mutations were made
by the receipts. The checkout was dirty, so `origin/main` was not pulled.

## Source and artifact identity

- Checkout commit: `bcf80d93695fa135e256595a7f545d2cad8d0099`
- Remote `origin/main`: `08daf097c8ac0d87144d49e6bf0aa36722c1138d` (five commits ahead; not synced because checkout was dirty)
- Package: `C:\Users\stanc\models\wrench-5060-preflight-20260921\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-Experimental-Preview`
- Hugging Face revision: `966a1720d84b330d90b6ad38f22e883e749448f3`
- Preflight source commit: `6d25fc8dfa21e53c8593d4d09df7ba7f6b74e4e1`
- Shard 1 SHA-256: `DE471EA7CE455A027232F33A59AC0B051739DAF9CDFFD4BD5CC6E220D2E8E42E`
- Shard 2 SHA-256: `8CECB339791DEDBE1B4926B351003F1723670F8442AB670148D3B533D6FFF2F7`

## Receipts

1. `ollama-api-chat-4m-receipt.json` — `PASS_OLLAMA_API_CHAT_4M`. The current package accepted the requested direct model-local `/api/chat` intake: nominal 4,000,000 tokens, raw estimate recorded by the package, 31,997,963 raw characters, raw payload hash bound, embedded mechanical backend, zero model calls, HTTP 200, and 495.980 ms end-to-end.
2. `model-local-4m-receipt.json` — supplemental OpenAI-compatible `/v1/chat/completions` receipt: nominal 4,000,000 tokens, raw estimate 3,999,995, 9 effective working tokens, 64,000-token working budget, zero model calls, HTTP 200, and 439.327 ms end-to-end.
3. `client-smoke/dsh-receipt.json` — real installed DSh headless client completed a read-only request through an isolated local overlay with exit code 0. The installed client reported `# Wrench SLM`.
4. `client-smoke/opencode-failure-receipt.json` — OpenCode smoke is precisely blocked: the CLI is absent from PATH and the downloaded package does not bundle the OpenCode/DSh overlay files. No installation was attempted.
5. `replay-220/evaluation.json` — all 220 canonical `evals/wrench-expanded-v1/cases.jsonl` traces replayed through the current package-local HTTP endpoint with the client shortcut disabled. The run is `QUALITY_GATE_OPEN`: zero prohibited accepts, zero unexpected mutations, 100% verifier success, 100% net frontier-token savings, 81.8396% Wrench weighted final success, and 51.8407% weighted mechanical frontier-token coverage. The 90% coverage gate remains open; this is diagnostic evidence, not a quality or production claim.
6. `replay-220/trace-manifest.json` — cases SHA-256 `BBEE2BC8754498A4A48A87625921E21467BACBD135545B86DFB78ED7C82C3CB9`; trace-set SHA-256 `FC95569527CC54682FC8B07BD4DE41C1E292FB0A3942D24F7CA3B402C33362C7`.
7. `resource-snapshot.json` — RAM and VRAM free fractions remained above the 10% reserve policy before and after the run.

The working tree remains intentionally dirty with the user-owned changes and
the new phase evidence; nothing was committed or pushed.
