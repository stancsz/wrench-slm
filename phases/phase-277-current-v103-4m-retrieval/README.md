# Phase 277: current v103 direct 4M intake and retrieval

Date: 2026-09-21

## Direct package intake

The current v103 NVFP4 portable package accepted a direct model-local worker
request containing a nominal 4,000,000-token payload. The request contained
35,199,491 raw characters and completed in 29.827 ms. The internal first-layer
context gate took 29.145 ms, bound the raw payload SHA-256, and selected the
latest intent plus an exact old-reference span. The route returned an embedded
mechanical proposal with zero model calls.

The gate receipt reported:

- `raw_context_limit_tokens`: 4,000,000
- `raw_input_tokens`: 4,000,642
- `effective_working_context_tokens`: 19
- `working_context_budget_tokens`: 64,000
- `selected_hot_spans`: 1
- `selected_reference_spans`: 1
- `omitted_reference_spans`: 0
- `gate_latency_ms`: 29.145
- `native_input_claim`: `false`

The `native_input_claim=false` field is intentional. This is direct package
intake and bounded internal MapReduce/pruner/cherrypicker behavior. It is not a
dense full-attention 4M decoder claim.

Receipt:

- `C:\Users\stanc\AppData\Local\Temp\wrench-v103-4m-route-20260921-115be613e3934433828a328c6fe06c14.json`
- SHA-256: `9A696A1E7894A1B4373CBAE6161B320C40EF9529448AABF75535B90EBE5F0AE9`

## Retrieval quality

The package retrieval probe placed unique old-reference needles at 1%, 50%,
and 99% offsets in both 2M and 4M payloads. All six cases passed. Each case
preserved the current intent, recovered the exact old reference, bound the raw
payload hash, and used zero model calls.

Observed latencies were 16.442, 17.988, 21.478, 28.056, 32.299, and 40.012
ms for the six cases. The receipt status was
`PASS_PACKAGE_RETRIEVAL_2M_4M`.

Receipt:

- `C:\Users\stanc\AppData\Local\Temp\wrench-v103-retrieval-20260921-0d73d5188ec842ffa410423a00918246.json`
- SHA-256: `9F617EE8B61854F3A3E4940137C01846EF03718FAA4F5C8EA3B6E968FFDB715A`

This is a package-local retrieval diagnostic. It does not prove dense-native
attention quality, learned MiniMax parity, or independent RTX 5060 Ti
performance.
