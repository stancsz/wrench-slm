# Wrench model-side toolbelt

> Historical v1 document. Its scope and active wording are superseded by
> [Wrench v2](../../../GOAL.md). Retained behavior still requires its original evidence.

The 2M or 4M payload is not treated as an undifferentiated prompt. Wrench
should expose a small deterministic toolbelt beside the model so the latest
intent stays visible while older context remains searchable reference data.

The first tools are read-only:

- source AST extraction for Python and a lexical fallback for other languages;
- a hash-bound symbol index for functions, classes, interfaces, and types;
- conservative import and call dependency evidence;
- a recent-intent tracker that gives the latest user message priority;
- lexical reference lookup with source path and line evidence;
- a compact repository map and changed-file to test selector;
- failure fingerprinting for bounded retry and escalation decisions;
- local syntax and placeholder gates for proposed source text;
- patch and diff inspection before a draft is sent to the independent verifier.

These tools are not autonomous authority. They do not execute shell commands,
write files, or apply patches. The model chooses a bounded proposal, and the
verifier decides whether it is eligible. Old lookup hits are marked
`reference_only` and never override the newest user intent or the authority
boundary.

The production fast path is a package-local hybrid runtime. It accepts the raw
4M logical payload, performs an explicit staged prefill, keeps current intent
and hot tool state verbatim, and turns old lookups into hash-bound reference
cards in a read-only lookup table. The receipt reports both raw input tokens
and model prefill tokens, so internal compression cannot be misreported as
native dense attention.

This hybrid path is the active productive-value target when it meets the complete workflow
gates: retrieval quality, safety, final success, frontier-token savings, and
end-to-end latency. Dense native attention, native-direct comparison, and
model-runtime adapter work are skipped under the current goal. They are not
Wrench product claims and must not hold the hybrid productive-value path
hostage.

The dynamic prefill uses cheap regex anchors first, then AST or lexical symbol
extraction for code. It preferentially retains paths, symbols, tests, errors,
URLs, identifiers, and the newest unresolved observations. A lookup expansion
is an explicit second action, not accidental attention pollution.

The default effective working context is 64K, with roughly 48K for recent hot
context and 16K for mechanical lookup cards. The 100 ms target is a hot-path
target for cached 4M-to-64K selection.
Cold indexing is incremental work performed as context arrives. It is reported
separately from request latency and never hidden inside a model benchmark.

## Frontier handoff, not frontier replay

An abstention is now accompanied by a bounded
`wrench.advisor-handoff.v1` packet. The packet contains the newest intent, the
selected working context, the local failure reason, the Wrench attempt, and
the hash-bound prefill receipt. It does not contain the raw 2M or 4M payload or
an unbounded lookup table. The original payload remains available out of band
for audit and explicit lookup.

The handoff policy is deliberately small: one frontier review pass followed by
at most one repair pass. Each frontier result returns to Wrench's parser,
authority checks, and multi-pass verifier before it can be accepted. The
frontier model has no tool execution or mutation authority. If the packet
cannot be built within its byte budget, Wrench keeps the original abstention
and fails closed instead of forwarding the monster context.

When a client executes a verified read-only proposal and sends the result back,
the upstream path has one additional bounded state. The second response must be
exactly `wrench.final-answer.v1` with `schema`, `answer`, and
`tool_result_sha256`. Wrench accepts the answer only when the hash matches the
bounded result associated with Wrench's read-only tool-call id. A repeated
proposal, wrong hash, free-form text, invalid transition, or third frontier
call terminates as an abstention. This keeps completion, safety, loop freedom,
and token accounting inside the portable model package rather than delegating
them to OpenCode, DeepSeek Harness, or Claude Code.

This is the main cost lever. Wrench performs the repetitive map, retrieve,
AST, and verification work continuously, while the paid model sees only the
latest intent and a bounded evidence packet. The useful success metric is the
matched workflow's final success and total frontier-token savings, including
handoff, retries, corrections, and fallback overhead. A smaller model score by
itself is not a production-value claim.

For context-sensitive requests, the package has a conservative adaptive tier.
The newest intent must contain a marker such as `debug`, `compare`, `trace`,
`root cause`, or `review-only`, and the raw payload must be materially larger
than the base tier. Those requests may use a 128K working context, subject to
`WRENCH_MODEL_PREFILL_MAX_BUDGET`. Ordinary reads remain at 64K. The policy is
deterministic and its receipt records the marker, base budget, selected budget,
hard maximum, and raw character pressure. Setting
`WRENCH_DYNAMIC_PREFILL_ADAPTIVE=0` disables the promotion. This changes the
working-context size only; it does not turn the staged path into dense native
attention over the omitted raw tokens.

## Bounded test-time-compute schedule

The Wrench schedule is intentionally asymmetric:

| Profile | Use | Model passes | Local gates |
| --- | --- | ---: | --- |
| `fast` | routine reads and status | 1 | schema, authority, evidence, consistency |
| `guarded` | context pressure, search, health | 2 | fast gates plus AST and diff checks |
| `deep` | patch drafts, review, debugging, multi-step work | 4 | guarded gates plus blind critic and final gate |

The clean path exits immediately after the deterministic gates. The deep path
has a hard pass budget and must not silently add retries. A future model-backed
blind critic receives the user requirement and candidate only, not generator
scratchpad, so it cannot simply agree with the first pass. If two candidate
steps are ever expanded for a complex bounded task, a mutual verifier must
agree on the exact state before that step enters the trunk. Disagreement prunes
the branch or triggers one explicitly recorded re-derivation.
