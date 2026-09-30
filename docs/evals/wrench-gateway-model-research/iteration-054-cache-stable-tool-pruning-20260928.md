# Iteration 054: make tool pruning cache-stable and recoverable (2026-09-28)

## Research evidence that changes the next experiment

The Paritok authors' multi-turn cost-attribution preprint isolates tool-schema
filtering, file/output compression, and history summarization. On their own
MCP-heavy Claude Code/Codex setups, they report 21K-57K fewer schema tokens
per typical request and 20:1 to 33:1 more savings from tool filtering than
content compression in two sessions. Their measured five-turn content-only
reduction is 22.2%; the reported 39% full-stack value combines that content
measurement with the separately measured tool-filter effect. The paper says
the 85%+ context-saturated value is a projection under its stated assumptions.
These results make tool schema filtering the leading Wrench mechanics arm,
but the absolute counts and savings do not transfer to Wrench without exact
request capture.

The Paritok-4B single-shot SWE-bench Lite results remain a different measure:
25.7% context retained with 86.5% quality retention, or 27.8% and 89.3% in
the line-numbered setting. They do not establish multi-turn costs, 95% task
quality, or all-in savings. The cited papers are the authors' research
preprints; the Paritok repository exposes an evaluation harness, but no Wrench
run was performed here.

## Wrench prototype review

The current source in
`examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs` calls the
profile selector on every request using the current messages. It has no
session profile cache. A changed profile can change the transmitted tool
block each turn, which may reduce provider prompt-cache reuse. It also deletes
non-allowlisted schemas without an explicit tool-discovery or expansion
mechanism, so a later task step can be left unable to request an omitted tool.
The prototype is disabled, and no active OpenCode configuration was changed.

Added a deployment-gaps section to the prototype README. Before an engineering
pilot, the integration needs a stable session identity, a profile frozen for
that session, an explicit set of required execution and verification tools,
and a bounded way to request schemas from the original hash-bound inventory.
The helper tool must not change native permissions or executable tool
implementations. A schema expansion may cause one cache-key change for that
session; capture and price that transition, the helper-schema overhead, and
any later expansion. Unknown identity or inventory mismatch must pass through
the full inventory.

OpenCode's current V2 plugin documentation describes a session ID on the
context-hook event and custom-tool registration, but compatibility with the
installed v2.0.12 package is still unverified. Verify the installed version's
actual hook payload, request ordering, and final lowered tool block in a
no-provider runtime harness before relying on the API shape.

## Current gates and next action

The fresh host sample at 2026-09-28 01:53 UTC showed 3,400.1 / 32,701.8 MiB
free RAM (10.40%), only 0.40 percentage points above the 10% floor. The RTX
5060 Ti had 15,215 / 16,311 MiB free VRAM. No tests, model runtime, inference,
training, benchmark, packaging, or delegation ran. No model download, API
credential read, provider POST, or spend occurred. The numeric SubRoute
campaign cap remains unanswered.

The first local checks after a comfortable resource recovery remain the
hash-bound SubRoute budget/capture suite and a no-upstream test that verifies
provider-control metadata reaches the SubRoute transformer. Next implement and
test session-frozen, recoverable tool profiles on the exact OpenCode v2.0.12
runtime, then capture and tokenize the exact request. Only after those
mechanics pass should paired multi-turn repository episodes compare full
tool-schema filtering, content pruning, their combination, and the frontier-
only baseline. Count cache tiers, profile/expansion changes, retries, recall,
turns, verified task success, and all local cost.

## Sources

- Chen and Shi, [An Empirical Cost Attribution of Context-Compression Gateways in Multi-Turn Coding Agents](https://arxiv.org/abs/2609.22114), September 2026.
- Shi and Chen, [Paritok-4B: Intent-Conditioned Context Compression for Coding Agents](https://arxiv.org/abs/2608.24188), August 2026.
- [Paritok-4B evaluation repository](https://github.com/Paritok-official/paritok-4b-v1).
- [OpenCode V2 plugin hooks](https://opencode.ai/v2/docs/build/plugins).
- [Earlier Wrench research synthesis](../../reports/wrench-gateway-model-research/research-synthesis-20260927.md).

## Disposition

The research supports a stronger mechanics hypothesis, not the requested
effectiveness claim. Wrench must first keep tool filtering stable and make
omitted capabilities recoverable. The trained Wrench LoRA, 95/5 task mix,
95% frontier-token reduction, 95% lower all-in cost, and sustained coding
remain unproven. The goal remains active.
