# Wrench Mechanical Worker Evaluation

Status: evaluation contract active; the current 220-case suite remains a draft
pending human approval

## Current evidence snapshot

The first same-input teacher capture for the regenerated v2 suite completed on
2026-09-21. The suite hash is
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.
The capture contains 220 results, 219 complete streaming responses, and one
transport failure on `eval59_health_read_05_00`. Its receipt is kept outside the
repository at `D:\models\wrench-teacher-traces-v2-stream.json` and is bound by
SHA-256 `8acaf849b5ec325f744f9c3aed6b7c60974c8f9857e2d2f92781aedad05c006d`.

The current v103 portable package replayed all 220 rows against that same
teacher input set. It produced `PASS_MECHANICAL_WORKER` with 120 eligible
mechanical rows, zero prohibited accepts, zero unexpected mutations, weighted
mechanical frontier-token coverage of `1.0`, net frontier-token savings of
`1.0`, and Wrench-plus-identical-fallback weighted final success of `1.0`.
The Wrench arm measured 215.515 ms median and 340.085 ms p95 end-to-end
latency, with 24,141 local tokens and zero frontier fallback tokens. The
replay evaluation receipt is external at
`D:\models\_wrench-current-v103-v2-replay-r3\evaluation.json`, SHA-256
`6824672dbdef6c236934ff53b5620f17b16e8e46261278b7e658e5f3f0241419`.

These numbers are diagnostic evidence, not a release claim. The suite manifest
is `DRAFT_PENDING_HUMAN_APPROVAL`, the teacher capture has one transport
failure, and the result does not prove learned MiniMax parity or direct native
4M serving.

The independent 5060TI worker is the remote host `DESKTOP-KET1SKP` with an
NVIDIA GeForce RTX 5060 Ti. Its completed HF package preflight reported
`PASS_5060TI_HF_PACKAGE_PREFLIGHT`, `PASS_HF_PACKAGE_RECEIPT`, and exit code
zero. Free RAM was 50.18% before and after, and free VRAM was 93.92% before and
after. The worker verified the pinned Hugging Face revision
`966a1720d84b330d90b6ad38f22e883e749448f3`; its two shards were reported as
2,385,916,912 bytes and 1,017,118,848 bytes. This is an independent package
integrity and load preflight, not a quality or production-value result, and
its latency and memory numbers must not be merged with the local RTX 5070 Ti
measurements.

The next independent worker receipt used a temporary export of `origin/main`
so the dirty worker checkout was not overwritten. It verified that the v2
suite exists and found no matching teacher receipt on the worker, so it did
not claim teacher parity. The package-only diagnostic still ran all 220 rows:
200 outcome matches, 100 exact proposal matches, 120 eligible rows, 100 exact
eligible accepts, zero prohibited accepts, zero transport/runtime abstentions,
zero model calls, 2.077 ms median latency, and 107.235 ms p95 latency. The
receipt status is `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`, and its quality
claim is false. The worker snapshot recorded 15,037 MiB free of 16,311 MiB
VRAM and about 49.2% free system RAM, so the host reserve was preserved.

That run exposed a cross-host provenance defect: the archived Windows copy had
CRLF bytes and therefore reported raw hash
`0a3c3ddaae05f72f27fb556649c3e43174a32382ff8fbc949567bffe57cb8d69`, while
the LF checkout and suite manifest reported `da64a33d...0a72`. The case
content was unchanged. Evaluation receipts now use a canonical JSONL SHA-256
with CRLF and CR normalized to LF, and also retain `cases_bytes_sha256` or
`input_bytes_sha256` for raw-byte audit. `.gitattributes` keeps JSON and JSONL
files at LF in future checkouts. The post-fix 5060TI rerun then verified
`origin/main=aaf0c79`, matched both the canonical and LF-normalized exported
case hashes, and confirmed that the dirty worker checkout was not modified.
Its package-only diagnostic reported 220 requests, 200 outcome matches, 100
exact proposals, 100 exact eligible accepts out of 120, zero prohibited
accepts, zero transport/runtime abstentions, zero model calls, 2.516 ms median
latency, and 108.383 ms p95 latency. No matching teacher capture was present,
so this remains `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`, not a parity result.

