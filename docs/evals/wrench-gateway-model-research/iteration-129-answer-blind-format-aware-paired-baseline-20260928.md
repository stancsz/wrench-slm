# Iteration 129: answer-blind paired baseline with format-aware verification

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER129`  
Status: **complete; E0 passes 3/3 on this tiny synthetic set; 94.8236% local-model input-token reduction**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired result

This reruns Iteration 128's same three answer-blind synthetic lookups at E0
context budget 64. The verifier accepts whitespace around comma-separated
integers, compares their parsed ordered integer pairs, and checks the function
identifier after trimming whitespace or backticks. Both arms use the same
`answer_blind_lookup_format_v2` verifier.

| Task | Full-context answer / result | E0 answer / result | Full / E0 model input tokens |
|---|---|---|---:|
| Retry policy | `250, 4000` / fail | `3, 250` / pass | 8,738 / 557 |
| Session lifetime | `1800, 300` / pass | `1800,300` / pass | 8,731 / 445 |
| Retry function | `calculate_retry_delay` / pass | `calculate_retry_delay` / pass | 8,727 / 354 |
| **Total** | **2/3** | **3/3** | **26,196 / 1,356** |

The paired local-model input-token reduction is **94.823637%**. Including
generated output, totals are 26,226 versus 1,382 tokens, a **94.730420%**
reduction. The separate target-tokenizer prompt totals are 19,297 versus
1,627, a **91.568638%** reduction. Compared with Iteration 128's byte-exact
check, the format-aware verifier correctly counts the space-containing numeric
answers as valid; the genuinely wrong full-context retry answer remains a
failure.

These are three synthetic repository lookups, not an estimate of task
completion, a confidence-bound claim, or frontier-token savings. No frontier
request occurred, so frontier-token savings remains null. No Wrench LoRA was
loaded. The run does not establish the 95/5 split, success retention, all-in
cost, or all-day engineering.

## Exact identity and runtime

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter.
- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `4b715627b0cb566b06b889cb768f863702b0b7f91b2c83a78fdb10eff5242c27`.
- Receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter129.json`,
  6,102 bytes, SHA-256
  `7bd77156a386102005b41f687b2b519e31998db2ee5ebda91d3948ec8c4988c0`.
- Runtime: Python 3.13.15, PyTorch 2.14.0+cu132, Transformers 5.17.0,
  CUDA 13.2, NVIDIA GeForce RTX 5060 Ti.
- Model load: 4.509 s; total: 42.277 s. Peak CUDA allocated/reserved:
  2,678,108,160 / 2,894,069,760 bytes.
- Minimum sampled free RAM: **14.0391%**; minimum free VRAM: **75.4031%**.
  The runtime reserve held. `causal-conv1d` and `flash-linear-attention` were
  unavailable, so Transformers used slower reference implementations.
- Storage was `WITHIN_LIMIT` at 15,434,097,470 actual bytes plus
  206,103,000 bytes of active reservations, including the Docker WSL model
  volume and hourly automation directory. C: had 139,983,740,928 bytes free.
  No provider call or spend occurred.

## Next action

Continue the answer-blind context-budget sweep below 64 with the same verifier
and exact task set, retaining every abstention and failure. Choose the smallest
budget that preserves the declared evidence and verified answers on a broader
predeclared workload, not merely this three-case fixture. Then resume the
representative code-task MVP and candidate-size comparisons. Refresh the
hash-bound Fit-03 review before any fit; this iteration did not train or open
held-out data.
