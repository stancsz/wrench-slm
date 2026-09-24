# Wrench SLM

**Affordable AI for the rest of us.**

We want people with less than 8 GB of GPU memory to get useful AI work done
on hardware they already own, with software that is free to use. The next
hardware milestone is a useful workflow below 2 GB, with older phones as a
related target. Longer term: lend your spare compute to friends.

These are product targets. Today's implementation is a bounded developer-tool
worker; small-device compatibility, shared compute, and general paid-cost
savings are not established.

- [Developer documentation source and preview](site/README.md)
- [No-model local example](examples/local_first.py)
- [Mission and hardware roadmap](site/pages/roadmap.html)
- [Current evidence and limitations](site/pages/evidence.html)

The source repository is currently private. There is no public install release
or public license in this checkout. The getting-started instructions are for
collaborators with repository access.

Wrench is a bounded developer-tool worker for fast, repetitive, verifiable
mechanical work. It proposes structured read-only or review-only actions, or
abstains. An independent verifier and the stronger-model fallback retain final
authority. Wrench does not execute arbitrary shell commands, access
credentials, or write autonomously.

## System 1 binary classifier

**Implemented:** Wrench reuses its existing Qwen weights to classify a request
as `abstain` or `not_abstain`. One text-backbone forward feeds a compact
binary readout. Classification generates no text and skips the vocabulary
projection. The original 2,048-to-2 head has 4,098 parameters, about 16 KiB
of raw weights. Later Qwen plus text-feature readouts are 126 to 359 KB on disk.
The Qwen backbone is still required; head size is not total model size.

Our two main metrics are **decision speed** and **binary classification
accuracy**. Speed includes tokenization, the Qwen forward and the returned
decision. Accuracy counts both correct abstentions and correct continuations.

| Model / result | Decision speed | Accuracy | Measurement conditions |
| --- | --- | --- | --- |
| Wrench original head, development set | 175.45 ms median, 202.09 ms p95 | 90.9%: 40/44 correct | RTX 5070 Ti, BF16, authored development requests |
| Wrench original head, new independent set | 186.60 ms median, 219.86 ms p95 | **61.7%: 37/60 correct** | Same GPU, 30 Wrench and 30 abstain requests; 13 unsafe continuations |
| Wrench policy head, new independent set | 180.59 ms median, 210.08 ms p95 | **60.0%: 36/60 correct** | Same requests; 7 unsafe continuations |
| Wrench Qwen plus text readout, frozen 5,600-case suite | **175.86 ms median, 228.54 ms p95** | **72.39%: 4,054/5,600 correct** | RTX 5070 Ti, BF16; 1,399/5,000 false Wrench decisions and 147/600 false abstentions; generated cases |
| Corrected Qwen readout, same suite replay | **184.92 ms median, 224.48 ms p95** | **78.80%: 4,413/5,600 correct** | Regression on consumed generated suite; 1,012 false Wrench decisions and 175 false abstentions |
| Qwen layer-8 readout, same suite replay | **148.62 ms median, 185.13 ms p95** | **79.20%: 4,435/5,600 correct** | Regression on consumed generated suite; 1,040 false Wrench decisions and 125 false abstentions |
| Qwen layer-8 plus verifier-aligned preflight | **172.93 ms median, 217.31 ms p95** on 475 correct eligible decisions | **89.58% balanced**; 0/5,000 unsafe continuations, 125/600 false abstentions | Measured local hybrid on the consumed generated suite after reviewing failures; not blind or matched to Jev |
| Owner-approved 5k-trained layer-8 head, fresh authored replacement suite | **170.33 ms median, 223.15 ms p95** across 5,600 warm decisions; model forwards 187.70/237.06 ms | **98.04% overall, 96.70% balanced**; 80/5,000 unsafe continuations, 30/600 false abstentions | RTX 5070 Ti, BF16; frozen candidate, first-pass generated holdout; diagnostic target failed |
| Same head with revised abstain preflight, posthoc replay | Not remeasured | **99.46% overall, 97.50% balanced**; 0/5,000 unsafe continuations, 30/600 false abstentions | Same now-consumed suite after reviewing errors; regression only, not fresh evidence |
| Hosted Jev, TypeSafe's published launch figures | **70–500 ms end to end** | No named aggregate accuracy figure identified in that launch post | Hosted service; vendor-reported measurements |
| OpenJev, published short-text / text-suite results | **About 80 ms per short-text decision** | **84.0%: 8,403/10,000**; routing/intent/topic subset **92.8% on 1,218 questions** | One H100, FP8 serving; broad text decisions with multiple possible labels |

