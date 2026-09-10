# Wrench-Pro v21 evaluation report

All results below were produced from the exact adapter in this package:
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.
The evaluator used greedy packaged inference, an explicit pinned base, and no
cloud or router requests. Fixture execution was restricted to the evaluator;
the distributed runtime executes no generated tool.

## Frozen development selection

Steps 100, 200, and 300 each scored 176/176 on the fixed development set with
all quality gates true. Step 200 was selected by the frozen rule: highest exact
rate, then lowest validation loss, then earliest step. Its validation loss was
`0.000010001144472248717`. The selection receipt is
`artifacts/model-release/selection-v21/selection.json` in the repository.

## Final V21 holdout

The package-independent V21 evaluation set scored 440/440 exact. It contained
280 routine and 160 fallback cases across 11 task kinds and 220 English plus
220 Chinese rows. Routine exact calls and actual fixture outcomes were 280/280.
Ambiguous, unsupported, missing-tool, and invalid-range cases all abstained
correctly. Raw protocol validity was 100 percent and observed filesystem
changes were zero. Latency was 1.175 seconds p50, 2.466 seconds p95, and 2.543
seconds p99. The full repository receipts are
`artifacts/model-release/v21-package-independent-evaluation/summary.json` and
`run.json`.

## Fresh context perturbation

The unused `context-release-v2b` suite scored 220/220 exact, with 140/140
routine calls and 80/80 fallback cases. All task-kind and language slices
passed, with zero filesystem changes. The suite includes reordered context,
decoy resources, quoted paths, Unicode paths, and new invalid-range wording.
Receipts are `artifacts/model-release/v21-package-context-release-v2b/summary.json`
and `run.json`.

## Package and environment checks

The package checksum verifier passed in a newly provisioned Python 3.14 virtual
environment with PyTorch 2.9.1+cu128, Transformers 4.57.1, PEFT 0.20.0,
Tokenizers 0.22.1, and Safetensors 0.6.2. It used an empty Hugging Face cache,
offline flags, the explicit base dependency, and two exact quickstart
predictions. The receipt is
`artifacts/model-release/v21-release-verifier-final2/receipt.json`. An earlier
check in the existing project environment is retained at
`artifacts/model-release/v21-clean-cuda/receipt.json`.

## Interpretation

These receipts support release of the adapter for the declared authored task
scope. They do not prove production-service reliability, router economics,
arbitrary command safety, broad language coverage, or CPU performance. The
historical V16 and V20 context failures remain preserved as diagnostic evidence
and were not used as final gates after they informed later training.
