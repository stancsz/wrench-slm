# Iteration 010: model scope, SubRoute, and evidence refresh

Date: 2026-09-27 (America/Edmonton)

Status: **MODEL SCOPE RECORDED; ROUTE READ-ONLY VERIFIED; NO GENERATION OR MODEL RUN**

## Owner direction

The owner authorized exploration of any pinned model below 10B parameters if
it runs smoothly on this machine, and specified the existing SubRoute at
`http://127.0.0.1:4000`. This expands the earlier 0.8B-only candidate choice.
It does not authorize arbitrary data, relax candidate inventory or hardware
gates, or supply a numeric frontier-spend cap.

## Read-only SubRoute and host checks

| Check | Result |
|---|---|
| `GET /health/liveliness` | HTTP 200, `I'm alive!` |
| `GET /models` | 19 aliases, including `openrouter` |
| Safe `GET /model/info` projection | Alias `openrouter`, display name `MiniMax M3`, provider adapter `OpenRouter`, mode `chat`, configured $0.30/M input and $1.20/M output; info id `7ec0fcd796f4452d965d34f010bc30802a1dd926dcb39eabd474cd913172a74e` |
| Force route / target | The latest saved route snapshot remains `active_model=openrouter`, `mode=force`, policy version 4; prior alias mapping is `openrouter/minimax/minimax-m3` |
| Upstream inference provider | **Not pinned.** `OpenRouter` is the gateway adapter; only a generation receipt can identify the provider selected upstream |
| Generation, token usage, billed cost | Not requested; zero provider spend |
| Host sample | RTX 5060 Ti, 15,256/16,311 MiB VRAM free; system RAM 4.92/31.94 GiB free (15.63%) |
| Storage and destination | Storage checker `WITHIN_LIMIT`: 10,955,597,992 actual bytes plus 16,103,000 reserved bytes; C: had 155,489,894,400 bytes free |

The RAM sample is above the general 10% reserve but below fit 03's 25% start
gate. No training or inference job was started. The saved force route was not
changed. A numeric aggregate USD cap and a fail-closed caller with per-request
model, upstream provider, token, and billed-cost receipts remain prerequisites
for any paid comparison.

## Model and role recommendation

The two read-only research tracks converge on a role split:

- Keep deterministic code responsible for indexing, exact retrieval, token
  counting, deduplication, schema checks, source hashes, truncation bounds,
  and verification. Preserve original evidence and retrieve it by reference
  after compaction.
- Train the Wrench LoRA to propose only bounded decisions such as keep,
  retrieve, compact eligible history, abstain, or recommend a route/escalation.
  Do not make it an arbitrary shell or code-mutation authority.
- Keep the already staged 0.8B candidate as the cheapest Wrench-specific
  LoRA control. Its prior 0/10 general semantic screen did not evaluate a
  trained LoRA on this finite action schema. If its frozen dev result shows a
  capacity limit, the next small controller challenger is Qwen3.5-2B.
- Treat local repository coding as a separate capability question. Qwen3.5-4B
  is the strongest candidate in this screen with a published BF16-LoRA VRAM
  estimate below 16 GB; Qwen2.5-Coder-3B is a simpler code-focused baseline.
  Neither has Wrench repository-task or endurance evidence. Qwen3.5-4B can
  also be tested as a separate local worker rather than assuming the 0.8B/2B
  context controller can engineer independently.

