# E0 OpenCode V2 context adapter contract

Status: provider-free Wrench seams implemented; isolated OpenCode v2.0.15 CLI installed and configured for localhost, but no client prompt/task/request or Wrench hook integration has run
Job: `W2-E0-OPENCODE-SESSION-ROOT-20260924`
Started: 2026-09-24 (America/Edmonton)

## Product outcome

Define a small, reviewable first-client boundary for Wrench's deterministic
Layer 1 context runtime. OpenCode V2 is the selected first integration target.
The original implementation increment pinned a candidate OpenCode release
and implemented provider-free validation from a hook session ID and returned
session record to an existing source root. It added no OpenCode plugin,
dependency, provider call, dispatch gate, or production route. A later
owner-requested local CLI install/configuration is separately recorded below;
it does not change the boundaries of that source increment.

## Contract

- OpenCode documents two distinct hook boundaries. The `prompt` hook runs at
  user-prompt admission, before attachments, skill resolution, and durable
  inbox admission. The guide says a failed or interrupted preparation does
  not admit that prompt, but the API still has no typed rejection result;
  runtime validation must establish and test the supported failure signal.
  This hook runs once per admission, not before each model
  call, and does not expose the resolved model or assembled tool map.
- The `context` hook runs immediately before agent-loop model dispatch,
  including tool-driven continuations, and exposes the assembled request
  fields below. Its documented API has no typed veto result and the docs do
  not specify callback failure behavior. Therefore the prompt hook's
  admission behavior cannot be generalized to the context hook or used to
  claim the complete request is blocked on preparation failure.
- A source trace against tagged OpenCode `v2.0.15` connects the Promise hook
  adapter, uncaught context-hook trigger, awaited request preparation, and
  later `llm.stream` call. It supports that a thrown/rejected context hook
  callback prevents `llm.stream` for that attempt. This is source evidence,
  not a typed veto or runtime proof; session settlement, user-visible errors,
  scheduler retries, and the installed client's behavior remain unknown.
- The public Promise context-hook type has no typed `kind` discriminator. In
  the tagged implementation, request preparation currently adds an internal
  `kind` field to the event before the Promise adapter forwards it. That
  undocumented extra may be visible at runtime, but is not a supported hook
  contract and must not be required for correct behavior.
- The context hook receives the semantic request before provider protocol
  lowering. The pinned `OpenAIResponses.fromRequest` function lowers an
  `LLMRequest` to a provider request body; it is not the complete final wire
  serializer. Before and after that step, request preparation resolves model
  defaults and capabilities, reconciles executable tools, transforms media,
  options, and headers, and selects a route and transport. HTTP overlays/hooks
  can alter the HTTP request, while WebSocket traffic follows separate
  experimental hooks and framing. The seven-field hook projection alone
  cannot reproduce or attest to the final outbound request. Neither the
  context hook nor the later transport hooks supply a provider-agnostic
  tokenizer or documented dispatch veto. Automatic compaction starts from the
  latest response's provider input usage when available, then adds output and
  newer content; without provider usage, OpenCode estimates text, media,
  instructions, and tools locally. It can retry a recognized overflow once
  when automatic compaction is enabled,
  but its heuristic estimate cannot prevent every provider-specific overflow.
  This is not an exact E0 prompt gate.
- The release candidate is OpenCode `v2.0.15`, tag commit `6f3639d`, with the
  matching `@opencode/plugin` package at `2.0.15`. Source and API are pinned
  for review. The CLI was installed separately; no Wrench hook was registered
  or run.
- `resolve_opencode_session_root` accepts the event `sessionID` and returned
  session record as data, requires both IDs to satisfy the pinned `ses`
  prefix and the record `id` to match, accepts only an absolute usable
  `location.directory`, rejects parent path components, and rejects nonempty
  or null `subpath` values. It never falls back to a cached path, plugin
  location, process directory, or guessed worktree.
- The validated root remains a configured lexical path and is passed to the
  snapshot-v3 API. The snapshot hash binds both that configured-root identity
  and a root-object identity captured through the retained read handle;
  retrieval compares the identity, and snapshot creation requires it to stay
  consistent across selected files. Source selection remains an explicit
  finite path list. No adapter-driven recursive discovery is introduced.
