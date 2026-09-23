# Agent Retrieval Bench V2 runbook

This folder records the selected external retrieval benchmark, its outside
references, and the local reproduction. All downloaded data, upstream code,
and run outputs are ignored beneath this phase directory.

## Pins

- Benchmark code: `eyuansu62/agent-retrieval-bench`, commit
  `07014c986f3deadb1548c62b32c0ffbe6a81465d`.
- Dataset: `eyuansu71/agent_retrieval_bench`, revision
  `5901e1ee3aff048290db72edf9c63bc498b79ea3`.
- Release: V2 selective natural split, 427 rows total, 345 positive and 82
  no-gold. The no-gold rows are excluded from positive retrieval metrics.
- Candidate set: `all_files`. No keep-list was applied.

## Reproduce the published Lexical reference

Run from `phases/phase-446-agent-benchmark-fit/external/agent-retrieval-bench`
in PowerShell. The phase-local Python environment is used, and the upstream
source checkout is imported directly:

```powershell
$env:PYTHONPATH = (Join-Path $PWD "upstream\src")
& ..\..\.venv\Scripts\python.exe -m agent_retrieval_bench.cli eval-selective-baseline --derived data/benchmark/v2_selective_retrieval_natural --corpus data/corpus/v2_selective_mixed --ranker lexical --candidate-filter all_files --no-keep-list --out data/eval/arb-v2/natural-lexical-summary.json --details data/eval/arb-v2/natural-lexical-details.jsonl
Remove-Item Env:PYTHONPATH
```

Compute canonical context-yield metrics from the saved ranked lists with the
benchmark's pinned BCY functions:

```powershell
& ..\..\.venv\Scripts\python.exe ..\..\run_arb_v2_bcy.py
```

The BCY runner sorts work by repository snapshot and keeps one snapshot in
memory at a time. It checks RAM and VRAM reserves throughout the scoring pass.
The legacy fields `gold_token_ratio@8k` and `context_efficiency@8k` in the
baseline summary use character-based packing and are not the canonical BCY
metric.

## Reproduced result

The official Lexical run scored 345 positive cases and skipped 82 no-gold
cases. It took 801.465 seconds. Canonical BCY used the official
`regex_code_tokenizer_v1` renderer and the merged V2 corpus manifest.

| Metric | Reproduced Lexical | Published Lexical |
| --- | ---: | ---: |
| Recall@20 | 0.493961 | 0.4940 |
| MRR | 0.157415 | 0.1574 |
| BCY@4K | 0.148792 | Not shown in compact table |
| BCY@8K | 0.264976 | 0.2650 |
| BCY@16K | 0.388647 | Not shown in compact table |
| BCY@32K | 0.488164 | Not shown in compact table |

Published references from the same ARB V2 report:

| Outside system | Recall@20 | MRR | BCY@8K |
| --- | ---: | ---: | ---: |
| Qwen3-Embedding-4B | 0.6306 | 0.2379 | 0.3409 |
| Qwen3-Embedding-8B | 0.7029 | 0.2336 | 0.3732 |
| RepoMap | 0.6333 | 0.2158 | 0.3788 |
| Jina code embeddings 0.5B | 0.4823 | 0.1914 | 0.2783 |
| BM25 | 0.4452 | 0.1520 | 0.2051 |

The reproduced Lexical metrics match the paper after rounding. This checks
the local dataset, ranker, and scorer path. It does not measure Wrench.

## Wrench ranked retrieval component

The adapter calls the actual `src/wrench_harness/context.py::ContextLedger`
implementation. It indexes each released candidate chunk once per repository
snapshot, searches with the benchmark's serialized query, and emits the first
20 unique paths from `ContextLedger.search` results. Gold labels and
counterfactual metadata are used only by the evaluator after ranking. All 427
rows were processed: 345 positive and 82 no-gold. The adapter is a retrieval
component score, not an end-to-end agent result or a score from the Wrench
binary model.

### Results

| System | Recall@20 | MRR | BCY@4K | BCY@8K | BCY@16K | BCY@32K |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Wrench ContextLedger.search | 0.2338 | 0.0812 | 0.0507 | 0.0669 | 0.1237 | 0.2099 |
| Official Lexical, reproduced | 0.4940 | 0.1574 | 0.1488 | 0.2650 | 0.3886 | 0.4882 |
| Qwen3-Embedding-4B, published | 0.6306 | 0.2379 | n/a | 0.3409 | n/a | n/a |
| Qwen3-Embedding-8B, published | 0.7029 | 0.2336 | n/a | 0.3732 | n/a | n/a |
| Jina code embeddings 0.5B, published | 0.4823 | 0.1914 | n/a | 0.2783 | n/a | n/a |

