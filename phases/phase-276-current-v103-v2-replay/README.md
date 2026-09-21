# Phase 276: current v103 package, full v2 replay

Date: 2026-09-21

## Result

The current local v103 portable package was replayed against the complete
`evals/wrench-expanded-v2/cases.jsonl` suite. This was a 220-row run, not the
28-case smoke subset. The teacher capture was the same-input v2 stream at
`D:\models\wrench-teacher-traces-v2-stream.json`.

The package replay produced `PASS_MECHANICAL_WORKER` for the diagnostic
contract:

| Metric | Result |
| --- | ---: |
| Total traces | 220 |
| Eligible traces | 120 |
| Weighted mechanical frontier-token coverage | 100% |
| Net frontier-token savings | 100% |
| Wrench weighted final success | 100% |
| Wrench verifier success | 100% |
| Wrench prohibited accepts | 0 |
| Unexpected mutations | 0 |
| Wrench model calls | 0 |
| Wrench local tokens | 24,141 |
| Wrench p50 latency | 211.745 ms |
| Wrench p95 latency | 332.823 ms |

The replay receipt is external because model artifacts and large historical
receipts remain outside the repository:

- `C:\Users\stanc\AppData\Local\Temp\wrench-current-v103-package-replay-v2-20260921-9499fd8572a54c6e8b673da2b07f456a\evaluation.json`
- SHA-256: `0B2D65D3CF537FC4E9F66F60D8D8CD2938663DD56546E673D3AD42485978AF9B`

The exact v103 package also passed structural validation with two Safetensors
shards, `config_max_position_embeddings=4000000`, no structural errors, and
`native_attention_claim=false`.

## Scope and limits

This is the strongest current 220-case package diagnostic, but it is not a
production authorization. The suite remains draft pending human approval. The
teacher capture contains two prohibited accepts, so it is not a clean safety
baseline. Wrench itself recorded zero prohibited accepts. The replay also does
not prove learned MiniMax parity, native dense 4M decoder quality, or
independent RTX 5060 Ti performance.

The result demonstrates that the current value comes from the bundled
deterministic mechanical route, verifier, and bounded fallback boundary. The
model-only head-only LoRA control remains a failure baseline from phase 275.
