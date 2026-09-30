# Token efficiency research for large coding projects

Date: 2026-09-26  
Scope: practical ways to reduce coding-agent token use and provider spend on a large repository, compared with Wrench v2's Layer 1 context-runtime direction.

## Executive summary

The most robust way to reduce tokens is to stop sending irrelevant material: retrieve a small, task-specific set of exact source evidence instead of repeatedly pasting repository files, broad search results, and full logs. Aider's repository map is a concrete example: it sends important symbols and signatures under a token budget, then exposes files for deeper reads when needed. Wrench's W0-W2 design already aims at this retrieval-and-exact-evidence pattern.

The next practical gains are usually command-output shaping, progressive tool/schema discovery, stable prompt prefixes, and explicit task/session boundaries. Prompt caching can materially lower the price and prefill latency of repeated prefixes, but cached tokens are still sent and count as input tokens. Compaction can avoid context-window overflow, but can create extra rereads if the continuation note loses task state. These approaches should not be combined into a single “tokens saved” number.

Community reports are useful for generating hypotheses, not proving savings. Developers report benefits from RTK/tokf-style CLI filters, repo maps and AST/code graphs, smaller project instructions with on-demand skills, session resets with durable handoff notes, and watching actual usage. Other developers warn that lossy compression can remove comments, imports, decorators, or the one critical log line. Measure task success and rereads along with token counts.

## What “saving tokens” means

Keep these quantities separate in any comparison:

1. **Total input/output tokens:** what the full request lifecycle processes, including retries, tool schemas, verification and compaction summaries.
2. **Billed cost:** determined by provider/model rates and cache writes/reads, not only by raw input count. Caching can lower cost without reducing sent tokens.
3. **Active-context pressure:** how much material the agent must keep in its current context. External memory and fresh sessions can reduce this even when they do not reduce total billed tokens.
4. **Work avoided:** fewer frontier calls or model-generated tokens through deterministic parsing, tests, routing, or stopping. This can save spend even if the remaining calls have similar prompt sizes.

For Wrench, compare complete matched task lifecycles as defined in [Experiment v2](../../northstar/V2_EXPERIMENT.md), and report provider usage fields, local processing, latency, task success, retrieval misses, rereads, retries, and cache behavior separately. A compressor's before/after count is not by itself a utility result.

## Practical approaches people use

