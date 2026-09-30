# Iteration 153: retain related implementation evidence

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-RELATED-SOURCE-SEMANTICS-ITER153-QWEN35-2B`  
Status: **Adding the retry implementation path restored 3/3 on this known development set. The path-scoped arm used fewer local tokens than full E0 but did not reach 95% on the target tokenizer.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Follow-up hypothesis

Iteration 152 restricted `retry-policy` to `config/service.toml` and Qwen3.5-2B
answered `2,250` rather than `3,250`. The path-scoped source receipt had no
`src/retry.py` implementation span. This run added `src/retry.py` to that
case's candidate path set while keeping the other two path sets unchanged.
The request hashes, source fixture, model, decoding, context budget, verifier,
and full-context arm were held fixed.

The related-source manifest has no answer or quote fields and was validated
against the exact requests and fixture. It remains an experimenter-authored
development annotation over cases already seen in prior runs. It is not an
independent annotation, fresh holdout, or confirmatory sample.

## Results

One pinned Qwen/Qwen3.5-2B BF16 base model ran all three arms. Identity:
revision `15852e8c16360a2fea060d615a32b45270f8a8fc`, inventory SHA-256
`23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`, and
snapshot receipt SHA-256
`59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014`.
Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2,
RTX 5060 Ti, BF16. No adapter was loaded.

| Arm | Verified | Local-model input + output tokens | Reduction vs full fixture |
|---|---:|---:|---:|
| Full fixture | 3/3 | 26,221 | baseline |
| E0, all fixture paths | 3/3 | 766 | 97.078677% |
| E0, related paths from manifest | 3/3 | 694 | 97.353266% |

The related-path arm used 72 fewer local-model tokens than all-path E0, a
9.3995% reduction relative to E0's 766-token total. The target tokenizer
counted 1,096 of 19,297 input tokens for this arm, a **94.320361% input
reduction**. All-path E0 counted 1,162 tokens, or 93.978339% lower. Thus this
variant added about 0.342 percentage points of target-tokenizer reduction and
still missed 95%. These are local/proxy prompt counts, not Frontier usage.

The path-scoped `retry-policy` case retained both `config/service.toml` and
parser-reported `src/retry.py` symbols, and returned `3,250`. `session-lifetime`
used only `config/service.toml`; `retry-function` used only `src/retry.py`.
These three passes do not establish that the path manifest generalizes.

Minimum sampled free RAM was 13.9053%; minimum VRAM was 61.3451%. Runtime
including model load was 56.3664 seconds. There were zero Frontier calls and
$0 provider spend. `frontier_token_savings_percent` is null because there was
no Frontier-only arm. The API spend cap remains absent, so no provider request
was made.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-source-iter153-qwen35-2b.json` | 21,827 | `A21062F331CA188E6CA904F60DF36AB0D871090F096A44916A7BD10B0AECFE80` |
| `docs/evals/wrench-gateway-model-research/iteration-153-related-source-manifest.json` | 923 | `783750123439F0335308F99B37F8793AA8512470C4DF8441183BBE8D94C1F90C` |
| `examples/gateway_context_mvp/run_local_model_mvp.py` | 17,057 | `9C6125F5F3BA0A45203903EFA470170DBDF82E8C17CE973D04C752A447351D0F` |
| `examples/gateway_context_mvp/run_paired_local_context_baseline.py` | 26,508 | `6B4D39DA818E04D423B2484919BBB2D74086A09DF86A054826A36FB2F18D4413` |

The manifest was accepted and hash-checked by the paired runner. The six
focused manifest/provenance tests from Iteration 152 remain applicable because
the loader and test sources did not change in this follow-up. No new tests
were run here. No training, held-out access, provider call, credential access,
or route change occurred.

## Next experiment

Keep the related TOML table and parser-reported retry implementation together.
Test a compact, relationship-preserving representation and compute every arm
with the pinned target tokenizer before running the model. A candidate that
does not preserve all verifier cases is rejected regardless of token count;
one that preserves quality but remains above 965 target tokens on this fixture
has not met the 95% input component goal. Full-lifecycle Frontier-token and
all-in-cost claims remain unmeasured.
