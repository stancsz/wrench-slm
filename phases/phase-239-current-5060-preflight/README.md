# Phase 239: current-source 5060 Ti preflight

This job verifies the current Wrench source commit `1674ce0088e4956e17087eab7cf36bb672ab3a5a` against the pinned BF16 artifact commit `e0ebd6f3762e30a118ade6bc47e01fc65d8e3eea` on the independent RTX 5060 Ti worker.

It is an integrity and runtime preflight only. It does not establish MiniMax parity, 4M dense-native retrieval quality, production latency, or release authorization.

The current-host deterministic stress probe also exercised 4,484,713 raw
token-equivalent input. It reduced the payload to 58,539 model-prefill tokens
with a 48K hot budget and 12K reference-card budget. Cold index ingestion was
137.134 ms and selection was 40.744 ms. This confirms the bounded first-layer
shape and exposes the cold versus hot latency distinction. It is not a 5060 Ti
result and it is not a dense-attention quality claim.