Qwen3.5-2B's model card reports 2B parameters, BFCL-V4 43.6 and TAU2-Bench
48.8. Unsloth currently estimates about 5 GB VRAM for BF16 LoRA, but warns
against QLoRA for Qwen3.5. Qwen3.5-4B's card reports LiveCodeBench v6 55.8,
BFCL-V4 50.3 and TAU2-Bench 79.9; Unsloth estimates about 10 GB for BF16
LoRA. Qwen3.5-9B's card reports stronger LiveCodeBench v6 65.6, BFCL-V4
66.1 and TAU2-Bench 79.1, but Unsloth estimates 22 GB VRAM for BF16 LoRA,
above this GPU's 16 GB capacity. Quantized 9B inference remains unmeasured.
The 4B LoRA estimate is tight against 16 GB and is not a measured fit.
Qwen3.5 uses a hybrid DeltaNet/attention architecture and needs current
serving support plus a candidate-specific LoRA target inventory.
Qwen2.5-Coder-3B is 3.09B parameters with a conventional Qwen2 architecture
and 32K context, but its public coding report is from 2024. Sources: [2B card](https://huggingface.co/Qwen/Qwen3.5-2B), [4B card](https://huggingface.co/Qwen/Qwen3.5-4B), [9B card](https://huggingface.co/Qwen/Qwen3.5-9B), [Unsloth Qwen3.5 fine-tuning guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune), [Coder-3B card](https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct), [Qwen2.5-Coder report](https://arxiv.org/abs/2409.12186).

**Candidate recommendation:** test the existing 0.8B LoRA as the first
low-cost finite-controller control once its approved resource gate passes;
keep Qwen3.5-2B as the next Wrench-controller challenger. Evaluate Qwen3.5-4B
or Qwen2.5-Coder-3B/7B separately for repository coding. If selecting one
new model for both LoRA training and code generation, Qwen3.5-4B has the
strongest recent public coding/tool signal among candidates whose BF16-LoRA
estimates are below 16 GB, but its memory/runtime/adapter fit and engineering
quality are unverified. The model-fit survey recommends 4B first; this
iteration favors 0.8B/2B first for the narrower, lower-memory Wrench controller
because the user explicitly prioritizes mechanical context work.

Before any new download or run: pin the exact revision; enumerate all shards
and metadata; sum persistent, staged, cache, quantized, and checkpoint copies;
reserve worst-case storage; check destination free space and live RAM/VRAM;
map the actual module names; and review the runtime, adapter composition, and
short-context preflight. Published memory estimates are not admission receipts.

## What current evidence says about savings

The strongest context-compression evidence supports a real but more modest
opportunity than the 95% target:

- ACON (ICML 2026) reports 26%-54% lower peak input tokens on AppWorld,
  OfficeBench and multi-objective QA, with task success improvements over
  its compression baselines. This is not a Wrench coding result or 95%
  end-to-end savings. [Paper](https://arxiv.org/abs/2510.00615)
- OpenHands reports 54% versus 53% solved on its tested subset of SWE-bench
  Verified and per-turn API costs settling below half after condensation.
  The vendor report does not publish enough sample-size/uncertainty detail to
  establish general parity or whole-task savings. [Report](https://www.openhands.dev/blog/openhands-context-condensensation-for-more-efficient-ai-agents)
- RouteLLM reports more than 2x cost reduction in some conversational routing
  settings; FrugalGPT reports up to 98% cost reduction on its query-cascade
  tasks. Those narrow task distributions and older price conditions do not
  transfer to long-horizon repository engineering. [RouteLLM](https://arxiv.org/abs/2406.18665), [FrugalGPT](https://arxiv.org/abs/2305.05176)

The sensible Wrench bet is mechanical: deterministic retrieval and context
bookkeeping with a LoRA-trained policy for uncertain selection decisions.
Compression is useful only when the final patch, tests, recoverability, and
human correction are preserved. A 5% share of task episodes routed to a
frontier model does not imply 95% token or dollar savings; escalation cases
may carry most retries, input, and verification. Count these metrics
separately and price all tiers.

## Experiment consequence

Use three paired arms on the same reviewed repository/task starts: frontier
only; local worker plus deterministic Wrench without the LoRA; and the same
local stack with the Wrench LoRA and frozen escalation policy. First run a
pilot to estimate paired success discordance and workload cluster counts,
then calculate confirmatory sample size before the sealed split opens. Keep
repository/time groups disjoint from training. Count all calls, cached and
uncached input/output tokens, retries, failed runs, human rescue, local
inference latency/energy, adapter training, and verification. Add a distinct
multi-session endurance run for full-day engineering; a single long session
or a public benchmark score is not a substitute.

The literature makes the mechanical-context hypothesis worth testing; it does
not support the requested joint 95% local completion, 95% frontier-token
savings, and 95%-cheaper claim. No Wrench task effectiveness or day-long
engineering result changed in this iteration.

## Work performed and limitations

Read-only surveys were completed under assignments
`WRENCH-SLM-MODEL-FIT-SURVEY-20260927-A` (nonce
`7f4a986b-31c8-4f96-9fd5-2978596e4df3`) and
`WRENCH-SLM-MECHANICAL-SAVINGS-20260927-B` (nonce
`556491ae-1163-4c60-867c-d86e172758f7`). The orchestrator independently
spot-checked the linked model cards, Unsloth guide, ACON, OpenHands,
RouteLLM, and FrugalGPT pages. No local model was downloaded or run, no
training was attempted, and no provider generation request was sent. The
reviewers' findings are research inputs, not Wrench evaluation evidence.
