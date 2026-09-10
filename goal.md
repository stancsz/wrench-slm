# Wrench-SLM: weight release goal

Updated: 2026-09-10
Status: COMPLETE for the declared weight-release scope.
Weight status: WEIGHTS READY FOR RELEASE.
Router status: DEFERRED.

## Outcome

The V21 Wrench-Pro adapter trained successfully, passed the frozen quality
gates on an unused holdout, passed a fresh context perturbation suite, and
loaded from the final package in a newly provisioned environment. The package
is usable by another operator when paired with the pinned Qwen base and the
documented dependencies.

This is a release decision for an adapter and its local inference runtime. It
does not certify a hosted service, a router policy, cloud failover, arbitrary
shell execution, or production traffic reliability. Those remain separate
workstreams.

## Final artifact

- Package: `artifacts/model-release/package-selected-v21`
- Package manifest status: `WEIGHTS READY FOR RELEASE`
- Package manifest SHA-256:
  `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`
- Adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Base: `Qwen/Qwen2.5-0.5B-Instruct`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Base weight SHA-256:
  `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`

The package contains the adapter, exact tokenizer files, inference runtime,
training contract and metrics, pinned requirements, runnable example, model
card, data card, evaluation report, lineage, resource report, evaluation
receipts, checksums, and upstream plus Wrench license notices.

## Evidence

| Gate | Observed result | Receipt |
| --- | --- | --- |
| Training | 300 steps, 4,800 presentations, finite loss, optimizer reset from V20 | `artifacts/model-release/pro-training-v21/run.json` |
| Data semantics | Zero errors and zero warnings for train, development, and evaluation | `artifacts/model-release/audit-v21-semantic-{train,development,evaluation}.json` |
| Data preflight | All splits valid within the 1,536 input and 192 output token budgets | `artifacts/model-release/data-preflight-v21-clean/preflight.json` |
| Exposure | Every task kind and language present at steps 100, 200, and 300, with no repeated rows | `artifacts/model-release/audit-v21-exposure.json` |
| Checkpoint selection | Steps 100, 200, and 300 each scored 176/176; step 200 selected by the frozen rule | `artifacts/model-release/selection-v21/selection.json` |
| Frozen holdout | 440/440 exact, 280/280 routine, 160/160 fallback, 11 kinds, both languages, zero filesystem changes | `artifacts/model-release/v21-package-independent-evaluation/summary.json` |
| Fresh context suite | 220/220 exact, 140/140 routine, 80/80 fallback, reordered context and unseen invalid-range wording | `artifacts/model-release/v21-package-context-release-v2b/summary.json` |
| Fresh package load | Passed in new Python 3.14 environment with pinned CUDA dependencies and empty model cache | `artifacts/model-release/v21-release-verifier-final3/receipt.json` |

The final holdout and context suite were scored after the adapter was frozen.
Neither set was imported into training. The earlier V16 and V20 failures are
preserved as diagnostic history and are not reused as release evidence.

## Training record

V21 used `data/pilots/release-generalization-v21` with 6,144 authored rows in
192 training families, 176 development rows, and 440 frozen evaluation rows.
The train split has SHA-256
`7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`.
English and Chinese are balanced. The 11 task kinds are balanced except for a
deliberate double-sized `lines` slice. Invalid ranges cover zero or negative,
reversed, and beyond-EOF cases with the file length visible in public context.

The run used microbatch 2, accumulation 8, learning rate 2e-6, seed 42, and
the pinned Qwen base. It initialized a fresh optimizer from the V20 adapter
SHA-256 `a15d22b2f30287a1ccc26100c4e0e552f0516c8d05a8639bbbf07ee3be2e0fda`.
The selected step-200 validation loss was `0.000010001144472248717`.

The run's sequential loader exposed all kinds and languages at every declared
checkpoint. At step 300 it had presented 4,800 unique rows, 2,400 in each
language, with no repeated presentations. This corrects the V16 exposure
failure documented in [the correctness audit](docs/TRAINING_CORRECTNESS_AUDIT.md).

## Quality interpretation

Within the authored task contract, the measured model behavior is usable:

- It returns valid tool calls for supported operations with complete arguments.
- It explicitly abstains for ambiguous, unsupported, unavailable-tool, and
  invalid-range cases.
- It preserves the execution boundary. The packaged runtime proposes an action
  and executes no generated tool. Disposable evaluator fixtures recorded zero
  unexpected filesystem changes.
- On the final Windows and CUDA measurements, prediction latency was 1.175
  seconds at p50 and 2.466 seconds at p95. These are one-machine observations,
  not service targets.

The evidence does not support claims about arbitrary repositories, arbitrary
PowerShell, POSIX environments, CPU throughput, high-concurrency serving,
router savings, cloud routing, or production traffic. A merged, quantized, or
converted artifact needs a new evaluation before release.

## Definition of done

- [x] Corrected training data passes semantic and structural audits.
- [x] Training exposure is deterministic, mixed, and recorded at each
  checkpoint.
- [x] A bounded V21 run completed with finite losses and recoverable retained
  checkpoints.
- [x] Every selectable checkpoint was evaluated on development data and the
  selected adapter was frozen before final scoring.
- [x] The exact package passes the frozen holdout and the fresh context suite.
- [x] The exact package loads and predicts in a newly provisioned environment.
- [x] Package documentation, provenance, evidence, resource measurements, and
  licensing notices are present and checksummed.
- [x] Model and checkpoint files are outside Git and within the storage budget.
- [x] Router tuning, gateway integration, and deployment remain explicitly
  deferred.

## Storage policy and retained files

The model and checkpoint budget is 5,000,000,000 bytes. The measured retained
weight and checkpoint total is 4,447,301,853 bytes. It includes the pinned base,
the V20 initializer package, the final V21 package, and exactly three V21
trainer snapshots: `step-000100`, `step-000200`, and final `checkpoint`.

Superseded selected packages V16 through V19 were pruned after their receipts
were preserved. The continuous sidecar trainer is stopped. No model weight or
checkpoint is tracked by Git; the current index contains zero files with model
weight suffixes. The separate `clean-env-v21` virtual environment is retained
for reproducibility and is dependency storage, not part of the model/checkpoint
budget. The older duplicate `clean-env-v1` environment was removed.

The detailed operator instructions and recovery notes are in
[MODEL_RELEASE_HANDOFF.md](docs/MODEL_RELEASE_HANDOFF.md). The historical data
repair rationale remains in [TRAINING_REPAIR_HANDOFF.md](docs/TRAINING_REPAIR_HANDOFF.md)
and [TRAINING_CORRECTNESS_AUDIT.md](docs/TRAINING_CORRECTNESS_AUDIT.md).

## Next work after this goal

No further training is justified by the current evidence. If a new failure is
found, create a new versioned data and evaluation contract before changing the
adapter. Keep the final package immutable as the V21 release artifact. Router
quality, hosted serving, cloud comparisons, and deployment can proceed as a
separate goal with their own acceptance evidence.
