# Proposed routing revision for review

Status: DRAFT. This does not replace protocol V1 or authorize a new run.

## Question the revised experiment would answer

Does adding the unchanged Wrench candidate improve task outcomes or resource use compared with cloud-only and deterministic rules when all arms use the existing dynamic gateway policy?

This measures the whole gateway workflow. It cannot isolate Wrench's effect under a constant cloud model. The gateway uses a shared allocation counter, so other traffic and differences in arm request counts can affect routing. Randomized arm order reduces systematic ordering bias but does not remove this interference. Report the result as specific to this gateway policy and run conditions.

## Proposed changes

1. Preserve the failed V1 comparison, all receipts, and its original protocol. Never pool those six episodes into a new complete comparison.
2. Keep the candidate, all three arms, tool boundaries, success definitions, family coverage, language allocation, and decision thresholds unchanged. Do not tune the candidate or prompts using exposed evaluation outcomes.
3. Create a separately versioned evaluation instance set with fresh fixture seeds, retaining the same 24 held-out wording families and 120 scenarios. Disclose that this is fresh instance evaluation, not previously unseen wording families relative to the interrupted run.
4. Record the live routing configuration before and after the run. Keep production settings unchanged. Record requested and resolved model identities per call and allocation metadata where available.
5. Accept documented single-call model promotions as part of the treatment environment. Continue to stop on missing provider usage, unaccounted internal calls, or unrecognized routing. Audit each request against gateway events before issuing any result.
6. Report actual model mix by arm alongside paired all-task outcomes, tokens, latency, failures, local overhead, and family uncertainty. Do not filter to favorable models or treat conditioning on resolved model as a causal correction. Tokens across models measure volume, not equivalent monetary cost or compute.
7. Carry forward V1's total request and token ceilings, subtracting previous experiment consumption. Account for the rejected response's reported tokens as well as accepted responses. Freeze exact remaining allowances before execution; a restart does not reset the resource budget.
8. Preserve the limit of three cloud turns per episode, two tool calls per message, 45-second timeout, zero transport retries, and strict draft-only writes. Freeze the revised schedule and analysis code before scored execution.

## Decision limits

The original quality and value gates remain necessary. An unexplained policy change, incomplete accounting, material tradeoff, or routing imbalance that prevents a defensible interpretation must qualify the result or make it INCONCLUSIVE. The pilot cannot establish fixed-model savings, production coverage, or a tight production reliability bound.

## Alternative

Retain the fixed-model scientific question and supply a separate endpoint that actually guarantees the requested model. This requires endpoint configuration and a new preflight; changing the production slider is outside the goal's scope. Preserve and disclose the interrupted run in either case.
