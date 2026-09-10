# Wrench-Pro model release progress

Updated: 2026-09-10
State: **WEIGHTS READY FOR RELEASE** for the declared adapter scope.

## Current release

V21 is the selected release artifact at
`artifacts/model-release/package-selected-v21`. Its adapter SHA-256 is
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348` and its
manifest SHA-256 is
`219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`.
The package status is `WEIGHTS READY FOR RELEASE`.

The model is a LoRA adapter for
`Qwen/Qwen2.5-0.5B-Instruct` at revision
`7ae557604adf67be50417f59c2c2f167def9a775`. It supports the narrow Wrench-Pro
contract: contextual file and configuration reads, inclusive line ranges,
literal filename search, Git status and latest subject, local health reads,
draft-only writes, and explicit abstention for ambiguous, unsupported,
unavailable-tool, and invalid-range requests. Its runtime proposes a JSON
action and executes no tool.

## V21 training receipt

V21 used 6,144 authored training rows in 192 families, with 176 development
rows and 440 frozen evaluation rows. Train data SHA-256 is
`7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`.
Semantic audits reported zero errors and zero warnings for all three splits.
Preflight passed the 1,536 input and 192 completion budgets. The deterministic
round-robin stream exposed every task kind and both languages at steps 100, 200,
and 300. The step-300 exposure receipt records 4,800 unique rows and 2,400
examples in each language.

The run completed 300 optimizer steps and 4,800 example presentations with
microbatch 2, accumulation 8, learning rate 2e-6, seed 42, and an optimizer
reset from the V20 adapter. Training and validation losses were finite. All
three declared checkpoints scored 176/176 on development; step 200 was selected
by highest exact rate, lowest validation loss, and earliest step.

## Final quality evidence

The frozen V21 package evaluation scored 440/440 exact. It includes 280 routine
cases and 160 fallback cases, 11 task kinds, and 220 English plus 220 Chinese
rows. Every fixed gate passed: raw protocol, routine exact calls, actual routine
outcomes, useful coverage, task and language slice floors, ambiguity,
unsupported and invalid fallback, and zero filesystem changes.

The fresh `context-release-v2b` suite was authored after the package was frozen
and scored 220/220 exact. It covers reordered tools, resources, and prior
results, decoy resources, quoted and Unicode paths, and new invalid-range
wording. Its routine slice is 140/140 and its fallback slice is 80/80.

The final package verifier passed in a newly provisioned Python 3.14 virtual
environment with PyTorch 2.9.1+cu128, Transformers 4.57.1, PEFT 0.20.0,
Tokenizers 0.22.1, and Safetensors 0.6.2. The verifier used an empty model
cache, offline flags, the explicit base copy, and two exact quickstart
predictions. The final receipt is
`artifacts/model-release/v21-release-verifier-final3/receipt.json`.

Observed packaged evaluation latency on an NVIDIA GeForce RTX 5070 Ti was
1.175 seconds p50 and 2.466 seconds p95. Peak CUDA allocation was
1,076,785,152 bytes and sampled process-tree RSS was 1,858,539,520 bytes in the
final verification. These are measurements for this authored evaluator, not
service objectives.

## Storage and Git state

The retained model and checkpoint bytes total 4,447,301,853, below the
5,000,000,000-byte budget. Retained weight-bearing paths are:

- `base-dependency-v1/model.safetensors`;
- `package-selected-v20` as the recorded V21 initializer;
- `package-selected-v21` as the release package;
- `pro-training-v21/step-000100`;
- `pro-training-v21/step-000200`;
- `pro-training-v21/checkpoint` as the final step-300 snapshot.

The V21 trainer therefore retains exactly three snapshots. Superseded selected
packages V16 through V19 were deleted after their small receipts and evaluation
records were preserved. The duplicate `clean-env-v1` environment was removed;
`clean-env-v21` remains for reproducible verification and is dependency storage,
not model or checkpoint bytes. The sidecar trainer is stopped. `git ls-files`
reports zero tracked files with model-weight suffixes.

## Earlier work

V16 exposed severe semantic and sequential-loader defects. V17 through V20
repaired public-input visibility, mixed exposure, and Chinese invalid-range
wording. Their receipts remain under `artifacts/model-release` as diagnostic
history. Any evaluation that informed a correction was retired from final
release decisions. The full rationale is in
[TRAINING_CORRECTNESS_AUDIT.md](TRAINING_CORRECTNESS_AUDIT.md).

## Boundaries after release

The package is ready for distribution as a local adapter within this declared
scope. It is not evidence for router savings, gateway behavior, hosted-service
uptime, high-concurrency serving, arbitrary shell safety, broad language
coverage, CPU performance, or clinical use. Keep those questions in separate
goals with separate measurements. Do not alter the V21 package after release;
any changed, merged, quantized, or converted artifact requires a new manifest
and complete evaluation.
