# SWE-Explore-Bench runbook

## Selection and fit

SWE-Explore-Bench is one of the four selected outside scorecards because it
directly grades read-only repository exploration before edits. Its official
evaluator reports line precision, recall and F1, hit-file and hit-region
rates, noise, context efficiency, and rank-aware quality at fixed region
budgets. The official release contains 848 issues. Published explorer results
are outside references; they are not Wrench comparisons unless the same cases,
ranked-region budget, adapter, and evaluator are used.

## Pinned sources

- Upstream code: `Qiushao-E/SWE-Explore-Bench`, commit
  `5602f031f2d9562d0a805f83402b536e831a5a11`.
- Benchmark rows: `bench.final.public.jsonl`, 848 rows, SHA-256
  `dc4f114ececd0bfb987361c26ae5e2440456e2cccb36adfccb09ea5385aec202`.
- The released benchmark file provides ground truth and trajectory provenance,
  but not issue text or base commits. Metadata is joined from the source
  datasets below by exact `instance_id`.
- Metadata source pins:
  - `princeton-nlp/SWE-bench@e48e2bd1e9fecd5bbd641e9414ac59da9f2e69f6`
  - `nebius/SWE-rebench@89cdfbab4ab1bd8f5a658bb212d1b63624f4f881`
  - `ScaleAI/SWE-bench_Pro@2d52cb3df914a3fcf80c7f66738b3a88ae37fc50`
  - `SWE-bench/SWE-bench_Multilingual@7566cd247075886ef34453ff5582908c0255f5e6`
- Joined metadata: `data/issue_map_and_commits.json`, 848 exact matches,
  64 unique source repositories, 847 unique base commits, SHA-256
  `aa689cf59efc6d0f8c8606a18de9a9ede2bb37d502fa0b2f370dd2cd4211bb39`.
- Lineage discrepancy: the pinned upstream README says 203 repositories, but
  the exact source joins resolve 12 Princeton SWE-bench repositories, 11
  SWE-bench Pro repositories, and 41 Multilingual repositories, 64 unique in
  total. Preserve the discrepancy; execution uses each joined `repo` and
  `base_commit`, not the README's aggregate count.
- `data/issue-source-manifest.json` records counts and source revisions.
  `merge_multilingual_sources.py` rebuilds the multilingual portion without
  modifying the official benchmark rows or labels.

## Run boundary

The official runner expects a repository snapshot at each case's exact base
commit. The 848 cases span 847 unique commits. A pilot established bounded
serial snapshot storage with a phase-local temporary directory mapped through
a short Windows `SUBST` path. The current host had 51,486,584,832 free bytes on
C: during the first preflight. Do not use HEAD as a substitute, and do not
report the 18-case pilot as the full 848-case official result.

The complete run must:

1. Use all 848 pinned rows and exact commits, or label a separately
   prespecified slice as a development pilot.
2. Keep all snapshots, generated inputs, results, logs, and score receipts
   inside this phase directory.
3. Run the real Wrench ranked file/line adapter and at least one free outside
   explorer/model on identical issues and repositories. Keep published
   full-suite numbers labeled as reference values.
4. Use the upstream `ExploreEvaluator`, disclose the exact case count and line
   budget, and report per-case paired outcomes with uncertainty.
5. Keep Wrench within its read-only action boundary. The evaluation harness may
   prepare snapshots and score outputs; Wrench itself does not run shell,
   mutate files, or apply patches.

From the repository root, map a short drive to the phase-local scratch
directory so long upstream filenames remain within Windows path limits. The
script checks 10% RAM and VRAM reserves before each task, uses exact commits,
and deletes each task snapshot after scoring:

```powershell
$scratch = (Resolve-Path "phases/phase-446-agent-benchmark-fit/_swe_tmp").Path
if (Test-Path "Z:\") { throw "Z: is already assigned" }
subst Z: $scratch
$env:WRENCH_SWE_TMP = "Z:\"
try {
  python phases/phase-446-agent-benchmark-fit/run_swe_explore_contextledger_pilot.py --full-suite
} finally {
  Remove-Item Env:WRENCH_SWE_TMP -ErrorAction SilentlyContinue
  subst Z: /D
}
```

The full-suite invocation currently writes to
`runs/wrench-contextledger-full848-v1/`. Check for a live process and its
case-level stdout before retrying; do not launch a duplicate run.

Dataset metadata now has full exact coverage. A bounded Wrench component pilot
is scored below; the full-suite score and independent outside-model run remain
pending.

## Development pilot receipt

An 18-case pilot was prespecified before scoring: six cases per source dataset,
one task per repository, seeded shuffle 446, and 20 ranked regions per system.
The official `ExploreEvaluator` scored Wrench's actual
`ContextLedger.search` component and the successful read trajectories included
with the released benchmark. Exact repository archives were fetched one at a
time at their pinned base commits, indexed, scored, and deleted. A Windows
`SUBST` drive mapped the short scratch path back into this phase directory;
the mapping was removed on process exit.

| System | Cases | Line F1 | Hit-file rate | nDCG@500 | Context efficiency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Wrench `ContextLedger.search` | 18 | 0.0243 | 0.2250 | 0.0756 | 0.0649 |
| GLM-5.1 saved trajectories | 10 | 0.4722 | 0.8149 | 0.5001 | 0.9888 |
| GPT-5.4 saved trajectories | 11 | 0.5688 | 0.6893 | 0.7849 | 0.9321 |
| Claude Sonnet 4.6 saved trajectories | 11 | 0.6882 | 0.4553 | 0.8382 | 0.9972 |
| Kimi K2.6 saved trajectories | 5 | 0.4962 | 0.6977 | 0.5987 | 1.0000 |
| Claude 4.5 saved trajectories | 6 | 0.6433 | 0.8472 | 0.5125 | 1.0000 |
| Gemini 3 Pro saved trajectories | 6 | 0.8361 | 0.7361 | 0.8708 | 1.0000 |
| GLM-4.6 saved trajectories | 6 | 0.7962 | 0.5972 | 0.6900 | 1.0000 |

Wrench's paired line-F1 deltas were negative against every saved trajectory
reference. Against GPT-5.4, the mean Wrench-minus-trajectory delta was -0.5535
(n=11, paired case-bootstrap 95% CI [-0.7398, -0.3532]); against GLM-5.1 it
was -0.4554 (n=10, CI [-0.5963, -0.3194]). These are development-pilot
comparisons to released successful trajectories, not fresh model calls or
official full-suite leaderboard entries. The raw path-overlap ranker therefore
does not support a Wrench strength claim for broad repository exploration.

The machine-readable receipt, full per-case predictions, and resource samples
are in `runs/wrench-contextledger-pilot-18-final/`. It scored 18/18 with zero
snapshot failures in 583.6 seconds. The 10% RAM and VRAM reserves were
maintained. Two earlier extraction attempts are retained in their separate
`pilot-18/` and `pilot-18-rerun/` directories; they are incomplete
infrastructure attempts and are not included in the metrics above.

This pilot uses released trajectories to compare exploration, so it is a
useful external diagnostic but a weak showcase fit for Wrench's specialized
proposal gate. Keep the benchmark in the predeclared slate and retain the
negative result. Do not tune against these pilot cases and call them a holdout.
Any retrieval change must be developed on a separate split and evaluated on a
new, repository-disjoint sample before a broader run.
