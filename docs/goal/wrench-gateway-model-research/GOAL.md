# Wrench gateway LoRA and cost-reduction experiment

Status: active; the owner has removed a fixed model-size preference: choose any exact, licensed model below 10B that runs smoothly on this machine, then train and evaluate a Wrench LoRA; the installed Qwen3.5-4B Q4 Ollama path failed a local smoke because Docker had no GPU device and CPU inference used ~100% CPU with no answer after ~4 minutes; an isolated --gpus all container also lacked /dev/nvidia0; Qwen3.5-0.8B Q8 has not had a fresh local-agent runtime evaluation; push a local end-to-end demo MVP while preserving the full 95/5 completion/routing, 95% frontier-token and all-in-cost, success-retention, and all-day engineering criteria; Fit-03's static package review is bound to the previous goal hash and must be refreshed before a fit; latest live sample after stopping only the isolated test container is 20.95% free RAM and 15,217/16,311 MiB free RTX 5060 Ti VRAM; SubRoute :4000 remains forced to OpenRouter with no numeric campaign cap, so no provider calls; the hourly heartbeat is ACTIVE; product claims remain unproven
Updated: 2026-09-28 (America/Edmonton)
Owner: human product owner; repository agent maintains the evidence

## Objective

Find out whether a deterministic Wrench gateway and a locally LoRA-trained
model can complete at least 95% of task episodes locally, use a frontier model
in at most 5% of episodes, retain at least 95% of the frontier-only baseline's
verified task success, reduce total frontier tokens by at least 95%, and cost
at least 95% less all-in on the same frozen workload. These are separate,
hard targets, not current results. The token metric is
`1 - hybrid_frontier_tokens / frontier_only_tokens`; the dollar metric is
`1 - hybrid_all_in_cost / frontier_only_all_in_cost`. Count every planned
episode, including failures, abstentions, timeouts, and human rescue. Only an
external frontier/provider call counts as an escalation. Remote retries,
verification, compaction, fallback, and re-fetch calls count; local compaction,
retrieval, and retries do not count as frontier use but remain in local token,
latency, compute, energy, and cost accounting. Keep route events separate
from task outcome and human intervention. Apply the primary 95/5/95 and
95%-cheaper gates to the LoRA hybrid arm independently; report deterministic
Wrench + frontier as a separate control and never pool arms. All-in cost
includes provider charges, measured local compute/energy, hardware/runtime
allocation, operator and human-rescue labor, and preregistered LoRA
training/evaluation amortization. Report latency, all-tier tokens, compute,
task outcomes, and confidence bounds separately.

The system must still support sustained software engineering. Mechanical
operations and context selection are valid local work; the experiment must not
pretend that exact file reads or synthetic routing choices prove open-ended
coding ability or a full workday of reliable engineering.

## Owner-directed priority update (2026-09-28)

Work in this order:

1. Select the most promising model size across the 0.5B-12B research band
   using multiple independent evidence sources and a common Wrench task
   battery. Compare task quality, verified completion, context/token savings,
   latency, inference and LoRA-training resource fit, licensing, and operating
   cost. Label evidence by type and quality; vendor benchmarks, papers,
   synthetic component results, and Wrench paired outcomes are not
   interchangeable. Make one overall recommendation with a confidence level,
   named alternatives, and explicit missing evidence. Parameter count alone
   is not the decision rule. Sizes above the already authorized sub-10B
   training scope remain research-only absent separate owner authority.
2. Once the evidence identifies the best candidate, continue engineering
   toward the highest reproducible full-lifecycle frontier-token savings the
   same frozen tasks can support. Optimize upward only while verified quality
   and every existing acceptance gate remain intact. Report failed attempts,
   regressions, denominators, retries, and uncertainty; a prompt-input or
   synthetic proxy cannot be called frontier-token savings.
3. Resume the existing Wrench engineering tasks, prioritizing reliable
   mechanical work, state-aware compaction, and context pruning that preserve
   exact hot evidence and permit audited recovery. Measure those components
   separately from any LoRA contribution, then measure the end-to-end task.

The model-size recommendation is a research choice, not permission to download,
train, activate, route, spend, or open sealed evaluation data. Each execution
still requires its own exact identity, storage and resource admission, rights
review, and applicable package review. This update changes the goal-file hash;
the existing Fit-03 static review is consequently stale and must be refreshed
against this exact goal before any Fit-03 execution. Its previous PASS remains
historical evidence only.

## Owner direction update (2026-09-28)

The owner requests a fresh model-size decision across 0.5B-12B, then sustained
work toward the highest verifiable frontier-token savings, followed by
resumption of existing engineering tasks. At that update, the research lead
was Qwen3.5-2B; the newer hardware-gated owner update below supersedes that
fixed preference. Paritok's Qwen3-4B compression result remains an external
task-linked comparison, not proof of 95% success retention or host fit. No
model in this band is proven to deliver reliable all-day open-ended repository
engineering. The comparative evidence and limits are in the [model-size
decision](../../reports/wrench-gateway-model-research/model-size-decision-20260928.md)
and [evidence refresh](../../reports/wrench-gateway-model-research/model-size-evidence-refresh-20260928.md).

## Owner direction update (2026-09-28): hardware-gated model choice and demo MVP

The owner removes any fixed preference for 2B or another size. Select and
train any exact model below 10B parameters when its license, complete inventory,
Wrench LoRA compatibility, measured inference/training fit, and sustained
behavior pass this machine's gates. The current GPU is an NVIDIA RTX 5060 Ti
with 16,311 MiB VRAM; the host has an AMD Ryzen 5 2600 (6 cores / 12 threads)
and 32 GiB visible system memory. These identifiers are hardware context, not
proof that a model runs smoothly. The existing Docker Ollama volume contains
Qwen3.5-0.8B Q8_0 and Qwen3.5-4B Q4_K_M tags. The Qwen3.5-4B Docker CPU smoke
did not return a result before it was stopped, and a separate `--gpus all`
container had no NVIDIA device. This rejects those Docker runtime paths, not
the base model under a CUDA-enabled host runtime. The 0.8B Q8 Ollama tag has
not yet had a local coding-agent evaluation. Keep the Hugging Face 0.8B training snapshot as
one ready candidate, not as a mandatory winner. Compare the best candidates
that pass hardware admission, including the installed 4B inference tag if its
storage and identity are admitted. Do not enlarge the base model beyond the
already authorized sub-10B scope.

"Runs smoothly" means the exact pinned model and chosen quantization complete
the representative local task battery without OOM, crash, lost work, or
breaching the 10% RAM/VRAM reserve; report cold/warm latency, throughput,
context length, peak resource use, and failures. A short smoke request is only
runtime feasibility, not all-day engineering proof. LoRA training is a
separate admission: estimate optimizer/checkpoint/activation peaks, use an
independently reviewed bounded training package, hold 10% RAM/VRAM free
throughout, keep the base and installed Wrench-Core frozen, and leave each new
candidate inactive until its evaluation passes.

The next deliverable is a provider-free local demo MVP that runs Wrench context
preparation plus the selected local model on a small reproducible code task,
verifies the result deterministically, and writes a hash-bound receipt for
baseline versus Wrench-prepared input tokens, output tokens, latency, resource
use, outcome, retries, and recovery. Add the bounded LoRA candidate as a
separate arm after training and evaluation. The interface may demonstrate a
frontier escalation branch with a fixed mock response; it must label mock
traffic clearly and may not report it as an actual provider call or cost. The
existing SubRoute `:4000` remains forced to OpenRouter and provider calls remain
closed until an enforced numeric campaign spend cap and usage receipt are
available. Keep the acceptance population and confidence-bound study intact:
95% local verified completion, at most 5% frontier-routed episodes, at least
95% frontier-only success retained, at least 95% fewer full-lifecycle frontier
tokens, at least 95% lower all-in cost, and reliable all-day engineering.

The current 86.4327% E0 prompt-input result is the largest local synthetic
component measurement, using only three fixtures with repetitive health logs.
It is not evidence of the 95% frontier-token requirement. See [Iteration 098
context demo](../../evals/wrench-gateway-model-research/iteration-098-context-demo-mvp-20260928.md).

This expands the **research comparison band** to 0.5B-12B. It does not extend
existing training permission beyond the previously authorized sub-10B staged
experiment. A 10B-12B candidate remains research-only unless separately
authorized. Every candidate still requires a pinned complete inventory,
license and runtime review, storage/peak-duplication accounting, and current
hardware admission before use. The 0.8B candidate remains the smallest control;
2B is the first research candidate, not a Wrench-proven winner; Paritok 4B is
the first compression challenger after a named 2B failure; larger models need
their own named failure and common-harness evidence.

The primary optimization is paired **full-lifecycle frontier-token savings**,
`1 - hybrid_frontier_tokens / frontier_only_tokens`, measured on identical
frozen episodes. Push this as high as verified evidence allows while retaining
the existing completion, escalation, success-retention, and cost gates.
Measure deterministic schema/filtering and context preparation separately
from the LoRA contribution. Count compaction, retries, verification, recovery
fetches, cache misses, and escalations. A tool-output compression percentage
or local prompt-token proxy is component evidence, not end-to-end frontier
savings. Keep hot code, diffs, active failures, and required evidence lossless;
retain exact originals and charge every recovery fetch.

This goal-file refresh changes its hash. Iteration 102's Fit-03 static package
review was bound to the prior hash and no longer admits a fit. Do not train
until the package is independently reviewed against this refreshed goal hash
and every Fit-03 resource, storage, path, and sealed-split gate passes.

## Owner authority and boundaries

The owner's 2026-09-27 request authorizes the staged experiment, a new
Wrench-authored synthetic-only training/development/held-out corpus, and
exploration of any model below 10B parameters when its pinned inventory,
storage, and hardware/resource admission pass. The already-present
Qwen3.5-0.8B snapshot is the first bounded LoRA candidate; its CPU preflight
and full training are separate recorded jobs. This is a narrow gateway
hypothesis; the 2026-09-26 decision closing that model as an OpenCode primary
or general semantic controller remains in force. Model-size permission does
not waive per-job admission or authorize paid calls.

The owner explicitly directed this experiment to use SubRoute at
`http://127.0.0.1:4000`. The saved read-only snapshot on 2026-09-27 showed
`active_model=openrouter`, `mode=force`, and policy version 4. The reviewed
configuration maps the `openrouter` alias to OpenRouter/MiniMax M3, and its
declared capabilities omit native tools; a separate `minimax` alias declares
tools, but this does not authorize switching around the forced active route.
A prior liveness check returned HTTP 200 and `/models` listed 19 aliases; that
does not identify the provider that would serve a generation. The numeric
aggregate USD cap is still missing, so generation calls remain closed. Do not
change SubRoute configuration to bypass force mode. Before a paid comparison,
record returned model/provider and usage receipts per request, and enforce a
durable hard aggregate cap in the caller.

This initial synthetic LoRA run does not authorize training on public
benchmarks, private/real task capture or transfer, paid calls, production
routing, publication, or adapter activation. Any later evaluation-data plan
must preserve rights, provenance, leakage controls, and a sealed final split.
The model must never gain arbitrary shell, credential, mutation, or permission
authority.

## Acceptance evidence

| Requirement | Evidence required |
| --- | --- |
| Hardware-gated candidate selection | The owner permits any model below 10B. For each finalist record exact upstream/runtime identity, complete files and quantization, license, Wrench LoRA compatibility, training peak estimate, cold/warm latency, throughput, target context, errors, and peak RAM/VRAM on this host. A short smoke test is feasibility only; require the representative local coding-task battery to choose the candidate. Compare only candidates that pass every gate and choose the highest quality/efficiency model that runs within reserves; do not preselect 2B or 0.8B. |
| Reproducible demo MVP | Provider-free end-to-end Wrench + local-model code task with deterministic verification, baseline versus prepared prompt/token counts, completion/result, latency, resource, retry/recovery receipts and exact hashes. Demonstrate a labeled mock frontier branch only. Add the evaluated Wrench LoRA as a separate arm; keep actual frontier calls closed until a hard numeric campaign cap and usage receipts are authorized. A demo pass is not product acceptance. |
| Train a Wrench-specific LoRA | New local-only adapter on an admitted, pinned model below 10B, frozen base/tokenizer hashes, training manifest and resource receipt; for Qwen3.5-0.8B compare or justify attention-only versus the current all-module profile before full fit; screen-01 and fit-01 did not produce an adapter |
| Measure the local gateway decision quality | [LoRA training protocol](../../evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md) and [held-out scoring protocol](../../evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md), exact synthetic oracles, deterministic and base-model controls, and independent review |
| Measure 95/5/95 and 95%-cheaper claims | [Product proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md): LoRA hybrid must independently meet one-sided, family-wise controlled, cluster-aware bounds for local verified completion >=0.95, frontier escalation <=0.05, paired success retention >=0.95, frontier-token savings >=0.95, and all-in dollar savings >=0.95; workload population and grouped/time-isolated final split mandatory; exhaustive denominators and auditable usage/cost receipts |
| Measure day-long engineering | Ten independent paired eight-hour sessions, >=3 unrelated repositories, >=2 languages, >=5 episodes/session and >=2 edit/test loops/session; interruption/context switch/restart in each; >=9/10 sessions finish without >10-minute product stall, 95th-percentile recovery <=10 minutes, zero severity-1/2 regressions/lost work/unauthorized actions; the powered primary bounds still apply; synthetic screens cannot satisfy it |
| Track iteration status | [Iteration 000 readiness record](../../evals/wrench-gateway-model-research/iteration-000-readiness-20260927.md), [Iteration 104 E0 stable-source test result](../../evals/wrench-gateway-model-research/iteration-104-stable-source-e0-runtime-verification-20260928.md), [latest campaign-wide spend-caller record](../../evals/wrench-gateway-model-research/iteration-033-subroute-campaign-budget-caller-20260927.md), followed by hash-bound run and review records |

## Current findings

- The tested Qwen3.5-0.8B general semantic route remains closed at 0/10 on
  its tool-backed screen. That result does not test a new Wrench-specific LoRA
  over finite, validated mechanical/context decisions.
- The existing 0.8B snapshot remains the already-staged narrow gateway
  baseline, not a mandatory final model. The owner now permits any pinned
  candidate below 10B when measured fit and runtime are smooth. The independent
  fit audit recommends Qwen3.5-2B as a gateway challenger and Qwen2.5-Coder-
  1.5B when code-specific decisions are the task; neither has passed a local
  LoRA preflight. Deterministic code still owns exact retrieval, budget checks,
  parsing, provenance, and verification.
- Qwen3.5-4B has a pinned 9.34 GB public snapshot. A fresh 2026-09-27 sample
  found an RTX 5060 Ti with 16,311 MiB total and about 15.1 GiB free VRAM. This
  idle snapshot does not admit a 4B training job; FP32 base weights alone are
  about 16 GB before activations. It needs a separately reviewed quantized
  training path, complete peak-memory/storage plan, and its own preflight.