- Windows source reads walk the resolved root from its volume/share anchor
  using component-relative directory handles, reject reparse components, and
  retain handles through each exact read. This closes the reviewed ancestor
  reparse-point replacement gap. Root IDs may be reused, the snapshot is not
  an atomic multi-file view, and UNC/network filesystem identity behavior is
  unqualified. The boundary must not be described as complete for those cases.
- At the context hook boundary, account for the complete semantic projection
  visible to that hook: session ID, system instructions, messages, agent,
  model identity, the full supplied tools map, and options. Preserve the tools
  map unchanged. Do not treat tool descriptions or schemas as authorization.
- Context-hook edits affect the outgoing model call. They do not rewrite
  persisted conversation history or establish an alternate no-model dispatch
  path. The public API provides no typed veto result or callback failure
  guarantee. The source-level rejected-callback observation above applies to
  `llm.stream` for one attempt only; it does not prove a durable dispatch gate,
  request settlement, or user-visible failure behavior.
- No exact final provider token budget or wire-equivalence claim is allowed
  until an OpenCode release, final request serializer, provider/model identity,
  and tokenizer are pinned and measured at the corresponding boundary. Any
  hosted token-count endpoint is a provider-specific external call and does
  not itself block a later model dispatch.
- Authored fixtures may verify mechanics only. The proposed future matched-task
  corpus is per-task opt-in OpenCode work on participant-authorized local
  repository snapshots, initially code localization and failing-test/log
  triage. This is a protocol choice, not collection authority: current
  authorization covers only Wrench-authored synthetic fixtures. Before real
  capture, the owner must approve consent, permitted use, source access,
  retention, withdrawal, and deletion. For later E4 work, freeze task-specific
  acceptance checks before replay and pair them with independent review blinded
  to comparison arm; treat missing, flaky, or ambiguous checks as unknown.
  This corpus/oracle choice does not authorize collection or establish E4
  utility.

## Acceptance

- Official OpenCode V2 plugin and API references are recorded and checked on
  2026-09-24; their mutable documentation is not a release pin.
- Session lookup, location/subpath handling, visible hook fields, supplied tool
  preservation, hook effect, and unavailable dispatch-veto behavior are
  explicitly bounded above.
- Prompt-admission and model-context hooks are distinguished; the documented
  prompt failure behavior is not claimed as a final-request veto.
- The release and matching plugin package are pinned to `v2.0.15`; the local
  CLI is also installed at `v2.0.15`. Runtime hook behavior, callback failure
  semantics, provider serializer, tokenizer, and dispatch authority remain
  unresolved.
- Offline validation rejects mismatched IDs, missing/invalid roots, ambiguous
  subpaths, and unusable directories before snapshot creation; isolated resolver
  fixtures cover these cases and the pinned session-ID prefix.
- `prepare_opencode_e0_context` injects the resolved root into the existing
  preparation facade and carries session/root/snapshot identity with its result;
  fixture coverage includes invalid-session short-circuiting and the real
  preparation path plus a mismatched-root case that expects no prompt. The
  focused OpenCode and pipeline fixtures pass on the recorded Windows Python
  3.11 environment.
- `check_opencode_preparation_admission` returns READY only for a matching
  session join with a READY preparation, inert `none` route, nonempty prompt,
  READY prompt gate, canonical INCOMPLETE preparation receipt with the expected
  snapshot/context identities and only the outcome field missing, and no
  retrieval misses. Its typed failure cases are fixture-covered. This is an
  internal classification only: callers can ignore it, and it is not connected
  to or capable of vetoing OpenCode dispatch.
- `finalize_opencode_preparation_outcome` binds the caller-supplied post-run
  session ID to the OpenCode preparation join before delegating to the generic
  receipt finalizer. Matching, null, and mismatched session fixtures pass.
  This is structural equality over caller-supplied values; it does not
  authenticate the session or observe the client lifecycle.
- `project_opencode_context_hook` copies all seven semantic context-hook fields
  under a shared 1 MiB JSON bound, preserves arrays and insertion order in its
  payload representation, and hashes canonical JSON with the schema and
  OpenCode `v2.0.15` source version. It rejects extra/missing fields, malformed
  model variants (including explicit null), cycles, non-JSON values, and
  oversized structures. Its caller must provide a stable event object; same-
  length or nested concurrent mutation cannot be detected atomically. This
  projection is not connected to prompt preparation, serialization, or
  dispatch.
- The parent E0 goal and goal index point to this slice and retain all broader
  E0/E4 gates as open.
- Independent read-only review and `git diff --check` complete; commit contains
  only this slice and owned index/goal updates.

