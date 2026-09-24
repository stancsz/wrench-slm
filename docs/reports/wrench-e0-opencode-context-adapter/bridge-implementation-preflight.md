# OpenCode bounded bridge implementation preflight

Task: assess and implement a project-local OpenCode v2.0.15 context plugin
connected to Wrench's existing Python preparation seam through a fixed,
bounded bridge.

Owner: `opencode_bridge_implementation_supervisor`
Date: 2026-09-24 (America/Edmonton)
Starting revision: `f2987036c90e5c6eb3603972bd82017cd179b4f2`
Status: implementation stopped at unresolved Wrench-owned configuration and
preparation-contract dependencies; no bridge or plugin code was added.

## Product path inspected

The intended outcome is a reversible OpenCode context-hook integration that
uses the deterministic E0 preparation engine and applies one compiler-bound
context insertion. The repository already has two useful offline seams:

- `src/wrench_harness/opencode_context.py::prepare_opencode_e0_context`
  wraps the E0 pipeline and joins a prepared result to a validated session
  root.
- `src/wrench_harness/opencode_prepared_context.py::materialize_opencode_prepared_context`
  validates an event and a READY join, then returns a copy with exactly the
  digest- and position-bound prepared message inserted.

These functions are Python APIs, not a subprocess protocol or runtime plugin.
The context callback's successful response can be materialized safely once a
valid preparation join exists, but the current path does not construct that
join from a bounded JSON request.

## Blocking contract gaps

`prepare_opencode_e0_context` needs an existing `SourceSnapshot`, selected
source paths, an `ArtifactStore`, query and budgets, a `NamespaceRegistry`,
schema lookups, base messages and insertion position, plus callable serializer
and tokenizer functions with declared IDs. The bridge cannot safely accept
these authorities or callback identities from the hook payload. There is no
project-local Wrench configuration schema that provides the needed values.

The current resolver gets its configured root from the OpenCode session
record's `location.directory`. The assigned bridge boundary requires both the
root and inventory policy to come from explicit Wrench-owned configuration,
never from the callback, process working directory, or plugin location. A
concrete rule is still needed to bind that configured root to an OpenCode
session and map inventory scopes to the finite source paths passed to E0.

The `ArtifactStore` uses process-local locking and documents that multiple
processes must not use the same store root concurrently. Spawning Python for
each context callback therefore does not yet have a qualified store lifecycle,
pin lifetime, or concurrency policy.

Finally, the hook event is upstream of provider lowering. The currently
configured OpenCode route is an OpenAI-compatible Chat Completions alias, but
the serving model/revision, final serializer behavior, and matching tokenizer
are not pinned. Existing fixture callbacks establish neither exact request
serialization nor tokenizer parity. An implementation that emits READY here
would overstate the prompt-budget evidence.

These are real dependencies of a functional source bridge. A JSON wrapper that
cannot reach `prepare_opencode_e0_context`, or that always rejects due to
missing configuration, would be disconnected protocol scaffolding and would
not advance the real user path. No such package was added.

## OpenCode hook evidence

Independent source review against tagged OpenCode `v2.0.15` found that a
project-local plugin may register the `context` hook through
`ctx.session.hook("context", ...)`. The context type includes session ID,
model, system parts, messages, generation options, agent, and the assembled
tools map. A rejected callback propagates through the awaited hook chain, and
the primary runner awaits context preparation before the model attempt. This
supports a source-level rejection contract for that attempt. There is no typed
veto result, and this does not prove runtime settlement, user-visible errors,
retry behavior, or durable dispatch denial.

The audit corrected a stale statement in the assigned OpenCode goal: tagged
context-hook event construction does not add `kind`; it passes the request
draft plus `agent` and `tools`. `kind` is available on later model-request and
transport hooks. The goal now records that distinction.

## Independent audits