- The 0.8B CPU/FP32 full fit aborted before its first optimizer step after RAM
  fell below the 10% reserve. No adapter was produced. Screen 02's first GPU
  preflight invocation used the unrelated AppData Python and stopped at
  `import torch`; its receipt shows no model/data hashes or optimizer step. The
  preserved attempt is not a quality result. A revised runner now uses a new
  job ID and output directory with the existing Wrench-local GPU environment.
  It enforces exact interpreter/add-on paths and versions, records imported
  module origins, and binds that identity between preflight and fit. Assignment
  25 found those checks missing in its reviewed predecessor. Assignment 26
  passed exact-hash static review, and distinct preflight attempt 02 completed
  one optimizer step with minimum recorded free RAM of 11.31% and free VRAM of
  53.79%. Full-fit attempt 01 then aborted before its first optimizer step
  when RAM reached 9.83%. The failure receipt is preserved; no adapter exists.
  Any retry requires a new job identity and paths, updated hash-bound source
  and protocol review, a matching new preflight, and fresh storage/resource
  admission. The next pinned 0.8B FP32 attempt adds a 25% free-RAM start
  buffer because the previous fit started at 16.70% and aborted 34.7 seconds
  later at 9.83%; the 10% RAM/VRAM runtime floor remains unchanged.
- Preflight 03 and 04 are historical compatibility receipts. The latest
  candidate evidence is assignment 04's exact-hash PASS and attention-only
  preflight 05: one finite optimizer update on eight synthetic examples, 24
  instantiated `self_attn` q/k/v/o modules, 540,672 trainable parameters,
  minimum free RAM 10.9850%, minimum free VRAM 54.4663%, and zero runtime
  scratch. The run wrote no adapter, opened no heldout row, and made no
  provider call. Its stopped 250,000,000-byte reservation was released after
  accounting for the 23,967-byte resource log, 5,622-byte manifest, and
  260-byte claim; the following storage status reported 10,955,471,440 actual
  bytes and 6,103,000 active reserved bytes, within the 50 GB limit. The
  manifest's observed free RAM at preflight start was 17.5017%, below fit 03's
  separate 25% start gate. A fresh read after preflight was 17% free RAM, so
  fit 03 is still closed. The fit path does not consume preflight 04 or fit 02
  identities. The [iteration 008 record](../../evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md)
  retains current hashes and receipts. The heldout scorer is still pinned to
  fit 02; it needs a fit-03-specific revision, exact-hash review, and fresh
  dev-only inference preflight before any heldout access.

- The [independent product proof audit](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md)
  verified that the 128-case synthetic splits contain 104 LOCAL, 8 FRONTIER,
  and 16 ABSTAIN labels. That distribution and the no-frontier-call protocol
  cannot prove local 95/5 operation, frontier-token savings, or all-in savings.
  It also found the historical 95/5/95 table omitted paired success retention
  and the original 95%-cheaper requirement; the new proof design records both.
- No matched real task or frontier usage pair exists. Quality retention,
  frontier savings, dollar savings, and all-day utility are all unmeasured.
- The [fresh research synthesis](../../reports/wrench-gateway-model-research/research-synthesis-20260927.md)
  adds evidence for treating deterministic tool-schema filtering as the first
  measurable cost lever and a small LoRA as an extractive context/route
  proposer. Recent coding-context results remain below the joint 95% quality,
  token-savings, and all-in-cost targets; they do not establish Wrench efficacy.
- The [model-role reassessment](../../reports/wrench-gateway-model-research/decision-reassessment-20260927.md)
  reviewed new 2026 LoRA/tool-pruning evidence. Squeez reports a Qwen3.5-2B
  LoRA at 92% tool-output input-token reduction with 0.86 evidence recall and
  0.80 F1 on its curated extraction evaluation. This supports 2B as a future
  extractive-pruning challenger, not as a Wrench result or all-day code model.
  Keep the staged 0.8B as the first Wrench feasibility candidate, and keep
  sustained coding as a separate paired system evaluation with the stronger
  worker on the specified SubRoute.
- The rehashed M3 tokenizer receipt measures 12.1099% ratio-of-sums reduction
  on five eligible synthetic pairs, with two positive evidence failures and
  zero frontier calls. The current OpenCode context transition protects the
  `tools` field, so full request-boundary accounting/filtering is the next
  no-provider engineering task. See [iteration 025](../../evals/wrench-gateway-model-research/iteration-025-request-accounting-gap-20260927.md).
- [Iteration 048](../../evals/wrench-gateway-model-research/iteration-048-opencode-tool-schema-pruning-20260927.md)
  clarifies that the current Wrench message-insertion transition protects tool
  schemas, while OpenCode V2's separate `context` hook exposes a mutable tool
  map and documents per-request removal. The no-provider `http.request`
  example still only observes a fixture and refuses transport. A project
  issue reports 37.6% input-token reduction from one manually scoped setup;
  this is self-reported and below the 95% target. The next engineering gate is
  a separate, fail-closed V2 context-hook tool profile, exact lowered-request
  measurement under egress block, and paired outcome evaluation. At that
  iteration RAM was below the runtime floor.
- [Iteration 049](../../evals/wrench-gateway-model-research/iteration-049-subroute-4000-tool-profile-prototype-20260927.md)
  reconfirms read-only access to the owner's SubRoute at :4000 and adds a
  disabled, source-only context-hook profile prototype. Ten synthetic unit
  tests pass, but OpenCode runtime integration, exact lowered-request capture,
  and token savings remain unverified. Current RAM is 10.97%, below fit-03's
  25% start gate; paid calls remain closed without a numeric aggregate cap.
- [Iteration 050](../../evals/wrench-gateway-model-research/iteration-050-tool-profile-snapshot-hardening-20260927.md)
  adds aggregate byte limits to tool-inventory hashing and builds immutable
  selector snapshots without executing accessors. Three regression cases
  were added; the resulting 13-case suite was not run because RAM varied
  between 9.70% and 10.12% free.
- New architecture-specific LoRA evidence directly studied Qwen3.5-0.8B: its
  attention-only profile used 24 modules / 1.08M trainable parameters versus
  186 modules / 10.82M for the all-layer profile, with domain-dependent
  quality/forgetting tradeoffs and weak sub-1B HumanEval results. This is a
  non-Wrench, single-seed preprint, not a result for our synthetic controller.
  The reviewed Wrench runner now has an attention-only candidate profile, and
  preflight 04 confirms target selection and one-step compatibility only. No
  profile has a quality result. Any training protocol change needs a fresh
  review, candidate-specific preflight, new run identity, and the existing
  resource gates.
- The third independent proof-spec critique found that the previous design was
  not yet preregistration-ready. The linked proof design now locks the tested
  arm, workload sampling frame, paired workspace resets/order, orthogonal
  outcome and route fields, family-wise power plan, escalation definition,
  cache-safe token accounting, all-in labor/hardware cost, and numeric
  day-long gates. The powered sample size remains uncomputed until a
  rights-cleared target workload and independent cluster counts are frozen;
  no product test may begin under an unpowered convenience sample.

## Stop conditions

Stop before training or inference if exact model identity, synthetic split
lineage, adapter targets, dependency compatibility, current 10% RAM/VRAM
reserve, destination free space, storage reservation, or output bound is
unknown. Stop a running job as soon as a reserve is breached. Stop routing if
the active gateway route, account/cost cap, model identity, or usage telemetry
cannot be pinned. Never tune on a held-out set after exposure.

## Hourly continuation

One active hourly heartbeat, `wrench-hourly-token-reduction-monitor`, continues
this full goal in the current Codex thread. Each run rechecks live processes,
hardware, storage, gates, user direction, and evaluation evidence, then makes
one bounded contribution. When a hard gate blocks model execution, it continues
independent no-cost research or protocol work and preserves the failure for a
new reviewed attempt. The duplicate `wrench-gateway-research` heartbeat is
paused to prevent overlapping runs. The active heartbeat does not authorize
frontier spend, held-out access, training outside the staged protocol, or
production enablement.

### Latest candidate preflight and route gate (2026-09-27)

The screen-02 trainer exposes the `softmax-attention-only` profile: 24 q/k/v/o
modules inside `self_attn`; the historical all-projection selector has 186
modules. Assignment 04 passed exact-hash review of the fit-03 path, focused
tests, protocol and supporting storage/goal records. Candidate preflight 05
then completed one optimizer step on eight synthetic train examples. It
matched 24 modules and 540,672 trainable parameters, recorded minimum free RAM
10.9850%, minimum free VRAM 54.4663%, and zero scratch, then wrote no adapter
and opened no heldout row. This proves target/runtime compatibility only.
Preflight 05's reservation is released. Fit 03 still requires its own fresh
1.5 GB reservation, at least 25% free RAM at start, and at least 10% free RAM
and VRAM throughout. The preflight-era RAM read was 17%; a later 14.1% sample
is current and still below the fit start gate, so no fit is admitted.
At the time of this preflight snapshot, the scorer remained pinned to fit 02.
Iteration 009 supersedes that scorer status: the fit-03 binding correction
passed exact-hash static review, and a successful dev-only inference preflight
is still required before any heldout row can open.

The user reconfirmed use of SubRoute on localhost:4000. Its previously audited
force-mode mapping is OpenRouter/MiniMax M3; provider selection and the
per-request bill still require receipts. Keep generation closed until a
numeric aggregate USD cap is supplied and a hard cap plus receipt validation
are present in the caller. The read-only follow-up is in
[iteration 004](../../evals/wrench-gateway-model-research/iteration-004-subroute-readonly-20260927.md).

### Current attention-only fit path and SubRoute (2026-09-27)

The owner specified SubRoute at `http://127.0.0.1:4000`. The route is used
only for read-only liveness/model inspection until an aggregate USD cap and
hard caller-side cost/receipt guard are authorized. No generation request has
been made.

The active Wrench trainer now selects only the `softmax-attention-only`
profile for candidate work: 24 instantiated `self_attn` q/k/v/o modules and
540,672 trainable parameters. A fresh candidate preflight 05 and fit 03 have
new job identities, reservation floors, receipt paths, and candidate-bound
checks; they cannot inherit preflight 04 or fit 02. The fit adds a 96-step
hard maximum, final adapter inventory/hash comparison after atomic no-replace
rename, and never activates the resulting candidate. The first new static
review passed the preflight-only route but found fit-hardening gaps. The latest
source uses an atomic no-replace rename, records minimum sampled RAM/VRAM
fractions, and requires destination free space of at least the active
reservation plus 5 GiB. Review 03 confirmed the rename and resource summary
but identified that the earlier source added the space thresholds separately.
The summed-headroom fix and new exact hashes are in
[iteration 007](../../evals/wrench-gateway-model-research/iteration-007-storage-headroom-20260927.md).

The latest trainer and fit path passed exact-hash source review 04. Candidate
preflight 05 has now completed and its 250,000,000-byte reservation was
released after accounting for the manifest, resource log, and claim. Review 04
covered the then-current goal and iteration 007; the updated goal and new
iteration 008 record still need an exact-hash package review before fit 03.
The preflight's minimum RAM was 10.9850% and minimum VRAM was 54.4663%; it wrote
no adapter and opened no heldout row. Fit 03 additionally requires at least
25% live free RAM at start, 10% RAM/VRAM throughout, a fresh 1,500,000,000-byte
storage reservation, and destination free space of at least the reservation
plus 5 GiB. The latest host sample had 17% free RAM, below the fit start gate.
Heldout scoring also requires a separately reviewed scorer revision pinned to
fit 03's identity, followed by its own dev-only inference preflight.

### Scorer binding correction review 02 (2026-09-27)

The fit-03 scorer correction now has an exact-hash independent static PASS.
The scorer pins the reviewed trainer source SHA-256 and exact ordered list of
24 attention projection targets, then checks profile, parameter count, fit
mode, preflight mode, and the exact 96-step receipt before any heldout marker
or content read. Assignment
`WRENCH-GW-FIT03-SCORER-CORRECTION-REVIEW-20260927-02`, nonce
`26a51e87-1d83-44d4-a52a-40d8216f89e9`, returned PASS with all six reviewed
file hashes unchanged before and after. See [iteration 009](../../evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md)
for the exact identities and scope.

The scorer-binding pytest module was added, but could not be run because
`pytest` is absent from both the system Python and the repository's Python
3.11 virtual environment. A no-bytecode manual check of the same verifier
accepted one matching receipt and rejected five mismatched identities or fit
properties. This is narrower than running the test module. Fit 03 remains
blocked by the 25% free-RAM start gate; after that gate passes it still needs
its own admission, and heldout scoring still needs a successful fresh
dev-only inference preflight. No heldout row, model inference, SubRoute
generation, adapter activation, or paid work occurred.

### Model scope and SubRoute read-only confirmation (2026-09-27)

The owner broadened the LoRA candidate scope from the already-present 0.8B
checkpoint to any pinned model below 10B parameters that runs smoothly on
this host, subject to candidate-specific inventory, runtime/LoRA compatibility,
storage, and live resource gates. Iteration 010 records the updated model
recommendation and sources. Its live read-only SubRoute check returned 200
from `/health/liveliness`, listed 19 aliases, and projected the `openrouter`
alias as MiniMax M3 at configured rates of $0.30/M input and $1.20/M output.
The selected upstream provider remains unknown until a generation receipt.
No generation request was made, and the numeric aggregate USD cap is still
unspecified. Current RAM free is 15.63%, below fit 03's 25% start requirement;
the storage checker reports 10,955,597,992 actual bytes plus 16,103,000
reserved bytes, within the 50 GB ceiling. See [iteration 010](../../evals/wrench-gateway-model-research/iteration-010-model-scope-route-controls-20260927.md).

### SubRoute source audit and current gates (2026-09-27)

The source-backed SubRoute mapping is `openrouter` to
`openrouter/minimax/minimax-m3`, using the LiteLLM image pinned by digest in
the local Compose file. The live container reports LiteLLM 1.103.0, while the
host project metadata declares 1.101.0. A local call to the installed
OpenRouter parameter mapper with `drop_params=True` removed a top-level
`provider.max_price`, `provider.only`, and `provider.allow_fallbacks` object.
The explicit `extra_body` path and public proxy forwarding still need a
no-spend integration check. SubRoute has `disable_spend_logs: true`; its
provider usage panel reads aggregate credits rather than per-generation
provider and billed-cost receipts. This route is not yet ready for paid
comparison. The user has not provided a numeric aggregate USD cap. No
generation was sent. See
[iteration 011](../../evals/wrench-gateway-model-research/iteration-011-subroute-source-audit-20260927.md).

The current live host sample has 15.34% free RAM, below fit 03's 25% start
gate, with 15,264 MiB of 16,311 MiB VRAM free. Training remains stopped. The
iteration 011 documentation reservation was released after accounting for its
files; no model or provider artifact was produced.

### Installed SubRoute adapter mapping probe (2026-09-27)

Using LiteLLM 1.103.0 inside the already-running container, the installed
OpenRouter mapper was called locally with `drop_params=True`. Both an ordinary
top-level `provider` object and `optional_params.extra_body.provider` lost
`max_price`, `only`, and `allow_fallbacks`; the constructed outbound body
contained only the synthetic message, model slug, and OpenRouter usage flag.
The read-only public OpenAPI schema also omits `provider` and `extra_body`,
though that schema alone does not prove raw JSON rejection. This was a
no-generation adapter check. Source tracing confirms the normal public route
passes request data through `llm_router.acompletion(**data)` and the SubRoute
hook only rewrites model/routing metadata, so the normal request reaches the
mapper that dropped both control forms. No public-proxy HTTP call was made.
The route remains force-mapped to a paid model. See
[iteration 012](../../evals/wrench-gateway-model-research/iteration-012-openrouter-mapper-probe-20260927.md).