| Approach | How it reduces use | Evidence and tradeoff | Wrench fit |
|---|---|---|---|
| Task-scoped retrieval and repository maps | Send relevant symbols, signatures, dependencies and exact excerpts rather than full trees/files. Expand only when a task needs implementation details. | Aider uses a graph-ranked repository map and a default 1k-token budget, then lets the model request relevant files. This is a documented product mechanism, not a universal savings guarantee. | Highest fit. This is already the W0/W1/W2 direction. Finish exact source retrieval and measure misses/extra reads. |
| Incremental indexes and external project memory | Keep reusable structure and verified facts outside the prompt; retrieve a small portion per task rather than rediscovering definitions. | Community users say persistent memory helps avoid rereading repeated schemas and definitions. Index staleness and inaccurate summaries can mislead. | High fit. Keep source-of-truth in versioned external state; bind evidence to snapshot/hash and retrieve originals. |
| Filter noisy CLI output | Return exit status, concise test summary, first/last relevant diagnostics and a stable handle to the full log. | RTK and tokf are examples. RTK itself clarifies its “up to 90%” figure refers to bash-output bytes, not the same percentage of total bill. Community users report large command-output reductions, but anecdotes are not matched task evaluations. | High fit for logs, successful test/build noise, cloud listings and repetitive output. Preserve full output locally and make expansion easy. Never trim source diffs or failure evidence blindly. |
| Progressive tool and schema discovery | Initially expose a small tool catalog; load namespace documentation/schema only when requested. | Anthropic's advanced tool-use material describes deferred tool discovery and orchestration; provider prompt-cache docs also show tool definitions as cacheable prefixes. More discovery steps can add calls if overused. | High fit. W3 already specifies namespace discovery and deferred schemas. Verify that schemas are compact and discovery requests are bounded. |
| Stable prompt prefixes and prompt caching | Keep system instructions, tool definitions and stable project context byte/token-identical at the start of requests so providers can reuse prefix computation and offer cache pricing. | OpenAI and Anthropic document prefix-based caches, usage reporting and pricing effects. It reduces repeated processing/cost, not total tokens transmitted; cache misses, TTLs, request ordering and edits matter. | Medium-high fit at the client/gateway boundary. Preserve stable ordering and track cache read/write/uncached tokens. Do not call cache savings “token reduction.” |
| Compact, layered project guidance | Keep always-loaded instructions short; move detailed how-tos and rarely used procedures into on-demand skills/docs. | Developers report trimming CLAUDE.md/AGENTS.md, loading skills on demand, and avoiding irrelevant auto-loaded tools. These are workflow reports; there is no common benchmark. Over-trimming can omit essential invariants. | High fit. Wrench's own root AGENTS is detailed and always relevant to Codex here, but do not rewrite owner-authored governance as a token optimization task. For downstream clients, make small core guidance point to staged, task-relevant docs. |
| Session boundaries and durable handoffs | Finish bounded work, persist verified state, and start a fresh session instead of carrying a long transcript indefinitely. | Community discussions report that auto-compaction may lose decisions and cause rediscovery; some users prefer starting a new session around halfway. A new session itself repeats system/project context. | Medium fit for orchestration guidance. Store task state, changed files, decisions, failures and next actions outside transcript; reopen exact evidence by handle. Measure repeated reads. |
| Structured compaction and history pruning | Replace stale/repeated history with a short structured continuation summary while preserving exact originals externally. | Popular harness feature, but users warn that lossy compaction creates rediscovery loops. Any summary may omit a needed fact. | Medium fit. Compaction should be reversible via source/session handles and preserve decisions, constraints, active diff, failures and open questions. Never compact away authority policy. |
| Usage telemetry and context profiling | Attribute tokens/cost to system prompt, tools, retrieval, files, terminal output, retries, verification and model output. Fix the biggest measured contributor first. | Community recommendation threads emphasize examining session logs and distinguishing local trackers from provider-side usage. RTK also offers session/gain analytics, but its byte savings are estimates. | Highest fit as a measurement prerequisite. Wrench E4 already requires complete accounting; add per-component attribution before choosing optimizers. Provider-reported usage is the accounting source of truth where available. |
| Call/output bounds and narrow tasks | Avoid repeated broad exploration, unconstrained retries, verbose narration, and oversized completion budgets. Use deterministic checks for deterministic work. | Claude's documentation advises reducing over-eager prompting for current models; community users recommend explicit turn limits, fail-fast commands, concise output and task plans. | High fit. Wrench already has bounded retrieval and lifecycle accounting. Set limits per route and record quality failures/escapes. |
| Model routing and local preprocessing | Use a cheaper/fast route for suitable subtasks or deterministic/local logic for mechanical work; reserve strongest models for difficult reasoning. | Common practice, but using a smaller model does not inherently reduce tokens and may increase retries or degrade quality. Wrench's 0.8B semantic-controller route failed its intended workflow screen; the 2B case is untested. | Conditional. Deterministic parsing/filtering remains promising; do not revive the rejected 0.8B route or claim a model-size solution without new scoped evidence. |
| Semantic/code compression | Replace source/log text with summaries, AST slices, graph context, or compressed representations. | It can reduce context substantially, but community reports highlight silent quality losses from dropped comments, imports, annotations, or failure details. Product claims such as “90%” are often not quality-controlled end-to-end measurements. | Use selectively. Safe for repeated boilerplate and cold history with exact retrieval. Keep active diffs, user-selected code, errors, and requested details lossless. Test on held-out task pairs. |
| Parallel agents | Split independent investigation or review so each worker sees less context. | Can reduce each agent's context pressure, but total token spend can increase due to duplicated setup, overlapping reads, and summaries. Not an automatic savings strategy. | Low as a token-savings lever. Use only where work is genuinely independent and the value of parallelism exceeds duplicated context. |

## What practitioners are trying

The community discussion is fragmented rather than converged on one winning tool. Patterns recurring across discussions include:

- **RTK / tokf and custom command wrappers:** intercept shell commands and replace boilerplate with a concise result while keeping the raw log available. Users like deterministic filters and repository-specific rules. Some prefer agent-written `tail`/`grep`/summary commands; others prefer hooks because they apply consistently. The deciding factor is reliable semantics and recoverability, not whether the filter is agentic or mechanical.
- **Repo maps and code graphs:** Aider's map is established and lightweight; some users experiment with Tree-sitter/AST-backed code graphs and MCP servers such as codebase-memory. Users disagree about whether full knowledge graphs are worthwhile outside very large repositories. For Wrench, start with bounded symbol/import/dependency edges and only deepen where measured retrieval misses justify it.
- **Smaller always-on instructions plus on-demand knowledge:** Users describe keeping project instructions concise, placing reusable workflows in skills, and disabling unneeded startup tools. This likely reduces repeated fixed context and improves focus, but should retain critical project rules.
- **Persistent notes and fresh sessions:** Some users keep a concise status/handoff file to avoid re-explaining the project; others warn that auto-compaction discards useful reasoning and prompts redundant file reads. The useful version stores verifiable state and source references, not a second prose copy of the repository.
- **Usage inspection:** Developers recommend looking at actual session logs and distinguishing prompt/input/output/cached tokens. Anecdotal trackers can diverge from provider quota meters; use server-reported usage where available.
- **Skepticism about aggressive compression:** Users point out that token reduction can damage performance, especially when compressing source code. External HTML, repetitive logs, long test output and noisy command responses are safer initial targets than code content.