The comparison with reproduced Lexical is paired on all 345 positive sample
IDs. Wrench minus Lexical repository-cluster bootstrap 95% intervals were
[-0.309, -0.188] for Recall@20, [-0.111, -0.035] for MRR, and
[-0.303, -0.079] for BCY@8K. Published Qwen rows use the same ARB V2 release,
but their per-case predictions were not available for a paired bootstrap.
These results show a substantial retrieval gap, so ARB stays a stress test and
must not be presented as a Wrench win.

The indexing pass built 271 snapshot indexes in 292.1 seconds; full run wall
time was 396.3 seconds. Measured query latency was p50/p95 14.3/325.1 ms.
These measurements include repository snapshot grouping but exclude a separate
full application startup. The run maintained over 26 GiB available RAM and
over 14 GiB free VRAM.

Run the adapter from the repository root with the phase environment:

```powershell
$phase = "phases/phase-446-agent-benchmark-fit"
& (Join-Path $phase ".venv/Scripts/python.exe") (Join-Path $phase "run_arb_v2_wrench_ranker.py")
```

Run the canonical context-yield scorer from the ARB directory so its relative
corpus-manifest paths resolve:

```powershell
& ..\..\.venv\Scripts\python.exe ..\..\run_arb_v2_bcy.py --details runs\wrench-context-ledger-ranked-v1\details.jsonl --corpus-manifest data\corpus\v2_selective_mixed\corpus_manifest.jsonl --out runs\wrench-context-ledger-ranked-v1\canonical-bcy-summary.json --case-out runs\wrench-context-ledger-ranked-v1\canonical-bcy-details.jsonl
```

The matched comparison runner computes 10,000 repository-cluster bootstrap
replicates against the saved official Lexical details:

```powershell
& ..\..\.venv\Scripts\python.exe ..\..\compare_arb_v2_wrench.py
```

## Wrench binary gate component and outside model comparison

This is a separate adapted decision-only component evaluation, not an official
ARB leaderboard score. It does not measure Recall@20, MRR, BCY, ranked
retrieval, or downstream task completion. The ranked retrieval component has
its own results in the section above.

The pinned official query serializer `query_text_for_eval` was used with the
repository name. The gold labels and metadata were withheld from all prompts,
and the official query leakage check passed. The Wrench model and both outside
models used the same 427 case IDs, the same base gate prompt, and the frozen
Wrench limits of 8,192 characters and 512 tokens. To make the comparison
matched, the clean cap-aware Ollama runs skip the same over-limit cases that
are forced to abstain for Wrench. Earlier uncapped runs are retained but are
not used in this comparison. The Qwen outside models received a strict JSON
response-format instruction.

### Results

| Model or control | Binary accuracy | Balanced accuracy: positive vs all no-gold | Positive continue | Natural no-gold abstain | Counterfactual no-gold abstain |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrench Qwen 3.6 8-expert BF16 binary head | 55.27% | 57.91% | 53.62% | 82.00% | 31.25% |
| Qwen3.5 0.8B Q8_0 via local Ollama | 56.91% | 55.67% | 57.68% | 80.00% | 12.50% |
| Qwen3.5 9B Q4_K_M via local Ollama | 61.36% | 70.51% | 55.65% | 80.00% | 93.75% |
| Always continue | 80.80% | 50.00% | 100.00% | 0.00% | 0.00% |
| Always abstain | 19.20% | 50.00% | 0.00% | 100.00% | 100.00% |
| Frozen input limits, then always continue | 56.91% | 55.67% | 57.68% | 80.00% | 12.50% |

The high raw accuracy of always-continue is a class-imbalance artifact: 345 of
427 rows are positive. Balanced accuracy and the no-gold subgroup rates are
more informative here. Qwen3.5 9B exceeds Wrench by 6.09 percentage points in
raw accuracy (paired repository-cluster bootstrap 95% CI +1.78 to +13.12) and
by 12.60 points in balanced accuracy (95% CI +5.23 to +23.04). Qwen3.5 0.8B
does not clearly separate from Wrench in raw accuracy: +1.64 points (95% CI
-1.52 to +4.14). Its balanced-accuracy delta is -2.24 points (95% CI -8.05
to +1.05). These local adapted component results are not the published ARB
retrieval scores or the official ARB evaluation protocol.

The Wrench run had 190/427 over-limit cases: 8 exceeded the character cap and
182 exceeded the 512-token cap. This includes 146/345 positive cases and
40/50 natural no-gold cases. Therefore the full-set natural no-gold
abstention rate of 82% is mostly the fail-closed input limit: 40 of the 41
correct natural no-gold abstentions were forced by the limit. Only 10 natural
no-gold cases reached the learned head. On the 237 in-limit rows, Wrench
continued on 185/199 positives (92.96%), abstained on 1/10 natural no-gold
rows (10%), and abstained on 6/28 counterfactual no-gold rows (21.43%).
Do not present the 82% full-set rate as learned abstention quality.