The current resource sample has 15.39% free RAM, below fit 03's 25% start
gate, and 15,236 MiB of 16,311 MiB VRAM free. A fresh 100,000-byte
documentation reservation covers this route-trace addition and its final
checks; no model or provider artifact was produced.

### SubRoute 4000 boundary decision (2026-09-27)

The owner's existing `http://127.0.0.1:4000` service returned 19 entries from
read-only `GET /v1/models`, including `openrouter`. Its current force-mode
state resolves the alias to the OpenRouter MiniMax M3 configuration. A fresh
local call against the deployed LiteLLM 1.103.0 mapper returned an empty
provider-control mapping, and the generic OpenAI mapper did not recognize the
same top-level OpenRouter controls. This supplements iteration 012; no public
completion POST was made. Exact container, source, and mapper identities plus
probe limitations are in [iteration 013](../../evals/wrench-gateway-model-research/iteration-013-subroute-boundary-decision-20260927.md).

The `codex-sol-advisor` consultation used 879 tokens (488 prompt, 391
completion) and changed the implementation decision: investigate a narrow
post-mapping adapter at the SubRoute-to-upstream boundary, with an isolated
mock-upstream test for outbound controls and per-generation receipts. No
adapter is implemented yet, no paid request was made, and the aggregate USD
cap is still missing. The current sample is 10.9% free RAM, below fit 03's
25% start gate. The 100,000-byte consultation/report reservation, the
100,000-byte source-trace reservation, and the 100,000-byte report-finalization
reservation were released after final storage accounting; no training or
inference ran.

The installed `/utils/transform_request` endpoint is not safe as a substitute
for that mock: its route calls `return_raw_request`, which invokes LiteLLM
completion with a fake API key to force failure and may attempt provider I/O.
The endpoint was inspected in source but not called. Use a separately isolated
mock upstream for the next boundary test; do not POST a transform request to
the active force-mode paid route. See iteration 013 for the exact source paths
and the upstream issue reference.

### Deployed post-mapping seam and current hourly gate (2026-09-27)

The exact LiteLLM 1.103.0 request path awaits the provider's
`async_transform_request`, delegates OpenRouter subclass behavior to
`transform_request`, then sends the transformed request through its OpenAI
client. The SubRoute alias hook runs earlier. Iteration 014 records the
source paths and a proposed MockTransport test that follows the same hook and
provider transformation without external I/O. A stable registration point for
the adapter and metadata survival still need to be demonstrated.

The single `wrench-hourly-token-reduction-monitor` heartbeat remains active;
the duplicate `wrench-gateway-research` heartbeat remains paused. The latest
sample is 14.1% free RAM, above the 10% host reserve but below fit 03's 25%
start gate. The external SubRoute checkout is included in storage accounting.
The 95/5, 95% savings, task quality, and sustained engineering requirements
remain open.

### Iteration 015: SubRoute mock boundary and realistic model split (2026-09-27)

The owner directed use of the existing SubRoute at
`http://127.0.0.1:4000`. Fresh read-only GETs returned HTTP 200 from
`/health/liveliness`, `/models`, and `/openapi.json`. `/models` lists 19
aliases. `/api/active-model` reports `openrouter`, `force`, policy version 4;
`/model/info` resolves that alias to `openrouter/minimax/minimax-m3`, but its
input and output cost fields are null. No completion POST or generation ran.
Current OpenRouter model pages list provider-dependent M3 prices, so neither
the alias metadata nor a catalog price is a per-request route or bill receipt.
The standard M3 route documented by OpenRouter does not accept native `tools`;
the M3 batch route is a separate slug and advertises tool calling. SubRoute's
source metadata was corrected to stop claiming tools for the standard route.
The distinct SubRoute `minimax` alias uses MiniMax's native API; its official
M3 tool-use guide shows Chat Completions function calling. The active force
route is still `openrouter`, so this does not establish tool support on the
currently selected route or authorize changing its policy.
See [iteration 015](../../evals/wrench-gateway-model-research/iteration-015-subroute-mock-boundary-20260927.md).

A narrow source adapter now wraps only LiteLLM's OpenRouter
`transform_request`, validates Wrench provider-control metadata, and moves
OpenRouter body fields into the OpenAI SDK's supported `extra_body` envelope.
The 4-test local `httpx.MockTransport` suite passed against the deployed
LiteLLM 1.103.0 package. The first attempt exposed an SDK error on top-level
`usage`; the envelope adjustment then passed. This proves request JSON
serialization at the SDK boundary only. It does not exercise the public proxy,
prove metadata survives the router hook, verify real upstream selection or a
cost receipt, or establish live deployment. Independent review found the
marker is optional and the monkeypatch targets a private method; the live
process was not restarted. No paid Wrench call is ready.

The practical model roles remain separate: deterministic code performs exact
search, compaction bookkeeping, source retention, and verification; the
Wrench LoRA learns bounded context/route proposals; a small coding worker
handles patch/test episodes; SubRoute is the stronger fallback. Keep the
already-present 0.8B as the first low-cost controller candidate, then test
Qwen3.5-2B only if frozen results show a capacity limit. Qwen3.5-4B is the
stronger local coding candidate from the public benchmark screen; Qwen2.5-
Coder-3B remains a simpler compatibility comparison. None has Wrench repo-task
or all-day engineering results. The existing 128 synthetic action labels are
mechanics fixtures, not representative local-completion or savings evidence.

The current host sample is 4,725,344 KiB free of 33,486,624 KiB RAM (14.1%),
above the 10% runtime floor but below the fit-03 25% start gate. The RTX 5060
Ti has 15,256 MiB free of 16,311 MiB VRAM. No model download, inference,
training, or provider call ran. Existing active storage reservations remain
within the strict 50 GB budget; this iteration's reservation is recorded in
the report after final accounting.

### Iteration 016: hourly resource and admission gate (2026-09-27)

At 19:00 UTC the host reported 4,052 MiB free of 32,702 MiB RAM (12.39%).
The RTX 5060 Ti had 15,243 MiB free of 16,311 MiB VRAM and 0% utilization;
C: had 131.24 GiB free. A process-list filter for Wrench training/inference
Python commands found no matching live process. The 0.8B fit-03 start gate
requires 25% free RAM, so no fit or model load was admitted. The read-only
observation is below the 25% gate and only 2.39 percentage points above the
general 10% floor. No unrelated application or service was stopped.

The staged local evidence-selection screen remains explicitly marked
preparation-only. Its exact local Qwen3.5-0.8B snapshot, Python interpreter,
and runtime lock exist, but its required one-shot admission manifest and
screen-specific 13-file inventory are absent. Its protocol additionally
requires a separate exact-run authority record and root review. No screen run,
one-shot marker, model inference, LoRA fit, or paid provider request occurred.

The single `wrench-hourly-token-reduction-monitor` automation remains
`ACTIVE` on its hourly recurrence and targets this thread. It already directs
each run to recheck gates and make one bounded contribution, so no duplicate
automation was created. Storage status before this report update was
`WITHIN_LIMIT`; its 100,000-byte documentation reservation is
`WRENCH-HOURLY-RESOURCE-GATE-RECORD-20260927-01` and will be released only
after final accounting. See [iteration 016](../../evals/wrench-gateway-model-research/iteration-016-hourly-resource-gate-20260927.md)
for the host sample, automation check, and admission findings.

Next experiment gate: take a fresh RAM/VRAM and storage sample; run fit 03
only when its reviewed candidate, reservation, disk-space, and >=25% RAM
start conditions all pass. Continue independent low-resource engineering while
they do not. Keep the screen-01 diagnostic closed until its root review,
inventory, and admission prerequisites are complete.

### Iteration 017: screen-01 inventory review (2026-09-27)

The pinned local Qwen3.5-0.8B snapshot now has a generated 13-file inventory,
bound to its verified manifest and accepted by an independent exact-hash
preparation review. The screen is still **PREPARATION ONLY**: the required
run-specific authority and admission record are absent, and no inference,
training, or provider call ran. The fresh host sample remains below the 25%
fit start gate. See [iteration 017](../../evals/wrench-gateway-model-research/iteration-017-screen01-inventory-review-20260927.md).

### Iteration 018: deterministic E0 context tests (2026-09-27)

Seven focused E0 context/runtime test modules passed, 54 tests total, using an
isolated `pytest==9.1.1` uv cache under the approved Wrench data root. The
default Python lacked pytest; it was not modified. This validates selected
mechanical and accounting invariants on the current worktree, not model
effectiveness, repository task success, provider-token reduction, or the 95%
goal. The screen-01 one-shot inference and LoRA fit remain closed under their
resource/admission gates. See [iteration 018](../../evals/wrench-gateway-model-research/iteration-018-e0-context-focused-tests-20260927.md).

### Iteration 019: SubRoute spend guard and receipt integrity (2026-09-27)

Read-only checks confirm SubRoute `127.0.0.1:4000` is alive and still
force-routes to the `openrouter` alias. The route choice is specified, but a
numeric aggregate USD cap is still absent, so no generation request was made.
The diagnostic runner now requires captured teacher traces, rejects the
SubRoute endpoint for its Wrench arm, preserves unknown token/cost fields as
unknown, and rejects direct calls in both child helpers. Twelve focused tests
passed with no model load or provider request. This is spend/accounting
control evidence, not a model-effectiveness result. The detailed hashes,
storage/resource record, and reservation underestimation are in
[iteration 019](../../evals/wrench-gateway-model-research/iteration-019-teacher-arm-budget-guard-20260927.md).

### Iteration 020: coding-agent context compression refresh (2026-09-27)

Primary-source research found coding-agent context-compression results below
the joint target: SWE-Pruner reports 23%-54% multi-turn token reductions;
Paritok-4B reports 74.3% single-shot context reduction with 86.5% solve-quality
retention (89.3% in its line-numbered setting); and SWE-Pruner Pro reports
backbone-dependent input/call changes. ACON's abstract supports smaller-model
distillation, but not the previously claimed >95% teacher-performance result;
that wording was corrected. The strongest next Wrench hypothesis remains
extractive, intent-conditioned evidence selection with deterministic source
preservation and recovery. No model was downloaded, loaded, trained, or run,
and SubRoute received no generation request. All 95/5/95, 95%-cost, and
sustained-engineering requirements remain unproven. See
[iteration 020](../../evals/wrench-gateway-model-research/iteration-020-context-pruning-literature-refresh-20260927.md).

### Iteration 021: hourly continuation and experiment admission (2026-09-27)

Revalidated `wrench-hourly-token-reduction-monitor`: it is `ACTIVE`, recurs
hourly, targets this thread, and directs each run to inspect current state and
resources, continue one bounded task, preserve the full acceptance goal, and
avoid provider spend without authorization. The duplicate gateway research
heartbeat remains paused, so no second scheduler was created.

At this check RAM was 3,960.8 / 32,701.8 MiB free (12.11%), VRAM was
15,228 / 16,311 MiB free at 1% GPU utilization, and C: had 131.13 GiB free.
No Wrench training or inference process was found; the Python processes were
an unrelated FreeToken daemon and two static HTTP servers, which were left
untouched. The staged Qwen3.5-0.8B fit-03 still fails its 25% free-RAM start
gate. The 12-case screen-01 remains preparation-only: its run-specific
admission JSON is absent, and its protocol permanently consumes the one-shot
fixture after marker creation. The owner's conditional experiment request does
not waive those candidate/run checks. No model or provider request ran.

Storage status including the SubRoute checkout was `WITHIN_LIMIT` before the
report update. The 200,000-byte documentation reservation is
`WRENCH-HOURLY-EXPERIMENT-ADMISSION-20260927-01`; the iteration report records
final accounting and release. See
[iteration 021](../../evals/wrench-gateway-model-research/iteration-021-hourly-experiment-admission-20260927.md).

### Iteration 022: hourly resource recheck (2026-09-27)

A new live sample found 3,376.7 / 32,701.8 MiB RAM free (10.33%), only 0.33
percentage points above the hard 10% operating floor. The RTX 5060 Ti had
15,243 / 16,311 MiB VRAM free at 1% utilization; C: had 131.13 GiB free.
No Wrench training/inference process was live. The fit-03 25% RAM-start gate
still fails, and the screen-01 admission JSON, output, and one-shot marker are
all absent. No experiment was started and no unrelated process was stopped.
The existing hourly heartbeat remains active. See
[iteration 022](../../evals/wrench-gateway-model-research/iteration-022-hourly-resource-recheck-20260927.md).

### Iteration 023: fit memory-path audit (2026-09-27)

The frozen screen-02 trainer already pins the model to the single CUDA device,
uses gradient checkpointing, limits sequence length to 512, and caps the
attention-only fit at 96 optimizer steps. Its fit-03 start gate is 25% free
RAM. At the latest 11.14% sample, the host was about 4.43 GiB below that gate.
The prior full-fit attempt crossed the 10% hard floor during startup, so the
static memory-path review provides no basis to weaken the gate. No code,
training data, adapter, or run protocol changed. See
[iteration 023](../../evals/wrench-gateway-model-research/iteration-023-fit-memory-path-audit-20260927.md).

### Iteration 024: hourly job execution priority (2026-09-27)

Updated the existing `wrench-hourly-token-reduction-monitor` prompt, preserving
its ACTIVE hourly schedule and target thread. Once a reviewed candidate has
passed every exact run gate and there is no duplicate live process, the job
now prioritizes starting and monitoring the bounded local training/evaluation
run in that hour. Fit-03 keeps its 25% free-RAM start requirement. The job is
directed to continue independent work when a gate fails, without substituting
documentation or screen-01 for an admissible full experiment. No duplicate
heartbeat was created. The current 11.05% free-RAM sample remains below fit-03
admission, so this prompt change did not start a run. See
[iteration 024](../../evals/wrench-gateway-model-research/iteration-024-hourly-execution-priority-20260927.md).

### Iterations 025-027: evidence limits and request-byte accounting

The model-role reassessment keeps the first staged feasibility candidate at
0.8B, identifies Qwen3.5-2B as a possible bounded extractive context selector
after a measured capacity failure, and treats a 3B-7B coding worker as a
separate unproven role. Current Wrench evidence does not demonstrate repo-task
completion or all-day engineering. The prior 12.1099% ratio-of-sums result is
synthetic input accounting, not provider-token or cost savings; the 0.8B
general semantic screen remains 0/10 and no Wrench LoRA has a held-out result.
See [iteration 026](../../evals/wrench-gateway-model-research/iteration-026-model-role-reassessment-20260927.md)
and the [model decision reassessment](../../reports/wrench-gateway-model-research/decision-reassessment-20260927.md).

