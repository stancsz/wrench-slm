# Wrench gateway SLM research refresh

Date: 2026-09-28 (America/Edmonton)  
Status: research recommendation and evidence audit; no model was loaded or trained  
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Recommendation

Keep Wrench as a deterministic Layer 1 context runtime with a small, trained
controller that proposes bounded decisions. Do not expect a sub-1B model to
be a dependable, all-day software engineer. Use a separate tool-capable coding
worker for implementation, and reserve the stronger SubRoute model for the
small set of genuinely difficult or uncertain tasks.

The most realistic split is:

1. **Deterministic mechanics first:** parse and count tool schemas, keep only
   tools explicitly allowed for the current client, retrieve exact source
   spans, preserve the original text, pack within a measured context budget,
   verify output schemas, and log every route and retry. Exact operations
   should not consume model tokens.
2. **Wrench LoRA controller:** train the existing Qwen3.5-0.8B candidate to
   rank source-backed evidence, choose among `KEEP`, `RETRIEVE`, `COMPACT`,
   `STOP`, and `ABSTAIN`, and estimate risk and token use. Host code validates
   every proposal. Its LoRA teaches Wrench's bounded workflow; it does not add
   coding capacity or execution authority.
3. **Local coding worker:** evaluate a separate 3B-9B code-capable model on
   repository tasks. The local Qwen3.5-4B quantization is a plausible first
   challenger, but it is not currently admitted to Wrench's storage accounting
   or reachable through the configured SubRoute `desktop` alias.
4. **Frontier fallback:** use the stronger route only after the aggregate USD
   cap and end-to-end provider, token, and billed-cost receipts are verified.
   The active MiniMax route has not been proven to provide the coding-agent
   tool interface needed for an apples-to-apples engineering comparison.

This keeps the model small where the decisions are narrow, while assigning
open-ended diagnosis, architecture changes, difficult test failures, and
recovery to a coding-capable worker. “All day” is a property of the entire
tool, context, verification, state-recovery, and interruption loop, not of a
model card or parameter count.

## What the current evidence says

The previous general semantic-controller direction failed its own small
synthetic screen ([decision reassessment](decision-reassessment-20260927.md)).
That rejects the claim that the tested 0.8B setup already
works as a general context agent; it does not show that every narrow learned
decision is useless. The current staged experiment tests a different,
bounded LoRA controller and has not yet completed its Fit-03 run or a sealed
held-out evaluation. The prior deterministic context prototype reported an
11.64% synthetic input-token reduction (see the [current goal record](../../goal/wrench-gateway-model-research/GOAL.md)), which is not full-session frontier
token or dollar savings.

Public model results support further measurement, not a product conclusion:

| Model evidence | What it supports | What it does not establish |
|---|---|---|
| Qwen3.5-0.8B model card: task-specific fine-tuning is an intended use; it reports 25.3 on BFCL-V4 and 11.6 on TAU2-Bench, and no LiveCodeBench result for this size in its table | It is a sensible low-cost candidate for a constrained controller and a useful LoRA experiment | Reliable tool use, repository coding, day-long continuity, or 95% task coverage |
| Qwen3.5-4B model card: 55.8 LiveCodeBench v6 and 50.3 BFCL-V4 | A plausible local coding-worker candidate worth a separate controlled evaluation | Wrench task success, native end-to-end tool calls through our gateway, runtime fit, or all-day performance |
| Gemma 4 card: E2B 44.0 and E4B 52.0 LiveCodeBench v6 | Small models can show coding signal, and multiple model families merit controlled comparisons | Direct superiority over Qwen on our workload; the vendor evaluations are not Wrench results |

Do not use SWE-bench scores as the deciding proof. OpenAI's 2026 audit reports
that contamination and flawed tests undermine SWE-bench Verified, and a later
audit estimated roughly 30% of SWE-Bench Pro tasks were broken. This is a
reason to use fresh, private, repository-grouped tasks with reviewed
acceptance criteria and recorded failures.

