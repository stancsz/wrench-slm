# Wrench-Pro v21 model-weight release handoff

Updated: 2026-09-10
Decision: **WEIGHTS READY FOR RELEASE** within the declared local adapter
scope. The router, hosted serving, gateway integration, and deployment are
separate future work.

This document is the operator handoff for the exact release artifact. It
records what passed, how to load it, what remains outside the evidence, and
which files can be removed without losing reproducibility.

## Start here

The release package is
`artifacts/model-release/package-selected-v21`. Keep this directory immutable
after distribution. Its `release_manifest.json` status is
`WEIGHTS READY FOR RELEASE`, and its manifest SHA-256 is
`219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`.

The adapter SHA-256 is
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.
It requires `Qwen/Qwen2.5-0.5B-Instruct` at revision
`7ae557604adf67be50417f59c2c2f167def9a775`, with base weight SHA-256
`fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.

Read the package cards before relying on it:

- [MODEL_CARD.md](../../artifacts/model-release/package-selected-v21/MODEL_CARD.md)
- [DATA_CARD.md](../../artifacts/model-release/package-selected-v21/DATA_CARD.md)
- [EVALUATION_REPORT.md](../../artifacts/model-release/package-selected-v21/EVALUATION_REPORT.md)
- [LINEAGE.md](../../artifacts/model-release/package-selected-v21/LINEAGE.md)
- [RESOURCE_REPORT.md](../../artifacts/model-release/package-selected-v21/RESOURCE_REPORT.md)

## What the weights do

The package maps a prompt plus supplied Windows and PowerShell context to a
validated JSON action. The evaluated scope includes configuration and file
reads, inclusive line ranges, literal filename search, Git status, the latest
Git subject, local health reads, and review-only draft writes. It abstains on
ambiguous requests, unsupported operations, unavailable tools, and invalid
line ranges.

The distributed runtime proposes an action and executes no generated tool. The
repository evaluator can execute allowlisted calls in disposable fixtures to
check real outcomes. This boundary is part of the quality result.

## Evidence that supports the decision

### Training and data

V21 used 6,144 authored training rows in 192 families. The train SHA-256 is
`7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`. The
development split has 176 rows and the final evaluation split has 440 rows.
English and Chinese are balanced. Semantic audits reported zero errors and
zero warnings for train, development, and evaluation. Preflight passed the
1,536 input and 192 completion token budgets.

The run completed 300 optimizer steps and 4,800 example presentations with
microbatch 2, accumulation 8, learning rate 2e-6, seed 42, and a reset
optimizer initialized from the V20 adapter. The complete receipt is
`artifacts/model-release/pro-training-v21/run.json`.

The exposure audit records every task kind and both languages at steps 100,
200, and 300. At step 300 it records 4,800 unique rows, 2,400 English and
2,400 Chinese presentations, with no repeated rows. This verifies that the
run did not spend its checkpoints on a grouped prefix of one task kind.

### Selection

Steps 100, 200, and 300 each scored 176/176 on the fixed development set with
all gates true. Step 200 was selected by the frozen rule: highest exact rate,
then lowest validation loss, then earliest step. Its validation loss was
`0.000010001144472248717`. The selection receipt is
`artifacts/model-release/selection-v21/selection.json`.

### Frozen final evaluation

The exact packaged adapter scored 440/440 on the unused V21 evaluation set.
The denominator contains 280 routine cases and 160 fallback cases across 11
task kinds, with 220 English and 220 Chinese rows. Routine exact calls and
actual disposable-fixture outcomes were both 280/280. All ambiguity,
unsupported, missing-tool, and invalid-range cases abstained correctly. Raw
protocol validity was 100 percent and observed filesystem changes were zero.

The complete receipts are:

- `artifacts/model-release/v21-package-independent-evaluation/summary.json`
- `artifacts/model-release/v21-package-independent-evaluation/run.json`

### Fresh context perturbation

After freezing V21, a new `context-release-v2b` suite was authored with fresh
identities and wording. It contains 220 rows in 44 families, including
reordered tools, resources, and prior results, decoy resources, quoted and
Unicode paths, and new invalid-range wording. It scored 220/220 exact, with
140/140 routine and 80/80 fallback cases. Its semantic audit, preflight, and
executable gold checks passed before model inference. Receipts are:

- `artifacts/model-release/v21-package-context-release-v2b/summary.json`
- `artifacts/model-release/v21-package-context-release-v2b/run.json`

The older V20 context suite remains under
`artifacts/model-release/v20-package-context-release-v1` as diagnostic history.
It exposed the invalid-range wording defect that motivated V21 and must not be
treated as an independent final gate.

### Clean package loading

The final checksum verifier passed in the newly provisioned
`artifacts/model-release/clean-env-v21` Python 3.14 virtual environment. It
installed PyTorch 2.9.1+cu128, Transformers 4.57.1, PEFT 0.20.0, Tokenizers
0.22.1, and Safetensors 0.6.2. It used an empty Hugging Face cache, offline
flags, the explicit base copy, and two exact quickstart predictions. The final
receipt is `artifacts/model-release/v21-release-verifier-final3/receipt.json`.

Across the two final verification runs, package load was 2.4463 to 2.5089
seconds, first prediction was 1.8946 to 2.0909 seconds, and warm prediction
was 1.3854 to 1.4741 seconds. Peak CUDA allocation was 1,076,785,152 bytes and
reserved memory was 1,153,433,600 bytes. Sampled process-tree RSS was
1,858,539,520 to 1,890,676,736 bytes. The process-tree value sums launcher and
descendant RSS samples and may count shared pages more than once.

## Reproduce the quickstart

The package is an adapter, so fetch or copy the exact pinned base first. The
repository copy is `artifacts/model-release/base-dependency-v1`.

```powershell
Set-Location C:\path\to\wrench-slm
py -3.14 -m venv .release-env
.release-env\Scripts\python.exe -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
.release-env\Scripts\python.exe -m pip install -r artifacts/model-release/package-selected-v21/requirements.txt
Set-Location artifacts/model-release/package-selected-v21
..\..\..\.release-env\Scripts\python.exe -B inference.py --input example.json --device cuda --base-path ..\base-dependency-v1
```

The relative command assumes the environment was created at the repository
root. From another directory, pass absolute paths. The runtime verifies the
package checksum, tokenizer contract, vocabulary, and base weight hash before
loading. Use `--local-files-only` when the base is already available locally.

CPU mode can be selected with `--device cpu`, but no CPU performance claim is
part of this release. The command prints a prediction record and never runs a
tool.

## Retention and recovery

The model and checkpoint budget is 5,000,000,000 bytes. The measured retained
weight and checkpoint total is 4,447,301,853 bytes. Keep these paths:

1. `artifacts/model-release/base-dependency-v1` for the pinned base.
2. `artifacts/model-release/package-selected-v20` as the recorded V21
   initializer and rollback reference.
3. `artifacts/model-release/package-selected-v21` as the immutable release.
4. `artifacts/model-release/pro-training-v21/step-000100`.
5. `artifacts/model-release/pro-training-v21/step-000200`.
6. `artifacts/model-release/pro-training-v21/checkpoint` as the final step-300
   snapshot.

The active trainer retains exactly three snapshots. They include optimizer
state for local recovery. Superseded selected packages V16 through V19 were
deleted only after their receipts and summaries were preserved. The older
duplicate clean environment was removed; `clean-env-v21` remains because it is
the environment used by the final verification receipt. The continuous native
sidecar trainer is stopped.

If another training run is proposed, do not reuse V21 final evaluation rows for
correction. Author a new versioned training contract, run semantic and
exposure audits, freeze a new holdout, and select a new package. Preserve V21
as the comparison artifact. Do not delete the only pinned base, final package,
or recoverable active checkpoint.

## Licensing and provenance

`LICENSE-QWEN` is the verified upstream Apache-2.0 license for the pinned base
and tokenizer, with SHA-256
`832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`. The
package includes the same full license as `LICENSE` and records Alibaba Cloud
attribution in `NOTICE`. `LICENSE-WRENCH` identifies the Wrench adapter,
runtime, and documentation as Apache-2.0 under the project contributors.
Check the project ownership and any downstream data obligations before a public
redistribution. The package contains no production or private fixture data.

The complete source chain is recorded in `LINEAGE.md`, including the base
revision, formatter hash, V20 initializer, V21 run, selected checkpoint,
adapter hash, data manifests, and evaluation receipts.

## Claims and boundaries

The evidence supports a local adapter release for the authored Wrench-Pro
scope. It does not establish arbitrary shell safety, POSIX behavior, CPU
throughput, high-concurrency serving, router savings, cloud failover, gateway
behavior, hosted-service uptime, or clinical use. Do not advertise those
claims from these receipts. A merged, quantized, converted, or otherwise
modified artifact requires a new checksum manifest and the complete quality
evaluation before distribution.

## If the package fails later

Keep the failed output and the exact input manifest. Check, in order:

1. The base file hash against `release_manifest.json`.
2. The package checksum manifest and tokenizer contract.
3. The documented dependency versions and Python architecture.
4. CUDA availability and device selection.
5. The model and runtime source hashes in the evidence receipts.

Do not repair a failed result by changing a frozen evaluation label, lowering a
threshold, or adding failed holdout rows to training. Open a new versioned
correction and retire the affected evaluation from release decisions.