Sources: [Wrench measured receipt](phases/system-one-readiness-20260922/baseline/receipt.json),
[strict development rescore](phases/system-one-readiness-20260922/baseline/strict-development-rescore.json),
[independent 60-case receipt](phases/system-one-readiness-20260922/policy-v2/receipt.json),
[5,600-case receipt](phases/system-one-readiness-20260922/sparse-v1/evaluation-5k-receipt.json),
[corrected-head regression receipt](phases/system-one-readiness-20260922/sparse-v3/regression-5k-receipt.json),
[layer-8 regression receipt](phases/system-one-readiness-20260922/layer8-v1/regression-5k-receipt.json),
[measured hybrid summary](phases/system-one-readiness-20260922/preflight-v2/measured-summary.json),
[owner-approved training and replacement evaluation](phases/system-one-authorized-training-20260923/README.md),
[TypeSafe Jev launch report](https://typesafe.ai/blog/introducing-system-one-models-and-jev),
and [OpenJev model card](https://huggingface.co/openjev/openjev).
OpenJev's report also measures hosted Jev at 85.4% on its same 10,000 questions;
that is an OpenJev-authored comparison, not TypeSafe's own accuracy figure.

These published numbers provide context, **not proof of Jev parity**. Hardware,
request lengths, label counts, datasets and timing methods differ. The new
independent 60-case set exposed a large accuracy drop from the 44-case
development result. The 5,600-case run missed its predeclared accuracy and
safety target, despite warm latency within that target. Neither run establishes
equivalent speed under matched conditions.

The measured Wrench head continued on 20/24 eligible requests and correctly
abstained on 20/20 ineligible requests. An always-abstain classifier would
score 20/44 (45.5%) on this set. The two prompt formats and 88 timing samples
do not turn 44 cases into 88 independent accuracy observations.

**Readiness:** the architecture is implemented, with 126 passing focused
classifier and real-intake contract tests (71 in the earlier
[recorded run](phases/system-one-readiness-20260922/contract-tests-mlp.json)).
Learned routing stays disabled. The first full
[5,000-abstain plus 600-Wrench diagnostic suite](phases/system-one-binary-5k-20260922/README.md)
run failed with 1,399 false Wrench decisions. A later audit found incorrect
positive file-size labels in both earlier training expansions, so their
calibration numbers are superseded. The corrected head scored 78.80% on a
replay of the consumed suite. An optional explicit-boundary preflight reached
91.02% abstain recall and 70.83% Wrench coverage in a posthoc same-suite
analysis. A layer-8 readout improved same-suite balanced accuracy to 79.18%
at 148.62/185.13 ms median/p95. A later
[verifier-aligned preflight](phases/system-one-readiness-20260922/preflight-v2/README.md)
reduced false Wrench decisions to zero on the already consumed generated
suite, while the Qwen head still falsely abstained on 125/600 controls.
The measured hybrid took 172.93/217.31 ms median/p95 on correctly continued
eligible requests. Its 0.0379 ms all-request median mostly reflects fast
abstentions and must not be counted as fast Wrench completion. This was a
posthoc regression. The required eligible coverage is still missed. These
generated cases do not by themselves establish
production readiness. The owner then approved training on that original
5,000-abstain suite, retiring it as evaluation material. The fitted head
scored 98.04% overall on a fresh, authored 5,000-abstain plus 600-control
replacement, but 80 unsafe continuations failed the target. A preflight
revision catches those 80 in a **posthoc** regression; it still needs a new
untouched measurement and real workflow labels. See the
[classifier evidence](phases/system-one-readiness-20260922/README.md).
For a future fit on approved real workflow text, use the
[local redacted-request intake](phases/system-one-readiness-20260922/REAL_REQUEST_INTAKE.md).
Current trace receipts do not retain the request text needed for that fit.

## Active productive-value scope

The project is intentionally narrow. We are keeping and continuing:

1. deterministic mechanical work;
2. independent verification and the no-mutation boundary;
3. hybrid long-context intake and retrieval;
4. the bounded two-state client protocol;
5. OpenCode, DeepSeek Harness, and Claude Code support;
6. latency and timeout repair;
7. one paired real-workflow canary;
8. targeted fallback expansion based on real traces;
9. sustained operational testing;
10. the explicitly authorized Qwen System 1 binary classifier, measured by
    decision speed and accuracy.

The North Star is measured productive value against the stronger-model
baseline: final success, safety, successful-task latency, frontier-token use,
local overhead, cost, retries, corrections, abstentions, and fallback.

## Explicitly skipped

RTX 5060 Ti verification, private release packaging as a separate workstream,
learned free-form routing and LoRA optimization beyond the authorized binary
classifier, dense-native 4M attention,
stock Ollama or vLLM or GGUF adapters, synthetic replay as a primary milestone,
broad speculative tool expansion, and public production release are out of
scope unless the human product owner changes the goal.

## Current status

The deterministic worker, verifier, hybrid intake, two-state protocol, and
three named client surfaces have current local evidence. The active proof still
requires the paired real-workflow canary, latency and timeout repair, targeted
fallback selection, and sustained operational testing.

Learned routing remains disabled. This repository is an active,
evidence-gated project, not a production release.

## Source of truth

- [GOAL.md](GOAL.md): active goal and North Star
- [COLLABORATION_CONTRACT.json](COLLABORATION_CONTRACT.json): Q4 authority and
  escalation contract
- [docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md):
  active productive-value evidence contract
- [docs/evidence/README.md](docs/evidence/README.md): evidence map
- [docs/archive/2026-09-22/](docs/archive/2026-09-22/): superseded plans and
  contracts
