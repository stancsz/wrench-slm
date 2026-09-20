# Phase 80: safety-native2M candidate

Status: `NATIVE_2M_STARTUP_PASS_QUALITY_REPLAY_OPEN`

The safety-calibrated BF16 8E weights were copied by immutable hardlink into a
derived candidate with a 2,000,000-token `text_config.max_position_embeddings`
and a YaRN context configuration. The original safety weights were not
modified. FreeToken loaded all five shards, allocated a 4M runtime KV address
space, completed warmup, and served the endpoint.

Config-only receipt: `config-receipt.json`.

The full 220 historical fixture replay completed through the same verifier and
mechanical fast path:
`wrench-safety-native2m-220.json`.

- 220/220 requests completed
- 160/220 expected outcome matches
- 80/120 eligible exact accepts
- 1 prohibited accept before the latest patch-format guard
- 137/220 mechanical fast-path requests
- median latency: 46.513 ms
- p95 latency: 10,033.084 ms

The replay proves startup compatibility and that the worker behavior broadly
survives the derived 2M config, but it does not close the native reducer-bypassed
2M or 4M direct-input receipt for this exact safety checkpoint. It also does
not pass the quality gate. The latest verifier adds a guard for the observed
`patch without a hunk marker` boundary; a fresh replay is required before this
candidate can be considered for packaging.