Reddit posts and tool author reports are self-selected and often promotional. Treat claimed percentages as hypotheses; the useful evidence is the workflow description and reported failure mode, not the headline number.

## Recommended order for Wrench

1. **Instrument a baseline before adding another optimizer.** Capture exact provider usage fields per request, route, retry, schema, cache read/write and output. Attribute input to stable instructions, tools, task text, source evidence, logs and conversation history. Keep total lifecycle tokens distinct from billed dollars and local context pressure.
2. **Complete task-specific retrieval.** Use compact structural candidates and lexical search; insert exact, hash-bound lines/symbols only for likely evidence. Keep omissions, budget decisions and retrieval handles inspectable. Expand with bounded follow-up reads on demand.
3. **Add lossless output shaping for noisy tools.** A successful test/build should return a concise status; failures should include exact failing test/error lines and a handle/path to the complete output. Keep user-selected files and active diffs lossless.
4. **Keep prompts cache-friendly.** Put stable instructions and stable tool definitions before dynamic task/source context. Avoid volatile timestamps or reordered schemas in the stable prefix. Track cache hits separately; caching is a cost/latency lever, not a reduction in transmitted tokens.
5. **Keep continuation state external and verifiable.** For long tasks, persist goal, current decision, changed files, checks, exact failures, source hashes and next action. Begin a clean session when useful, but include only a short handoff plus retrievable source IDs.
6. **Evaluate compression behind a quality gate.** Start with logs, repetitive tool output and cold history. Compare exact tasks against uncompressed input and score success, missed evidence, additional retrieval/rereads, retries, latency and total provider usage. Reject optimizations that lower tokens while raising error or recovery costs.

This priority order complements rather than replaces Wrench's staged E0-E4 experiment. No model download, training, provider call, production enablement or new data capture is part of this research task.

## Proposed decision metrics

For each matched task, record:

- downstream input, output, cached-read, cache-write and uncached-input token counts, plus dollars where usage is available;
- Wrench local prompt/completion tokens and deterministic processing time separately;
- first-pass and final task success, including evidence correctness and prohibited-action count;
- number and size of source/log reads, retrieval misses, rereads after compaction, retries, fallbacks and verification calls;
- median and p95 end-to-end latency; cache-cold and cache-warm cases;
- context compiler token count using the actual route tokenizer and final serialized request identity.

Report paired differences and uncertainty. A technique passes only if it reduces the target quantity with no material task-success regression, and does not hide extra calls, retries, or local cost.

## Sources

### Product documentation and primary sources

- [Aider repository map](https://aider.chat/docs/repomap.html): graph-ranked signatures and symbols selected under a configurable token budget; retrieved 2026-09-26.
- [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching): prefix reuse, cache diagnostics and cached-input billing; cached tokens still count toward token-per-minute limits; retrieved 2026-09-26.
- [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching): stable content ordering, cache breakpoints, pricing and usage-field accounting; retrieved 2026-09-26.
- [Anthropic prompt engineering](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables): prompt structure, large inputs, context tracking and multi-window workflows; retrieved 2026-09-26.
- [Anthropic advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use): deferred tool discovery and programmatic orchestration; retrieved 2026-09-26.
- [RTK documentation](https://github.com/rtk-ai/rtk/blob/develop/docs/guide/index.md): CLI output filtering and explicit distinction between bash-output bytes and total bill; retrieved 2026-09-26.
- [tokf project discussion](https://www.reddit.com/r/ClaudeCode/comments/1rdakgm/): user-configurable TOML filters and keeping full logs accessible; community/user report, retrieved 2026-09-26.

### Practitioner discussion (anecdotal, not controlled evaluations)

- [r/LLMDevs: tools for reducing coding-agent token usage](https://www.reddit.com/r/LLMDevs/comments/1ucqks9/tools_for_reducing_token_usage_in_coding_agents/): caching, compaction, persistent memory, and warnings about silent loss and rereads; retrieved 2026-09-26.
- [r/Codex: reported savings from an AGENTS.md rule and RTK](https://www.reddit.com/r/codex/comments/1t6iulo/i_cut_codex_token_usage_50_with_one_agentsmd_rule/): workflow claims and counterarguments about compression quality; retrieved 2026-09-26.
- [r/ClaudeCode: risks in token optimizers](https://www.reddit.com/r/ClaudeCode/comments/1spiy8t/token_optimizers_for_ai_coding_agents_are/): reports on filtering cloud CLI output and concerns about semantic loss and inaccurate usage tracking; retrieved 2026-09-26.
- [r/ClaudeCode: tokf CLI filter discussion](https://www.reddit.com/r/ClaudeCode/comments/1rdakgm/): community discussion of hooks, deterministic filters, agent-generated summaries and retaining full logs; retrieved 2026-09-26.
