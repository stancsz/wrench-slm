# Internal Wrench evidence

This folder keeps authored Wrench development diagnostics beside the five
benchmark scorecards. These are not external benchmark scores, not production
hybrid workflow results, and not release evidence. The final split was not
read. No provider calls or tool executions occurred. Calibration experiments
below trained only small heads on permitted calibration rows; the backbone
weights remained frozen.

## Binary abstention gate diagnostic

The frozen binary head was scored on 44 authored development cases:

- 20/24 eligible cases passed (83.3% coverage).
- 20/20 labeled abstention cases correctly abstained.
- 40/44 overall outcomes matched (90.9%).
- Warm latency p50/p95/max: 175.45/202.09/227.49 ms.
- No final-task quality claim is made.

The run used the Wrench Qwen model and saved gate from `qwen-system-one-run-v1/`.
The copied head SHA-256 is
`e33e28af544be5eaf156ff42dbe47d2098a36939bb4b0cfd0222d378d4ee3b0b`.
Receipts, predictions, and strict rescore in that directory retain the complete
case-level evidence.

## Separate proposal-generation diagnostic

`qwen8e-proposal-dev-44-20260922.json` contains a distinct 44-case development
run of the Qwen proposal generator. Strict rescore found 44/44 invalid JSON,
0/24 eligible exact accepts, 0/44 exact outcomes, and zero prohibited accepts.
The receipt reports verifier abstention on all 44. Median/p95 latency was
29,247.938/32,112.518 ms. The receipt SHA-256 is
`DD4A6ED562DA2017AF7B18D415F60E22754C9972E2DE64D7D91F2D6A31965CF5`; the
strict-rescore SHA-256 is
`58E611DD2D5F98835BB6B5D3B899D401F50BDCDF4D65DDCDE3D3F32871CD936F`.

This result exposes a proposal-format failure in that separate candidate. It
must not be blended with the binary head metrics or treated as a verdict on the
deterministic hybrid path.

## Product benchmark still required

The internal product scorecard is the three-arm matched real-workflow replay
defined in the repository's active `GOAL.md` and production utility test
contract. Its final success, safety, latency, and net frontier-token savings
remain unmeasured here. These diagnostics do not satisfy that gate.

## Matched local Qwen3.5 9B comparison

The unsealed 44-case System One development split was run through local
Qwen3.5 9B using the same saved Wrench inputs and binary labels, for both the
original Wrench system prompt and a plain-prompt variant. Wrench scored 40/44
(90.9%) on each style with 20/24 eligible continuations and zero unsafe
continuations. Qwen3.5 9B scored 35/44 (79.5%) on the original prompt with
45% unsafe continuations, and 22/44 (50.0%) on the plain prompt with 100%
unsafe continuations. On the original-prompt comparison, Wrench's point
estimates were +11.36 percentage points in accuracy and +14.17 points in
balanced accuracy, but both paired template-clustered 95% intervals include
zero. Wrench warm latency was 175/202 ms p50/p95; Qwen3.5 9B was 268/309 ms.

The same 44 case IDs were then run with local Qwen3.5 27B Q4_K_M, using 24
GPU layers and an 8,192-token context. With the original Wrench system prompt,
Qwen3.5 27B scored 44/44 (100%), 24/24 eligible coverage, and zero unsafe
continuations. Wrench scored 40/44 (90.9%), 20/24 coverage, and zero unsafe
continuations. The Qwen27B p50/p95 was 4,927/5,289 ms in this capped local
setup; Wrench remained 175/202 ms. Paired template-clustered 95% intervals
for the accuracy and balanced-accuracy differences include zero. With the
plain prompt, Wrench scored 40/44 while Qwen3.5 27B scored 27/44 and continued
on only 7/24 eligible cases. The original-prompt result is the primary
comparison; the plain prompt is secondary.

Model identity, per-style metrics, intervals, and reserve samples are in
`qwen-system-one-qwen35-9b-dev-v2/summary.json` and
`qwen-system-one-qwen35-27b-dev-v1/summary.json`. These are small, unsealed
development comparisons, not public benchmark results or production proof.
The sealed final split was not read.

## Calibration-only coverage candidates

Three offline candidates attempted to recover the four missed eligible
`git_read_status` cases while keeping zero false continuations on development:

- `qwen-system-one-run-v2/` removed the arbitrary 0.5 threshold floor and
  calibrated the threshold to the highest held-out calibration negative
  probability plus epsilon. Threshold: 0.3315.
- `qwen-system-one-run-v3/` used the same calibration rule with positive-class
  loss weight 2.0. Threshold: 0.4250.
- `qwen-system-one-run-v4/` used positive-class loss weight 5.0. Threshold:
  0.5563.

All three kept 20/24 eligible coverage, 20/20 correct abstentions, and 40/44
overall development accuracy. None improved the baseline on this development
set. The lower threshold alone did not change any development decisions, and
positive weighting did not recover the missed cases. These remain offline
candidate receipts; none is enabled in the worker.

## V2 training-data repair

The v1 receipt shows the cause of the four Git status misses: exact-overlap
filtering removed all 12 positive `git_read_status` calibration rows because
they repeated the same prompts used by the old development split. That left
five negative status examples for head training and one negative for threshold
calibration. The overlap filter was correct; the training pool was incomplete.

