# Phase 279: current v103 real generation gap

Date: 2026-09-21

## 4M model-local generation

The current v103 NVFP4 package was started through its bundled FreeToken
runtime and wrapper endpoint on the RTX 5070 Ti. An ambiguous request was sent
directly to the package-local OpenAI-compatible endpoint with a nominal
4,000,000-token payload.

The runtime genuinely accepted and reduced the payload:

- HTTP status: 200
- raw payload tokens: 3,996,317
- staged model-prefill tokens: 1,991
- first-layer gate latency: 159.6 ms
- total elapsed: 2,017.855 ms
- model calls: 1
- backend: `native-upstream-verified`
- VRAM remained above the 10% host reserve during the run

The generated assistant content was malformed:

```text
{"n}{"1}{"1}{"1}{"1}
```

The receipt status is `PASS_REAL_WORKER_HTTP_4M_INTAKE_AND_GENERATION`, which
only means that raw model-local intake, bounded staging, and one real decoder
call completed. It is not a proposal-quality pass. The receipt explicitly has
`native_attention_claim=false` and `quality_claim=false`.

Receipt SHA-256:

- `C:\Users\stanc\AppData\Local\Temp\wrench-v103-real-model-4m-20260921-d18562600ac6467080e593892d404f13.json`
- `CB88DD3035AF006E883DEA4441F924F2D282D3EC9E2A31F5FAAEF4770E3A6DA1`

## 64K control

The same runtime and ambiguous generation probe were repeated with a 65,536
token payload. It again made one real model call and returned HTTP 200, but the
assistant content was still malformed:

```text
{"n}{"n}
```

The 64K run measured 61,434 raw tokens, 1,991 staged model-prefill tokens,
3.488 ms gate latency, and 1,024.030 ms total elapsed. This control shows that
the malformed proposal is not caused only by 4M context pressure. It is a
current NVFP4 native decoder or protocol-quality gap.

Receipt SHA-256:

- `C:\Users\stanc\AppData\Local\Temp\wrench-v103-real-model-64k-20260921-5a773371069c4568aebf6cd208352b91.json`
- `439D7FC19E26FB788160A920E93849E09B5D5E34BC97DC26EF49436F5A562315`

Both services were stopped after the probes. VRAM returned to 15,435 MiB
free, and both ports were left without listeners.

## Product implication

The deterministic embedded mechanical route and bounded retrieval path remain
the practical fast worker lane. The learned/native decoder lane must remain
fail-closed and cannot be marketed as MiniMax-level proposal generation until
the malformed-output path is fixed and re-evaluated on the full suite.
