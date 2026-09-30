# Iteration 093: state-aware compression evidence on coding tasks

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-EVAL-ITER093-STATECOMP-CODING-CONTEXT-EVIDENCE-20260928`  
Status: **new external evidence; Wrench's 95% result remains unproven**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway research goal SHA-256 preserved:  
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## New paper and corrected interpretation

The 2026-09-23 preprint [StateComp: Learning When to Compress History in
Long Horizon Agents](https://arxiv.org/abs/2609.27298) is directly relevant to
Wrench's context-runtime direction. On WorkBuddyBench's 260 tasks, it reports
698.17M to 333.24M total agent-plus-summary tokens, a 52.27% reduction, while
mean reward moves from 0.6987 to 0.7026. WorkBuddyBench includes 80 Code, 50
Office, 60 Security, and 70 Web tasks. The Code slice saves 38.89% of tokens;
its reward changes from 76.99 to 77.12. Thus the headline is not a 95% coding
result, and the coding slice is materially below 95%.

The method learns when each past interaction is safe to replace given the
current state. It keeps complete interaction boundaries, requires evidence
already present in the prefix before marking an interaction ready, and uses a
separate summarizer. The tested router uses frozen Qwen2.5-7B representations.
In one high-precision operating point, external precision is 72.22% at only
0.11% recall. This illustrates the asymmetric tradeoff: missing a compression
opportunity costs tokens, while deleting needed context can damage later
actions.

The paper's bounded hidden-state input has a 5,120-token cap and reduces the
largest recorded representation input by 97.49%; that is a representation
efficiency result, not a 97.49% reduction in total agent tokens. For the
full-trajectory result, token totals include agent and summary calls, while
local representation cost is reported separately. The online method replaces
raw history with summaries and does not retrieve deleted raw interactions;
its audit copy is not an online evidence store. Wrench should retain
hash-addressed originals and support exact fetch-on-demand, then charge every
retrieval and recovery token to the result.

## Comparison with prior evidence

| Evidence | Reported savings | What the task/result supports |
|---|---:|---|
| [SKILL.state](https://arxiv.org/abs/2608.26263) | 95.12% at 100 steps; 34.8% at 10 steps | Deterministic simulated software-repository state transitions; not real repository edits or Wrench's local LoRA |
| [StateComp](https://arxiv.org/abs/2609.27298) | 52.27% overall; 38.89% on Code | Long-horizon mixed-domain agent trajectories, with a Qwen2.5-7B frozen-representation router; no 95% code result |
| [SWE-Pruner](https://arxiv.org/abs/2601.16746) | 23-54% on coding-agent tasks; up to 14.84x on a single-turn task | Task-aware line pruning; the high compression figure is not end-to-end multi-turn coding savings |
| [SWE-Pruner Pro](https://arxiv.org/abs/2607.18213) | Up to 39% | Prompt plus completion tokens on multi-turn coding benchmarks, with task quality reported as preserved |

The sources point to a credible layered opportunity: deterministic parsing,
tool-schema filtering, and exact source selection first; learned, conservative
state-aware retention next; a capable coding worker for edits and verification;
and frontier escalation for uncertain or difficult work. Published results
support studying this design. They do not support promising 95% savings in
advance.

## Wrench experiment consequences

1. Keep the already-pinned Qwen3.5-0.8B LoRA as a bounded context/routing
   controller candidate. Its proposals should identify `KEEP`, `RETRIEVE`,
   `COMPACT`, `STOP`, or `ABSTAIN`, plus evidence IDs and a reason code. A
   deterministic validator owns schema checks, state merge, rollback, route
   allowlists, and all tool permissions.
2. Keep code implementation separate from that controller. The installed
   Qwen3.5-4B quantization remains a plausible local worker candidate only
   after its Docker-volume bytes are admitted to storage accounting and its
   route is safely connected through the requested SubRoute on port 4000.
   Neither model's local repository-engineering performance has been measured
   here.
3. Compare the same seeded repository episodes across four arms: full
   transcript; current Wrench ledger; validated external state with exact
   evidence retrieval; and external state plus the LoRA controller. Use
   private, reviewed repository tasks with actual edits, tests, failed tests,
   interruption/restart, external changes, stale evidence, and requests to
   explain prior decisions. Stratify by episode length so long sessions do not
   hide short-task behavior.
4. Count serialized request input, generated output, tool schemas, local
   controller calls, summary calls, retries, state validation, refetches, and
   recovery across every tier. Check exact target-tokenizer counts against
   SubRoute usage receipts when a generation route is separately admitted.
   Report local compute and all-in cost separately from frontier-token
   savings. Evaluate end-to-end quality on the same paired tasks.
5. Preserve complete event/source evidence outside the active prompt. Before a
   state transition, require current evidence IDs, version and hash checks,
   required-field validation, and deterministic rollback on malformed,
   stale, or conflicting patches. Add held-out probes for evidence omission,
   error-trace recovery, and historical explanation before compression is
   enabled.
6. Measure the 95/5 requirement by episodes and by tokens separately. A 5%
   episode escalation rate does not imply 5% of baseline frontier tokens: if
   escalated episodes are ten times as token-heavy as the rest, they account
   for about 34.5% of baseline tokens before retry costs.

The paper's task-success parity and its token reduction are not a proof of
all-day engineering. Wrench still needs paired eight-hour sessions across
unrelated repositories and languages, with completion quality, recovery,
stall time, lost-work incidents, unauthorized actions, and human rescue all
measured. None of the sources establishes that one sub-10B model can perform
all such work.

## Run disposition

This was a literature and source synthesis only. No source code or goal file
was changed. No tests, model load, inference, training, benchmark, provider
call, credential read, or delegation occurred. The latest live sample during
this iteration showed 9.24% free system RAM and 15,232/16,311 MiB free VRAM;
the RAM runtime floor is breached, so runtime work remains closed. Storage
status including the automation directory and Docker model volume was
`WITHIN_LIMIT` at 15,418,779,477 actual bytes before the 25,000-byte report
reservation. No SubRoute completion request was sent.

## Primary papers

- Wang et al., [StateComp: Learning When to Compress History in Long Horizon
  Agents](https://arxiv.org/html/2609.27298), 2026-09-23, sections 3-5 and
  Appendix F.
- Badhe, Tiwari, and Chung, [SKILL.state: Scalable Long-Horizon Agent
  Skills](https://arxiv.org/abs/2608.26263), 2026-09-02.
- Wang et al., [SWE-Pruner: Self-Adaptive Context Pruning for Coding
  Agents](https://arxiv.org/abs/2601.16746), revised 2026-05-07.
- Wang et al., [SWE-Pruner Pro: The Coder LLM Already Knows What to
  Prune](https://arxiv.org/abs/2607.18213), 2026-07-20.