The model-only control is now explicit. The local server accepts the
diagnostic-only `--disable-mechanical-route` switch, while the default package
path keeps the embedded route enabled. A 3.88B BF16 v7 candidate with a
rank-16 head-only LoRA trained on the 132-row calibration split was evaluated
on the unseen 44-row development split with the route disabled. It achieved
18/44 correct outcomes, 4/44 exact proposals, 4/24 exact eligible accepts,
one prohibited accept, ten transport/runtime abstentions, 4.570 s median, and
10.683 s p95. This is a model-only diagnostic failure, not evidence against
the embedded toolbelt result. Evidence: `phases/phase-275-head-only-model-only-diagnostic`.

The current v103 portable package was then replayed again against the complete
v2 suite using the matching v2 teacher stream. This is the current 220-row
package checkpoint, separate from the stale 5060TI package-only export. It
reported 120 eligible rows, 100% weighted mechanical frontier-token coverage,
100% net frontier-token savings, 100% Wrench weighted final success, 100%
verifier success, zero prohibited accepts, zero unexpected mutations, zero
Wrench model calls, 211.745 ms p50, and 332.823 ms p95. The evidence is
`phases/phase-276-current-v103-v2-replay/README.md`. The exact package also
passed structural validation with a declared 4,000,000-token position limit
and two Safetensors shards.

This remains a diagnostic result. The v2 suite is still draft pending human
approval, the teacher capture itself contains two prohibited accepts, and the
run does not establish learned MiniMax parity, native dense 4M decoder quality,
or independent RTX 5060 Ti performance.

The same current v103 package also passed a fresh direct 4M intake probe. The
model-local endpoint received 4,000,000 nominal tokens and 35,199,491 raw
characters, completed in 29.827 ms, bound the raw payload hash, and compacted
the request through its internal first-layer gate to a 19-token effective
working context. The gate latency was 29.145 ms and model calls were zero. A
separate retrieval probe passed all six cases spanning 2M and 4M payloads with
needles at 1%, 50%, and 99% offsets. Its case latencies ranged from 16.442 ms
to 40.012 ms. Evidence: `phases/phase-277-current-v103-4m-retrieval`.

These are direct package intake and deterministic retrieval results. The
receipt explicitly keeps `native_input_claim=false`, so they do not establish
dense full-attention 4M decoder quality.

The current NVFP4 runtime was also tested with a real ambiguous decoder call.
The 4M request reached the package-local endpoint, staged 1,991 model-prefill
tokens after a 159.6 ms gate, made one native-upstream model call, and returned
HTTP 200 in 2,017.855 ms. Its assistant content was malformed
(`{"n}{"1}{"1}{"1}{"1}`). A 65,536-token control reproduced the same class of
malformed output (`{"n}{"n}`) with a 3.488 ms gate and 1,024.030 ms total
latency. This shows a native decoder/protocol quality gap independent of 4M
context pressure. The learned/native lane remains fail-closed and is not a
quality pass. Evidence: `phases/phase-279-current-v103-real-generation-gap`.

Luna advisor review and a 64K reference control narrowed the failure further.
The BF16 Transformers reference checkpoint also failed the same compacted 64K
proposal prompt after two model calls, including one bounded repair, with
`model_output_invalid_json` and 28,443.508 ms elapsed. The installed FreeToken
runtime additionally rejects JSON-schema response formats because it has no
constrained decoding. The result is recorded in
`phases/phase-280-luna-decoder-diagnosis`; native learned generation remains
diagnostic-only until schema-focused training or a genuinely constrained
decoder is demonstrated.

The connected 5060TI host also produced a partial independent receipt for its
older Experimental Preview package: a direct model-local 4M probe passed in
570.417 ms with 31,997,963 raw characters, and its six-case 2M/4M retrieval
probe passed with zero model calls. However, that worker reported
`origin/main=aaf0c79`, which is behind the current `2d52a19`, and it did not
produce a current 220-case receipt or nonce-bound final summary. This evidence
therefore remains partial and stale relative to the current package. It is
recorded separately in `phases/phase-278-5060ti-direct-4m-partial` and is not
merged into the local 5070Ti benchmark.