Iteration 027 adds a bounded, content-free request-byte receipt parser and
paired accountant initially hard-bound to OpenCode 2.0.15 and local SubRoute
`127.0.0.1:4000`. Its 7 passing tests use synthetic bodies only. It is not
connected to OpenCode's final transport, and caller-supplied completeness
cannot establish that every request or retry was captured. It reports request
body bytes only; provider tokens, task outcomes, and costs remain unknown. No
SubRoute generation, model load, or LoRA fit ran. The latest RAM sample was
11.67% free, below fit-03's 25% start gate. See
[iteration 027](../../evals/wrench-gateway-model-research/iteration-027-request-capture-accounting-20260927.md).

### Iteration 028: OpenCode 2.0.12 SubRoute hook observer (2026-09-27)

Corrected the parser's version pin to the installed OpenCode 2.0.12 and added
an inert-by-default synthetic-only observer example for the actual
post-lowering `http.request` hook and SubRoute `127.0.0.1:4000`. Seven Node
observer tests and seven Python accountant tests passed. It requires an exact
synthetic prompt marker and a pinned digest of the full normalized request
template, rejects duplicate keys, and writes bounded content-free receipts.
It was not loaded into OpenCode and made no route request. Source inspection
shows later-registered hooks can still mutate the request, so a future isolated
integration must pin observer order and test retries and episode closure. The
live route is force-configured to `openrouter`, and no generation, provider
usage, or billing receipt was observed. RAM remained below the 25% fit-03
start gate. The Wrench LoRA, 95/5 local completion, 95% frontier-token/cost
savings, and sustained engineering remain unproven. See
[iteration 028](../../evals/wrench-gateway-model-research/iteration-028-opencode-http-hook-20260927.md).

Next proof step: verify the reviewed hook in an isolated OpenCode 2.0.12
configuration with a local mock transport, including exception propagation
before transport, request identity, retries, and episode closure. Continue to keep
the local model fit behind the candidate, 25% RAM, storage, and run-specific
admission gates. Keep paid SubRoute requests closed until an explicit numeric
spend cap and caller-side provider/usage/billing receipt controls exist.

#### Iteration 028 hardening update

The first independent review of the initial hook returned **FAIL** because the
expected digest and IDs were caller supplied, the callback did not stop
provider transport, and receipt growth/linkability were insufficiently bounded.
The example now uses a source-controlled exact synthetic fixture, fixed
one-shot output paths, no request/session hashes, and a hook that throws after
capturing metadata. Its updated checks pass: Node **8/8**, Python accountant
**7/7**, and plugin syntax validation. The sink checks existing path components
with `lstat` and `realpath` before and after directory creation. Reviews 4 and
5 returned **CONDITIONAL**: source review addresses the path redirection gap,
but tests do not establish OpenCode runtime exception propagation or zero
transport, and a local directory-replacement race remains. No generation
request was sent to SubRoute. The report preserves the original **FAIL** and
follow-up verdicts. See the post-review addendum in
[iteration 028](../../evals/wrench-gateway-model-research/iteration-028-opencode-http-hook-20260927.md).

### Iteration 029: hourly experiment continuation (2026-09-27)

Revalidated and updated the existing `wrench-hourly-token-reduction-monitor`
in place. It remains the single active hourly heartbeat for this goal, targets
this thread, uses the Northstar skill, and directs the next run to start a
bounded local LoRA/evaluation job when a sub-10B candidate passes its measured
hardware, context, storage, and run-specific gates. No duplicate was created;
the separate gateway-research heartbeat stays paused.

The live recheck found 11.45% free RAM, below fit-03's 25% start gate, and
15,227/16,311 MiB free VRAM on the RTX 5060 Ti. No Wrench inference/training
process was live. Storage remained within the 50 GB ceiling. No model run or
provider call started. The model-size preference is removed, but resource and
candidate gates remain. See
[iteration 029](../../evals/wrench-gateway-model-research/iteration-029-hourly-experiment-continuation-20260927.md).

### Iteration 030: explicit provider-cost accounting (2026-09-27)

Removed `_arm_record`'s implicit `cost_usd=0.0` default; every caller must now
provide a value, and an unknown paid-call cost remains `null`. The focused
offline diagnostic suite passed **13/13**. Live provider calls remain disabled;
this is accounting hardening, not spend-cap enforcement or cost-savings proof.

The current RAM sample was 11.42% free, below fit-03's 25% start gate; VRAM
was 15,224/16,311 MiB free. Storage remained within 50 GB. No training,
inference, or provider request occurred. See
[iteration 030](../../evals/wrench-gateway-model-research/iteration-030-explicit-cost-accounting-20260927.md).

### Iteration 031: SubRoute :4000 route and spend-gate audit (2026-09-27)

The owner specified the existing SubRoute endpoint at `127.0.0.1:4000` for
the frontier comparison. Read-only inspection confirmed force routing through
the `openrouter` alias, which the current SubRoute config maps to MiniMax M3.
The provider-control marker is optional, and route-level `max_price` is not an
aggregate budget. Wrench's existing diagnostic runner still blocks SubRoute
calls; its spend guard is pinned to direct OpenRouter and a different approval
schema. No provider request or route change occurred. A numeric aggregate spend
cap remains required before paid calls. The current 10.9% free-RAM sample is
below fit-03's 25% start gate. The live safe-field model-info projection lists
`$0.30/M` input and `$1.20/M` output for the forced alias, but this identifies
the gateway adapter configuration, not a selected upstream provider or bill.
See
[iteration 031](../../evals/wrench-gateway-model-research/iteration-031-subroute-4000-route-audit-20260927.md).

### Iteration 032: SubRoute metadata capture preparation (2026-09-27)

Added opt-in OpenRouter response-metadata header propagation to the
Wrench-marked SubRoute adapter and corrected its mock test to inspect the
captured HTTP request. Source and test AST parsing passed. The isolated test
command did not reach the test suite because the container image's default
entrypoint treated the unittest arguments as LiteLLM CLI options; the suite
was not retried. The running :4000 gateway was not restarted, so this source
change is not active there. No provider request was sent. A numeric aggregate
spend cap remains unspecified, and the route's per-token price filter is not a
budget. See
[iteration 032](../../evals/wrench-gateway-model-research/iteration-032-subroute-metadata-capture-20260927.md).

### Iteration 033: campaign-wide SubRoute spend caller (2026-09-27)

Added a host-side caller and one SQLite campaign ledger for all separately
approved jobs. It binds approvals to the caller source hash, commit, exact
synthetic case file, route, and provider. A later job cannot reset or raise the
campaign cap; unknown charges keep their full reservation and stop further
calls. The final implementation parses, but its six-test draft result predates
the campaign-wide schema. The final suite was not run because the latest free
RAM sample was 9.78%, below the required 10% floor. Read-only SubRoute config
still specifies zero retries and no fallbacks, but the running process and
metadata propagation remain unverified. No request reached port 4000, and no
spend cap or approval file exists. Model effectiveness and every
95%/95-5/all-day target remain unproven. See
[iteration 033](../../evals/wrench-gateway-model-research/iteration-033-subroute-campaign-budget-caller-20260927.md).

### Iteration 034: hourly goal heartbeat refresh (2026-09-27)

Updated the existing `wrench-hourly-token-reduction-monitor` in place. It
remains the single active hourly heartbeat for this goal and targets this
thread. Its prompt preserves the full 95/5, 95% frontier-token-saving,
quality, all-in cost, and sustained-engineering requirements. It now directs
the next run to recheck current jobs and resources, run the exact-hash
campaign-ledger tests only after the 10% RAM/VRAM floors pass, then test the
4000 request-control path without provider traffic. No Wrench model job or
provider request started. RAM was 7.80% free, below the runtime floor; storage
remained within 50 GB. The goal and all effectiveness claims remain open. See
[iteration 034](../../evals/wrench-gateway-model-research/iteration-034-hourly-heartbeat-refresh-20260927.md).

### Research update: coding-context LoRA evidence and port-4000 check (2026-09-27)

The Paritok-4B paper is a close external match for intent-conditioned,
extractive coding-context compression. Its 300-instance SWE-bench Lite
results report 72.2-74.3% context reduction and 86.5-89.3% retained solve
quality. Its author-reported 39% five-turn full-stack saving and later 72-85%+
session ceilings are not 95% Wrench results; later ceilings are projections.
Treat it as a benchmark reference, not a selected Wrench base or proof of
open-ended engineering. The report records method limits, base-model identity,
hardware mismatch, and the exact safe role suggested for Wrench:
[Paritok coding-compressor addendum](../../reports/wrench-gateway-model-research/paritok-4b-context-compression-addendum-20260927.md).

Following the owner's port-4000 direction, read-only GETs to `/v1/models` and
`/api/active-model` returned HTTP 200. The latter reports `openrouter`, `force`,
policy version 4. No generation request was made. This confirms local
availability, not upstream model selection or billed usage. The aggregate
campaign spend cap remains unspecified, so paid calls stay closed. Current RAM
was 9.65%, below the 10% runtime floor; no tests, inference, training, or
delegation started. All Wrench effectiveness and savings claims remain open.

### Iteration 035: episode and token savings are separate gates (2026-09-27)

The product proof design now makes explicit that `<=5%` frontier-routed
episodes does not imply `>=95%` fewer frontier tokens. The token claim must
pass independently on paired sums of provider-reported tokens, including all
remote retries and verification. If the routed 5% contain 12% of baseline
frontier-token volume, raw full-context calls on those episodes yield only
88% savings; they must be pruned to at most 41.7% of their baseline tokens to
reach the 95% gate, before extra calls. This is an algebraic feasibility
check, not a Wrench benchmark result. See [iteration 035](../../evals/wrench-gateway-model-research/iteration-035-token-weighted-frontier-budget-20260927.md)
and the [product proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md).

### Iteration 036: SubRoute model identity layers (2026-09-27)

Read-only source review resolved the apparent prefix discrepancy: SubRoute's
LiteLLM route is `openrouter/minimax/minimax-m3`, while its adapter test
preserves the upstream OpenRouter model slug `minimax/minimax-m3`. The current
Wrench caller's expected model pin matches the canonical slug, and the
OpenRouter metadata schema documents the `provider`/`model`/`selected` fields
the parser expects. This confirms source-level intent only. No live paid
receipt has confirmed the running gateway's selected endpoint, and generation
remains disabled without the aggregate cap. See
[iteration 036](../../evals/wrench-gateway-model-research/iteration-036-subroute-model-identity-layers-20260927.md).

### Iteration 037: Qwen3.5-2B inventory and SubRoute liveness (2026-09-27)

Requeried the exact pinned Hugging Face revision and reconciled its 13-file
inventory. It totals 4,571,274,023 bytes, 10,244,553 bytes above the earlier
research-report total; the exact revision and per-file sizes are in
[iteration 037](../../evals/wrench-gateway-model-research/iteration-037-qwen-inventory-and-subroute-liveness-20260927.md).
The model remains metadata-only, not downloaded or admitted for a run. The
closest external evidence is Squeez's Qwen3.5-2B LoRA for extractive
tool-output pruning: 92% input-token removal, 0.86 recall, 0.80 F1 on its
curated test. That motivates a narrow capacity challenger but misses Wrench's
95% token goal and proves no Wrench task quality.

The owner-designated SubRoute `:4000` returned HTTP 200 on read-only
`/api/active-model` and `/v1/models`; the active projection remains
`openrouter` / `force` / policy version 4. No POST, provider call or spend was
made. RAM was 3,216.9/32,701.8 MiB free (9.84%), below the 10% runtime floor,
so no tests, inference, training, or delegation started. The numeric campaign
spend cap remains unprovided. All effectiveness, savings and sustained
engineering claims remain open.

### Iteration 038: OpenCode no-provider hook registration seam (2026-09-27)

Split the synthetic no-provider plugin setup from its OpenCode SDK adapter and
added focused coverage for disabled behavior, hook registration, fail-closed
callback order, content-free receipt handling, and disposal. OpenCode's pinned
v2.0.12 source awaits `http.request` hooks before invoking the handler, but the
installed runtime behavior remains unverified. The current RAM sample was
8.45%, so the new suite and runtime preflight did not run. The change and
remaining evidence are recorded in
[iteration 038](../../evals/wrench-gateway-model-research/iteration-038-opencode-hook-registration-seam-20260927.md).

### Iteration 039: SubRoute OpenCode setup and fresh admission (2026-09-27)

Added a v2.0.12 custom-provider example for `wrench-subroute/openrouter`,
pointing at `http://127.0.0.1:4000/v1` and keeping it out of OpenCode's default
model selection. The setup uses a process environment variable for the
optional gateway credential and does not wire the campaign spend ledger into
arbitrary OpenCode traffic. Its client-side token limits are not cost
enforcement. No active user config was changed.

Fresh read-only GETs returned HTTP 200. `/model/info` now reports the forced
`openrouter/minimax/minimax-m3` alias at `$0.30/M` input and `$1.20/M` output,
and advertises function-calling and tool-choice support. These fields conflict
with earlier route metadata/source findings and are not evidence of a
successful tool round trip, selected provider, or bill. Historical iterations
remain unchanged; resolve the discrepancy through a capped request only after
the numeric campaign spend cap and durable receipt checks are in place.

The completed preflight-05 manifest confirms a single compatibility optimizer
step over eight synthetic train rows, no adapter output, and no held-out read.
Its minimum logged free RAM was 10.985%; this did not meet fit-03's separate
25% start gate. Current free RAM is 8.76%, so no tests, inference, or fit were
admitted. The hash-bound fit protocol's final sentence still says preflight 05
has not run; it remains unchanged to preserve its exact-hash review and needs a
reviewed amendment before fit-03 admission. See
[iteration 039](../../evals/wrench-gateway-model-research/iteration-039-subroute-opencode-setup-20260927.md)
and the [OpenCode setup example](../../../examples/opencode_v2_subroute_capture/SUBROUTE_SETUP.md).

### Iteration 040: hourly experiment continuation (2026-09-27)

Updated the existing `wrench-hourly-token-reduction-monitor` heartbeat in
place. It remains ACTIVE, runs hourly, and targets this thread. Its refreshed
prompt preserves the under-10B hardware-permitted model scope, the complete
95% local / 5% frontier / 95% token reduction criteria, paired success and
all-in cost requirements, all-day engineering evidence, and iteration
reporting. It prioritizes an admitted LoRA run when every gate passes; below
the 10% RAM or VRAM floor it limits work to source-level/research progress and
prohibits runtime jobs and delegation. It retains the existing `:4000`
SubRoute and spend-cap boundary.

The automation tool returned `Updated automation` with status `ACTIVE`. Its
local record confirms the hourly recurrence and target thread ID
`01a0e15d-1974-7691-9584-372374c98560`; the saved prompt contains all primary
targets, the under-10B condition, the resource floor, and an hourly concrete
advance requirement. No duplicate heartbeat was created. This verifies the
stored schedule and prompt, not that a post-update hourly firing has already
occurred.

The current sample is 3,228.3/32,701.8 MiB free RAM (9.87%), 15,222/16,311 MiB
free VRAM, and 132.19 GiB free on C:. Storage is `WITHIN_LIMIT` at
10,990,214,291 actual bytes plus 8,103,000 bytes in existing reservations
before this documentation job. No tests, model work, or delegation started
below the RAM floor. The goal remains active; the full effectiveness criteria
are unproven. See [iteration 040](../../evals/wrench-gateway-model-research/iteration-040-hourly-automation-refresh-20260927.md)
and the [hourly continuation setup](../../reports/wrench-gateway-model-research/hourly-continuation-setup-20260927.md).

