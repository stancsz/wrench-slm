# Iteration 208: Fail-Closed Frontier Usage Accounting and Direction Review

Date: 2026-09-29
Status: focused local verification passed; product acceptance remains unproven.

## Identity

- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
- `src/wrench_harness/server.py`: `CF86ED50DCA499438E71D98D1AE989F6B992BB4457226BE674AD0039F98BE6F9`
- `tests/test_wrench_server.py`: `0D442762A73A6F484C8AFAEECB4601700E42DCC396D27D2630429F0E0E4C910E`

## Change and local verification

Frontier usage aggregation now treats any attempt with missing, malformed, negative, or inconsistent token usage as incomplete. Aggregate prompt/completion/total token fields become unavailable rather than summing partial retries. Cost is independently reported only when every attempt supplies a finite, nonnegative cost. A declared Frontier call with no usage receipt no longer contributes zero to workflow tokens. Dynamic-prefill accounting also fails closed when any attempt lacks complete usage.

Focused tests passed via Python 3.13 direct invocation because `pytest` is not installed in the global interpreter:

- `test_frontier_usage_receipt_fails_closed_on_empty_or_partial_retry_usage`
- `test_native_upstream_uses_one_bounded_repair_pass_after_format_failure`
- `test_native_upstream_receives_staged_prefill_for_monster_payload`

`git diff --check` passed. The command emitted existing line-ending conversion warnings for dirty worktree files. No provider request, model inference, training, held-out read, or benchmark occurred. This verifies synthetic/local behavior only, not provider-reported billing or savings.

Admission sample before the focused tests: 29.86% system RAM free; RTX 5060 Ti VRAM free 15,223/16,311 MiB, GPU utilization 0%. Storage checker reported `WITHIN_LIMIT`, 32,708,925,250 bytes actual and 57,103,000 bytes reserved at that time. This is a point-in-time sample, not a sustained workload guarantee.

## Sol advisor consultation

- Job: `WRENCH-LUNA-ADVISOR-DIRECTION-20260929-01`
- Nonce: not provided by caller
- Endpoint/model: dedicated local expert endpoint on port 4040, `codex-sol-advisor`; read-only model-list check confirmed only Sol and Astra aliases. Port 4000 SubRoute was not used.
- Packet: 2,327 characters; no secrets; asked which direction is aligned and for one provider-free experiment and quantitative stop condition.
- Reported usage: 628 prompt tokens, 537 completion tokens, 1,165 total. Caller reported no cost field.
- Advice: prioritize deterministic context runtime and measurement over LoRA scaling. Suggested a paired 40-episode local coding battery with 20 route and 20 retrieve-stop cases, and stopping model-scaling work if a larger model adds fewer than 2/40 verified completions or misses more than 1/20 in either category. It explicitly warned local results cannot prove Frontier token/cost targets.
- `decision_changed: false`. The advice supports the already selected v2 architecture and current instrumentation direction. The 40-case recommendation and its thresholds are hypotheses, not validated acceptance criteria; test whether a representative, license-safe task set and valid local endpoint can support that experiment before admission.

## Research interpretation and next gate

Current 4B LoRA synthetic dev score (26/64 vs base 18/64) is a provisional lead over the separately evaluated 2B LoRA (8/64 vs base 16/64), not an overall parameter-size winner. Both 4B arms scored 0/16 on route and retrieve-stop; 4B LoRA schema validity was 59/64 vs 64/64 for base. A separate three-case lookup battery retained 3/3 answers while local target-tokenizer prompt counts fell from 26,244 to 521 (98.0148%); it had zero Frontier calls and cannot be called Frontier token or cost savings.

The product direction is still right as a hypothesis: deterministic Wrench code reduces or compacts text before it is sent to the downstream model, and the API normally receives text, not Wrench's local token IDs. A local tokenizer count estimates length. Only paired provider-reported usage on identical frozen episodes can establish actual billed token savings. Keep 4B as the provisional small-controller experiment lead, not as the winner or an autonomous coding model. Next prioritize an auditable paired engineering/task battery and final outgoing-context/usage correlation; defer model-size scaling until this measurement path and task representativeness are sound. All acceptance thresholds remain unproven.
