# Wrench-Pro weight release protocol V1

Frozen before release-set model evaluation, 2026-09-09. This protocol follows
goal.md: successful training and independently validated, usable model weights.
No router request or production configuration change is needed.

## Artifact and task scope

Base: Qwen/Qwen2.5-0.5B-Instruct at revision
7ae557604adf67be50417f59c2c2f167def9a775. Train LoRA rank 16, alpha 32,
dropout 0.05 on q/k/v/o and gate/up/down projections. Preserve the original
tokenizer and the hashed wrench/dataset.py prompt formatter. Greedy decoding,
1536 input-token budget, 192 output-token budget; invalid output and budget
rejection are failures, never successful abstention.

Scope: contextual file/config reads, inclusive line ranges, literal filename
search, Git status and latest subject, local health reads, and draft-only file
writes. Inputs carry the actual schemas, resources, and prior selection state.
Include ambiguous requests, unsupported operations, unavailable tools, and
invalid ranges. English and Chinese are both evaluated. The weight package
returns a call or ROUTER_FALLBACK; it does not execute generated commands.

The concrete execution test target is Windows with Git, rg, and curl available.
Shell commands in fixtures are dispatched as argument vectors through the
allowlisted tool adapter. This does not certify arbitrary PowerShell scripts,
POSIX runtime support, Raspberry Pi performance, or production traffic coverage.

## Data and training budget

Use data/pilots/release-authoring-v1 and its SHA-256 manifest: 1,408 training
examples in 44 wording families; 176 development examples in 22 families;
440 release evaluation examples in 22 separate families. Every split includes
English and Chinese. Partition wording families before generating examples.
These are newly authored scenarios with generated fixtures, not production logs.
No old pilot evaluation task is imported. Shared fixture generators and limited
wording diversity remain limitations, even when all checks pass.

Preflight validates every target against its schema and verifies complete prompt
plus completion fits 1536 tokens. Regression tests execute representative gold
calls against real resettable file/Git/search/HTTP fixtures and reject incorrect
outcomes. No discarded row may disappear from the manifest without a new version.

First run: 400 optimizer steps, microbatch 2, accumulation 4, constant learning
rate 0.0001, seed 42, BF16 base, on the local RTX 5070 Ti. Save checkpoints and
development validation loss at steps 100, 200, 300, and 400. No cloud requests.
This is at most 3,200 example presentations. Reserve at most 60 minutes for this
run, including validation/save overhead; investigate if observed progress does
not fit that budget. Preserve a failed run and resume only from a verified local
checkpoint rather than restarting automatically.

Select among these checkpoints using development exact-call rate, then lowest
development validation loss to break ties. Compare the original pilot and
unchanged base on the same development set. If development gates fail, repair
data/training using development evidence before touching the release set. Each
additional run requires a recorded numeric budget and versioned input contract;
do not start an unlimited optimization loop.

## Model quality gates

All gates must pass on the exact artifact intended for distribution:

| Gate | Required observation |
| --- | --- |
| Raw protocol | At least 99.5% schema-valid calls or explicit model abstentions across all assigned cases. Invalid output converted to fallback does not pass. |
| Routine exact arguments | At least 95% exact tool and complete-argument matches across the 280 supported-task cases. |
| Real routine outcomes | At least 95% correct actual outcomes across those same cases. Calls run in disposable fixtures; writes remain drafts. |
| Useful coverage | At least 70% correct, usable predictions on supported tasks, counting fallback and rejection as unsuccessful. |
| Slice floor | At least 90% exact predictions in every supported task kind and each language's supported-task slice. |
| Ambiguity | At least 95% explicit correct abstention on ambiguous requests. |
| Unsupported and invalid inputs | Zero non-fallback predictions for unsupported operations, unavailable tools, and invalid ranges. Invalid output is still a protocol failure. |
| Execution boundary | Zero unexpected filesystem changes; no state-changing execution through the distributed inference example. |

Report all assigned tasks, raw outputs, rejection causes, explicit abstentions,
exact matches, execution errors, per-kind and per-language counts. Report Wilson
intervals as descriptive only and bootstrap uncertainty clustered by wording
family with seed 20260909 and 2,000 resamples. Repeated fixtures or paraphrases
do not establish independent production reliability. No post-result threshold
relaxation or task exclusion is allowed.

Keep a fresh independently authored challenge set as a second check before
release, covering context switching, distractors, escaping, long inputs, and
unsupported requests. Freeze its manifest before scored inference and apply
the same applicable gates. If scored outcomes are used to change the candidate,
retire that test to development and create a fresh test version.

## Relationship to earlier acceptance documents

Retain the 99.5% format and 95% Windows/task correctness floors; strengthen syntax
checks to actual outcomes and keep all failures in denominators. Keep the 70%
useful-coverage floor as a model-scope measurement, not a live offload claim.
Record raw and validated behavior separately. The previous 20 ms TTFT, 30 ms
full-call, 1.2 GB and 3.5 GB memory numbers are incompatible definitions and
unverified targets, so none is an advertised weight-release performance claim.
Measure actual full-call latency, startup, PyTorch allocated/reserved memory,
and system memory for the final package and publish those requirements.
Gateway shadow comparisons, service soak, 10 QPS serving, and deployment gates
remain requirements for any later claims about those systems, not weight-export
completion gates under the user's revised goal.

## Release package and clean loading

Prefer an explicitly labeled adapter with the exact base revision, or validated
standalone merged weights if conversion preserves quality. Include tokenizer,
configuration, prompt contract, checksums, pinned dependencies, minimal local
inference example, model card, provenance summary, evaluation receipts, license
and attribution. Training checkpoints with optimizer state are not the public
weight package. Verify clean loading with a fresh cache/environment using only
documented dependencies, including the base for an adapter release.

Merging/quantizing/conversion requires evaluation of the converted artifact.
WEIGHTS READY FOR RELEASE requires all model and packaging checks to pass.
A completed training run alone remains TRAINED CANDIDATE. Upload and deployment
are outside this protocol.
