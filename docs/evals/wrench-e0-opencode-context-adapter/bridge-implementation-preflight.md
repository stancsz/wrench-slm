# OpenCode bounded bridge implementation preflight evaluation

Reviewer: `/root/opencode_bridge_implementation_supervisor/opencode_callback_contract_audit`  
Nonce: `E0-BRIDGE-REVIEW-20260924-A14C`  
Evaluated revision: `f2987036c90e5c6eb3603972bd82017cd179b4f2`  
Working tree: assigned goal file modified; preflight report and pre-existing
`uv.lock` untracked. Review was read-only except for this evaluation file.

## Result

**PASS for the preflight decision to stop before adding a protocol-only bridge.**
The proposed fixed JSON protocol would be fail-closed if it rejected every
unconfigured request, but it would not connect OpenCode to useful E0
preparation. The existing Python functions accept already-constructed runtime
objects and caller-supplied authorities; they do not expose a JSON operation
that creates a bound snapshot, selects allowed paths, owns an artifact store,
and returns compiler output. An always-rejecting package would be inert
scaffolding, not a connected context runtime.

## Evidence and findings

- `prepare_opencode_e0_context` requires a `SourceSnapshot`, finite paths,
  `ArtifactStore`, budgets, query, namespace registry, schema lookups, base
  messages, insertion position, serializer and tokenizer callables, and their
  declared IDs. It resolves the root from the supplied OpenCode session
  record's `location.directory`; it has no Wrench project configuration or
  session lookup. `materialize_opencode_prepared_context` accepts that
  in-memory join and a supplied hook event, then inserts only the gate-bound
  compiler message. It cannot produce the join or authenticate that OpenCode
  invoked it. Sources: `src/wrench_harness/opencode_context.py` and
  `src/wrench_harness/opencode_prepared_context.py`.
- The context event contains no project root. OpenCode's `ctx.location` is the
  plugin load location, not every session's project location. A future adapter
  can retrieve the session by ID using `ctx.session.get`, but must compare its
  location to an explicit Wrench-owned project/root binding and apply an
  explicit finite inventory-to-source-path policy. The event and session
  response alone do not provide that Wrench policy.
- `ArtifactStore` documents one instance per root and process-local
  concurrency protection only. It holds request pins in instance memory.
  Creating an instance in a subprocess for each hook does not establish
  single ownership, safe same-root concurrency, pin lifetime, or cleanup
  through the downstream request lifecycle. A serialized persistent owner or
  a separately justified per-request store design is needed before claiming
  the existing lifecycle is connected.
- `compile_prompt` accepts caller-provided serializer/tokenizer callbacks;
  receipts bind declared IDs but do not authenticate callback identity. The
  configured Chat Completions route's immutable serving model and tokenizer
  remain unknown, and the context hook precedes OpenCode request lowering.
  Consequently a bridge cannot validly label a provider-exact prompt gate
  READY from the currently available evidence. The existing materializer
  specifically requires a READY gate. A separate context-only capability
  would need to expose a distinct non-gated status and avoid presenting the
  approximate budget as final-request parity.
- Tagged OpenCode v2.0.15 defines the Promise callback as
  `(event) => Promise<void> | void`, with no typed deny result. The core awaits
  context callbacks in order, and the primary runner awaits preparation before
  the model attempt. Rejection therefore blocks that primary attempt at the
  pinned source level only. The context payload is constructed from the draft,
  `agent`, and `tools`; it has no `kind`. It is upstream of route hooks and
  provider serialization. These facts support a future source plugin's
  fail-on-error behavior, but do not resolve the missing engine/configuration
  contract or establish runtime settlement and dispatch denial.

## Recommendation

Do not add a deny-by-default protocol package by itself. First define the
Wrench-owned project binding, root/session equality rule, inventory scopes and
finite source selection, store root ownership and request/pin lifecycle, and
the explicit status returned when exact serializer/tokenizer gating is
unavailable. Then implement and review the JSON entry point against those
contracts so a valid request reaches the existing preparation and materializer
seams. A later TypeScript project plugin can register `ctx.session.hook(
"context", ...)`, call the fixed bridge, preserve the supplied tools and other
fields, apply only verified compiler output, and throw on every failure. Its
runtime test remains separately gated on process-level egress confinement and
authorization.

Primary OpenCode sources: [Promise context hook types](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts),
[Promise hook adapter](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/adapter.ts),
[ordered hook trigger](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/hooks.ts),
[context request construction](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts),
[primary runner](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts),
and the [official plugin guide](https://opencode.ai/v2/docs/build/plugins).

## Limitations

This was repository and pinned-source review only. No tests/build, OpenCode
client, plugin, endpoint, provider, prompt, model, or runtime process was
invoked. No code or other document was edited.
