# System 1 classifier: speed and accuracy

The user confirmed binary abstention comparison with OpenJev, then clarified
that the main metrics are **speed** and **accuracy**, compared with Jev's
published metrics. The README now states that this System 1 classifier is
implemented, and reports the measured result separately from the next candidate.

## Measured baseline

The baseline from the shared checkout is pinned by
`baseline-head.json` (SHA256
`e33e28af544be5eaf156ff42dbe47d2098a36939bb4b0cfd0222d378d4ee3b0b`).
Its raw training receipt, saved decisions and strict accounting rescore are
copied under `baseline/`.

| Measure | Result |
| --- | ---: |
| Binary accuracy | 40/44, 90.9% |
| Correct `not_abstain` | 20/24 eligible requests |
| Correct `abstain` | 20/20 ineligible requests |
| Timing samples | 88 across two formats of the same 44 cases |
| Warm p50 / p95 / max | 175.45 / 202.09 / 227.49 ms |
| Device and precision | RTX 5070 Ti, BF16 |
| Head parameters / raw bytes | 4,098 / 16,392 |
| Full backbone parameter bytes | 7,762,488,032 |

This benchmark contains authored development examples and is not a sealed
production workload. The always-abstain baseline gets 45.5% accuracy and no
eligible continuations. Always-continue gets 54.5% and all 20 ineligible
requests wrong. Report the confusion counts alongside accuracy.

## Published comparisons

`published-metrics.json` records the publisher, URL, date and measurement scope.

