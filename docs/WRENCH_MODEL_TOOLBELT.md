# Wrench model-side toolbelt

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

This hybrid path is the release target when it meets the complete workflow
gates: retrieval quality, safety, final success, frontier-token savings, and
end-to-end latency. A separate native-direct runtime may still ingest the full
sequence for comparison and research. It is only needed to claim dense native
4M attention, and it should not hold the hybrid production-value path hostage.

The dynamic prefill uses cheap regex anchors first, then AST or lexical symbol
extraction for code. It preferentially retains paths, symbols, tests, errors,
URLs, identifiers, and the newest unresolved observations. A lookup expansion
is an explicit second action, not accidental attention pollution.

The default effective working context is 64K, with roughly 48K for recent hot
context and 16K for mechanical lookup cards. The 100 ms target is a hot-path
target for cached 4M-to-64K selection.
Cold indexing is incremental work performed as context arrives. It is reported
separately from request latency and never hidden inside a model benchmark.

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