### Iteration 041: OpenCode v2.0.12 context hook and SubRoute (2026-09-27)

The owner selected the existing `http://127.0.0.1:4000` SubRoute. Read-only
GETs confirmed service liveness and the forced `openrouter` alias. A numeric
aggregate USD cap was not provided, so no provider POST or generation ran.

Pinned OpenCode v2.0.12 source confirms `session.context` runs before request
construction and permits bounded changes to messages, system text, options,
and tool schemas. The current Wrench projection and E0 composition still label
their contract `2.0.15`, so they cannot yet substantiate compatibility with the
installed `2.0.12` runtime. Preserve historical receipts and add a separate
versioned adapter before claiming integration. Removed tool schemas also
remove the corresponding executable tools, which makes any pruning policy a
paired capability and retained-success experiment.

RAM was 10.08% free and VRAM 93.35% free. No runtime checks ran at this narrow
RAM margin. Full effectiveness targets remain unproven. See
[iteration 041](../../evals/wrench-gateway-model-research/iteration-041-opencode-v2012-context-hook-20260927.md).

### Iteration 042: versioned OpenCode context adapter (2026-09-27)

Added explicit v2.0.12 version identity through offline preparation, context
projection, prepared insertion, and lifecycle receipts while preserving the
v2.0.15 default and its historical receipt identity. Cross-version joins,
projections, observations, and transitions now fail closed. Regression tests
cover both versions and unknown-version rejection, but were not run.

The existing SubRoute `:4000` again passed read-only liveness and active-model
GETs. No paid POST occurred. RAM was 10.12% free, below fit-03's 25% start
requirement and too close to the 10% reserve for safe tests or runtime
preflight. The adapter is not yet wired to the OpenCode plugin, and no
effectiveness or token-savings claim follows. See
[iteration 042](../../evals/wrench-gateway-model-research/iteration-042-versioned-opencode-context-adapter-20260927.md).

### Iteration 043: SubRoute port 4000 reconfirmation (2026-09-27)

The owner directed use of the existing `http://127.0.0.1:4000` setup. Fresh
read-only GETs returned HTTP 200 for liveness, active-model, and model inventory;
the route reports the forced `openrouter` alias, policy version 4, and 19 model
entries. The existing OpenCode profile remains the selectable
`wrench-subroute/openrouter` model at `:4000/v1`, not a default. No active
OpenCode or SubRoute configuration was changed. The numeric aggregate spend cap
is still unspecified, so no POST or provider generation ran. RAM was 9.96%
free, below the runtime floor, so tests and runtime preflight stayed closed.
See [iteration 043](../../evals/wrench-gateway-model-research/iteration-043-subroute-4000-confirmation-20260927.md).

### Iteration 044: request-attempt gap guard (2026-09-27)

The paired OpenCode byte accountant now rejects duplicate or missing
zero-based attempt indices within each episode arm, with focused regression
cases added. Static AST and whitespace checks passed; the unit test did not run
because RAM was 9.95% free. This does not prove complete transport capture:
`capture_complete` is caller-supplied, the accountant is not wired to OpenCode,
and omitted trailing calls can still escape detection. No model or provider run
occurred. See
[iteration 044](../../evals/wrench-gateway-model-research/iteration-044-request-attempt-gap-guard-20260927.md).

### Iteration 045: Qwen2.5-Coder-7B QLoRA fit screen (2026-09-27)

Added a fully pinned 14-file inventory for the 7.61B code-specialized
Qwen2.5-Coder-7B-Instruct model, totaling 15,242,807,397 bytes. Qwen's QLoRA
memory profile for a related 7B model makes a 1,024-token run on this 16,311
MiB GPU plausible, but not proven. The current Wrench trainer is Qwen3.5-only
FP32, and this environment lacks bitsandbytes; a candidate-specific runner and
dependency inventory are required. Conservative storage projections remain
under 50 GB, including a second full model copy. No model or packages were
downloaded. RAM is 10.08% free, below the fit start gate, so no runtime work
ran. See [iteration 045](../../evals/wrench-gateway-model-research/iteration-045-qwen25-coder-7b-fit-screen-20260927.md)
and the [candidate report](../../reports/wrench-gateway-model-research/qwen25-coder-7b-fit-feasibility-20260927.md).

### Iteration 046: model choice and proof refresh (2026-09-27)

The new comparison prioritizes pinned Qwen3.5-4B for the next coding-worker
fit preflight, with Qwen2.5-Coder-7B retained as a code-specialist challenger.
The Wrench controller remains a separate LoRA problem: test the staged
Qwen3.5-0.8B finite-action candidate first and advance to 2B only for a
measured capacity failure. The Qwen3.5-4B inventory is complete at revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 9,342,907,469 bytes. Its
published BF16-LoRA estimate is about 10 GB, not an RTX 5060 Ti fit result.

The evidence audit clarifies that the 0/10 base screen did not test a Wrench
LoRA, the one-step preflight did not show learning, and the existing synthetic
route mix cannot achieve 95% LOCAL / 5% FRONTIER even with perfect predictions.
At iteration 046, RAM was 7.98% free; the latest iteration-048 sample is
8.86%, still below the runtime floor, so no model, tests, or runtime job can
start. Fresh read-only SubRoute GETs at `:4000` returned liveness, 19 aliases,
and the configured `openrouter/minimax/minimax-m3` mapping; no POST or spend
occurred. The missing numeric cap and billed-usage receipt gate remain. See
[iteration 046](../../evals/wrench-gateway-model-research/iteration-046-model-choice-and-proof-refresh-20260927.md),
[iteration 047](../../evals/wrench-gateway-model-research/iteration-047-subroute-live-readonly-20260927.md),
[iteration 048](../../evals/wrench-gateway-model-research/iteration-048-opencode-tool-schema-pruning-20260927.md),
and the [decision and proof report](../../reports/wrench-gateway-model-research/model-choice-and-proof-plan-20260927.md).

### Iteration 049: SubRoute 4000 and tool-profile prototype

The owner reconfirmed the existing SubRoute at `http://127.0.0.1:4000`.
Read-only GETs returned HTTP 200 for liveness, active-model, and model
inventory; the active alias is `openrouter`, mode is `force`, policy version
is 4, and 19 aliases are listed. No POST, provider generation, or route
configuration change occurred; the aggregate USD cap is still missing.

Added a separate source-only context-hook prototype scoped to provider ID
`wrench-subroute`. It accepts only a reviewed profile ID bound to the exact
tool-schema inventory, removes schemas for one request, and passes through on
uncertainty. The plugin is not registered or activated. Its ten synthetic
Node tests passed; OpenCode v2.0.12 runtime ordering, final HTTP request
capture, tool recovery, and actual token reduction remain unverified.

RAM after the tests was 10.97% free, below fit-03's 25% start gate. Storage,
including SubRoute, was WITHIN_LIMIT at 10,992,728,920 actual bytes plus
8,223,000 bytes in active reservations. See [iteration
049](../../evals/wrench-gateway-model-research/iteration-049-subroute-4000-tool-profile-prototype-20260927.md)
and the [profile prototype](../../../examples/opencode_v2_subroute_tool_profiles/README.md).

### Iteration 050: harden tool-profile snapshots

Confirmed the hourly automation record: wrench-hourly-token-reduction-monitor
is ACTIVE on an hourly interval and targets this thread; the older duplicate
gateway heartbeat is PAUSED.

The tool-profile prototype now enforces an aggregate UTF-8 inventory budget
and gives the local selector a frozen JSON snapshot. Accessors are rejected
without execution, and unsupported or oversized input keeps the full tool
set. Three regression cases were added. The current 13-case suite was not run;
the previous 10/10 result applies only to Iteration 049's source hash.

RAM varied from 9.70% to 10.12% free, with the latest sample at 10.12%.
Training and inference remain below the separate 25% RAM start gate. Storage
including SubRoute remains WITHIN_LIMIT. No provider request occurred, and
the 95/5 routing, 95% frontier-token savings, 95% cost reduction, and
all-day engineering evidence remain unproven. See [iteration
050](../../evals/wrench-gateway-model-research/iteration-050-tool-profile-snapshot-hardening-20260927.md).

### Iteration 051: refresh the hourly continuation

Updated the existing Codex heartbeat wrench-hourly-token-reduction-monitor.
It remains ACTIVE, hourly, and attached to this thread; the older
wrench-gateway-research heartbeat remains PAUSED. The active prompt now
recognizes the Iteration 050 prototype, marks its current 13-case suite
unverified, and directs the next run to verify it only when RAM and VRAM can
remain above the 10% reserves, then proceed to isolated no-provider OpenCode
v2.0.12 request capture. The complete acceptance criteria and :4000 spending
gate remain in the prompt.

Current RAM was 10.03% free, too close to the reserve to start tests or model
work. No provider request, training, inference, benchmark, or delegation ran.
See [iteration
051](../../evals/wrench-gateway-model-research/iteration-051-hourly-continuation-refresh-20260927.md).

### Iteration 052: owner confirms SubRoute at port 4000

The owner confirmed that experiments should use the existing SubRoute setup at
`http://127.0.0.1:4000`. Fresh read-only GETs returned HTTP 200 for liveness,
active-model, and model inventory. The live route reports alias `openrouter`,
mode `force`, policy version 4, and 19 model entries. The OpenCode setup example
uses `http://127.0.0.1:4000/v1` and selectable model
`wrench-subroute/openrouter`; it does not change the active OpenCode config.

The endpoint confirmation supplies no aggregate USD cap. The forced route may
send a request to a remote provider, so no POST, generation, credential read,
or OpenCode configuration change occurred. Independent source reviews also
found that the synthetic OpenCode observer has not proven transport-level
provider suppression, the legacy teacher capture still needs a verified
SubRoute caller seam, and the 0.8B inventory/scorer reviews are preparation
only. None is live model or savings evidence.

Free RAM was 3,260.2 / 32,701.8 MiB (9.97%), below the 10% reserve. No tests,
OpenCode runtime, inference, training, benchmark, packaging, or delegation ran.
The storage checker including SubRoute remained within the 50 GB limit. The
goal stays active; 95/5 routing, 95% frontier-token savings, 95% all-in cost
reduction, and sustained engineering remain unproven. See [iteration
052](../../evals/wrench-gateway-model-research/iteration-052-subroute-4000-owner-confirmation-20260927.md).

### Iteration 053: reconcile the SubRoute caller path

Current-source inspection confirms the bounded SubRoute teacher-capture path
already exists in `tools/capture_subroute_teacher_traces.py`, backed by the
shared campaign ledger in `tools/subroute_budget_guard.py`. It writes the
same teacher-trace schema consumed by `tools/run_diagnostic_worker_arms.py`.
This is distinct from the older direct OpenRouter capture path; route work
should use the guarded caller rather than duplicate or silently reuse the
legacy one.

The exact caller, ledger, test, and diagnostic-runner hashes still match the
Iteration 033/036 receipts. Source contracts cover hash-bound human approval,
synthetic-only cases, pre-dispatch worst-case reservations, campaign-wide
spend limits, no retries/fallbacks, and provider/model/usage/cost settlement.
The current focused tests remain unrun, and SubRoute's incoming metadata to
final OpenRouter request path is not verified end to end. The hourly heartbeat
was updated and verified ACTIVE/hourly to prioritize this focused source test,
then metadata-path verification and the isolated OpenCode v2.0.12 transport
check when resource gates allow.

RAM was 10.25% free, only 0.25 percentage points above the runtime floor;
focused tests and delegation stayed closed. Fit-03 still requires 25% free RAM
at start. No provider request occurred and the numeric spend cap remains
unanswered. The route, LoRA effectiveness, 95/5 routing, 95% token savings,
95% all-in cost reduction, and sustained engineering remain unproven. See
[iteration
053](../../evals/wrench-gateway-model-research/iteration-053-subroute-caller-reconciliation-20260928.md).

### Iteration 054: make tool pruning cache-stable and recoverable

An additional primary-source review of multi-turn gateway economics reinforces
tool-schema filtering as the first mechanical savings lever. The cited study
reports 21K-57K tokens removed per typical request in its own MCP-heavy
Claude/Codex setup, while content compression had a much smaller immediate
cache-priced effect. These quantities are not Wrench estimates and do not
prove 95% savings.

Inspection of the current OpenCode tool-profile prototype found it selects a
profile again on each request and deletes omitted schemas without an explicit
schema-discovery/expansion tool. This can invalidate provider prompt caches
and can strand later turns without needed tools. The prototype README now
marks both gaps and blocks engineering enablement until session freezing,
bounded schema recovery, and v2.0.12 runtime verification exist. The hourly
heartbeat was refreshed to prioritize those gaps after focused SubRoute
caller checks pass.

At 2026-09-28 01:53 UTC, RAM was 10.40% free and GPU VRAM was 15,215/16,311
MiB free. RAM was only 0.40 percentage points above the 10% floor, so no tests,
OpenCode runtime, inference, training, benchmark, or delegation ran. No model
was downloaded and no provider call was sent. The 95/5, 95%-token, 95%-cost,
and all-day engineering requirements remain unproven. See [iteration
054](../../evals/wrench-gateway-model-research/iteration-054-cache-stable-tool-pruning-20260928.md)
and the [tool-profile prototype](../../../examples/opencode_v2_subroute_tool_profiles/README.md).

### Iteration 055: verify the live SubRoute at port 4000

Following the owner's direction, read-only GETs to the existing SubRoute at
`http://127.0.0.1:4000` returned HTTP 200 for `/health/liveliness`,
`/api/active-model`, and `/v1/models`. The active route is `openrouter` in
`force` mode, policy version 4; the model endpoint returned 19 entries. The
gateway is reachable and confirmed as the comparison route, but its forced
remote provider means generation remains behind the numeric USD cap and the
shared caller's pre-reservation gate. No POST, provider traffic, credential
read, or spend occurred. The generic `/health` path timed out; the SubRoute
liveness endpoint is `/health/liveliness`.

Free RAM was 3,348.4 / 32,701.8 MiB (about 10.24%), too close to the 10%
runtime floor for tests or model work. The next local step remains the exact-
hash SubRoute capture/budget checks and metadata-path verification once
resources recover. The LoRA, 95/5 task routing, 95% frontier-token savings,
95% all-in cost reduction, and sustained engineering remain unproven. See
[Iteration 055](../../evals/wrench-gateway-model-research/iteration-055-live-subroute-4000-20260928.md).

### Iteration 056: pin the session-profile key to the OpenCode V2 contract

The current official OpenCode V2 plugin reference types the context hook with
a read-only `sessionID`, agent, and mutable tool map, and says agent-loop
context hooks include tool-driven continuations. This resolves the API-level
session key for freezing a tool profile. It does not verify the installed
v2.0.12 runtime. The disabled prototype README now specifies reuse by session
and full inventory hash, fail-through on missing or changed identity/state,
required execution/verification tools, and bounded restoration from the
original schema map without permission changes.

