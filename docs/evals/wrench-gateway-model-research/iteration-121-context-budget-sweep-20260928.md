# Iteration 121: verified E0 context-budget sweep

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DEMO-BUDGET-SWEEP-ITER121`  
Status: **3/3 exact synthetic lookup answers passed at the smallest tested passing context budget; product targets remain unproven**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired result

Using the same three authored synthetic lookup tasks, fixture, target tokenizer,
Qwen3.5-0.8B base checkpoint, and exact-answer verifier as Iteration 119, the
adaptive run tested context budget 48, then 64. At 48, E0 kept the required
quotes and the model answered two cases correctly, but preparation rejected
`retry-function` because required evidence was omitted. At 64, all three
preparations retained their required quotes and all three model answers passed.
The search stops at the first passing budget; 64 is the smallest **tested**
passing value, not a proven global minimum.

| Case at budget 64 | Target baseline tokens | Wrench target tokens | Input reduction | Local input/output | Exact verifier |
|---|---:|---:|---:|---:|---|
| Retry policy | 6,448 | 631 | 90.2140% | 565 / 8 | Pass, `3,250` |
| Session lifetime | 6,450 | 549 | 91.4884% | 460 / 11 | Pass, `1800,300` |
| Retry function | 6,439 | 493 | 92.3435% | 367 / 6 | Pass, `calculate_retry_delay` |
| **Ratio of sums / total** | **19,337** | **1,673** | **91.348193%** | **1,392 / 25** | **3 / 3; all 7 quotes visible** |

Iteration 119 used the same cases at budget 160 and measured 19,337 to 2,135
target input tokens, or 88.958991% reduction. Budget 64 therefore lowered the
prepared input by 462 tokens (21.64% relative to Iteration 119's prepared
input), while retaining all three exact answers in this fixture. This is a
useful within-fixture improvement, not a frontier-token or task-success
retention result. At budget 48, the 90.967592% ratio is over the two cases
prepared before E0 rejected the third; it is incomplete and must not be
compared as an all-case score.

## Runtime, resources, and identity

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16 CUDA, no adapter.
- Runtime: Python 3.13.15, PyTorch `2.14.0+cu132`, CUDA 13.2,
  Transformers 5.17.0, NVIDIA RTX 5060 Ti.
- Target-tokenizer runtime: Transformers 5.17.0, tokenizers 0.23.2,
  huggingface-hub 1.33.0.
- Fixture SHA-256: `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Model inventory SHA-256:
  `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`.
- Snapshot-verification receipt SHA-256:
  `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6`.
- Runner SHA-256:
  `d0a694e0cf54c3367c2d6a67ce84820cd19f3021a083b30cbfef4ebcade9227e`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\budget-sweep-iter121.json`,
  6,072 bytes, SHA-256
  `db7ec618e9c5612fc1df747768089a8f1ffa0a5fbbf61f77a30dbc7e2cd338aa`.
- Model load: 5.4685 s; total: 31.2702 s; three generations: 8.8738 s.
- Peak CUDA allocated/reserved: 1,633,046,528 / 1,654,652,928 bytes.
- In-process sampled minimum free RAM: 14.167%; minimum free VRAM: 82.576%;
  21 resource samples, no monitor error. The 10% runtime floor held. The
  separate Fit-03 start condition of 25% free RAM was not met.
- Admission reserved 100,000,000 bytes, included the Docker WSL model volume
  and hourly automation directory, and found C: had over 140 GB free. Actual
  storage remained within the 50 GB aggregate ceiling.

Transformers used reference fallback kernels because `causal_conv1d` and
`flash-linear-attention` are absent from the admitted local environment. No
packages were installed, no network was used, no provider call or spend
occurred, and the held-out split was not opened.

## Preserved setup failure and limits

The first attempt, `WRENCH-DEMO-BUDGET-SWEEP-ITER120`, failed before model load:
the selected Python environment lacked `accelerate`, required by
`device_map="cuda"`. It produced no receipt or generation. Its process exited,
the output absence was checked, the reservation was released, and the retry
used the already-installed LoRA-screen addons path under a new job ID. No
dependency was installed.

The successful run is three synthetic lookups over one fixture with 240
repetitive log lines. It does not measure patch authoring, uncompressed-model
success retention, a trained Wrench LoRA, full-lifecycle frontier tokens,
frontier-routing rate, all-in cost, or sustained engineering. The 91.348193%
value is target-tokenizer prompt-input reduction only. Keep the 95/5, success,
95%-frontier-token, 95%-cost, and all-day engineering gates unchanged.

Next compare the same frozen cases against deterministic retrieval, then pair
that result with the best verified model budget. Revisit candidate fitting only
after the current goal hash is reviewed and RAM is at least 25% free at
admission. Keep SubRoute `:4000` unchanged and provider calls closed without an
enforced numeric campaign cap.