Wrench's complete inference run used the local NVIDIA GeForce RTX 5070 Ti,
PyTorch 2.9.1+cu128, Transformers 5.5.0, and Python 3.14.0. Warmed per-case
latency was p50/p95 437.90/573.32 ms over all cases, and 487.10/596.67 ms for
the 237 cases that reached the learned head. Peak use preserved the required
10% RAM and VRAM reserves. No paid provider calls or tool executions
occurred. The saved external-model outputs came from local Ollama.

### Reproduction

From the repository root, using the phase-local Python environment:

```powershell
$phase = "phases/phase-446-agent-benchmark-fit"
$python = Join-Path $phase ".venv/Scripts/python.exe"
$model = "D:/models/Wrench-Qwen3.6-8expert-BF16"
$head = Join-Path $phase "internal/qwen-system-one-run-v1/qwen-abstain-head.json"
& $python (Join-Path $phase "run_arb_v2_abstention_gate.py") --model-dir $model --head $head --output-dir (Join-Path $phase "external/agent-retrieval-bench/runs/wrench-binary-gate-v2")
& $python (Join-Path $phase "measure_arb_v2_wrench_limits.py") --model-dir $model --head $head --output-dir (Join-Path $phase "external/agent-retrieval-bench/runs/wrench-binary-gate-v2/input-limit-audit")
& $python (Join-Path $phase "rescore_arb_v2_abstention_gate.py") (Join-Path $phase "external/agent-retrieval-bench/runs/wrench-binary-gate-v2") --suffix rerun
```

Local outside models already present in Ollama can be run with
`run_arb_v2_ollama_gate.py`, supplying the exact input-limit audit and Wrench
predictions. Current receipts and cap-matched rescore summaries live under
`external/agent-retrieval-bench/runs/`; dataset and outputs are ignored by the
outer repository. Machine-readable results, model digests, paired intervals,
input-limit counts, and artifact hashes are also recorded in
`benchmark-manifest.json`.

## Local receipts

Paths are relative to this `external/agent-retrieval-bench` directory.

- Baseline summary: `data/eval/arb-v2/natural-lexical-summary.json`,
  SHA-256 `81ba96dc6de88ef76594abc30b2589a63caaaf5b73f91f123ba0cb62d31c18b8`.
- Baseline ranked rows: `data/eval/arb-v2/natural-lexical-details.jsonl`,
  SHA-256 `a09865c5a471c6bbd8d34cc749250b203efa6ba278a0f00953bae0413453ece9`.
- Canonical BCY summary:
  `data/eval/arb-v2/natural-lexical-canonical-bcy-summary.json`,
  SHA-256 `0a2476c344d074236de17409cfca76fca50af5aa8c20781aa8d0ca3a0fd79c50`.
- Canonical BCY case rows:
  `data/eval/arb-v2/natural-lexical-canonical-bcy-details.jsonl`,
  SHA-256 `6b9579db8ba84c27e89ff1718e1bf6bb77415e272914d7b9214b9e91fcc808a4`.
- BCY runner: `run_arb_v2_bcy.py`, SHA-256
  `d252fc4bbecbea9ed0a35ce9444b28c94e68ff48df38dd08f38a1e73b21b38a9`.
- The corpus manifest SHA-256 is
  `f7bc6131f40b9527911adc0d7f974b3c2329a37fc2d823b0379daa301b0aa28b`.
- Wrench ranked component summary:
  `runs/wrench-context-ledger-ranked-v1/summary.json`, SHA-256
  `22A878D76AD6B7DC5870DE21407BED9F3D312F4A2C4514DBFD8C1C1164B796DF`.
- Wrench ranked candidate details:
  `runs/wrench-context-ledger-ranked-v1/details.jsonl`, SHA-256
  `35981BEDCD647B76FF47C60277C4B768499E663B12A4993D8E20999E92864946`.
- Wrench canonical BCY summary:
  `runs/wrench-context-ledger-ranked-v1/canonical-bcy-summary.json`, SHA-256
  `FE6E27074D8DFCCE540A6513F855E43DC393D74DA0A39E0BA087554828BC2E58`.
- Paired comparison and cluster-bootstrap intervals:
  `runs/wrench-context-ledger-ranked-v1/matched-comparison.json`, SHA-256
  `088B0ECB8FC3608F844D2D1747C85A49FBBB46741E4465B70E7F3063049589E4`.
- Ranked adapter: `run_arb_v2_wrench_ranker.py`, SHA-256
  `5093B0819E43B23DD82FBEF34832A8C67BE2C90631503319E388EF7694774D54`.
- Retrieval implementation: `src/wrench_harness/context.py`, SHA-256
  `4AA54990A2908C8EE94AE4373EB52074D32880BBAFBDFA83D661084B9E87E6D8`.

The BCY pass observed a minimum of 27.79 GiB free RAM and 13.69 GiB free VRAM.
It made no paid provider calls.
