# Iteration 152: answer-free path-scope pruning screen

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-ANSWER-BLIND-PATH-PRUNE-ITER152-QWEN35-2B`  
Status: **Path-scoped context raised local token reduction slightly, but the 2B model failed one of three verifier cases. Reject this path-only pruning variant.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question and frozen manifest

Does restricting E0's source candidates to a request-to-path manifest lower
input tokens beyond ordinary full-repository E0, while preserving task
quality? The manifest binds each request hash and the synthetic fixture hash
to one source path. It contains no answer strings or required-answer quotes.
Selection ran before model generation; quote checks are used only to detect a
missing required source after preparation, not to select paths or segments.

This is an exploratory development screen, not an independent or fresh
held-out evaluation. The three synthetic cases have appeared in prior runs,
and the source-path annotations were authored by the experimenter. Do not use
these results as confirmatory answer-blind or population evidence.

## Paired run

One pinned Qwen/Qwen3.5-2B BF16 base model answered the same three cases in
three arms: full fixture, existing E0 over all fixture paths, and E0 limited
to the manifest paths. Identity: revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`, inventory SHA-256
`23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`, and
snapshot receipt SHA-256
`59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014`.
Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2,
RTX 5060 Ti, BF16. No adapter was loaded and no provider was called.

| Arm | Verified | Local-model input + output | Reduction vs full fixture |
|---|---:|---:|---:|
| Full fixture | 3/3 | 26,221 | baseline |
| E0, all fixture paths | 3/3 | 766 | 97.078677% |
| E0, manifest path scope | 2/3 | 632 | 97.589718% |

The path-scoped arm's 97.589718% is a local Qwen tokenizer result and fails
the quality comparison, so it is not an acceptable efficiency improvement.
Using the separate target-tokenizer count, path-scoped input was 1,034 of
19,297 tokens, or **94.64165% lower**, also below 95%. The all-path E0 input
was 1,162 of 19,297, or 93.978339% lower. Both figures measure prompt input,
not Frontier tokens.

The failed case was `retry-policy`: path-scoped E0 answered `2,250`; full
context and all-path E0 answered `3,250`. The path-scoped source receipt
contains only `config/service.toml`; all-path E0 also selected parser-reported
symbols from `src/retry.py`. Loss of code-level retry semantics is consistent
with the error, but this small experiment does not isolate its cause. Keep the
all-path context for this task until a relation-preserving variant verifies.

Minimum sampled free RAM was 13.6472%; minimum VRAM was 61.3942%. Runtime
including model load was 57.2431 seconds. All three case receipts have prompt,
E-label and source-reference bindings. There were zero Frontier calls and
$0 provider spend. Frontier-token savings are null because no Frontier-only
arm was run.

## Verification and artifacts

The focused `unittest` suite passed **6/6**, including request/fixture hash
binding and rejection of answer fields or stale request hashes. Python syntax
compilation and `git diff --check` passed. The available Python environments
do not contain `pytest`; no pytest result is claimed.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-answer-blind-path-iter152-qwen35-2b.json` | 19,668 | `45ECD149BDDDCDEF650F8D9B59DD455DE497AF364A1434FFEA602FE25E74B5F2` |
| `docs/evals/wrench-gateway-model-research/iteration-152-answer-blind-path-manifest.json` | 907 | `E2D7CA8F37926007338136BD603BFB4505716F4FD099AA57659380868F8552FF` |
| `examples/gateway_context_mvp/run_local_model_mvp.py` | 17,057 | `9C6125F5F3BA0A45203903EFA470170DBDF82E8C17CE973D04C752A447351D0F` |
| `examples/gateway_context_mvp/run_paired_local_context_baseline.py` | 26,508 | `6B4D39DA818E04D423B2484919BBB2D74086A09DF86A054826A36FB2F18D4413` |
| `tests/test_gateway_compact_provenance_receipt.py` | 6,336 | `50C04ED1BACB67B0971754DDDD191F930C9DF4B831508851F279C69DCD0C67D8` |

## Decision

Do not activate single-path pruning. The failure shows that a relevant file
path alone may not preserve semantic relationships needed for correct work.
Continue with structured, answer-independent retrieval that keeps the
configuration evidence and related implementation semantics together, then
measure that variant on frozen tasks. Keep local tokenizer reductions
separate from provider-reported Frontier usage and all-in cost. No training,
held-out access, provider spend, route change or activation occurred.
