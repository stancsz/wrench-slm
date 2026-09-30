# Context-compression evidence refresh: tokens are not utility

Date: 2026-09-30  
Scope: provider-free research update for the 0.5B-12B gateway comparison  
Candidate decision at start: provisional Qwen3.5-2B for bounded evidence/context decisions; no local winner established.

## New evidence

The 2026-09-26 preprint *Beyond Token Savings: A Systematic Study of Context Compression in LLM Agents* varies compression policy across three open-weight models on SWE-bench Verified and Terminal-Bench 1.0, reporting nearly 35,000 agent runs. Its abstract reports that on Terminal-Bench with Qwen, some policies using roughly one-third as many tokens took 20-80% longer than the uncompressed agent. Policies with similar aggregate success also solved different tasks, and a policy behaved differently across models. This is unusually direct support for measuring end-to-end completion, latency, and task-level paired outcomes rather than promoting token reduction by itself. It is a new arXiv preprint, not an independently replicated Wrench result. Source: [arXiv:2609.32961](https://arxiv.org/abs/2609.32961).

The full text separates policy into **primitive**, **trigger**, and **compression depth**, then evaluates 65 policies over Qwen3.5-35B-A3B, Devstral-Small-2-24B, and GLM-4.7-Flash, with three runs per task/policy/model configuration. On SWE-bench, tool-result clearing (TRC) used about 0.57x the tokens, 0.79x the latency, and 0.71x the billed input cost of full context while mostly matching its resolve rate. A summarization policy using a similar 0.59x token volume lost 11 percentage points of success. On Terminal-Bench, 11 of 12 policies reduced success by 5-13 points; most used 0.25-0.4x the tokens and took 1.05-1.8x as long. The authors also find that frequent compaction can invalidate reusable prompt prefixes; their cost figures assume cached input receives a discounted rate. These figures are the paper's benchmark outcomes and pricing assumptions, not Wrench estimates.

Two task-specific compression results help explain why a small controller remains plausible but do not validate the product target:

- **Qwen3.5-2B / Squeez:** LoRA tool-output pruning reports 0.86 recall and 0.80 F1 on a manually reviewed 618-example test set while removing 92% of input tokens. The task is selecting verbatim evidence from a single tool observation. It does not measure downstream repository-task completion, a multi-turn gateway, or the all-in cost of a complete coding episode. Source: [arXiv:2604.04979](https://arxiv.org/abs/2604.04979).
- **Qwen3-4B / Paritok-4B:** on 300 SWE-bench Lite tasks, context was reduced to 25.7% of its input and reported solve quality retained was 86.5%; with line-numbered input the figures were 27.8% context retained and 89.3% quality retained, with a paired result that did not reach statistical significance (`p=0.079`). This is closer to downstream coding utility than per-observation extraction, but still falls short of Wrench's 95% success-retention threshold and uses a different model, harness, data and hardware. Source: [arXiv:2608.24188](https://arxiv.org/abs/2608.24188).

## Effect on the size decision

The new systems study does not establish which model size Wrench should deploy. It strengthens the current role-based hypothesis: a 2B LoRA controller is a credible first candidate for narrow, extractive evidence selection, while 4B remains a serious compression challenger and neither has proven the full 95/5/95 target here. The model-size decision remains provisional because the local 2B adapter, resource fit, paired end-to-end success, and sustained workload have not been measured.

The evidence also changes what counts as a useful token-saving result. Future local screens must retain each episode in the denominator, preserve the complete full-context and prepared-context arms, attribute retries and recovery, record output as well as input tokens, and report verified task outcome, paired discordances, latency and all-in cost alongside token counts. A low token count with a failed or slower episode receives no success credit.

For Wrench's next paired policy study, keep the evidence mechanism, its trigger, and its reduction depth separately identifiable. Include a deterministic tool-result clearing or exact-span selection control next to the learned controller, and keep cache state, compression work, call count, and per-task gains/losses visible. The existing `frontier_usage` code records response-reported cached input tokens across requests but explicitly does not verify the provider bill; pricing and cache assumptions still need a separate auditable ledger. The paper's models are 24B-35B-class agents, so these findings support the evaluation design, not a 2B or 4B model-size ranking.

## Current Wrench gate

This is external research, not Wrench performance evidence. The Iteration 220 tokenizer-only screen has a wired 65,536-token source-ingestion cap but was not rerun in this evidence update. The on-disk active-goal hash remains `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`; the heartbeat declares `b847d638b0ca4f9c24041dccec2fb440861f0b27be0441e37e288057f701b027`. No model/provider calls, training, local token measurement, sealed-data access, or adapter changes occurred.