RAM was 9.83% free, below the 10% runtime floor; no tests, runtime, model job,
or delegation ran. No provider request or spend occurred. The next concrete
step is implementing the session cache and expansion helper, then verifying
the exact installed runtime without upstream transport. The Wrench LoRA,
95/5 success, 95% frontier-token reduction, 95% all-in savings, and all-day
engineering remain unproven. See [Iteration
056](../../evals/wrench-gateway-model-research/iteration-056-opencode-session-hook-contract-20260928.md).

### Iteration 057: implement session-frozen profiles and schema recovery

Added opt-in session state to the disabled tool-profile prototype. It freezes
one selection per session and full schema hash, fails through on missing
identity or inventory drift, and bounds its cache by session count and name
index size. Added an always-visible schema-expansion helper with one-shot name
discovery and limits on names, calls, and bytes. Seven source cases raise the
suite to 20; they remain unrun. Static review then found that profile hashes
must bind the exact registered expansion-tool schema. Added a shared exported
schema definition for profile generation and tool registration.

RAM was 9.61% free, below the 10% runtime/test floor. The SubRoute at
`127.0.0.1:4000` remains live on read-only GETs, forced to `openrouter`; no
generation or spend occurred. The prototype is not installed. Its in-memory
cache is lost on plugin restart, and installed v2.0.12 behavior, final HTTP
request, local LoRA selection, task success, token/cost savings, and sustained
coding are still unverified. Next add restart-safe state handling, then run
the focused suite and no-provider runtime check after resource recovery. See
[Iteration
057](../../evals/wrench-gateway-model-research/iteration-057-session-profile-expansion-prototype-20260928.md).

### Iteration 058: persist session choices behind the Wrench storage boundary

Added restart restoration for frozen session profiles and expansion state to
the disabled OpenCode tool-profile prototype. It uses an injected store with a
process-wide atomic claim contract, caps claims at 256 and state records at
128 KiB, hashes session IDs in keys, and persists a decision before filtering
tools. Three source cases cover simulated restart restoration, restart-time
inventory drift, and storage failure. The suite is now 23 cases, not run.

OpenCode documents plugin-scoped durable JSON storage but does not document
its Windows backing path. The prototype therefore does not write into
`ctx.storage`; Wrench has no approved adapter under `C:\\wrench-slm-data` yet.
Until that adapter and its storage admission exist, session mode cannot be
enabled. No tests or runtime requests ran because RAM was 9.74% free, below
the 10% floor. Read-only SubRoute checks still identify the forced `openrouter`
route at `127.0.0.1:4000`; no provider POST or spend occurred, and the numeric
campaign cap remains unspecified. See [Iteration
058](../../evals/wrench-gateway-model-research/iteration-058-durable-session-profile-state-20260928.md).

Iteration 057's final next-step sentence referred to a 19-case suite by typo;
the suite at that point contained 20 cases. Historical report text remains
unchanged. The Wrench LoRA, 95/5 completion mix, 95% frontier-token reduction,
95% cost reduction, and all-day engineering ability remain unproven.

### Iteration 059: launch the bounded LoRA experiment when hardware admits it

Updated the existing ACTIVE hourly heartbeat; no duplicate was created. The
owner explicitly directed that the local experiment proceed when this machine
can run it. The prompt now instructs the next hourly run to start the pinned
Qwen3.5-0.8B controller experiment as soon as the exact protocol gates pass,
and keeps the choice open to other fully inventoried models below 10B if Wrench
evidence justifies them.

The fresh host sample was 3,283.4 / 32,701.8 MiB RAM free (10.04%),
15,235 / 16,311 MiB VRAM free, and 141.04 GB free on C:. The existing fit-03
protocol requires 25% free RAM at start and at least 10% RAM/VRAM throughout.
The current sample is only marginally above the operating floor and below the
training gate, so no runtime or experiment ran. No Wrench model job was active.
The hourly job keeps training closed from 10% to 25%, then starts the admitted
local experiment directly when its storage, identity, runtime, and authority
gates also pass. No paid SubRoute request is authorized by the port-4000
selection because the separate numeric campaign cap is still absent.

Storage status was within the 50 GB ceiling. See [Iteration
059](../../evals/wrench-gateway-model-research/iteration-059-hourly-experiment-trigger-20260928.md).

### Iteration 060: reconcile the preflight receipt and fit-package review gate

The hourly gate recheck found 3,165.3 / 32,701.8 MiB RAM free (9.68%),
15,225 / 16,311 MiB VRAM free, and 141.04 GB free on C:. No Wrench model
process was active. Fit 03 requires at least 25% RAM at process start and 10%
RAM/VRAM throughout; no model runtime, fit, test, or provider request started.

Read the existing preflight-05 manifest and resource receipt. The manifest is
`PREFLIGHT_COMPLETED`, binds the current trainer hash
`62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` and
current protocol hash
`EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A6E75EE12DACE33B5`, and
records one optimizer step on eight synthetic rows, 24 attention targets,
540,672 trainable parameters, no adapter output, and no heldout read. The
preflight need not be repeated unless those identities change. The protocol's
trailing sentence saying preflight 05 never ran is stale; leave the
hash-bound protocol unchanged and prefer the manifest plus Iteration 008.

There is conflicting fit-package review bookkeeping. The GOAL status heading
had claimed review 05 passed, while Iteration 008 says a fresh exact-hash
package review is required before fit 03. No matching review report was found
in the current `docs/evals` or `docs/reports` trees. Iteration 009's independent
scorer-binding review covers the current trainer, scorer, and protocol hashes,
but does not cover the current goal/Iteration 008 package scope. Mark review 05
unverified and obtain one fresh independent review before fit; do not rerun the
already hash-matched preflight.

Updated the ACTIVE hourly heartbeat to use the completed preflight receipt,
resolve that exact-hash review gap, and start fit 03 directly when RAM, storage,
disk headroom, and remaining exact gates pass. It does not wait for another
user approval for the bounded local experiment and keeps paid SubRoute traffic
separately closed. Storage was `WITHIN_LIMIT` at 10,993,249,229 actual bytes
before a 100,000-byte documentation reservation. No advisor or subagent was
used because RAM was below the delegation floor and the immediate gate is
explicit in the protocol. The local LoRA, 95/5 success, 95% frontier-token and
all-in cost reductions, and all-day engineering remain unproven. See
[Iteration 060](../../evals/wrench-gateway-model-research/iteration-060-preflight-fit-gate-reconciliation-20260928.md).

## Iteration 061: current resource and SubRoute recheck

The latest hourly check measured 2,515.7 / 32,701.8 MiB free RAM (7.69%),
15,245 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 140.77 GB free on C:.
No Wrench training, inference, or benchmark process was found. The only
matching process was the PowerShell command performing this check. RAM is
below the 10% operating floor, so no tests, runtime, inference, training,
benchmark, or delegation ran.

The storage checker reported `WITHIN_LIMIT`: 10,991,205,108 bytes actual and
8,103,000 bytes in active reservations before this iteration's 100,000-byte
documentation reservation. C: has ample volume headroom. The 100,000-byte
reservation is recorded under
`WRENCH-HOURLY-GATE-RECHECK-ITER061-20260927` and must be released after the
report is accounted for.

At the owner's direction, the existing SubRoute `http://127.0.0.1:4000` was
checked using only `GET /health/liveliness` and `GET /models`; both returned
HTTP 200 and the list contained 19 aliases. The `openrouter` row only exposed
the alias and null context/pricing metadata. This confirms local liveness,
not the selected upstream provider or bill. No completion POST was sent.
The campaign USD cap remains absent; provider generation remains closed.

Static source inspection confirmed the trainer's resource monitor samples
RAM, VRAM, and scratch every second, interrupts the main thread on a reserve
or log/scratch breach, and checks breach state between training batches. Its
finalizer re-reads the resource log, checks GPU identity and reserve floors,
and converts an apparent completion to `FAILED_RESOURCE_FINALIZATION` if a
breach is found. Adapter output is staged, inventoried, size-checked, and
finalized without replacing an existing candidate. This was source inspection,
not an execution result; it is not the independent package review still
required for fit 03.

The completed preflight 05 receipt remains reusable as recorded in Iterations
008 and 060; no preflight was repeated. Fit 03 output and the missing fresh
package-review receipt are still absent. The existing hourly automation is
`ACTIVE` with an hourly schedule. Continue source-only preparation while RAM
is below 10%; once the host clears the operating floor, obtain one bounded
independent exact-hash package review, and launch fit 03 only after free RAM is
at least 25% at start and RAM/VRAM remain at least 10% throughout.

Hashes observed for the unchanged fit package at this check:

| File | SHA-256 |
| --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |

## Iteration 062: IID power floor calibration

The fresh resource sample in this continuation measured 2,635.9 / 32,701.8
MiB free RAM (8.06%), 15,246 / 16,311 MiB free VRAM, and 140.77 GB free on C:.
No Wrench training, inference, or benchmark process was found. RAM remains
below the 10% runtime floor, so no workload or delegation ran.

The product proof design requires five one-sided primary bounds and family-
wise alpha 0.05. As a planning-only IID calculation, allocating alpha 0.01 to
one binary adverse-rate endpoint and assuming a true adverse rate of 2%, the
exact one-sided Clopper-Pearson rule first reaches at least 80% power at
`n=398`, accepting at most 10 adverse outcomes. Its one-sided upper bound is
4.9971385% and its pass probability at 2% is 82.1871%. At `n=397`, at most 9
adverse outcomes pass the bound, but power is only 72.5369%.

This was recomputed from the binomial CDF by solving
`P[X <= k | n, p_upper] = alpha` and calculating `P[X <= k | n, p=0.02]`.
It is only a lower-bound illustration for one binary rate. It does not power
the paired success-retention metric, frontier-token ratio, dollar ratio, or
all five claims jointly. Repository, task-family, and workday clustering can
increase the required sample. The existing product-proof design correctly
keeps the final sample size unadmitted until the workload frame and independent
cluster counts are frozen. The 128-case synthetic screen remains mechanics
evidence, not product-level 95/5 proof.

No tests, provider request, model inference, or training ran. The 100,000-byte
documentation reservation for this note is
`WRENCH-95-5-POWER-CALIBRATION-ITER062-20260927`; release it after final
accounting. The local LoRA, 95/5 operation, 95% frontier-token reduction,
95% all-in savings, and all-day engineering remain unproven.

## Iteration 063: held-out read-order source audit

The latest host sample measured 2,679.8 / 32,701.8 MiB free RAM (8.19%),
15,226 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 140.53 GB free on C:.
No Wrench training, inference, or benchmark process was active. RAM is below
the 10% operating floor, so no test, runtime, workload, or delegation ran.

Source inspection at the current exact hashes confirmed that the training
runner's data loop opens only the train and dev payloads; the sealed heldout
count and hash are read as manifest metadata. In the scorer, the preflight,
training receipt, resource log, model tree, and adapter are verified before
the heldout path is resolved. The scorer loads both model arms, writes the
global and per-job heldout-access markers, and only then opens heldout bytes
at `score_gateway_lora_screen_02.py:1778`. No heldout payload was read during
this audit. This is a source-order observation, not runtime verification or
the missing independent fit-package review.

| File | SHA-256 |
| --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |

The storage checker reported `WITHIN_LIMIT` at 10,991,333,358 bytes actual
and 8,103,000 bytes in active reservations before this report's 100,000-byte
reservation, `WRENCH-HELDOUT-READ-ORDER-ITER063-20260927`. Release it after
accounting. The independent package-review receipt and fit-03 output remain
absent. The active hourly job must obtain that review once RAM reaches 10%; it
may start fit-03 only after the review passes and free RAM is at least 25% at
start, with RAM/VRAM at least 10% throughout.

## Iteration 064: SubRoute 4000 and small-model fit research

The fresh host sample measured 2,747.2 / 32,701.8 MiB free RAM (8.40%) and
15,246 / 16,311 MiB free VRAM on the RTX 5060 Ti. C: had 140,513,570,816 bytes
free. The process query matched only its own PowerShell probe; no Wrench
training, inference, or benchmark process was found. RAM remains below both
the 10% operating floor and 25% fit-start threshold. No tests, runtime calls,
inference, training, packaging, or delegation ran.

The owner specified SubRoute at `http://127.0.0.1:4000` for the stronger-model
route. Static inspection of SubRoute at HEAD
`51d262370b3de790ee97ec6b9d43c33e4b44a2ee` found the configured `openrouter`
alias maps to `openrouter/minimax/minimax-m3` and declares streaming but not
native tool calling. A separate `minimax` alias maps to `minimax/MiniMax-M3`
and declares tools plus streaming; do not switch the forced `openrouter` route
without the appropriate route authority. SubRoute has retries set to zero and
no fallback, but spend logging is disabled. This config/source inspection does
not prove a live request's metadata, selected provider, usage, or billed cost.
No completion POST was sent. The numeric campaign USD cap and durable
caller-side reservation/settlement remain absent, so provider generation stays
closed. OpenRouter currently lists MiniMax M3 at $0.23/M input and $0.96/M
output tokens, with $0.05/M cache-read pricing; these rates are a reference,
not a verified bill for the local gateway route.

The first candidate remains the already pinned `Qwen/Qwen3.5-0.8B` LoRA screen
from the prior fit package. It is appropriate to test as a narrow Wrench
controller for typed proposals, context compaction, bounded routing, and
abstention. Its published scores are weak on broad agent and long-context
tasks, so do not treat it as an all-day repository coder. The next local
coding-worker candidate is `Qwen/Qwen3.5-4B`, revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. The complete pinned remote
inventory contains 14 files, including two weight shards of 5,329,398,688 and
3,990,429,408 bytes; the exact total of all repository files is
9,342,907,469 bytes. The Hub `usedStorage` field is lower, so the larger
enumerated file sum is used for planning. Three full-size copies plus a 1 GB
job buffer would project to 40,028,363,160 bytes against the current aggregate
actual/reservations, leaving 9,971,636,840 bytes below the 50 GB ceiling. This
is a planning estimate only, not a download or training reservation. A fresh
storage admission and volume-space check are required before acquisition.

Qwen's model card reports for its 4B model 55.8 on LiveCodeBench v6, 50.3 on
BFCL-V4, and 79.9 on TAU2-Bench; the 0.8B card reports 25.3 on BFCL-V4 and
11.6 on TAU2-Bench. These vendor-reported results are directional only and
do not measure Wrench repository engineering. Unsloth's current
Qwen3.5 guide estimates bf16 LoRA at 3 GB VRAM for 0.8B and 10 GB for 4B,
does not recommend 4-bit QLoRA for this architecture, and requires current
Transformers support. On a 16 GB GPU, 4B is physically plausible for a
bounded LoRA job, but framework/kernel compatibility, context length,
throughput, and resource reserves still require local validation. The 4B
package is not yet reviewed, downloaded, or selected for the next run.

Published work supports the mechanism, not the Wrench target: RouteLLM reports
over 2x cost reduction on its evaluated settings; FrugalGPT reports up to 98%
cost reduction in its studied workload; LLMLingua-2 reports 2x-5x prompt
compression with end-to-end latency improvements on its benchmarks. These
results do not imply 95% local completion or savings on our task mix. In
particular, 5% of episodes sent to the frontier does not guarantee 95% fewer
frontier tokens or 95% lower all-in cost: escalation episodes can be longer,
can retry, and require more output, while local compute, training, and human
rescue have nonzero costs.

