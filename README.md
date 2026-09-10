# Wrench-SLM

Wrench-SLM trains small models to propose structured tool calls for routine developer tasks. The current artifact is **Wrench-Pro V21**, a LoRA adapter for Qwen2.5-0.5B-Instruct.

V21 completed training and passed its authored evaluation suites. The current priority is model correctness and usable weights. Router integration, hosted serving, and measurements of cloud cost savings remain future work.

## What V21 does

Given a request and supplied Windows/PowerShell context, V21 predicts a JSON tool call or `ROUTER_FALLBACK`. The context includes available tool schemas and relevant resources or prior results.

The evaluated tasks cover:

- Configuration and file reads, including inclusive line ranges.
- Literal text search that returns matching filenames.
- Git status and the latest commit subject.
- Local health endpoint reads.
- File-write proposals for review.
- Abstention for ambiguous requests, unsupported operations, missing tools, and invalid line ranges.

The inference runtime returns a proposal and validation result. It does not execute the generated tool call. The evaluator separately checks permitted actions in disposable fixtures; write proposals remain drafts.

This is a narrow tool-call model. These results do not establish general coding ability, arbitrary shell reliability, or safe autonomous execution.

## Current release

| Item | V21 |
| --- | --- |
| Artifact | PEFT LoRA adapter |
| Base model | Qwen/Qwen2.5-0.5B-Instruct |
| Required base revision | `7ae557604adf67be50417f59c2c2f167def9a775` |
| Selected checkpoint | Step 200 of the 300-step V21 run |
| Training method | Supervised LoRA fine-tuning, initialized from V20 with a fresh optimizer |
| Languages evaluated | English and Chinese |
| Evaluated token budgets | 1,536 input tokens and 192 generated tokens |
| Distribution | [Hugging Face: stancsz/wrench-pro-v21](https://huggingface.co/stancsz/wrench-pro-v21) |

The adapter requires the pinned base model. Git contains source and documentation; weights are stored separately on Hugging Face. The Hugging Face repository was published privately, so access requires an authorized account.

The adapter file is 35,237,104 bytes. Its SHA-256 is:

```text
6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348
```

## What was measured

These results come from the frozen V21 package evaluation and the subsequent context suite recorded on September 10, 2026.

| Evaluation | Observed result |
| --- | --- |
| Frozen holdout | 440/440 exact predictions |
| Holdout routine cases | 280/280 exact, with fixture outcomes checked |
| Holdout fallback cases | 160/160 correct abstentions |
| Fresh context suite | 220/220 exact: 140 routine and 80 fallback |
| Unexpected fixture filesystem changes | Zero |
| Clean package load | Passed with the pinned base and dependencies in a fresh environment |
| Holdout prediction latency | 1.175 seconds p50; 2.466 seconds p95 |

Latency was measured on one Windows machine with an NVIDIA GeForce RTX 5070 Ti. It is full prediction latency in the evaluator, not time to first token or a hosted-service guarantee.

Both suites contain authored scenarios with generated fixtures. Their perfect scores show success on those specific cases, not universal accuracy or proven generalization to production traffic. The context suite varies wording, paths, resource identities, and context ordering, but remains within the authored task contract.

See the [release handoff](docs/reference/MODEL_RELEASE_HANDOFF.md) for receipt locations, selection rules, environment details, and limitations. The [training correctness audit](docs/reference/TRAINING_CORRECTNESS_AUDIT.md) documents earlier defects and their repairs.

## Download and use

Authenticate with a Hugging Face account that has access, then download the published adapter snapshot:

```powershell
python -m pip install huggingface_hub
hf auth login
hf download stancsz/wrench-pro-v21 --revision 0c77f1520091d30ed0613319a307cdbbed247320 --local-dir artifacts/model-release/hf-v21
```

The model Hub snapshot contains the adapter, tokenizer, training metadata, model README, and licenses. Full inference packages, the V20 initializer, source snapshots, and historical authored assets are available separately through the [release asset catalog](releases/v21/README.md). See [Training from a clone](docs/reference/TRAINING_FROM_CLONE.md) for setup, downloads, audits, training, evaluation, and export.

There are two ways to work with the release:

- **Load the adapter with PEFT.** Follow the model README on Hugging Face and use the exact base revision above. Loading weights alone does not apply Wrench's input formatting or output validation. Those are implemented in [the dataset formatter](wrench/dataset.py) and [the prediction runtime](wrench/pilot_inference.py).
- **Use the complete verified local package.** Operators who have `artifacts/model-release/package-selected-v21` can follow the [handoff quickstart](docs/reference/MODEL_RELEASE_HANDOFF.md#reproduce-the-quickstart). That package includes an example input, runtime, dependency pins, and checksum manifest. Restore it with `python scripts/fetch_assets.py --asset package-v21` after authenticating to the private asset repository.

The verified package environment used Python 3.14, PyTorch 2.9.1+cu128, Transformers 4.57.1, PEFT 0.20.0, Tokenizers 0.22.1, and Safetensors 0.6.2. CPU performance and other hardware configurations have not been qualified by these release results.

## Training and reproduction

V21 used 6,144 authored training rows in 192 wording families, 176 development rows, and a frozen 440-row evaluation set. Training used rank-16 LoRA, microbatch 2, gradient accumulation 8, learning rate `2e-6`, and seed 42.

The run completed 300 optimizer steps and presented 4,800 unique training rows. Checkpoints at steps 100, 200, and 300 each scored 176/176 on development. Step 200 was selected by the declared rule: highest exact rate, then lowest validation loss, then earliest step.

V21 uses authored supervised examples. Earlier teacher-data experiments and experimental reinforcement-learning code are separate from this release's training recipe.

For reproduction and later work:

- [Release handoff](docs/reference/MODEL_RELEASE_HANDOFF.md): exact artifact, dependencies, evidence, and recovery instructions.
- [Release progress](docs/reference/MODEL_RELEASE_PROGRESS.md): recorded V21 results.
- [Training next steps](docs/reference/MODEL_TRAINING_NEXT_STEPS.md): earlier operator plan; consult the current handoff before executing it.
- [Training repair handoff](docs/reference/TRAINING_REPAIR_HANDOFF.md): data and training corrections.
- [Current goal](goal.md): completed weight-release scope and deferred work.

Small release receipts and cards are included under `releases/v21/`. The checksummed asset catalog supplies the full packages, V20 initializer and historical source/evidence. Historical handoffs preserve original paths; `releases/v21/path-map.json` records relocated data.

## What remains future work

Wrench-Flash is a proposed smaller CPU/edge model tier. This release provides no validated Flash checkpoint or Raspberry Pi benchmark.

The repository also contains experimental policy, grammar, workflow, and training code. Their presence does not mean they are enabled in V21. In particular, the packaged Pro runtime generates tokens and validates the output afterward; it does not use grammar-constrained decoding to guarantee correctness.

Future work may include quantization, constrained generation, broader independent evaluation, serving, and router integration. Token-level speculative decoding and multi-token prediction are research directions. No measured acceptance rate, throughput gain, cloud token reduction, or end-to-end speedup is claimed for them here.

The [engineering techniques assessment](docs/reference/AI_ENGINEERING_TECHNIQUES.md) records implementation coverage and possible extensions. Historical architecture documents may contain older targets; use the current release evidence when describing V21.

## Repository layout

```text
wrench/          Model, training, inference, validation, and experimental runtime code
scripts/         Data preparation, training, evaluation, and packaging entry points
tests/           Repository tests
data/            Frozen release inputs and a clearly separated legacy baseline
releases/v21/    Cards, evidence, checksums and downloadable asset catalog
requirements/    Training and test dependencies
examples/        Historical integrations
docs/
  index.html     Static website overview
  status.html    Static release-status page
  assets/        Website assets
  reference/     Specifications, audits, training instructions, and handoffs
    archive/     Historical documentation
artifacts/       Ignored local weights, checkpoints, packages, and receipts
```

The website files are directly in `docs/`. Project reference documentation lives in `docs/reference/`. See the [directory guide](docs/README.md) for website maintenance.

Model and checkpoint storage has a 5 GB budget. The retention policy keeps the selected release, its initializer, the pinned base, and three V21 trainer snapshots. See the handoff for exact retained paths; historical storage measurements should not be treated as a live disk-usage report.

## Licensing

The published adapter includes Apache-2.0 license terms and Wrench attribution. Redistributed Qwen tokenizer files retain the upstream license and Alibaba Cloud attribution. The base model is a separate dependency. Consult the licenses and notices in the [model repository](https://huggingface.co/stancsz/wrench-pro-v21/tree/main) before redistribution.
