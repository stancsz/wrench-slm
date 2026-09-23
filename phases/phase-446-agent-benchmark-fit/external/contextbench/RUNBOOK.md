# ContextBench: Wrench retrieval component

## Why this scorecard is selected

ContextBench evaluates code context retrieval with human-annotated line spans
and reports line-level recall, Context F1, task Pass@1, efficiency, and cost.
This is a useful outside scorecard for Wrench's read-only context role. It is
not a general code-generation benchmark, and a retrieval-only Wrench result
must not be presented as Pass@1 or end-to-end agent performance.

## Frozen sources

- Upstream repository: [EuniAI/ContextBench](https://github.com/EuniAI/ContextBench)
- Local upstream commit: `1436c28a8eb95496da4ea69ad458b9f8a8eb7d61`
- Dataset: `Contextbench/ContextBench` at revision
  `c2855792b006af41c67202d33883fb9d46362853`
- Verified subset: `data/contextbench_verified.parquet`, 500 rows, SHA-256
  `e9dcfd504cbfb849ac815a79040c793d0d92f94eecc9b5a4ee3e1445a2f8a791`.
- The verified subset covers Verified, Pro, Poly, and Multi task sources and
  all eight release languages. The full release contains 1,136 tasks across
  66 repositories and eight languages.

An initial 50-row test-split preflight was stopped before scoring because that
parquet's `gold_context` field contains formatted text rather than the JSON
schema expected by the pinned `GoldLoader`. That failed preflight is retained
under `runs/wrench-test50-contextledger-v1/`, with no predictions or metrics.
The selected run uses the official 500-row verified subset, whose annotation
schema is supported by the pinned upstream code. The adapter creates the
upstream `Gold` object from those parsed annotations and redirects only the
upstream checkout callback to the exact archive it fetched. It calls
ContextBench's pinned `evaluate_instance` and `aggregate_results` functions.

## Wrench adapter and boundary

The adapter indexes repository text as 32-line windows using a hash-pinned
`ContextLedger` implementation, searches with the issue text,
and emits the top 20 ranked windows as ContextBench trajectory spans. It
evaluates all 500 verified rows with the upstream line, file, span, and
trajectory metrics. The host runs Python 3.14, where this upstream checkout's
tree-sitter grammars are unavailable; the adapter strips AST-symbol fields and
does not report symbol metrics. Each snapshot is fetched at its exact benchmark
base commit and deleted after all cases for that repository commit are scored.

The adapter does not give Wrench shell, write, credential, patch, or test
authority. It deliberately omits patch and test-patch data from the evaluator's
`Gold` object to prevent EditLoc from using oracle patch contents. It reports
retrieval metrics only; it does not run a downstream solver, so Pass@1 and cost
are not measured.

## Outside model references and comparison limits

The [official leaderboard](https://contextbench.github.io/) currently lists
15 agent-model systems. It reports line-level retrieval recall and Context F1.
Published Qwen references include mini SWE-agent + Qwen3-8B (recall 0.048,
Context F1 0.076) and mini SWE-agent + Qwen2.5-32B (0.076, 0.108). Other
references include mini SWE-agent + GPT-5 (0.606, 0.312), Claude Sonnet 4.5
(0.588, 0.344), and DeepSeek-V4-Pro (0.291, 0.338 in the mini SWE-agent
configuration). These leaderboard runs are context, not paired comparisons:
their exact case coverage and agent configurations are not guaranteed to match
this adapter's 500-row verified subset.

The ContextBench scorecard in this phase is therefore labeled a Wrench
retrieval-component diagnostic. A direct outside-model claim requires a free
outside model to produce predictions on the same 500 IDs through the same
interface and the same official metric code. Do not use paid APIs without
explicit authorization. The internal Wrench gate comparisons against local
Qwen3.5 9B and 27B remain a separate scorecard and must not be conflated with
ContextBench results.

## Run

From the repository root, use an unused short drive letter to map phase-local
scratch storage. Check the existing ContextBench run before retrying; the
runner checkpoints predictions and metrics after every case and resumes by
case ID.

```powershell
$scratch = (Resolve-Path "phases/phase-446-agent-benchmark-fit/external/contextbench/_scratch").Path
if (Test-Path "Y:\") { throw "Y: is already assigned" }
subst Y: $scratch
$env:WRENCH_CONTEXT_TMP = "Y:\"
try {
  python phases/phase-446-agent-benchmark-fit/run_contextbench_wrench_retrieval.py `
    --context-source phases/phase-446-agent-benchmark-fit/external/contextbench/baseline-component/context.py
} finally {
  Remove-Item Env:WRENCH_CONTEXT_TMP -ErrorAction SilentlyContinue
  subst Y: /D
}
```

Persistent receipts are written under
`runs/wrench-verified500-contextledger-v1/`: the fixed sample manifest, ranked
trajectory predictions, per-case official metrics, and a hash-bound summary.
The adapter enforces 10% RAM and VRAM reserves and a 5 GiB free-disk floor.
For an initial three-case infrastructure slice, add `--limit 3`.

The full baseline run must use the saved pre-BM25 source at
`baseline-component/context.py`; do not resume it with the current working-tree
implementation. If GitHub returns HTTP 404 for a pinned snapshot, the runner
records the affected case in `exclusions.jsonl` and continues. Other HTTP and
runtime errors stop the run. The aggregate covers only successfully scored
rows. The summary keeps `complete` false when any row is excluded, even when
every input row is accounted for. In that case publish the exact denominator
and the unavailable case ID, and label the result a partial diagnostic.

### Canonical repository mapping repair

ContextBench's transformed `repo` field can be a dataset alias rather than a
GitHub repository slug. For Multi-SWE-Bench Jackson tasks, map each
`original_inst_id` module to its canonical repository before fetching the
exact base commit: `jackson-core`, `jackson-databind`, or
`jackson-dataformat-xml` under `FasterXML`. The runner records both the
original dataset alias and `snapshot_repo` in the frozen sample manifest.
Do not classify a codeload 404 caused by the collapsed `fasterxml/jackson`
alias as a missing benchmark snapshot. The first attempt's nine alias-related
404 records are preserved separately as
`exclusions.wrong-repository-alias-v1.jsonl`; the corrected full run resumes
from saved case IDs and retains the exact pre-BM25 component source.

## Result state

An initial three-case engineering slice passed through the pinned line-level
metric path. Its line recall was 0.0287, line precision 0.0162, and derived
line Context F1 0.0207. This is too small and repository-clustered to represent
the 500-row subset. It trails the official leaderboard's published Qwen3-8B
reference (recall 0.048, Context F1 0.076), but that comparison is not paired
and uses a different sample/configuration. Preserve it as an early negative
signal, not a scorecard conclusion.

The three-case receipt and its exact predictions are preserved under
`runs/wrench-verified500-contextledger-v1/pilot-3-engineering-slice/`.

The current run stopped after 184 rows at an unavailable pinned repository
commit. Resume the pinned baseline source to score the remaining available
rows. ContextBench remains a retrieval diagnostic until an outside model is
run through the same adapter and a downstream solver is paired for Pass@1 and
cost.
