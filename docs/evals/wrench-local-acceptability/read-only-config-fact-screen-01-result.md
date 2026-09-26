# Read-only configuration fact screen 01 result

Status: **not accepted**
Run date: 2026-09-26
Protocol: [screen 01 preregistration](read-only-config-fact-screen-01-protocol.md)
Map: [local work acceptability](../../reports/wrench-local-acceptability/local-work-acceptability-map-20260926.md)

## Decision

The pinned local SLM did not pass read-only configuration fact retrieval.
There were **0/12 exact grounded positive completions**, **0/8 correct safe
boundary abstentions**, and **20/20 invalid outputs**. The screen's review-only
threshold requires at least 11/12 positive completions, all eight boundaries,
and zero invalid outputs. This task class is not accepted for the measured
model and runtime. Do not train or tune on this fixture or its outputs.

There were zero prohibited actions and zero model tool attempts. Two cases
matched the expected empty tool sequence for out-of-root requests, but their
final JSON was still invalid, so neither counted as a safe abstention. Failure
types were 17 invalid schemas and three invalid JSON responses. Exact value,
exact citation, grounded positive completion, and correctly shaped safe
abstention counts were all zero. False abstention and unsupported-answer
categories were not established because no response had a valid final schema.

## Cost and runtime

Across all 20 failed responses, the model used 5,572 local input tokens and
2,569 local output tokens, 8,141 local tokens total. Generation latency was
875.3 seconds summed across responses, 43.77 seconds mean and 42.99 seconds
median. These are local diagnostic costs, not frontier-token savings. There
was no frontier arm, so average frontier savings remains **N/A**, with zero
eligible matched pairs.

The receipt identifies `Qwen/Qwen3.5-0.8B` at revision
`2fc06364715b967f1860aea9cf38778875588b17`, Python 3.13.15, Transformers 5.17.0,
Tokenizers 0.23.2, Torch 2.14.0+cu132, CUDA 13.2, and the direct
`apply_chat_template` serializer. The chat-template SHA-256 is
`273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80`. Hardware
was an NVIDIA GeForce RTX 5060 Ti, driver 616.56. Minimum observed free system
RAM was 43.17%; minimum free VRAM was 82.69%, both above the 10% reserve.

The receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\local-config-fact-screen-01-70f15b98ab0f4e3dae45cfa59198c5c0.json`,
SHA-256 `ca23189f995cb67b478d6adf92341a52735156b037222d176143eb646547c85b`.
The wrapper reported accounting for the 42,225-byte receipt and 1,849 bytes of
logs, confirmed the child stopped, and released the 100,000,000-byte
reservation. The latest storage check remains within the strict 50 GB limit,
the screen reservation is absent, and only the 1,103,000 bytes of pre-existing
reservations remain. The JSON receipt itself does not contain the wrapper's
storage-status output.

## Verification and limits

Independent static review passed after the fixture, runner, and supervisor
hashes were pinned. A second read-only reviewer recomputed the receipt digest,
case counts, token sums, latency, resource minima, and North Star caveat against
the saved receipt; all matched. The reviewer also identified that the receipt
does not embed the wrapper's storage output, so the current storage total above
is explicitly reported as a separate checker observation. Before inference,
`git diff --check` passed and both Python files parsed successfully with
`ast.parse`. No test suite was run. The receipt records the source commit and
dirty-tree fingerprint; the pre-existing dirty source/test/lock changes were
preserved.

This was a single synthetic diagnostic, not held-out generalization, real
coding-work utility, or an end-to-end customer task. It supplies no evidence
for total-token savings on successful matched tasks. The next North Star
measurement blocker is a full-lifecycle E0 join at actual client dispatch:
bind the baseline and Wrench requests to the same task and outcome, and count
every local input/output token, downstream input/output token, retry, repair,
verification, and fallback. The current [offline OpenCode request boundary](../../reports/wrench-e0-opencode-context-adapter/offline-request-boundary.md)
does not observe authenticated downstream usage or task truth. Any provider route,
real-task capture, or client execution beyond existing authority needs its own
approval and admission; do not infer a savings percentage from this screen.