- `python_bridge_path_audit`, nonce `E0-PY-20260925-6A17`: read-only audit of
  the Python API, root/inventory policy, and artifact-store boundary. It
  confirmed that the required values are not currently exposed through a safe
  JSON entry point and that per-hook subprocesses have an unresolved store
  lifecycle.
- `opencode_callback_contract_audit`, nonce `E0-OC-20260925-3D42`: read-only
  audit of the tagged OpenCode v2.0.15 plugin API and source callback path. It
  confirmed callback rejection behavior at source level and identified the
  stale `kind` claim. Neither audit ran OpenCode or contacted any endpoint.

A follow-up public-source check (nonce
`E0-M3-TOKENIZER-ROUTING-20260924-72BF`) confirmed that the configured
OpenRouter alias does not identify an immutable deployed tokenizer or model.
The official MiniMax Hugging Face repository exposes `chat_template.jinja`,
`added_tokens.json`, `config.json`, and `merges.txt` at revision
`f0e1c1e04d40177e4673a22097036854f536e9c0`. That pins upstream files only; it
does not show which artifacts an OpenRouter provider deploys. OpenRouter's
official routing documentation describes default load balancing and fallback
across providers. Its live catalog and endpoint metadata do not bind this
configured alias to a provider, model-weight revision, tokenizer bytes, or
template hash. No API or endpoint was called and no model/tokenizer file was
downloaded. This strengthens the finding that a provider-exact READY prompt
gate cannot be established from public source metadata alone.

Sources: [pinned MiniMax repository tree](https://huggingface.co/MiniMaxAI/MiniMax-M3/tree/f0e1c1e04d40177e4673a22097036854f536e9c0), [pinned chat template](https://huggingface.co/MiniMaxAI/MiniMax-M3/blob/f0e1c1e04d40177e4673a22097036854f536e9c0/chat_template.jinja), [OpenRouter MiniMax-M3 catalog](https://openrouter.ai/minimax/minimax-m3), [provider routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection), and [endpoint API reference](https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model).

Primary sources: [tagged Promise session API](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts), [hook adapter](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/adapter.ts), [hook trigger](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/hooks.ts), [request construction](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts), [primary LLM runner](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts), and the [official plugin guide](https://opencode.ai/v2/docs/build/plugins).

## Files, verification, and limits

Changed files:

- `docs/goal/wrench-e0-opencode-context-adapter/GOAL.md`: corrected the
  context-hook `kind` statement and recorded this feasibility outcome.
- `docs/evals/wrench-e0-opencode-context-adapter/bridge-implementation-preflight.md`:
  independent review and public-source evidence update.
- This report.

No plugin, bridge, configuration, test, or client files were changed. No
OpenCode process or plugin was invoked or installed; no local endpoint,
provider, model, prompt, or client session was used. No Python tests or build
were run. The storage checker admitted 65,536 bytes for this report and goal
update, then 32,768 bytes for the public-source evidence update; both
reservations were released after the files were accounted for. C: had
182,467,321,856 bytes free. Host inspection
showed about 13.4 GiB free of 31.9 GiB RAM and 15,222 MiB free of 16,311 MiB
VRAM. The reservation must be released after the final storage check.

Current checkout differs from the starting revision only by this report and
the assigned goal update. The pre-existing untracked `uv.lock` was left alone.
The independent evaluation is recorded at
`docs/evals/wrench-e0-opencode-context-adapter/bridge-implementation-preflight.md`.

## Next step

Define a Wrench-owned project binding/configuration that explicitly supplies
the repository root, inventory scopes/exclusions, finite source-selection
policy, store path/ownership, and request budgets. Decide whether the OpenCode
session root must exactly match that binding. Separately pin and measure a
serializer/tokenizer contract for the selected OpenCode route or keep the
prompt gate unavailable and define what useful context preparation may do
without claiming a token gate. Then design a single-owner persistent bridge
lifecycle, implement a strict versioned protocol and project-local plugin,
and arrange a process-confined runtime rejection test before any client use.

This preflight does not close E0 or authorize runtime/client/provider work.
