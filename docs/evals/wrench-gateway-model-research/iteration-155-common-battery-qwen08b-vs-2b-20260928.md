# Iteration 155: common local battery, Qwen3.5-0.8B vs 2B

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-COMMON-BATTERY-QWEN035-08B-ITER155-20260928`  
Status: **On this fixed three-case mechanical lookup battery, 2B passed two cases the 0.8B control passed, including the retry-policy case; the 0.8B failed that case even with full context. Neither model passed the aggressive TOML-table arm on that case.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Paired method

This run used the same Iteration 153 fixture, three answer-blind requests,
related-source manifest, deterministic verifier, compact prompt mode, and
runner as Iteration 154. It evaluated Qwen3.5-0.8B against the Iteration 154
Qwen3.5-2B run. Both were BF16 base models without an adapter. The response
oracle, source fixture, and request hashes were held fixed. The cases are
experimenter-authored, previously exercised development examples; they are
not a fresh holdout or a representative coding workload.

## Results

| Model | Full fixture | E0 all paths | E0 related paths | E0 related TOML tables |
|---|---:|---:|---:|---:|
| Qwen3.5-0.8B | 2/3 | 2/3 | 2/3 | 2/3 |
| Qwen3.5-2B | 3/3 | 3/3 | 3/3 | 2/3 |

Both models passed `session-lifetime` and `retry-function`. On
`retry-policy`, the 0.8B returned `250, 4000` across the full, E0, and related
path arms; the expected answer is `3,250`. The 2B returned `3,250` on those
same arms. Both returned an incorrect retry count in the table-only arm: the
0.8B returned `2, 250`, and the 2B returned `2,250`. Thus the 2B has a clear
paired advantage over 0.8B on this one harder case when the related
implementation evidence remains available. The table-only regression is
repeatable on this known example and remains rejected.

All Wrench context arms had the same target-tokenizer inputs across models
because context preparation is deterministic. For Qwen3.5-2B the related-path
arm used 1,096 / 19,297 target tokens (94.320361% fewer); its table arm used
977 / 19,297 (94.937037% fewer) but failed the retry case. Qwen3.5-0.8B does
not improve token reduction simply by being smaller. The local model's own
input/output token counts are not Frontier usage or Frontier savings.

## Exact identities and machine result

| Identity | Qwen3.5-0.8B | Qwen3.5-2B |
|---|---|---|
| Revision | `2fc06364715b967f1860aea9cf38778875588b17` | `15852e8c16360a2fea060d615a32b45270f8a8fc` |
| Inventory SHA-256 | `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519` | `23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5` |
| Snapshot-receipt SHA-256 | `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6` | `59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014` |

Both used Python 3.13.15, PyTorch 2.14.0+cu132, Transformers 5.17.0,
CUDA 13.2, and an NVIDIA RTX 5060 Ti with 16,311 MiB VRAM. The 0.8B run
loaded in 6.1589 s, completed in 62.7111 s, and kept minimum sampled free
RAM/VRAM at 14.4447% / 75.2560%. The paired 2B run completed in 63.5549 s
with minimum sampled free RAM/VRAM at 11.7538% / 61.4187%. Both stayed above
the general 10% run floor. The 2B RAM margin was narrow; neither run proves
long-duration engineering or LoRA-training fit.

| Receipt | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-table-span-iter155-qwen35-08b.json` | 30,156 | `00CDAC14325E3A8BE9BBC5A32D3DA984CF55E95F8BA0D3119A60FE2815F5B397` |

There were zero Frontier calls and $0 provider spend. The frontier-token,
routing-rate, and all-in-cost metrics are undefined. No credentials, sealed
data, SubRoute change, or live provider traffic was used.

## Candidate decision

For a **bounded Wrench context controller**, the direct same-battery result
increases support for Qwen3.5-2B over 0.8B: 2B retained verified success on
the retry case where 0.8B failed even with the entire source fixture. This is
still low-confidence experiment-prioritization evidence from one fixed,
three-case synthetic set. It does not prove that 2B is an overall product
winner, and no Wrench LoRA has been evaluated.

For an **all-day coding worker**, this battery has no reach: it contains no
code edits, execution, tests, recovery, interruptions, repository switching,
or sustained sessions. The model-size decision across the wider 0.5B-12B
research band remains provisional. 4B/9B coding benchmarks and the 12B
research upper bound remain external, non-paired evidence; they do not
establish on-host fit or Wrench outcomes.

Do not promote the 0.8B as the winner solely because it is smaller, and do
not promote 2B to all-day coding based on these lookups. The next candidate
work should test the strongest authorized controller hypothesis (2B plus a
Wrench-specific LoRA) only after current-goal package review, exact training
peak admission, and the applicable RAM start gate. A coding-worker claim
requires a broader same-hardware task battery.