Next evaluation should keep the Wrench controller and coding worker roles
separate: (1) train the pinned 0.8B LoRA only on reviewed, outcome-backed
behavior and test compaction against fact-recovery probes; (2) measure actual
mechanical tool outcomes with deterministic verification; (3) after separate
inventory/admission and exact-hash review, compare a 4B worker on held-out
repository tasks; and (4) use the owner's forced SubRoute route as the
frontier-only comparator only for calls supported by its capabilities and
after a numeric spend cap is installed. A private, sealed paired workday suite
covering repo changes, tests, interruptions, recovery, and regressions remains
the primary engineering proof. Pin Terminal-Bench 4.0 as an external secondary
check, not as a substitute for Wrench's own held-out tasks.

For acceptance, keep the current separate gates: at most 5% of episodes may
call the frontier; hybrid verified success must retain at least 95% of the
frontier-only arm; frontier tokens across every retry, check, compaction,
fallback, and re-fetch must be at most 5% of the frontier-only total; and
all-in hybrid cost must be at most 5% of frontier-only cost after local compute,
energy, adapter amortization, operator time, and rescue are counted. Use paired
episodes and confidence bounds with repository/task-family clustering. Do not
promote synthetic mechanics passes, model-card scores, or a router score into
product effectiveness evidence.

The 200,000-byte documentation reservation was
`WRENCH-SUBROUTE-4000-MODEL-RESEARCH-ITER064-20260928`; release it after the
report and GOAL update are accounted. Fit 03 remains blocked by the 25% RAM
start gate and missing fresh exact-hash package review. The local LoRA's
quality, 95/5 operation, frontier-token savings, all-in savings, and sustained
engineering remain unproven.

## Iteration 065: fix the confirmatory family and cluster-inference plan

The current sample measured 3,044.4 / 32,701.8 MiB free RAM (9.31%),
15,234 / 16,311 MiB free VRAM, and 140,508,729,344 bytes free on C:. No Wrench
job was found. RAM remains below the 10% runtime floor and the 25% fit-03
start gate, so no tests, model/runtime jobs, benchmarks, or delegation ran.

Updated the product-proof protocol to state that its five confirmatory claims
are for the LoRA Wrench hybrid arm, with one-sided 99% bounds under Bonferroni
family-wise alpha 0.05. The deterministic Wrench + frontier arm is a separate
secondary control unless another multiplicity plan is preregistered. The
protocol freezes weighted completion/route rates, conditional success
retention, and paired ratios of weighted token/cost totals. It treats task
families as weighted strata, requires inference to follow the repository and
workday cluster structure, and requires design-specific coverage and joint
power simulations before enrollment. The 234 and 398 IID binary illustrations
are not product sample sizes. See [Iteration
065](../../evals/wrench-gateway-model-research/iteration-065-cluster-inference-and-subroute-4000-20260928.md)
and the [product-proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md).

The user-specified SubRoute setup at `http://127.0.0.1:4000` remains the
frontier comparison route. The forced `openrouter` alias maps to MiniMax M3
and does not declare native tool calling. No generation was sent because the
numeric campaign cap and durable caller-side spend ledger are absent; do not
ask the owner for the cap again. No sealed data was opened and no private task
data was collected. The 0.8B LoRA and 4B coding-worker candidate remain
unvalidated for the product. The 95/5 outcome, success retention, 95% token
and cost reductions, and all-day engineering remain unproven.

## Iteration 066: revalidate preflight identity and stage package review

The latest host sample measured 2,964.2 / 32,701.8 MiB free RAM (9.06%),
15,232 / 16,311 MiB free VRAM, and 140,502,839,296 bytes free on C:. No Wrench
training, inference, test, or benchmark process was found. RAM is below the
10% operating floor and the 25% fit-03 start gate. No runtime, test, or
delegated review ran.

Revalidated the preflight-05 receipt. Its manifest remains
`PREFLIGHT_COMPLETED`, with one finite optimizer step over eight synthetic
rows, the expected 24 attention targets, 540,672 trainable parameters, no
adapter output, and no heldout access. The current trainer and protocol hashes
match the manifest; scorer/helper hashes match the earlier scorer review.
There is no need to repeat this completed compatibility preflight while the
identities stay unchanged.

The fresh package review is still needed because the current GOAL and
Iterations 008/009 are outside the old review scopes. Captured the exact
current twelve-file review identity and prepared assignment
`WRENCH-FIT03-EXACT-PKG-REVIEW-ITER066-20260928` with nonce
`0e0e9778-2111-4136-a518-b445ad0ebd8c`. It was not dispatched under the
10% resource floor. The reviewer may run once fresh RAM/VRAM reserve checks
pass; fit itself still requires at least 25% RAM free at start. See [Iteration
066](../../evals/wrench-gateway-model-research/iteration-066-preflight-identity-and-review-packet-20260928.md).

The active hourly heartbeat remains in place. The user-specified SubRoute at
`http://127.0.0.1:4000` remains the comparator route, with generation closed
pending the campaign cap and caller ledger. The adapter's decision quality,
95/5 split, 95% frontier-token/cost savings, and all-day engineering remain
unproven.

## Iteration 067: diagnose the host memory gate

The latest resource sample measured 1,861.6 / 32,701.8 MiB free RAM (5.69%),
15,244 / 16,311 MiB free VRAM, and 140,502,839,296 bytes free on C:. No Wrench
training, inference, test, or benchmark process was active. This leaves a
1,408.6 MiB gap to the 10% floor for delegated review and a 6,313.9 MiB gap to
fit 03's 25% start gate.

A read-only process sample measured `vmmemWSL` at 15,564.9 MiB working set.
`docker-desktop` is the only running WSL distribution. The repository requires
explicit user authorization before stopping Docker or WSL, so permission was
requested and no service was terminated. See [Iteration
067](../../evals/wrench-gateway-model-research/iteration-067-host-memory-gate-20260928.md).

The preflight-05 runner and protocol hashes still match the completed receipt.
The independent fit-package review remains prepared but undispatched until a
fresh host sample clears 10% free RAM. Fit 03 still requires that review to
pass and a separate 25% RAM start sample. The hourly heartbeat remains ACTIVE;
SubRoute `:4000` received no generation request. The LoRA's task quality, 95/5
routing, 95% token/cost savings, and all-day engineering remain unproven.

## Iteration 068: measure Docker memory options

The host sample measured 2,031.7 / 32,701.8 MiB free RAM (6.21%),
15,250 / 16,311 MiB free VRAM, and 140,308,824,064 bytes free on C:. The
10% floor needed for independent review is 1,238.5 MiB above this sample.
Fit 03's 25% start floor is 6,143.8 MiB above it.

Read-only Docker inspection showed 26 running, healthy containers under the
only running WSL distribution, `docker-desktop`. The Ollama container uses
2.382 GiB; the SubRoute/gateway stack, Supabase, and portal services also use
host resources. Stopping Ollama alone might permit the static review but would
not satisfy the training gate. Stopping Docker Desktop WSL would interrupt
all 26 services. No service was stopped. Explicit authorization was requested
because the repository prohibits stopping Docker or WSL without it. See
[Iteration 068](../../evals/wrench-gateway-model-research/iteration-068-docker-memory-options-20260928.md).

The exact-hash package review remains prepared but undispatched. The
preflight-05 runner/protocol hashes still match the completed receipt. The
hourly heartbeat remains ACTIVE and will continue resource checks; no paid
generation went to SubRoute. Product quality, the 95/5 task split, 95% token
and cost savings, and all-day engineering remain unproven.

## Iteration 069: exact-hash fit-package review

The independent static review completed under assignment
`WRENCH-FIT03-EXACT-PKG-REVIEW-ITER066-20260928` with nonce
`0e0e9778-2111-4136-a518-b445ad0ebd8c`. The reviewer confirmed the expected
Git HEAD and all 12 assigned SHA-256 identities before and after review. The
review found no static blocker for the bounded fit package and wrote the
hash-bound receipt at [fit 03 package review](../../evals/wrench-gateway-model-research/fit03-package-review-iter066-20260928.md).
This is a static package pass, not fit authorization or evidence of model
quality.

The lowest RAM sample during review was about 14.4%; the latest sample after
review was 5,023.9 / 32,701.8 MiB (15.36%), with 15,218 / 16,311 MiB VRAM
free. The fit-start requirement is at least 25% free RAM, so fit 03 remains
closed. Storage is `WITHIN_LIMIT` at 10,991,642,425 bytes with 8,103,000
bytes in unrelated active reservations; C: has 141,112,000,512 bytes free.
The review reservation was released after its 7,489-byte report was accounted.

The owner-directed SubRoute at `http://127.0.0.1:4000` remains the frontier
comparison route. Fresh read-only `GET /health/liveliness` and `GET /models`
both returned HTTP 200; `/models` listed 19 aliases. This confirms gateway
liveness and its alias list, not which provider would serve a completion. No
completion request was sent: the numeric aggregate cap and durable caller-side
reserve/settlement/usage-cost receipt controls remain absent. The local
adapter's held-out quality, 95/5 operation, frontier-token and all-in cost
savings, and sustained engineering remain unproven. The next fit attempt still
requires a fresh sample at or above 25% free RAM plus fresh storage,
destination-space, identity, and 10% RAM/VRAM admission checks.

## Iteration 070: verify the SubRoute campaign-budget caller offline

Ran the pending focused campaign-wide caller and SQLite ledger suite against
the exact five source/test hashes listed in [Iteration 070](../../evals/wrench-gateway-model-research/iteration-070-subroute-budget-caller-unit-verification-20260928.md).
All 8 tests passed through injected mock transport using the existing Python
3.11.16 environment. Coverage includes cross-job cap enforcement, full reserve
retention for ambiguous calls, settlement validation, and failure-closed
behavior when approval or credentials are unavailable. The initial system
Python 3.13 `pytest` command did not execute tests because that interpreter
lacks pytest; the Python 3.11 unittest run did execute all 8.

RAM was 14.77% before and 14.82% after the test, below fit 03's 25% start
gate. Storage remained `WITHIN_LIMIT`; the pending test reservation was
released after outputs were accounted. No live HTTP or provider request was
sent, and the local caller test does not verify SubRoute's loaded request
metadata path or actual billed cost. Keep generation closed. No fit,
inference, benchmark, or held-out operation ran; product utility and all
95/5/95 targets remain unproven.

## Iteration 071: SubRoute ingress-control path review

The independent review `WRENCH-SUBROUTE-REQUEST-CONTROLS-REVIEW-ITER071-20260928`
returned **CONDITIONAL**. Both repository HEADs and all five assigned file
hashes matched before and after. The Wrench caller sends both top-level
provider controls and `metadata.wrench_openrouter_provider_controls`; the
SubRoute adapter validates mapped LiteLLM metadata and adds provider controls
to the outbound OpenRouter body. However, its regression test constructs
`litellm_params` directly and uses a mocked outbound transport. It never posts
through LiteLLM's `/v1/chat/completions` ingress, and the successful case also
sets `provider_argument`. This does not prove that inbound HTTP metadata reaches
the adapter or that the running service loaded this dirty checkout. See
[Iteration 071](../../evals/wrench-gateway-model-research/iteration-071-subroute-request-controls-path-review-20260928.md).

A fresh read-only check against the owner-directed SubRoute at
`http://127.0.0.1:4000` returned HTTP 200 from `/health/liveliness` and `/models`;
the latter listed 19 aliases. No completion request, credential read, or
provider call occurred. The smallest next proof is a no-provider integration
test that posts the exact Wrench-shaped body through LiteLLM's ASGI ingress and
mocks the OpenRouter transport, asserting the adapter receives the metadata
and emits the required provider controls and metadata header. Generation
remains closed pending that ingress proof, caller-side durable spend controls,
and a numeric campaign cap. Fit 03 remains closed below its 25% free-RAM start
gate; the 95/5 success and cost/token targets and all-day engineering remain
unproven.

## Iteration 072: SubRoute ASGI ingress and mocked wire-body integration

The no-provider ASGI integration used LiteLLM 1.103.0 from the existing
`unified-llm-gateway` image, an in-memory Router for the configured `openrouter`
model, and a synthetic transport restricted to `127.0.0.1:9`. The request
metadata reached the Wrench adapter validator and the `X-OpenRouter-Metadata`
header was present. The test failed its provider-body assertion: the captured
wire JSON nests `provider` and `usage` under `extra_body`, with no root-level
`provider`. This is a negative integration result, not evidence that SubRoute
enforces the provider controls. The previous direct SDK test uses
`.chat.completions.create`, while LiteLLM 1.103.0's actual request helper uses
`.with_raw_response.create`; that difference may explain the gap but has not
been isolated. See [Iteration 072](../../evals/wrench-gateway-model-research/iteration-072-subroute-asgi-ingress-no-provider-integration-20260928.md).

The independent static review matched both repository HEADs and all four
SubRoute file hashes before and after, and confirmed that the test proves
metadata arrival but fails the required wire-body contract. It did not rerun
the test. It also notes that plugin import applies a process-global patch and
that the test bypasses configured proxy startup/lifespan; each experiment ran
in a short-lived container process, so it did not patch the live 4000 server.
See [the independent review](../../evals/wrench-gateway-model-research/iteration-072-subroute-asgi-ingress-independent-review-20260928.md).

The running `http://127.0.0.1:4000` received GET-only health and model-list
checks; no completion was posted to it and no provider request occurred. The
ASGI test imports the app directly and does not establish that the deployed
4000 process loaded the dirty checkout's callback. Keep paid generation closed
until the wire-body integration is corrected, the deployed process path is
verified, and a numeric campaign-wide cap plus durable caller-side accounting
are approved. The 95% success, 5% frontier route, 95% lower frontier-token and
all-in cost targets, and all-day coding ability remain unmeasured. Fit 03 also
remains below its 25% free-RAM launch gate.

Both Iteration 072 reservations were released after the test and review stopped
and the reports were accounted. A final storage check including the SubRoute
root remained `WITHIN_LIMIT` at 10,993,972,986 actual bytes; C: had 135.22 GB
free at the run check.
The final report/goal text update was covered by a separate 25,000-byte
reservation including the SubRoute root; it was released after close-out.

## Iteration 073: fix root-level provider controls in the mocked route

Source inspection of the deployed LiteLLM 1.103.0 image traced the prior
nested `extra_body` failure to `custom_httpx`: LiteLLM serializes the mapped
request dictionary directly with `json.dumps(data)`. A separate no-network
OpenAI 2.33.0 probe showed both `.create` and `.with_raw_response.create`
flatten SDK `extra_body` into the JSON root, ruling out the earlier raw-wrapper
hypothesis. The SubRoute adapter now flattens provider extensions at the root
and fails closed on conflicts.

The updated SubRoute controls suite passed 5/5, and the metadata-only ASGI
mock integration passed 1/1 on LiteLLM 1.103.0. It verifies the marker reaches
the adapter, the header is present, and provider controls plus usage are
root-level in the captured request. All egress was intercepted at loopback
port 9. The test still uses a manually built Router and does not load the
deployed `litellm.yaml` callback or prove that port 4000 runs this dirty
checkout. The host lock remains LiteLLM 1.101.0, so exact-lock compatibility
also remains unverified. See [Iteration 073](../../evals/wrench-gateway-model-research/iteration-073-subroute-root-wire-controls-20260928.md).