## Limits and evidence

The resolver and admission classifier are Wrench-side data checks, not a
registered OpenCode hook. They do not establish exact provider payload
reconstruction, model dispatch control, tokenizer parity, tool authority,
recovery qualification, complete lifecycle accounting, or production fitness.
The isolated local CLI is installed and configured as recorded in the
[installation report](../../reports/wrench-e0-opencode-context-adapter/local-client-install.md),
but no Wrench plugin/hook integration or client prompt/task/request has run.

Implementation details and review evidence are in the
[session-root resolution report](../../reports/wrench-e0-opencode-context-adapter/session-root-resolution.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/review.md),
plus the [local admission-check report](../../reports/wrench-e0-opencode-context-adapter/admission-check.md)
and [session-bound outcome report](../../reports/wrench-e0-opencode-context-adapter/session-outcome-binding.md).
Projection behavior and its bounded evidence are recorded in the
[context-hook projection report](../../reports/wrench-e0-opencode-context-adapter/hook-projection.md).
The pinned request-lowering trace and selected research pins are in the
[request-lowering source audit](../../reports/wrench-e0-opencode-context-adapter/request-lowering-source-audit.md).

References: official [OpenCode v2.0.15 release](https://github.com/anomalyco/opencode/releases/tag/v2.0.15),
[tagged plugin package manifest](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/package.json),
[tagged context hook type](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/session.ts),
[tagged hook adapter](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/adapter.ts),
[tagged hook trigger](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/hooks.ts),
[tagged model request](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts),
[tagged model runner](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts),
[tagged session schema](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/schema/src/session.ts),
[tagged location schema](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/schema/src/location.ts),
official [OpenCode V2 plugin guide](https://opencode.ai/v2/docs/build/plugins),
[OpenCode V2 API](https://opencode.ai/v2/docs/api), and
[V1-to-V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1).
The [V2 compaction guide](https://opencode.ai/v2/docs/compaction) describes
its preflight size estimates and explicitly warns heuristic estimates cannot
prevent every provider-specific overflow.

## Next action

Implementing the actual OpenCode plugin remains gated on an owner-approved
integration design and pinned runtime validation. Exact prompt gating remains
gated on the complete provider/model request path, token counting for that
request, and a documented or verified fail-closed dispatch contract. The future
matched-task corpus and outcome-oracle protocol are selected below, but owner
approval and participant consent remain prerequisites before any real capture
or E4 utility measurement.

The selected E0 characterization target is OpenCode `v2.0.15`, the OpenAI
Responses route, and model `gpt-4.1-2025-04-14`. Pin the candidate provider-body
lowering to the tagged `@opencode/ai@2.0.15` `OpenAIResponses.fromRequest`
path, and separately pin the route, endpoint, transport, and any downstream
request hooks before claiming final-request equivalence. Pin the local text
tokenizer to `tiktoken==0.9.0`, explicitly loading `o200k_base`
(encoding-file SHA-256
`446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d`). These
are source/research pins only; neither dependency was installed or run. The
local tokenizer is not an exact count of a Responses request with tools,
images, files, or provider-specific structure. Exact input counting requires
the Responses input-token endpoint with the final equivalent request body;
that would send request data to OpenAI and requires separate provider-data and
spending approval before any call. A count of a submitted body would not itself
establish that it is OpenCode's actual final request or that a later model call
is blocked. The endpoint also does not establish that the hook projection
matches OpenCode's later request transformations. Therefore the E0 prompt gate
remains open. The pinned tokenizer's v0.9.0 model map also does not establish
the selected model-to-encoding association; explicit `o200k_base` is a
reproducible research pin only.

For corpus mechanics now, use only a small Wrench-authored synthetic
matched-task fixture set with deterministic task-specific checks and independent
blinded verification. This can check harness behavior but cannot establish E4
customer utility. The future source and oracle protocol are designated above;
real utility work still needs owner-approved consent, use, access, retention,
withdrawal, and deletion processes before collection.

## Follow-up: isolated local CLI setup and mock runtime preflight

At the owner's request, OpenCode CLI `v2.0.15` and its wrapper/config were
installed in the isolated directory recorded in the
[local CLI report](../../reports/wrench-e0-opencode-context-adapter/local-client-install.md).
The only gateway request was `GET
http://127.0.0.1:4000/v1/models`, which returned HTTP 200 and advertised
`current`. No OpenCode prompt, task, chat, inference, or external provider
request was made. The current config selects the generic OpenAI-compatible
Chat Completions route and `wrench-local/current`. This differs from the E0
Responses route and `gpt-4.1-2025-04-14` research pin; select and revalidate the
route/model identity before characterization.

The [synthetic mock runtime preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
describes one success-only request using an isolated per-run config for
`wrench-local/current` at `127.0.0.1:43117`. It is a plan, grants no run
authority, and is **not ready to launch** until a process-level egress
confinement mechanism is selected and validated. The
`SessionHooks.context` Promise callback has no typed admission/veto result.
This transport-only plan does not register or exercise a Wrench hook. Failure
injection and any live hook integration require separate owner authorization.
The [preflight evaluation](../../evals/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
records API-contract and containment reviews, point-in-time resource evidence,
the egress-confinement precondition, and the exact owner approval needed.

The follow-on `prepare_opencode_e0_context` seam resolves the supplied session
record and carries its `SourceRootBinding` into `prepare_e0_context`. To keep
the selected directory continuous across intervening work, a future adapter
should use the resolved token for both snapshot creation and preparation:
`resolved = resolve_opencode_session_root(...)`, then
`create_snapshot(resolved.binding, paths)`, then
`prepare_opencode_e0_context(..., resolved_session_root=resolved)`. Preparation
re-resolves the session record and rejects a changed binding before composing
context; exact retrieval also checks the captured root identity. This detects
same-path directory replacement locally, but does not authenticate the session
record or provide an atomic multi-file snapshot. The helper performs no session
lookup, provider request, or dispatch. A future OpenCode adapter must explicitly
pass the `session.get` response's `data` record; the resolver does not accept
the outer response wrapper. Optional `workspaceID` is not part of the current
join. `OpenCodeSessionRoot.configured_root` remains a readable property, while
the returned dataclass field/constructor shape now exposes `binding`. The
remaining root identity and UNC/network limitations above are recorded in the
[session-root resolution report](../../reports/wrench-e0-opencode-context-adapter/session-root-resolution.md)
and [snapshot root-identity goal](../wrench-e0-snapshot-root-identity/GOAL.md).

## Follow-up: offline context-hook transition contract

Status: bounded caller-supplied projection comparison implemented; live hook
integration remains uninstalled and unrun.

The transition validator accepts only two self-consistent, pinned-version
projections whose protected top-level fields are unchanged and whose message
list adds exactly the expected prepared message at the declared position. Its
bounded receipt contains projection digests and identifiers, not message
content. Nested OpenCode message and option schemas are not fully validated.
This records intended mutation mechanics only: it does not prove OpenCode used
the projections, prevent dispatch, validate the complete post-hook request, or
establish request/tokenizer parity. See the [transition contract report](../../reports/wrench-e0-opencode-context-adapter/hook-transition-contract.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/hook-transition-contract.md).

The local source audit establishes the `ses` session-ID prefix and matching
record ID but does not record the complete suffix grammar. The resolver's
current prefix and shape checks are therefore not evidence of full pinned
schema conformance. The [session-ID grammar audit](../../reports/wrench-e0-opencode-context-adapter/session-id-grammar-audit.md)
records the missing local source evidence; no suffix pattern is inferred.

## Follow-up: bind transition to E0 preparation identity

The offline transition validator now requires the inserted message digest and
position recorded by a READY E0 prompt gate. A content-free wrapper receipt
binds the preparation aggregate digest to the before/after projection
digests. The partial lifecycle trace requires this receipt alongside completed
route-preparation evidence and checks its session and after-projection
identity. See the [prepared transition report](../../reports/wrench-e0-context-pipeline/prepared-context-transition.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/prepared-context-transition.md).

This is a structural check over caller-provided objects. It does not prove
OpenCode executed the transition, validate the full nested client message
schema, prevent dispatch, or establish final request/tokenizer parity. Runtime
integration and overall E0 acceptance remain open.

## Follow-up: pinned text-message subset

The OpenCode preparation seam now serializes its inserted context and deferred
schema text as typed user text parts. The bounded hook projection validates
system text parts, message roles, content arrays, and the shape of Wrench's
single inserted text message. It does not validate the complete OpenCode
content-part union or the installed runtime. See the [message-shape report](../../reports/wrench-e0-context-pipeline/opencode-message-shape.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/opencode-message-shape.md).