The first v2 data build accidentally retained two unique prompts from the old
44-case development split. Training stopped after 64/206 feature encodings,
before any candidate score; see
`system-one-v2/train-run-001/rejection-receipt.json`. The corrected builder
removes all 12 source calibration rows that overlap that old split. Clean
calibration and fresh 80-row development data are frozen in
`system-one-v2-data-clean/`, with disjoint prompt and template IDs. Candidate
training completed in `system-one-v2/train-run-002/`. On the original prompt,
Wrench scored 71/80 with 5 unsafe continuations; Qwen3.5 9B scored 56/80 with
24 unsafe continuations, and Qwen3.5 27B scored 79/80 with one unsafe
continuation. Wrench's 9B accuracy advantage does not pass the strict
zero-unsafe gate, and the candidate is slower than both the prior Wrench head
and Qwen3.5 9B. Full predictions, model hashes, latency samples, and paired
intervals are in `system-one-v2/qwen35-9b-dev-v1/` and
`system-one-v2/qwen35-27b-dev-v1/`. No v2 head is enabled in Wrench.

### V3 same-case comparison: promising accuracy, still fails safety

V3 uses a new frozen 80-case split with 20 template clusters, disjoint from
its calibration data and the earlier development splits. On original prompts,
Wrench scored 67/80 (83.75%), accepted 26/32 eligible requests, and made 7
unsafe continuations among 48 abstention cases (14.6%). Qwen3.5 9B scored
54/80 (67.5%) and made 26 unsafe continuations. Wrench's accuracy advantage
was 16.25 points (paired template-cluster 95% interval [7.5, 25.0]); Wrench
latency was 403/495 ms p50/p95 versus 250/262 ms for Qwen3.5 9B.

On plain prompts, Wrench scored 70/80 (87.5%) with 3 unsafe continuations,
while Qwen3.5 9B scored 34/80 (42.5%) with 44 unsafe continuations. This is a
secondary prompt condition. The original-prompt candidate still violates the
zero-prohibited-accepts gate and misses the latency target against 9B.

The same-case Qwen3.5 27B run scored 78/80 (97.5%), with one unsafe
continuation, against Wrench's 67/80 and seven. Its accuracy advantage was
13.75 points (paired template-cluster 95% interval [5.0, 23.75]); Wrench was
faster at 403/495 ms versus 5,042/5,532 ms p50/p95. On plain prompts Wrench
scored 70/80 and Qwen3.5 27B scored 55/80. The original-prompt candidate still
fails the safety and 27B quality targets despite its latency advantage. Do not
enable the candidate or treat accuracy alone as a release-quality win. Full
data, predictions, latency, model identity, and intervals are in
`system-one-v3/`.

### V4 same-case comparisons: 9B lead, 27B target still open

V4 freezes a fresh 80-case development set with 20 template clusters. It has
zero exact-prompt overlap with calibration or prior development sets. Its
316-row calibration set adds 64 boundary examples focused on partial status,
status plus mutations, remote operations, content advice, credentials,
permissions, and cleanup. The head SHA-256 is
`77d4a3dbec0f1fa420fc6224e1f8c94fb610da26eb21a384f44642fbc0e3cb74`; the
calibration threshold is `0.5379163487`. The Qwen3.6 backbone was frozen, and
the gate used one forward and generated zero tokens per decision.

On the primary original-prompt condition, Wrench scored 71/80 (88.75%),
accepted 25/32 eligible cases, and made 2 unsafe continuations among 48
abstention cases (4.17%). Same-case Qwen3.5 9B scored 57/80 (71.25%),
accepted 32/32, and made 23 unsafe continuations (47.92%). Wrench's accuracy
advantage was 17.5 points (paired template-cluster 95% CI [+3.75, +30.0]).
Wrench p50/p95 decision latency was 213.5/257.1 ms versus 250.2/278.8 ms for
Qwen3.5 9B. This is a favorable 9B development comparison, but V4 still fails
the zero-prohibited-accepts gate.

Same-case Qwen3.5 27B scored 79/80 (98.75%), accepted 31/32 eligible cases,
and made zero unsafe continuations. It led Wrench by 10 points (paired
template-cluster 95% CI [+5, +15]). Its p50/p95 latency was 5,309/6,395 ms.
Wrench remains much faster, but does not meet the 27B accuracy or safety
target. Plain prompts are secondary: Wrench scored 68/80 with 4 unsafe
continuations; Qwen3.5 9B scored 32/80 with 44 unsafe, and Qwen3.5 27B scored
47/80 with 5 unsafe.

The two original-prompt Wrench unsafe cases were a request to read and test an
API secret in the repository and a request to change repository permissions.
V4 also missed seven eligible full-repository status requests. These errors
inform new calibration examples only; V4 development labels are not used to
set another threshold. The full data, receipts, same-case predictions,
confidence intervals, and timing samples are under `system-one-v4/`. No V4
head is enabled.

Training used a phase-local Transformers 5.17.0 overlay with the existing
CUDA-enabled PyTorch 2.8.0+cu129 runtime. This kept the ComfyUI environment
unchanged and supplied the Qwen3.5-MoE architecture support missing from its
installed Transformers 4.57.3. Optional `causal_conv1d` and flash-linear
attention kernels were unavailable, so Transformers used its correct but
slower PyTorch fallback. The failed compatibility preflight is preserved in
`system-one-v4/train-run-001-cuda/`; the completed candidate is
`system-one-v4/train-run-002-cuda/`.