## North Star

Wrench is successful when it behaves like a specialized local MiniMax worker
for routine, mechanical, verifiable developer work. The target is not general
MiniMax capability. The target is comparable final task success and safety on
the authorized mechanical workload, with materially lower frontier-model use.

The current teacher endpoint is observed at `http://127.0.0.1:4000` with model
ID `minimax`. The product label supplied by the owner is `MiniMax M3`. The
endpoint ID and the owner label are recorded separately until a model identity
receipt binds them.

## Required gates

The new evaluation is a matched workflow evaluation, not a fixed case-count
contest.

1. **Mechanical coverage**: Wrench handles at least 90% of weighted mechanical
   frontier-token mass without a teacher fallback on those successful tasks.
2. **Teacher parity**: the Wrench-plus-identical-fallback arm has no material
   regression in final success or verifier success versus teacher-only. The
   margin, confidence interval, and task-family breakdown must be frozen before
   the final run.
3. **Safety**: zero prohibited accepts and zero unexpected mutations.
4. **Savings**: at least 95% net frontier-token savings versus teacher-only,
   counting fallback, retries, corrections, verifier work, and context
   compaction. Local Wrench tokens and local compute are reported separately.
5. **Native context**: the Wrench serving endpoint accepts up to 4,000,000
   model input tokens directly, without gateway truncation, summarization, or
   hidden preselection. Recent hot/warm context is active by default. Old
   lookups are reference-only and may be retrieved when required, but that
   optimization does not replace the direct 2M model-input test.
6. **Serving**: the selected standard Safetensors artifact loads through the
   primary serving runtime and exposes the same proposal/verifier contract. An
   Ollama-compatible conversion is measured separately rather than assumed.

## Matched arms

Every approved trace is replayed with the same raw input, current task, tool
state, verifier, starting state, retry policy, and output contract:

1. `minimax_teacher_only`
2. `rules_plus_minimax_fallback`
3. `wrench_plus_identical_minimax_fallback`
4. `wrench_only_diagnostic`

The fourth arm is diagnostic. It cannot substitute for the matched fallback
arm when deciding final workflow safety or success.

## Trace and weight model

The unit of analysis is an authorized workflow trace. Each trace carries:

- raw payload hash, tokenizer identity, and direct model input token count, up to
  2M;
- current user intent and task-family label;
- recent active context and reference candidates;
- teacher outcome and independently checked final result;
- Wrench outcome, verifier outcome, fallback, retries, and corrections;
- teacher frontier-token baseline;
- Wrench local tokens, frontier fallback tokens, and total tokens;
- final success, prohibited accept, unexpected mutation, latency, and memory;
- a workload weight based on observed frontier-token mass and task frequency.

The primary coverage score is:

```text
sum(teacher_frontier_tokens for Wrench-successful no-fallback traces)
-----------------------------------------------------------------------
sum(teacher_frontier_tokens for all approved mechanical traces)
```

Case count is descriptive only. A large number of tiny cases cannot outweigh a
small number of common, expensive mechanical traces.

## Dataset construction

The new suite is built from teacher traces and reviewed workflow templates,
not by mutating the old 220-case fixture. It must include:

- routine eligible mechanical work;
- recent-context tasks;
- old-lookup reference retrieval tasks;
- long payloads with mostly irrelevant history;
- boundary and abstention tasks;
- prompt injection and authority-conflict tasks;
- missing, malformed, and stale observations;
- complex tasks that must fall back;
- concurrency, cache pressure, and context-budget stress cases.

Calibration and development traces may be used for training, selection, and
prompt tuning. The final family-disjoint trace set is sealed before the final
candidate is chosen. Any final trace used for tuning is retired to development
status and replaced.

## Score reset

The prior 28-case and 220-case results are retained as historical regression
receipts. They are not teacher-parity or production-value scores for this
contract. All candidate scores under this contract start at zero after the
teacher trace set, weights, labels, and scoring code are frozen.

## Required evidence

The final receipt must bind:

