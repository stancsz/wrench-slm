# Phase 349: exact current-head package binding

Date: 2026-09-22

HEAD `8d9ea2c` was materialized as
`D:\models\_wrench-release-candidate-8d9ea2c` with immutable weight files
reused by hard link. Structural validation passed with two Safetensors shards,
4,000,000 configured positions, and the expected 3,881,244,016-parameter
package identity.

The package-local Ollama-shaped surface then passed version, tags, show,
small chat, and a `3,995,426`-token monster chat. The monster request
completed in `44.373 ms` at the Wrench response layer, with a `24.636 ms`
first-layer gate, `9` effective working tokens, a bound raw-payload SHA-256,
and zero model calls. RAM reserve passed before and after.

This is model-local hybrid intake and mechanical-worker evidence. It is not a
dense-native 4M attention, learned MiniMax parity, 5060Ti, or production
claim.
