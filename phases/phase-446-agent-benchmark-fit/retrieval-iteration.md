# Retrieval iteration log

## Starting evidence

The frozen ARB V2 adapter evaluated the production `ContextLedger.search`
path on all 427 rows, with 345 positive retrieval cases and 82 no-gold cases.
Wrench scored Recall@20 0.2338, MRR 0.0812, and BCY@8K 0.0669. Reproduced
official Lexical scored 0.4940, 0.1574, and 0.2650. Published Qwen3-Embedding
4B/8B references scored Recall@20 0.6306/0.7029. These are measured retrieval
gaps, not showcase wins. See `external/agent-retrieval-bench/RUNBOOK.md` for
the dataset and evaluator pins.

## Candidate change

On 2026-09-23, `src/wrench_harness/context.py` changed `ContextLedger.search`
from raw query-term hit counts to BM25 scoring with inverse document frequency
and document-length normalization (`k1=1.2`, `b=0.75`); ties retain the
existing newest-source-order preference. Term frequencies are held in the
inverted postings, with one lexical token-length integer per segment. The exact
pre-change source was Git blob
`0dc7e14e6e1e3f656c7b340e18c5c620d2e89476`; the candidate source is
`cb5b4ab0767094e2411a1be720c6e63b01e8b22a`.

The pinned 427-row ARB V2 comparison is complete. Candidate Recall@20 is
0.2645 versus 0.2338 pre-change (paired repository-cluster delta +0.0307,
95% CI [-0.0398, 0.1345]); MRR is 0.0856 versus 0.0812 (delta +0.0044, CI
[-0.0186, 0.0303]). Neither ranking-metric interval excludes zero. Canonical
BCY@8K is 0.1193 versus 0.0669 (delta +0.0524, CI [+0.0071, +0.0978]), a
paired budgeted-context-yield gain on this suite. The other budget CIs include
zero. The candidate still trails published Qwen embedding references, so
describe this as a component-level 8K context-yield improvement, not a general
retrieval or end-to-end win. Preserve the pre-change receipts as the baseline.

## Runs already in progress

The SWE-Explore-Bench 848-row run and ContextBench 500-row run started before
the source change and loaded the pre-change `ContextLedger` implementation.
They remain baseline runs. Their receipts must not be attributed to the BM25
candidate. The Qwen3.5 27B ToolBeHonest run is a separate local outside-model
comparison and does not use ContextLedger.

## BM25 candidate comparison result

The Qwen3.5 27B supplemental run completed all 700 rows and its model was
unloaded before the candidate run. The BM25 ranker completed all 427 ARB V2
rows and its canonical BCY rescore and paired repository-cluster comparison
completed with at least 10 percent RAM and VRAM reserves. The full ContextBench
and SWE-Explore baseline runs continue independently and were not changed.
Do not attribute those older source runs to this BM25 candidate.

Do not launch a duplicate or overwrite the saved receipts. Any follow-up
candidate must use a new output directory and a predeclared retrieval
experiment.

## Reproduce the candidate comparison

Use a new output directory so the frozen pre-change ARB receipts remain
untouched:

```powershell
$phase = (Resolve-Path "phases/phase-446-agent-benchmark-fit").Path
$python = (Resolve-Path (Join-Path $phase ".venv/Scripts/python.exe")).Path
$candidate = "external/agent-retrieval-bench/runs/wrench-context-ledger-bm25-v1"
& $python (Join-Path $phase "run_arb_v2_wrench_ranker.py") --output-dir (Join-Path $phase $candidate)
```

Recompute official BCY for that saved ranking:

```powershell
$external = Join-Path $phase "external/agent-retrieval-bench"
Push-Location $external
try {
  & $python (Join-Path $phase "run_arb_v2_bcy.py") `
    --details "runs/wrench-context-ledger-bm25-v1/details.jsonl" `
    --corpus-manifest "data/corpus/v2_selective_mixed/corpus_manifest.jsonl" `
    --out "runs/wrench-context-ledger-bm25-v1/canonical-bcy-summary.json" `
    --case-out "runs/wrench-context-ledger-bm25-v1/canonical-bcy-details.jsonl"
} finally { Pop-Location }
```

Then compute paired repository-cluster intervals against the saved baseline:

```powershell
& $python (Join-Path $phase "compare_arb_v2_retrieval_iterations.py") `
  --candidate-dir (Join-Path $phase $candidate)
```

The ranker runner records the `context.py` SHA-256 and BM25 identity. The
comparison covers 345 positive cases and the canonical BCY scorer. It streams
the corpus JSONL instead of retaining a second full copy in RAM, samples RAM
and VRAM every 500 chunks, and stops if the 10 percent reserve cannot be
measured or maintained. Keep every output and comparison under
`phase-446-agent-benchmark-fit/`.