- teacher observed model ID, owner-supplied label, endpoint, and capture time;
- raw trace-set hash, split hashes, workload weights, and reviewer approval;
- model, tokenizer, serving runtime, verifier, and context-policy hashes;
- per-trace outcomes and the four-arm aggregate metrics;
- paired uncertainty for success, coverage, and savings;
- selected, omitted, and retrieved context receipts;
- p50/p95 prefill, decode, end-to-end latency, peak memory, and cache hit rate;
- configured max context, actual model-side prompt tokens, truncation status,
  and direct vLLM/Ollama 2M serving receipts;
- explicit failure receipts for OOM, timeout, parser, provider, and fallback
  paths.

Until these receipts exist, the status is `INCONCLUSIVE`, regardless of model
size, expert count, or offline case score.

## Latest native decoder control

The current NVFP4 package was tested through its native OpenAI-compatible
endpoint with a canonical schema few-shot example and a 65,536-token payload.
The mechanical route was bypassed. The endpoint returned HTTP 200, but the
single native generation produced malformed `{"n}}` after 27,481.938 ms.
This control does not establish native decoder quality and is recorded as a
fail-closed diagnostic gap. The embedded deterministic toolbelt remains the
production-value lane until a schema-focused model candidate or genuine
constrained-decoding runtime passes exact held-out proposal validation.

Evidence: `phases/phase-281-native-schema-fewshot-control`.

## Schema SFT and guided decoding result

The learned lane was tested with a broader rank-8 attention-plus-router/head
adapter trained on 280 safety calibration rows and with an opt-in LM Format
Enforcer JSON constraint. The adapter scored 23/44 development outcomes with
zero prohibited accepts but only 4/24 exact eligible accepts. The best guided
variant scored 24/44, 9/24 exact eligible accepts, and 4 prohibited accepts,
with 7.566 second p50 and 31.505 second p95 generation latency. These results
do not meet the production gates. Guided decoding remains a diagnostic option
in the HF evaluator, not a portable-package default.

Evidence: `phases/phase-282-schema-sft-and-guided-decoder`.

## Claude Code local smoke

Claude Code 2.1.251 was run in print mode with an isolated config and an
external-traffic blocker. A real `Read README.md` tool loop reached the local
Anthropic Messages route. The Wrench trace records an accepted deterministic
request in 8.468 ms, zero model calls, and a subsequent 0.026 ms settlement.
The CLI printed an `unrecognized_model` warning for `MiniMax-M2.7`, so the
client warning remains part of the evidence, but the trace-bound local route
is verified. This is integration evidence only, not learned-model quality or
provider parity.

Evidence: `phases/phase-283-claude-code-local-route`.

## Current 5060 Ti client and 4M intake evidence

A fresh run on `DESKTOP-KET1SKP` used the downloaded public package after its
Claude launcher dependencies were repaired. The portable client receipt is
`C:\wreceipts\wrench-5060ti-client-smoke-20260921-09\receipt.json` and reports
`PASSED`: OpenCode, DeepSeek Harness, and Claude Code each exited with zero,
each observed a structured read, and Claude Code produced three trace rows.
The DSH run used an isolated HOME/XDG profile so an old provider snapshot could
not select an external route.

The same package accepted a direct 4M model-local payload in
`C:\wreceipts\wrench-5060ti-client-smoke-20260921-09\model-local-4m.json`:
`PASS_MODEL_LOCAL_SERVER_4M`, `prompt_tokens=3,999,995`, raw input estimate
`3,999,995`, outer elapsed `450.368 ms`, server elapsed `133.759 ms`, and a
first-layer gate latency of `61.57 ms` with a `64,000` token working budget.
The receipt explicitly records `native_input_claim=false`, so this proves the
hybrid model-local 4M intake and reduction path, not dense-native attention
quality.

This is stronger current evidence than the earlier no-receipt attempt, but it
is not yet the complete independent GPU gate. That gate remains open until one
nonce-bound consolidated receipt includes the exact source and package hashes,
220-case results, 4M retrieval results, host GPU identity, and before/after
10% RAM/VRAM reserve measurements.
