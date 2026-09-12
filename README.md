# Wrench-SLM

### Let the small model handle the boring work. Keep the strong model in charge.

Wrench-SLM is an evidence-gated experiment in selective local execution for
developer tools. It proposes narrow structured actions, verifies what actually
happened, and falls back whenever the request or result is uncertain.

The current artifact, **Wrench-Pro V21**, is a LoRA adapter for
Qwen2.5-0.5B-Instruct. It is a **private release candidate**, not a production
service.

> **Current operator decision: `DISABLE`.** The local path works on a narrow
> authored evaluation, but trusted production replay and matched cloud-value
> evidence do not exist yet.

## Why Wrench exists

Most routing demos ask whether a small model can answer. Wrench asks a harder
question: **can it finish a real task safely enough that the larger model never
needs to redo the work?**

That changes the design:

- deterministic rules own rigid cases;
- a small model may propose only explicitly supported actions;
- a runtime verifier checks real tool observations, never fixture gold;
- ambiguous, failed, timed-out, or boundary-changing work falls back intact;
- rules-only and full disable are successful outcomes when learning adds no value.

## What is real today

The supported local slice is intentionally small: selected configuration reads
and bounded line reads. The runtime does not grant arbitrary shell access and
write proposals remain review-only drafts.

| Evidence | Observed result | What it does not prove |
| --- | --- | --- |
| Frozen V21 holdout | 440/440 exact authored predictions | General coding ability or production accuracy |
| Fresh authored context suite | 220/220 exact predictions | Independent generalization |
| Selective local gate | 90/600 accepted, 90/90 successful accepted completions | Production prevalence or savings |
| Boundary results | Zero accepted prohibited actions and zero unexpected mutations in the frozen gate | Safety under untested traffic |
| Operator package | `VALID_FAIL_CLOSED`, decision `DISABLE` | A production-ready route |

Latency on the V21 holdout was 1.175 seconds p50 and 2.466 seconds p95 on one
Windows workstation with an NVIDIA GeForce RTX 5070 Ti. This is full local
prediction latency in the evaluator, not hosted-service performance.

All evaluated rows above are authored scenarios or generated fixtures. Wrench
currently shows **no measured frontier-token savings** and makes no claim of
lower cost, production reliability, user adoption, or broad model advantage.

## Verify the evidence boundary

Clone the repository, create an environment with the test dependencies, then
run the tracked provider-free test suite:

```powershell
py -3 -m pip install -r requirements/dev.txt
py -3 -m pytest -q tests/test_selective_offload.py tests/test_policy.py tests/test_pilot_workflow.py tests/test_release_boundaries.py
```

This clean-clone subset currently covers 33 routing, policy, workflow, and
release-boundary tests. It does not download private weights, contact a
provider, independently replay the 600-row local-quality campaign, or establish
production value. The full suite includes tests that require ignored local
receipts and model-package manifests.

For the shortest route through the repository:

1. Read the [maturity ladder](goal.md).
2. Inspect the [active acceptance contract](goals/active/selective-offload-real-runtime-v2/GOAL.md).
3. Review the [production value scorecard](docs/PRODUCTION_VALUE_SCORECARD.md).
4. Follow the [V21 release handoff](docs/reference/MODEL_RELEASE_HANDOFF.md) if you have private artifact access.

## From toy to production

```text
M0 Toy
  -> M1 Safe prototype
  -> M2 Reproducible candidate       <- current verified boundary
  -> M3 Useful matched pilot         <- blocked on trusted data and budget
  -> M4 Production candidate
  -> M5 Production proven
```

The immediate gate is not another synthetic benchmark. It is an authorized,
deterministically redacted replay package with joinable request/context and
provider-usage records, followed by a fixed A/B/C comparison:

- cloud-only;
- deterministic rules plus fallback;
- learned proposal plus the identical fallback path.

Every arm must account for calls, prompt/completion/cached tokens, cost,
latency, retries, corrections, failures, and final outcomes. The learned route
earns enablement only if it improves on rules without making outcomes worse
than cloud-only.

## V21 artifact

| Item | Value |
| --- | --- |
| Form | PEFT LoRA adapter |
| Base | `Qwen/Qwen2.5-0.5B-Instruct` |
| Base revision | `7ae557604adf67be50417f59c2c2f167def9a775` |
| Selected checkpoint | Step 200 of 300 |
| Training | Supervised LoRA, initialized from V20 with a fresh optimizer |
| Evaluated languages | English and Chinese |
| Adapter size | 35,237,104 bytes |
| Adapter SHA-256 | `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348` |
| Distribution | Private candidate at [stancsz/wrench-pro-v21](https://huggingface.co/stancsz/wrench-pro-v21) |

The adapter requires the pinned base model plus Wrench input formatting and
output validation. It is not standalone weights. Authorized users can follow
[Training from a clone](docs/reference/TRAINING_FROM_CLONE.md) and the
[release asset catalog](releases/v21/README.md). Hardware beyond the recorded
Windows/RTX 5070 Ti environment, including CPU operation, is not qualified.
Downloading the private artifact requires an authorized account.

## Repository map

```text
wrench/          Training, inference, validation, and experimental runtime code
scripts/         Reproducible build, evaluation, readiness, and evidence gates
tests/           Unit and integration tests
data/            Frozen release inputs and separated legacy data
releases/v21/    Release cards, checksums, and evidence snapshots
docs/            Product, architecture, operations, audit, and website material
goals/active/    The single active engineering contract
artifacts/       Ignored local weights, packages, and run receipts
```

Durable boundaries live in [NORTHSTAR.md](NORTHSTAR.md) and
[ARCHITECTURE.md](ARCHITECTURE.md). Historical plans are preserved in the
[documentation archive](docs/reference/archive/), not mixed into the
current execution path. The [marketing review](docs/MARKETING_REVIEW.md) records
the audience, funnel diagnosis, launch dependencies, measurement baseline, and
claim boundaries.

## Contributing

The most useful contributions tighten evidence or reduce operator friction:
independently authored evaluation cases, clean-install reproduction, safe
service boundaries, receipt verification, and documentation fixes. Do not open
an issue containing private prompts, credentials, proprietary traces, or raw
customer data.

Look for issues labeled `good first issue`, `help wanted`, `evidence`, or
`production-gate`. A green local test is useful, but it does not close a
production milestone unless the active goal names it as exit evidence.

## License and attribution

The private adapter snapshot carries Apache-2.0 terms and Wrench attribution.
Redistributed Qwen tokenizer files retain their upstream license and Alibaba
Cloud attribution. The base model is a separate dependency. Authorized users
should inspect the model repository notices before redistribution.