New context-compression evidence reinforces the layered design, but does not
support the 95% target for real coding work. [StateComp](https://arxiv.org/abs/2609.27298)
reports 52.27% fewer agent-plus-summary tokens across 260 mixed-domain tasks,
with reward moving from 0.6987 to 0.7026. Its 80-task Code slice saves 38.89%
and changes reward from 76.99 to 77.12. The router uses frozen Qwen2.5-7B
representations; a reported high-precision threshold has 72.22% precision but
only 0.11% recall. Its 97.49% reduction is for the bounded representation
input, not the full agent trajectory. These results favor conservative,
state-aware retention and exact evidence recovery. They do not validate a
sub-1B coding worker or a Wrench result.

### Model-role decision

| Role | Practical size/type | Wrench disposition |
|---|---|---|
| Routing, evidence ranking, compaction policy | 0.8B-2B instruction model with a task-specific LoRA and constrained output | Start with the already-pinned Qwen3.5-0.8B Fit-03 protocol; grow only after a named capacity failure |
| Small repository changes | About 4B code-capable model, with actual test-running tool loop | Qwen3.5-4B is the first local challenger, not yet approved or measured |
| Hard, ambiguous, cross-repository engineering | Tool-capable stronger model | Keep as fallback; first establish the exact SubRoute provider/interface and hard spend accounting |

The Qwen3.5-0.8B card lists a 262K context window, but a large advertised
window does not guarantee accurate retrieval or safe long-context behavior.
Keep context accounting, source selection, exact-span recovery, and original
storage outside the model. Prefer lossless/extractive retention for active
code and errors. Compact repetitive cold history only when a recovery probe
and continuation check show that required state survives.

## The 95% target is five separate metrics

The project goal correctly separates local completion, frontier use, quality
retention, frontier-token savings, and all-in dollar savings. Keep all five
metrics and the sustained-work requirement independent:

- at least 95% of planned episodes finish locally with verified outcomes;
- at most 5% of episodes invoke a frontier provider;
- the hybrid retains at least 95% of frontier-only verified task success;
- frontier tokens across the complete episode are at least 95% lower than the
  paired frontier-only baseline; and
- all-in hybrid dollars, including local inference, energy, hardware/runtime,
  training amortization, retries, and human rescue, are at least 95% lower.

Five percent of episodes is not necessarily five percent of baseline tokens.
If the escalated 5% are each ten times as token-heavy as an ordinary episode,
they account for about 34.5% of frontier-only tokens before retries. That
would cap frontier-token savings near 65.5%, even if the other 95% of episodes
finished locally. Route by expected *baseline token/cost avoided* and verified
local success, not by episode count alone.

For each frozen paired workload, report:

```text
frontier token savings = 1 - hybrid frontier tokens / frontier-only tokens
all-in dollar savings  = 1 - hybrid all-in cost / frontier-only all-in cost
success retention     = hybrid verified success / frontier-only verified success
```

Include retries, tool schemas, local model tokens/compute, compaction,
verification, re-fetches, cache effects, interruptions, and human rescues.
Use paired confidence bounds with task/repository clustering; preserve every
failure and abstention in the denominator. A small convenient sample or a
synthetic pass is inconclusive.

For sustained engineering, retain the current preregistered goal: ten paired
independent eight-hour sessions across at least three unrelated repositories
and two languages, with task episodes and edit/test loops, interruption and
restart recovery, low stall time, zero severe regressions or lost work, and
zero unauthorized actions. Do not substitute short benchmark tasks.

## LoRA and experiment design

LoRA is appropriate for teaching a small model a narrow, repeated Wrench
decision format. It is not a substitute for a capable foundation model,
correct state, or a deterministic verifier. Keep the foundation and installed
Wrench-Core adapter frozen; train a new personal candidate only on reviewed,
outcome-backed experience. Store current repository facts externally. Treat
teacher disagreement and later corrections as candidate labels until checked.

The current Fit-03 package identity was reconciled in
[Iteration 083](../../evals/wrench-gateway-model-research/iteration-083-fit03-hash-pin-reconciliation-20260928.md):
12/12 identities match. Iteration 082's no-pass came from a one-character
expected-hash typo. This is an identity review, not execution authorization.
Fit-03 remains synthetic-only at 256 train / 64 dev, three epochs and exactly
96 optimizer steps. It remains closed until a fresh start check shows at
least 25% free RAM, storage and destination checks pass, and the 10% RAM/VRAM
floor can be maintained. The latest sample during this refresh was 10.81%
free RAM, 4,640 MiB short of the 25% start threshold; VRAM remained above the
10% floor. No model inference or training was done.

Only after Fit-03 and its dev gate should Wrench compare the frozen base,
Wrench-Core, and new LoRA on sealed synthetic held-out mechanics. That can
validate bounded decision mechanics; it cannot validate coding, route
economics, real task coverage, or workday reliability. Before any product
claim, freeze a representative, powered, private task set and run matched
frontier-only, deterministic Wrench plus frontier, and Wrench LoRA plus
frontier arms. Include an independently verified coding worker if the product
claims local code execution.

## SubRoute :4000 status

On 2026-09-28, read-only `GET` requests to `/health/liveliness`, `/models`,
and `/v1/models` returned HTTP 200. The catalog contains 19 aliases. This
proves the control-plane endpoints respond; it does not prove a model route,
provider, tool interface, completion, or billed cost.

The existing local Ollama inventory found Qwen3.5-4B Q4_K_M and Qwen3.5-0.8B
Q8_0 in a 4.426 GB Docker volume outside the approved Wrench storage root.
SubRoute's `desktop` alias points to `ollama/qwen2.5-coder`, which is not one
of the installed tags, and its configured Ollama endpoint is unreachable from
the gateway container. Do not count those weights as usable through port 4000
or start using them in Wrench until storage accounting and the route are
admitted. No running service was modified or restarted.

The user specified SubRoute at port 4000 but has not supplied a numeric
aggregate USD cap. Therefore this refresh used only the three read-only GETs;
it sent no completion or paid provider traffic. No credentials were read.

## Next steps

1. Preserve the rejected general semantic-controller result and the 11.64%
   synthetic-only context result as separate historical evidence.
2. Wait for Fit-03's 25% RAM start gate; then recheck exact identities,
   storage, destination space, and the runtime reserve before the already
   bounded synthetic LoRA run.
3. Score only through the frozen development protocol, then obtain fresh
   exact-hash review before any sealed held-out access.
4. If the 0.8B controller fails on a named capacity error, inventory and
   admit a specific 2B controller separately. Do not change the current fit.
5. Before a Qwen3.5-4B worker experiment, reconcile its Docker-volume bytes
   with the 50 GB boundary, pin the intended artifact/runtime, and repair the
   local SubRoute route only under the relevant service-change authority.
6. Keep provider generation closed until the aggregate cap, hard caller
   reservation, provider/model identity, and complete billed-cost receipts
   are established.
7. Compute paired sample-size power before beginning the product study, then
   test the five numerical claims and eight-hour sessions independently.

## Sources

- [Qwen3.5-0.8B model card](https://huggingface.co/Qwen/Qwen3.5-0.8B)
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Gemma 4 model card and benchmark table](https://ai.google.dev/gemma/docs/core/model_card_4)
- Wang et al., [StateComp: Learning When to Compress History in Long Horizon
  Agents](https://arxiv.org/html/2609.27298)
- [OpenAI: Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- [OpenAI: Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [Wrench product proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md)
- [Iteration 080: local snapshot and SubRoute read-only check](../../evals/wrench-gateway-model-research/iteration-080-subroute-and-model-snapshot-check-20260928.md)
- [Iteration 081: local Ollama inventory and configured route](../../evals/wrench-gateway-model-research/iteration-081-ollama-model-inventory-and-subroute-route-20260928.md)
- [Iteration 083: corrected Fit-03 package identity review](../../evals/wrench-gateway-model-research/iteration-083-fit03-hash-pin-reconciliation-20260928.md)