No generation, LoRA fit, or coding comparison ran. Free RAM fell to 10.43%
in the latest post-test sample, below fit-03's 25% start gate and close to the 10%
reserve floor. Keep model work closed until resources permit its admitted
experiment. The 95% local completion, 5% frontier route, 95% success
retention, 95% token/cost reduction, and sustained engineering targets remain
unproven. No live 4000 completion or provider call was made.

## Iteration 074: use the existing SubRoute control plane at port 4000

The owner directed use of the existing SubRoute at `127.0.0.1:4000`. Read-only
`GET /health/liveliness` and `GET /models` both returned HTTP 200; the model
list contained 19 aliases. The configured `openrouter` alias maps to
`openrouter/minimax/minimax-m3`. No completion, credential read, or upstream
request was made. The campaign-wide USD spend cap remains missing, so the
frontier comparison remains closed.

The port is served by container `unified-llm-gateway` using image
`ghcr.io/berriai/litellm-database@sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`.
Its `/app/config` and `/app/src` paths are bind-mounted from the SubRoute
checkout. The container started at `2026-09-25T21:52:44Z`, before the current
config file timestamp (`2026-09-27T18:46:18Z`) and request-controls plugin
timestamp (`2026-09-28T05:15:07Z`). Therefore the live GETs establish control
plane liveness only; they do not establish that the running LiteLLM process
loaded the updated callback or wire-body fix. No restart was performed.

At the check, free RAM was 3,479.3 / 32,701.8 MiB (10.64%) and free VRAM was
15,195 / 16,311 MiB (93.16%). C: had 144,947,118,080 bytes free. Storage status
including the SubRoute checkout was `WITHIN_LIMIT` at 10,994,085,927 actual
bytes before this report reservation. Model work remains below the 25% fit
start gate. The 95% local completion, 5% frontier route, retained task
success, frontier-token and all-in cost reductions, and all-day coding ability
remain unproven.

## Iteration 075: source-level compatibility check against LiteLLM 1.101.0

The current SubRoute `uv.lock` pins LiteLLM 1.101.0. Its upstream tagged
`OpenrouterConfig.transform_request` has the same parameter sequence enforced
by the Wrench adapter (`self`, `model`, `messages`, `optional_params`,
`litellm_params`, `headers`). It extracts `extra_body` and merges its members
into the transformed request dictionary. The same version's `custom_httpx`
handler serializes that dictionary with `json.dumps(data)` before posting.
These source details match the 1.103.0 path used by Iteration 073 and the
adapter's signature check/root merge. See the [tagged OpenRouter
transformation](https://github.com/BerriAI/litellm/blob/v1.101.0/litellm/llms/openrouter/chat/transformation.py#L134-L158)
and [tagged custom HTTP handler](https://github.com/BerriAI/litellm/blob/v1.101.0/litellm/llms/custom_httpx/llm_http_handler.py#L297-L323).

This narrows the lock-version question to a source-level match; it is not an
exact-version runtime regression pass. Fresh free RAM was 3,074.5 / 32,701.8
MiB (9.40%), below the 10% safety floor, so no test or runtime was started.
The RTX 5060 Ti had 15,200 / 16,311 MiB VRAM free, and C: had 144,944,050,176
bytes free. Storage including SubRoute was `WITHIN_LIMIT` at 10,994,140,944
actual bytes before the report reservation. Port 4000 still predates the
modified config/plugin, and its loaded controls remain unverified. No
completion or provider request was sent; the numeric campaign cap remains
unspecified. All 95/5, success, token/cost, and all-day engineering goals
remain unproven.

## Iteration 076: static audit of the bounded SubRoute caller

Source review of the Wrench caller found a fail-closed approval path. The
approval loader pins the endpoint to `127.0.0.1:4000`, alias `openrouter`, and
upstream `minimax/minimax-m3`; requires human approval, synthetic-only cases,
matching repository/caller/case hashes, `automatic_retries=0`,
`allow_fallbacks=false`, and an aggregate cap that covers every per-request
worst-case reserve. Before each POST, `BudgetLedger.reserve` obtains an
immediate SQLite transaction, refuses to dispatch if any call is unresolved,
checks campaign and job request ceilings, verifies total committed exposure,
and commits the full request reserve.

The sender uses one POST to the fixed local endpoint, disables environment
proxies and redirects, and bounds the response to 1 MiB. The caller requires a
single selected OpenRouter endpoint with the approved provider/model, token
usage and billed cost before settlement. Actual cost above the reserve is
rejected; ambiguous or invalid results keep the reservation unresolved. This
is a static source audit only. Iteration 070's 8/8 mocked tests remain the
latest execution evidence; this turn ran no caller test or provider request.

Reviewed file hashes at Wrench HEAD `af01304824f079a64b6c3902397a2034b843511a`:

- `tools/subroute_budget_guard.py`:
  `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B`
- `tools/capture_subroute_teacher_traces.py`:
  `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6`

Fresh free RAM was 2,647.9 / 32,701.8 MiB (8.10%), below the 10% floor;
15,197 / 16,311 MiB VRAM was free. C: had 144,940,871,680 bytes free. Storage
including SubRoute was `WITHIN_LIMIT` at 10,994,197,220 actual bytes before
the report reservation. No runtime, test, inference, training or provider call
was started. The live port-4000 process remains unverified against the current
callback; the numeric campaign cap is still missing. The 95/5 routing,
95% success/token/cost targets and all-day engineering remain unproven.

## Iteration 077: identify the RAM gate's host-side cause

The fresh Windows sample measured 2,385.8 / 32,701.8 MiB free RAM (7.30%),
15,191 / 16,311 MiB free VRAM, and 144,936,685,568 bytes free on C:. Fit-03
requires 25% free RAM, or 8,175.5 MiB; the current sample is 5,789.7 MiB below
that start gate. The 10% floor is also currently breached, so no test, runtime,
inference, training, benchmark, packaging, or delegation is admitted.

The top process was `vmmemWSL` at 14,440 MiB. A read-only Docker stats sample
showed 26 running services; the largest was `canada-local-platform-ollama-1`
at 2.381 GiB, followed by `unified-llm-gateway` at 728 MiB,
`unified-llm-gateway-staging` at 552 MiB, and
`unified-llm-gateway-experts` at 474 MiB. This indicates that Docker Desktop's
WSL VM is the dominant observed host process, but stopping it would interrupt
all 26 services, including the owner's requested SubRoute at port 4000. No
container or WSL distribution was stopped. The owner was asked whether to
authorize a temporary WSL shutdown; until explicit approval, keep services
running.

Storage including SubRoute was `WITHIN_LIMIT` at 10,994,255,550 actual bytes
before the report reservation. The fit-start 25% gate and current 10% runtime
floor remain unmet. This report does not establish model quality, task routing,
token savings, or cost savings. The LoRA experiment remains ready to proceed
only after safe resource admission and its full pinned protocol checks.

## Iteration 078: verify SubRoute reachability and pin the callback reload gate

The requested local SubRoute control plane at `127.0.0.1:4000` answered the
GET-only liveness request with HTTP 200. `/v1/models` returned 19 aliases. The
healthy `subroute-antigravity-1` container and `unified-llm-gateway` process
both report roughly two days of uptime, so this confirms reachability of the
existing service, not that it loaded callback edits made after startup. No
generation request or provider call was sent.

Official LiteLLM v1.103.0 source initializes configured callbacks inside
`ProxyConfig.load_config`; the periodic reload code describes model cost map
and Anthropic beta-header refreshes. The reviewed `/config/update` handler
persists config sections and adds deployments, but the examined path did not
show callback initialization or plugin re-import. Official routing docs list
settings that support runtime updates, but do not document callback reload.
This is source evidence that hot reload is not established, not proof about
the exact running image. In particular, the source reviewed here is v1.103.0;
the Wrench adapter's prior exact-tag source review was v1.101.0, and neither
is a runtime inspection of the current container. References: [startup config
load](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L1133-L1145),
[callback initialization](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L5413-L5544),
[periodic reload](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L9400-L9416),
[`/config/update`](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L15847-L16033),
and [runtime routing configuration](https://docs.litellm.ai/docs/routing).

The live Windows sample showed 3,408.8 / 32,701.8 MiB free RAM (10.42%),
which is just 139.0 MiB above the 10% runtime floor and 4,766.7 MiB below
fit-03's 25% start gate. C: had 144,692,109,312 bytes free. No test,
inference, training, restart, or provider request was run. Since the owner has
not authorized stopping Docker/WSL and a restart could interrupt the requested
SubRoute service, the current process was left running. The next live callback
check must wait for an approved safe restart/redeploy window, then verify the
loaded callback identity before any bounded synthetic generation. The numeric
campaign spend cap is still unspecified. The 95/5 routing, 95% success,
token/cost reduction, and all-day engineering claims remain unproven.

## Iteration 079: revalidate Fit-03 package identity after the goal update

The Iteration 066 Fit-03 package review bound 12 identities, including the
research goal file. Iteration 078 updated that goal file, so the old identity
was no longer current. An independent read-only review rechecked the package
at Wrench HEAD `af01304824f079a64b6c3902397a2034b843511a`. All 11 other
identities matched the Iteration 066 review. The only changed identity was
`docs/goal/wrench-gateway-model-research/GOAL.md`, whose current SHA-256 is
`57A2EB77AA336196BBE917290566DB50281EFDAC645D882CA655134EE5136235`; the
reviewer confirmed the Iteration 078 addition did not change Fit-03's objective,
authorization conditions, 25% RAM start gate, 10% runtime floors, train/dev
boundary, or held-out gate. The review passes for static package identity and
the specified documentation scope. It confirms code-hash continuity only and
is not a source re-review or fit authorization. See [Iteration
079](../../evals/wrench-gateway-model-research/iteration-079-fit03-goal-hash-review-20260928.md).

Before, during, and after the review, RAM remained between 11.11% and 11.25%
free; VRAM remained between 15,198 and 15,202 MiB free of 16,311 MiB. The
latest sample is 3,766,480 / 33,486,624 KiB free RAM (11.25%), still about
4,497.2 MiB short of Fit-03's 25% start gate. No tests, model loading,
inference, training, held-out reads, provider calls, or network requests were
made. The next Fit-03 step remains a fresh sample at or above 25% free RAM,
followed by fresh storage and destination-space admission.

### Iteration 080: SubRoute GET and local model snapshot verification

The owner-directed SubRoute at `127.0.0.1:4000` returned HTTP 200 for
`/health/liveliness`, `/models`, and `/v1/models`; both model listings returned
19 aliases. A five-second GET to `/health` timed out, while the configured
liveness path succeeded. No generation or provider request was sent. This is
control-plane reachability only; callback reload and provider billing behavior
remain unverified.

The pinned read-only verifier matched all 13 files of the Qwen3.5-0.8B local
snapshot (1,769,980,465 bytes) to the exact candidate manifest and inventory.
It checked raw SHA-256 for the LFS weight and tokenizer, plus the available Git
blob identities for other files. LFS pointer blob IDs were not recomputed. The
receipt is `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\local-snapshot-verify-iter080-20260928.json`;
details are in [Iteration 080](../../evals/wrench-gateway-model-research/iteration-080-subroute-and-model-snapshot-check-20260928.md).

Free RAM was 10.65% at verification admission; the monitored hash pass sampled
a 10.627% minimum. A second unchanged-content check on the retained handles
passed, and free RAM after it was 10.90%. That second pass was not continuously
sampled. VRAM was 15,199 / 16,311 MiB free. Storage including SubRoute was
`WITHIN_LIMIT`. No model load, inference, fit, benchmark, held-out read, or
provider call ran. Current RAM is about 4,611.6 MiB below the 25% Fit-03 start
gate. The snapshot check confirms artifact identity, not model utility. The
95/5 routing, 95% token/cost reduction, and all-day engineering claims remain
unproven.

### Iteration 081: existing local Qwen models and the disconnected SubRoute alias

Read-only Ollama metadata shows existing Qwen3.5 tags in the Docker named
volume `local-ai-models`: `qwen3.5:4b` is 4.7B parameters at Q4_K_M with a
3,389,971,840-byte model layer; `qwen3.5:0.8b` is 873.44M parameters at Q8_0
with a 1,036,034,688-byte model layer. Their installed manifest SHA-256 values
and every layer's declared digest and byte size are recorded in [Iteration
081](../../evals/wrench-gateway-model-research/iteration-081-ollama-model-inventory-and-subroute-route-20260928.md).
The complete Ollama model tree is 4,426,052,564 bytes. These are quantized
inference packages, not the pinned Hugging Face Fit-03 training snapshot; no
weights were read or rehashed, no model was loaded, and no inference ran.

The Ollama model tree resides in Docker's Linux named volume, which the current
Wrench storage checker cannot include. The running SubRoute `desktop` alias
maps to `ollama/qwen2.5-coder`, while its `OLLAMA_API_BASE` points at
`host.docker.internal:11434`. The Ollama container is on a separate Docker
network and the gateway's read-only `/api/tags` check failed. Thus the installed
Qwen candidates are not currently reachable through SubRoute; do not count
them as Wrench-selected or smooth-running candidates until storage accounting
and an isolated route are established.

At admission, free RAM was 3,733.0 / 32,701.8 MiB (11.42%); VRAM was 15,203 /
16,311 MiB free. Fit-03 remains 4,442.5 MiB below its 25% start gate. The
storage checker, including SubRoute and the hourly automation directory,
remained `WITHIN_LIMIT`; it did not include the external Docker model volume.
No service config was changed. The 95/5 route split, token and cost savings,
coding reliability, and workday-long performance remain unproven.

## Iteration 083: Fit-03 hash pin reconciliation

The Iteration 082 package review compared the current GPU protocol hash against
a mistyped expected value. A fresh read-only review corrected the assignment
and matched all 12 listed identities before and after review, including the
then-current goal hash `D89487E2E880FB7F22360AEC9327DB1B370D3792B5B1D3041FEA79927B285E88`.
The corrected protocol SHA-256 is
`EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5`. This
reconciles identity only; it did not authorize training, inference, held-out
scoring, spending, or activation. See [Iteration
083](../../evals/wrench-gateway-model-research/iteration-083-fit03-hash-pin-reconciliation-20260928.md).

## Iteration 084: binary-gate power sensitivity

An exact one-sided binomial sensitivity used `alpha=0.01` per primary endpoint
and the 5% adverse-rate boundary. At a true 2% event rate, a single binary
endpoint requires 398 IID episodes for 80% marginal power; 606 gives at least
95.635% marginal power, the equal-independent-gates illustration for 80%
joint power across five claims. The latter does not power the paired success,
token, or cost ratios, and the independent-equal-gates assumption is not the
product design. The 128-case synthetic split and 50-episode workday minimum
are not powered product studies. Final joint power still requires a frozen
target workload and cluster layout, a separately permitted development pilot,
paired token/cost distributions, and design-specific simulation. See
[Iteration 084](../../evals/wrench-gateway-model-research/iteration-084-gate-power-sensitivity-20260928.md)
and the [research refresh](../../reports/wrench-gateway-model-research/research-refresh-20260928.md).
