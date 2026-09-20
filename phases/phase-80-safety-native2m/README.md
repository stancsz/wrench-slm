# Phase 80: safety-native2M candidate

Status: `NATIVE_2M_DIRECT_INPUT_PASS_QUALITY_REPLAY_OPEN`

The safety-calibrated BF16 8E weights were copied by immutable hardlink into a
derived candidate with a 2,000,000-token `text_config.max_position_embeddings`
and a YaRN context configuration. The original safety weights were not
modified. FreeToken loaded all five shards, allocated a 4M runtime KV address
space, completed warmup, and served the endpoint.

Config-only receipt: `config-receipt.json`.

The full 220 historical fixture replay completed through the same verifier and
mechanical fast path:
`wrench-safety-native2m-220-guarded.json`.

- 220/220 requests completed
- 163/220 expected outcome matches
- 80/120 eligible exact accepts
- 0 prohibited accepts
- 137/220 mechanical fast-path requests
- 0 transport/runtime abstentions
- median latency: 45.341 ms
- p95 latency: 2,854.370 ms
- mean latency: 967.432 ms

The replay proves startup compatibility and that the worker behavior broadly
survives the derived 2M config, but it does not pass the quality gate. The
latest verifier adds a guard for the observed `patch without a hunk marker`
boundary. The fresh replay now confirms zero prohibited accepts, but eligible
exact acceptance remains 80/120 and this candidate cannot be considered a
MiniMax-parity or production-quality worker.

The reducer-bypassed direct 2M probe for this exact safety checkpoint then
completed through the native-attention probe profile. The endpoint returned
HTTP 200 with 1,999,912 actual model-side prompt tokens, no truncation, and
`native_context_pass=true` in 967,098.697 ms. The probe used the derived 2M
YaRN config, a 4M runtime KV allocation, and an 8K SWA serving window. This is
direct-input capacity evidence for the safety candidate, not a claim of full
2M global attention, retrieval quality, or fast serving. Receipt:
`native-2m-bf16-direct.json`.

After the direct probe, the mechanical router was tightened so a rigid local
health request with an omitted numeric value uses the verifier's bounded
defaults instead of spending a model call. Invalid hosts, paths, query strings,
fragments, and bounds still fail closed in the verifier. The refreshed 220-case
diagnostic moved to 173/220 outcome matches, 81/120 exact eligible accepts,
zero prohibited accepts, 157/220 mechanical fast-path requests, 8.203 ms
median latency, 5,057.505 ms p95, and 1,025.603 ms mean latency. The p95 is
higher because the fixture points at an unavailable health service and the
verifier waits for bounded connection timeouts. This is a real safety and
latency tradeoff, not a MiniMax workflow result. Receipt:
`wrench-safety-native2m-220-health-mechanical.json`.