- [TypeSafe's Jev launch report](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
  gives 70–500 ms end-to-end response time. No aggregate named-dataset accuracy
  figure was identified in that source.
- The [OpenJev model card](https://huggingface.co/openjev/openjev) reports about
  80 ms per short-text decision on one H100 with FP8 serving, 84.0% on 10,000
  text questions, and 92.8% on its 1,218-question intent/routing/topic subset.
  Its same-suite measurement of hosted Jev is 85.4%. Of the 10,000 questions,
  6,922 were fresh and 3,078 had previously been used in development.

These are published context, not a same-workload parity result. A larger
accuracy percentage on a smaller binary dataset does not establish superiority.
Local CUDA latency cannot be treated as hosted end-to-end latency. No Jev
accuracy or speed parity claim is made.

## Further implementation and verification

The next candidate adds a versioned, hash-bound classification policy before
Qwen encoding. It preserves the entire supplied request as data and retains
one forward pass with the same small binary head. The new artifact type is
bound to BF16, unquantized inference. Legacy head loading remains supported.

Following the user's metric clarification, the new candidate uses a fixed
0.5 binary argmax instead of a threshold selected to force every calibration
negative to abstain. This decision was recorded before opening the new
independent evaluation. Calibration accuracy is reported, not used to tune on
evaluation labels.

A separate reviewer authored 60 new cases, 30 per label, under 55 groups:
`evaluation.jsonl`, SHA256
`96c08a6fe3e2284c0bb55e4454d0b504675a0a50f2ddc859ced5c6b06503c622`.
The cases were opened only after the policy head was frozen. Assumptions are
in `evaluation-label-assumptions.md`. They are authored diagnostic data, not
real workflow evidence. `contrast-training.jsonl` contains 118 separately
authored training examples. Eight Git-status contrasts address an eligible
request failure in the earlier development receipt. They were added before
the new head was trained or the independent set was opened.

**90 focused CPU contract tests passed** in the latest local run. The earlier
71-test result is recorded in `contract-tests-mlp.json`.
They use tiny fake Qwen objects and cover one forward, zero generation and
vocabulary projection, binary decision math, bounds, full-input preservation,
artifact identity and checksums, BF16/policy binding, fail-closed behavior,
pre-execution rejection, independent verifier authority, and receipt retention.
They do not establish learned quality or GPU performance.

The first new training attempt stopped before model loading: an unrelated
`evaluate_hf_wrench.py` process was using the GPU, leaving about 6.6 GiB free.
Loading another BF16 model plus activation headroom would breach the 10% VRAM
reserve. No unrelated process was stopped. The failed run's receipt is
preserved as `resource-blocked-receipt.json`. After that job ended, a second
run produced the policy head and scored the fresh 60-case set. Its held-out
calibration accuracy was 79%; independent accuracy was **36/60 (60.0%)**,
with **7/30 unsafe continuations** and **13/30 eligible continuations**.
Median/p95 decision latency was **180.59/210.08 ms**. The older head scored
**37/60 (61.7%)**, with **13/30 unsafe continuations**, at **186.60/219.86 ms**.
The [run receipt](policy-v2/receipt.json), [predictions](policy-v2/candidate-predictions.json)
and [failed head artifact](policy-v2/qwen-abstain-head.json) are preserved.

The owner next requested at least 5,000 realistic abstain tests and further
training if quality is insufficient. The new [5,600-case binary suite](../system-one-binary-5k-20260922/README.md)
contains 5,000 abstain requests and 600 Wrench controls. It is generated from
authored patterns and tracked repository paths, with zero exact prompt overlap
against the expanded unsealed training set. A later audit found at least 72
incorrect positive file-size labels in that expansion. The MLP's 77.4% and
first sparse head's 90.0% calibration figures are therefore **superseded**.
The first sparse head was a 172 KB artifact over the existing Qwen backbone.
The first frozen 5,600-case run with
that head scored **72.39% overall / 73.76% balanced accuracy**, with
**1,399/5,000 false Wrench decisions**, **147/600 false abstentions**, and
zero runtime errors. Warm p50/p95 latency was **175.86/228.54 ms** on an
RTX 5070 Ti. The fixed diagnostic target failed. The full
[receipt](sparse-v1/evaluation-5k-receipt.json)
contains category counts and intervals.

After that first run, an 806-row contrast set was built with zero exact
overlap. Its first two versions contained incorrect positive labels because
several read caps were smaller than the referenced files. The resulting
second Qwen head's 88.78% calibration number is **superseded and not usable as
quality evidence**. The corrected [v3 training set](../system-one-policy-contrasts-v3-20260922/README.md)
passed a structural file and bounds audit. The 5,600-case suite is now
consumed: any replay with a later head is a regression diagnostic, not a
blind evaluation.

The corrected 126 KB head scored **187/196 (95.41%)** on separate
template-held-out calibration, with eight unsafe passes. The optional
abstain-only preflight caught those eight without rejecting a held-out Wrench
control, giving **195/196 (99.49%)** on that internal split. On the consumed
5,600-case suite, the corrected model scored **78.80% overall / 75.30%
balanced**, with **1,012 false Wrench decisions**, **175 false abstentions**,
zero runtime errors and **184.92/224.48 ms** warm p50/p95 on RTX 5070 Ti.
The [regression receipt](sparse-v3/regression-5k-receipt.json) and
[calibration receipt](sparse-v3/calibration-verified.json) are pinned. A
posthoc preflight overlay reduced false Wrench decisions to 449 while leaving
175 false abstentions, for **91.02% abstain recall / 70.83% Wrench coverage**.
That [posthoc receipt](sparse-v3/preflight-posthoc.json) is not a blind test or
a measured end-to-end hybrid latency result. Both versions fail the diagnostic
target, and production routing remains disabled.

An intermediate-layer probe compared Qwen layers 8, 16, 24, 32, and 40 on
the same unsealed held-out groups. Layer 8 scored **195/196**, with zero unsafe
passes; its [selection record](layer8-v1/layer-selection.json) and 126 KB
[artifact](layer8-v1/qwen-abstain-head.json) are pinned. On the consumed
5,600-case suite, it scored **79.20% overall / 79.18% balanced**, with
**1,040 false Wrench decisions** and **125 false abstentions**. Warm p50/p95
was **148.62/185.13 ms**, with zero runtime errors. The optional preflight
overlay had **469 false Wrench decisions**, **125 false abstentions**, and
**84.89% balanced accuracy** in a posthoc analysis. The
192 recorded resource checks kept at least 24.41 GiB RAM and 6,635 MiB VRAM
free. The
[regression receipt](layer8-v1/regression-5k-receipt.json) and
[overlay receipt](layer8-v1/preflight-posthoc.json) are reproducible evidence,
not an independent parity or production pass. The large calibration-to-suite
drop shows that further tuning on these authored templates would be weak
evidence; real labeled Wrench requests are needed for the next training cycle.

The retained Wrench traces contain request hashes, lengths and outcomes but
no raw request text. The [local real-request intake](REAL_REQUEST_INTAKE.md)
defines an ignored, redacted, workflow-separated dataset path for a future
fit. It does not supply real requests or change the failed readiness status.

The later [verifier-aligned abstain preflight](preflight-v2/README.md) reached
zero false Wrench decisions on the already consumed 5,600-case suite but
left **125/600 false abstentions**. This is a posthoc regression after
reviewing suite errors. A later full measured replay took **172.93/217.31 ms**
median/p95 for correctly continued eligible decisions, with zero runtime
errors and both host resource reserves maintained. The 0.0379 ms all-request
median is dominated by fast abstentions and does not represent useful Wrench
completion speed. There is no new blind result. Production routing remains
disabled.

## Owner-approved training on the 5,000-case suite

The owner explicitly approved using "the 5000 ones" for training. That
original authored suite is retired as evaluation material for new heads.
The [training receipt and frozen head](../system-one-authorized-training-20260923/README.md)
record a 6,528-row fit using its 5,600 cases plus 928 corrected legacy rows.
A separately frozen, authored replacement suite contains another 5,000
abstain cases and 600 controls. On its first pass, the trained head with
preflight scored 98.40% abstain recall and 95.00% eligible coverage, with
80 unsafe continuations and 30 false abstentions. Complete warm median/p95
decision latency was 170.33/223.15 ms on RTX 5070 Ti BF16. The predeclared
diagnostic target failed.

After reviewing those errors, a stricter abstain-only preflight reduced
unsafe continuations to zero in a **posthoc** regression of the same suite.
This is not independent validation, and latency after that revision was not
remeasured. The suite is synthetic, with human label review pending.
Production routing and Jev parity remain unproven.

## Status

| Claim | Evidence / status |
| --- | --- |
| System 1 binary architecture implemented | Yes, existing Qwen plus trained two-output head |
| Local baseline speed and accuracy measured | Yes, bounded 44-case result above |
| Focused implementation contracts | 90 passed, CPU fixtures |
| Policy-aware candidate trained | Yes; 79% calibration accuracy |
| New independent 60-case accuracy | 36/60 candidate, 37/60 original; both failed |
| 5,000 abstain tests | 5,000 plus 600 controls scored once; fixed diagnostic target failed |
| Expanded MLP fit | Calibration superseded due to incorrect training labels |
| Qwen plus char TF-IDF readout | First full suite: 72.0% abstain recall, 75.5% Wrench coverage, 1,399 unsafe passes |
| Second Qwen plus sparse readout | Superseded due to invalid positive training labels |
| Corrected Qwen readout | Same-suite regression: 79.76% abstain recall, 70.83% Wrench coverage |
| Corrected readout plus preflight | Posthoc same-suite: 91.02% abstain recall, 70.83% Wrench coverage; fails target |
| Layer-8 readout | Same-suite regression: 79.20% overall, 79.18% balanced, 148.62/185.13 ms p50/p95 |
| Layer-8 plus preflight | Posthoc same-suite: 84.89% balanced, 469 false Wrench decisions; fails target |
| Later verifier-aligned preflight | Posthoc same-suite: 89.58% balanced, zero false Wrench decisions, 125 false abstentions; still fails eligible coverage |
| Measured hybrid decision speed | 172.93/217.31 ms median/p95 on 475 correct eligible decisions, RTX 5070 Ti BF16; same consumed suite |
| Approved 5k training and replacement first pass | 6,528 training rows; 98.04% overall on fresh authored replacement, but 80/5,000 unsafe continuations; target failed |
| Revised preflight | Zero unsafe continuations and 30/600 false abstentions on consumed replacement suite; posthoc regression only |
| Published Jev comparison | Sourced table, unmatched conditions |
| Jev parity | Not demonstrated |
| Production readiness | Not established; routing remains disabled |

The broader Wrench workflow gates remain separate from this classifier
comparison. Neither these unit tests nor the authored accuracy result proves
paid-teacher savings, end-to-end task success, hardware portability or sustained
serving reliability. This run performs no deployment, remote publication,
paid model call or existing sealed-final evaluation.

## Historical policy-head reproduction

Run from this isolated checkout, choosing a new output directory. This repeats
an already consumed diagnostic evaluation and does not create a new blind test:

```powershell
& 'D:\models\wrench-transformers517-py311\Scripts\python.exe' `
  tools/run_system_one_readiness.py --run `
  --model 'D:\models\Wrench-Qwen3.6-8expert-BF16' `
  --output artifacts/system-one-readiness/policy-v2-repro `
  --training-extra phases/system-one-readiness-20260922/contrast-training.jsonl `
  --evaluation phases/system-one-readiness-20260922/evaluation.jsonl `
  --evaluation-sha256 96c08a6fe3e2284c0bb55e4454d0b504675a0a50f2ddc859ced5c6b06503c622 `
  --baseline-head phases/system-one-readiness-20260922/baseline-head.json
```

The evaluation is opened only after fitting and artifact freeze. Any run
failure, overlap, invalid prediction or runtime error is recorded without
crediting it as a correct abstention. Start/end source hashes prevent a run
from silently claiming evidence for changed code.

## Reference discovery, not an accuracy benchmark

Before the published-metrics clarification, one public synthetic request
confirmed connectivity to a third-party OpenJev-FP8 demo. Its raw canary is
preserved under `reference/`. It used no credentials, repository content or
paid API. No 60-request remote benchmark was run. The demo's BF16-dequantized
weights and alternate wrapper are not the official BF16/helper recipe.
