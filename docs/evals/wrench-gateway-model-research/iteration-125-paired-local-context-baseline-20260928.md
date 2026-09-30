# Iteration 125: paired full-context and Wrench E0 local-model arms

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER125`  
Status: **same local model passed all three tasks in both arms; local-model input-token reduction was 94.7264%**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired result

This is the first same-model, same-episode comparison between the entire
authored repository fixture and Wrench E0-prepared context. Qwen3.5-0.8B
answered each task once per arm, greedily, with the same answer limit and exact
string verifier. The source fixture, task, model revision, chat template, and
runtime were held constant within each pair.

| Task | Full-fixture local input | Wrench E0 local input | Output tokens, full / E0 | Verified, full / E0 |
|---|---:|---:|---:|---|
| Retry policy | 8,751 | 559 | 8 / 8 | Pass / Pass |
| Session lifetime | 8,754 | 463 | 11 / 11 | Pass / Pass |
| Retry function | 8,739 | 362 | 6 / 6 | Pass / Pass |
| **Total** | **26,244** | **1,384** | **25 / 25** | **3/3 / 3/3** |

On the local model's own tokenizer, E0 lowered input tokens by **94.726414%**.
Including generated output tokens, the local-model token reduction was
**94.636263%** (26,269 to 1,409 total tokens). Separately, the pinned target
tokenizer measured full-fixture input 19,337 and E0 input 1,662, or
**91.405078%** input reduction. These are two different token conventions and
neither is a frontier-token result. E0 preserved the exact answer on all three
cases, but the sample is far too small for a quality-retention claim.

The result identifies a concrete gap to the requested 95% local-model input
target: this paired arm is 0.273586 percentage points short. The total local
input-plus-output reduction is 0.363737 points short. A lower budget must be
tested on these exact paired episodes with all evidence and answers verified;
budget 48 previously failed closed on the retry-function evidence, so do not
assume smaller is better.

## Runtime and identity

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter.
- Runtime: Python 3.13.15, PyTorch `2.14.0+cu132`, CUDA 13.2,
  Transformers 5.17.0, NVIDIA RTX 5060 Ti.
- Wrench context budget: 64. Target tokenizer runtime: Transformers 5.17.0,
  tokenizers 0.23.2, huggingface-hub 1.33.0.
- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Model inventory SHA-256:
  `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`.
- Snapshot verification SHA-256:
  `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6`.
- Runner SHA-256:
  `458e8f3ffda4483c36ae0039811b415e693c408556aa38cd9627d1f3c8208c8c`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter125.json`,
  4,687 bytes, SHA-256
  `b0ee57687c6854d3aa5ea55d1ca43cf2a0c4535b59edbb28c1173837fd5d3033`.
- Model load 5.1057 s; full/E0 generation totals 20.4346 / 7.9481 s;
  total process 42.127 s. Peak CUDA allocated/reserved: 2,678,610,944 /
  2,894,069,760 bytes.
- In-process minimum free RAM 13.9129%; minimum free VRAM 75.3111%; 30
  samples, no monitor error. The 10% runtime floor held. Fit-03's 25% RAM
  start condition was not met.
- The 100,000,000-byte reservation included the Docker WSL model volume and
  hourly automation directory; C: had over 139 GB free. No provider call or
  spend occurred. The held-out split remained unopened.

Transformers used reference fallback kernels because `causal_conv1d` and
`flash-linear-attention` are absent. This affects latency and remains part of
the exact tested runtime identity.

## Scope and decision

This validates a strong, narrowly bounded prompt-input reduction result on
three synthetic lookup questions. It does **not** validate frontier-only task
success, local-versus-frontier success retention, 95% episode completion,
<=5% frontier routing, full-lifecycle frontier-token savings, all-in cost,
LoRA contribution, patch authoring, test repair, or all-day engineering.
Frontier-token savings remains **N/A** because no paid frontier comparison
ran and SubRoute's hard aggregate campaign cap is still absent.

Next, sweep lower context budgets between 48 and 64 using this paired harness,
retaining all three completions and evidence. Then expand the exact paired
design beyond lookups to code modification and test repair; any 95% claim must
use the full product episode ledger and its frontier-only arm.
