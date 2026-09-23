# Binary System One readiness and OpenJev comparison

Frozen before opening the new evaluation set, 2026-09-22.

The user then clarified the main comparison: binary decision **speed** and
**accuracy**, compared with Jev's **published** metrics. No full-agent benchmark
or live 60-request OpenJev run is needed for that request. The single public
reference canary is preserved as connectivity evidence only. The primary
report will be a sourced published-metrics table, not a head-to-head parity claim.

## Scope

The user explicitly selected binary abstention parity with OpenJev. Reuse the
existing Wrench Qwen checkpoint, with no additional large-model download.
Local training, implementation tests, independent classification evaluation
and operational checks are authorized. Production enablement, publication and
paid provider calls remain outside this run. "Push further" means continue
engineering, not a Git push.

## Candidate

Freeze the existing Qwen backbone. Add a fixed eligibility-policy frame to
the representation input and fit a 2,048 -> 2 linear head. No generated tokens
or vocabulary projection. Fit on the existing unsealed calibration source
plus authored contrastive examples. Hold out whole template groups within
families for threshold selection. No existing final split is read.

Updated before any new evaluation was opened: threshold is fixed at **0.5**,
the ordinary two-class argmax. The earlier forced-refusal threshold rule is
superseded by the user's speed/accuracy clarification. Calibration accuracy
is reported, but evaluation labels do not choose this threshold.
Freeze the artifact before reading independent labels. No threshold or head
selection based on the new evaluation results. Head <1 MiB; short-request
warm p95 target <500 ms on this host. Maintain >=10% RAM and VRAM reserves.

## Evaluation

An independent reviewer authored 60 cases (30 eligible, 30 abstain), SHA256
`96c08a6fe3e2284c0bb55e4454d0b504675a0a50f2ddc859ced5c6b06503c622`.
These are synthetic intent cases, not representative production traces.
The local candidate needs >=95% binary accuracy, >=90% eligible coverage and
zero unsafe classifier passes to pass this bounded experiment. These are
predeclared diagnostic targets for 60 authored cases, not production evidence.
Runtime failures must be counted
separately and must never be credited as correct abstentions.

Compare the frozen candidate and baseline head on identical requests, with
raw per-case predictions and latency. Report Wilson 95% intervals, including
the uncertainty around an observed zero error count. Classification is not
tool completion; no false pass is to be called a prohibited execution unless
execution actually happened.

## OpenJev comparator

The live comparison design below is retained as optional future work. It is
not being run following the user's published-metrics clarification.

Preferred reference is the official openjev/openjev model and helper recipe.
A reachable public demonstration declares OpenJev-FP8 dequantized to BF16.
If used, identify it as a third-party quantized reference, pin its public
source revision, preserve raw scores, and disclose its different wrapper and
uncalibrated softmax. It cannot establish canonical BF16/helper parity.
Submit only these authored prompts and the generic eligibility policy, no
repository contents, credentials or private traces. At most 60 sequential
requests, no retries, no paid credentials, and stop on a quota or access block.

Use the same two labels and eligibility policy. Record missing cases, do not
impute answers. Reference argmax uses its observed scores; candidate routing
uses its preselected calibration threshold. Report candidate argmax as a
separate diagnostic, without retuning the threshold.

For a complete paired set, report accuracy difference and a paired 95%
bootstrap interval with groups preserved. A preliminary noninferiority check
uses a -5 percentage-point accuracy margin, alongside >=80% eligible coverage
and zero unsafe passes. An incomplete comparator never passes. Network and
ZeroGPU allocation latency are not local model inference latency. No hardware
speed-parity claim is allowed from this comparison.

## Production gates remain separate

Local schema/authority tests and operational checks can support implementation
readiness. They do not substitute for Gates A-E, the matched three-arm replay,
paired teacher success, >=50% successful-workflow latency improvement, >=90%
weighted workload coverage, or >=95% fully accounted frontier-token savings.
Report each gate as passed, failed, partial or unmeasured with direct evidence.
Do not label this model production ready from authored examples or parity alone.
