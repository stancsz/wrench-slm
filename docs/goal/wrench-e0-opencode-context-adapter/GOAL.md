# E0 OpenCode V2 context adapter contract

Status: provider-free Wrench seams, a synthetic offline loopback request/lease boundary, and a strict Wrench-owned project enrollment registry are implemented and independently reviewed; isolated OpenCode v2.0.15 CLI is configured, but no Wrench hook integration or client prompt/task request has run
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
- The public Promise context-hook type has no `kind` field, and the tagged
  implementation constructs the context event from the request draft plus
  `agent` and `tools`. The `kind` discriminator belongs to the later
  `model.request` and transport hooks. Context-hook code must not inspect or
  require `kind`.
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
The install setup check used `GET
http://127.0.0.1:4000/v1/models`, which returned HTTP 200 and advertised
`current`. Later read-only model-list checks on 2026-09-24 also showed
`owned_by: openai` for that alias and several other model aliases in the list.
Safe inspection of the mounted gateway config showed `current` maps to
`openai/current`, while active routing state is `mode: force`,
`active_model: openrouter`, policy version 4; that alias maps to
`openrouter/minimax/minimax-m3`. Under that state, the mounted routing callback
would rewrite requests to the forced alias. The running router supports an
environment override for the state-file path, which was not inspected. This
is configured-route evidence, not an observed generation request, but it means
the local port does not establish local inference or no-spend behavior. No
OpenCode prompt, task, chat,
inference, or external provider request was made. The OpenCode config selects
the generic OpenAI-compatible Chat Completions route and `wrench-local/current`.
This differs from the E0 Responses route and `gpt-4.1-2025-04-14` research
pin. The immutable MiniMax model revision and matching tokenizer remain
unresolved; the exact prompt-token gate cannot claim runtime parity.

The [synthetic mock runtime preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
describes one success-only request using an isolated per-run config for
`wrench-local/current` at `127.0.0.1:43117`. It is a plan, grants no run
authority, and is **not ready to launch** until a process-level egress
confinement mechanism is selected and validated. The
`SessionHooks.context` Promise callback has no typed admission/veto result.
The tagged v2.0.15 source trace now shows that a rejected context callback
prevents a primary request attempt from reaching the downstream step, but
auxiliary requests use separate hook kinds and installed-runtime error,
settlement, and retry behavior remain unverified. This transport-only plan
does not register or exercise a Wrench hook. Failure injection and any live
hook integration require separate owner authorization. See the [route and
hook-failure source review](../../evals/wrench-e0-opencode-context-adapter/runtime-route-and-veto-source-review.md)
and [updated request-lowering source audit](../../reports/wrench-e0-opencode-context-adapter/request-lowering-source-audit.md).
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

## Follow-up: isolated OpenCode localhost setup

The isolated OpenCode v2.0.15 install is configured for
`wrench-local/current` at `http://127.0.0.1:4000/v1` through the OpenAI-
compatible Chat Completions provider, with no plugins. The client-side setup
was verified without contacting port 4000 or running a prompt. The mounted
gateway route is currently configured to force requests to OpenRouter's
`openrouter/minimax/minimax-m3`; no generation was made, and the tokenizer or
immutable serving revision remains unknown. See the
[localhost install follow-up report](../../reports/wrench-e0-opencode-context-adapter/localhost-install-followup.md).

## Follow-up: pinned text-message subset

The OpenCode preparation seam now serializes its inserted context and deferred
schema text as typed user text parts. The bounded hook projection validates
system text parts, message roles, content arrays, and the shape of Wrench's
single inserted text message. It does not validate the complete OpenCode
content-part union or the installed runtime. See the [message-shape report](../../reports/wrench-e0-context-pipeline/opencode-message-shape.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/opencode-message-shape.md).

## Follow-up: materialize compiler-bound context for the hook event

Status: provider-free materialization seam implemented and independently
reviewed; four focused modules passed 112 tests. The adapter accepts the
`OpenCodePreparationJoin` from `prepare_opencode_e0_context`, requires a
matching `event.sessionID` and READY local admission, and inserts the exact
compiler-produced context message once at the prompt-gate position. The
compiler carries that bounded canonical message as an ephemeral value through
`PromptGateResult` and `PreparationResult`; the adapter verifies its digest
against the gate, preserves the other six event fields and original message
order, and returns READY only with a verified content-free transition receipt.
The input event is unchanged. The bridge and returned event are omitted from
dataclass repr output and are not included in preparation or transition
receipts.

The independent static review found no materialization defect. It noted that a
caller still needs to pass the returned transition evidence through the
existing lifecycle-trace builder; no test yet joins the materialized adapter
output directly into that envelope. This source-level contract does not prove
runtime hook registration, callback invocation, dispatch veto, final provider
serialization/tokenizer parity, or full E0 acceptance. See the
[implementation report](../../reports/wrench-e0-opencode-context-adapter/prepared-context-adapter.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/prepared-context-adapter.md).

## Follow-up: join adapter output to the lifecycle trace

Status: integration fixture added and independently reviewed. The test sends a
synthetic event through the prepared-context materializer, projects the
original and returned event, and passes both projections with the same READY
preparation join and finalized outcome receipt to `build_partial_lifecycle_trace`.
It verifies the READY envelope transition receipt matches the adapter receipt
and binds the preparation, session, inserted-message digest, gate position,
and before/after projection digests. A different-session event is rejected
by the adapter and cannot produce a READY trace. The focused lifecycle module
passed 26 tests, and the independent static review passed. See the
[integration report](../../reports/wrench-e0-opencode-context-adapter/adapter-trace-join.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/adapter-trace-join.md).

This remains synthetic caller-supplied structural evidence. It does not prove
runtime hook execution, atomic capture, dispatch enforcement, provider or
tokenizer parity, complete lifecycle accounting, or overall E0 acceptance.

## Follow-up: v2.0.15 runtime config inspection boundary

The isolated wrapper's version-only command reports OpenCode v2.0.15, and the
corrected workspace config and preserved prior-shape backup match their
recorded hashes and parse as JSON. No resolved-config command was run: the
installed distribution has no inspectable command-handler source, and the
pinned docs do not establish whether that command can load/install the custom
provider package or perform external work. The configured endpoint and model
selection therefore remain unverified at runtime. No localhost or provider
request was intentionally issued; implicit traffic during the version-only
command was not monitored. See the
[config-load preflight report](../../reports/wrench-e0-opencode-context-adapter/config-load-preflight.md).

## Follow-up: reconcile the isolated v2.0.15 config schema

The isolated workspace config now follows the custom-provider field names in
the exact OpenCode `v2.0.15` release-tag docs: singular `provider`, `npm`,
`options.baseURL`, and `models.current.name`. The preceding config was retained
with its byte hash in a non-loader backup. Offline JSON parsing and a static
field allowlist passed; the OpenCode CLI was not run, so runtime loading is
unverified. No prompt or localhost request was made. See the
[schema reconciliation report](../../reports/wrench-e0-opencode-context-adapter/localhost-config-schema-reconciliation.md).

## Follow-up: runtime fail-closed boundary readiness

Independent source and E0 acceptance audits agree that the highest-value open
gate is runtime-enforced dispatch denial. The tagged context-hook path runs
before the primary request attempt, but has no typed veto and no documented
failure-settlement contract. Existing Python admission and transition receipts
remain caller-supplied and inert. The recommended next source slice is a
project-local OpenCode v2 plugin with a fixed, bounded bridge to the Python
preparation engine; it must reject on every bridge or preparation failure.
This still requires a separately authorized, process-confined runtime test
before any dispatch-denial or E0 acceptance claim. See the
[fail-closed boundary evaluation](../../evals/wrench-e0-opencode-context-adapter/runtime-fail-closed-boundary.md).

## Follow-up: next integration contract recommendation

Independent project-binding, store-lifecycle, route-parity, and utility-oracle
reviews recommend that any future integration use a Wrench-owned project
registry, finite explicitly enrolled source paths, one persistent store owner,
and a Wrench request boundary that owns the final request stream and source
lease lifetime. The boundary must bind each preparation lease to exactly one
lowered request; session identity alone cannot distinguish concurrent or
retried attempts. Missing, duplicate, stale, or ambiguous correlation must
fail closed. The pinned Promise API supports a candidate single-active-ticket
handoff from context to `model.request`, where a fresh nonce header can be
attached, then checked at `http.request`; the runner's outer retry loop
re-enters primary preparation, while transport retries may reuse the request.
This algorithm is not implemented or verified. A plugin response hook can observe
EOF/cancel for a returned response but cannot wrap the send or handle a
pre-response failure. The proxy remains the candidate owner for request and
stream cleanup. Any offline fixture must
exercise concurrent tickets, retries, timeout poisoning, and nonce reuse
before this handoff is accepted. Exact-token E0 remains closed while the
localhost route's immutable serving identity and matching tokenizer are
unknown. Any fixture/store job must reserve peak bytes under the 50 GB
aggregate limit, preserve at least 5 GB physical-volume headroom after
projected writes, and keep 10% RAM/VRAM free for client/runtime jobs.

The selected future matched-task source is prospective per-task opt-in work on
participant- and repository-authorized snapshots. E0 evidence selection and
E4 task completion require separate frozen oracles; the current synthetic
seed remains development regression only. No real task data is admitted.

The install request is complete at the static-configuration boundary:
OpenCode v2.0.15 is installed in the approved data root and its isolated
profile points to `http://127.0.0.1:4000/v1`. Runtime config loading and
effective route resolution remain unverified. Next, implement and review the
offline-only Wrench request boundary with synthetic data, leaving OpenCode
configuration unchanged. Any later config change or forwarding to port 4000
needs a separate explicit step. See the [next-contract recommendation](../../reports/wrench-e0-opencode-context-adapter/bridge-next-contract.md).

## Follow-up: bounded bridge implementation feasibility

The proposed project-local plugin and Python subprocess bridge were not
implemented in this source-only increment. Independent audits found that the
existing Python seam is not a JSON-callable preparation operation: it requires
an existing snapshot, explicit source paths, budgets, a namespace registry,
serializer/tokenizer callbacks and IDs, and an `ArtifactStore`.
`prepare_opencode_e0_context` derives its source root from the OpenCode session
record, while the bridge boundary requires the project root and inventory
policy to come from explicit Wrench-owned configuration. The per-root artifact
store uses process-local locking and disallows concurrent instances, so a
subprocess per hook is not a qualified lifecycle.

OpenCode `v2.0.15` provides a source-level rejection point: the plugin callback
may reject, and the primary runner awaits it before that model attempt. The API
has no typed veto result, and source tracing does not establish user-visible
settlement, retries, or runtime dispatch denial. Implementation can resume
when Wrench has a concrete configuration contract for the root/session binding,
scope-to-source policy, artifact-store ownership, and serializer/tokenizer
posture. No client, localhost endpoint, provider, model, or plugin was run for
this review. See the [bridge feasibility report](../../reports/wrench-e0-opencode-context-adapter/bridge-implementation-preflight.md)
and [independent evaluation](../../evals/wrench-e0-opencode-context-adapter/bridge-implementation-preflight.md).

## Follow-up: synthetic offline loopback request boundary

Status: implemented, focused tests pass, and independent read-only review
passed. The source increment adds a reusable request/lease boundary and a
fixture HTTP server bound only to `127.0.0.1` on an ephemeral port. It accepts
one nonce-correlated request on the fixed Chat Completions route, validates a
bounded text-only request with exactly one supported JSON content type, and
serves only immutable bounded fixture bytes. It has no upstream address,
forwarding path, or OpenCode plugin wiring. The active timeout is cooperative:
it marks cancellation and retains the lease until stream/request cleanup.

The focused command
`.venv\Scripts\python.exe -m unittest tests.test_opencode_request_boundary -v`
passed 17 tests. `git diff --check` passed. Independent review job
`W2-NS-OFFLINE-REQUEST-BOUNDARY-REVIEW3-20260924`, nonce `ORB-REV3-F97A`,
returned PASS on the frozen source, test, and report hashes. Implementation
job `W2-NS-OFFLINE-REQUEST-BOUNDARY-20260924` and correction jobs FIX1/FIX2
were integrated in commit `c102cf0`. The detailed
[offline request-boundary report](../../reports/wrench-e0-opencode-context-adapter/offline-request-boundary.md)
records the bounds, test paths, and limitations.

This evidence covers synthetic offline protocol and lease mechanics only. It
does not establish OpenCode plugin registration, runtime hook invocation,
dispatch denial, a request to `localhost:4000`, provider behavior, or tokenizer
parity. The E0 exact-token gate remains closed, and the broader E0/E4 goals
remain incomplete. No real-task data collection is authorized by this slice.

## Follow-up: Wrench-owned OpenCode project enrollment registry

The new `wrench.opencode-project-registry.v1` registry binds an opaque project
ID to one captured local root identity, a finite explicit relative-path set,
fixed inventory policy, hard source caps, and a store path derived below the
configured Wrench data root. Only the explicit enrollment API writes entries;
repository configuration and hook payloads cannot grant source access.
Resolution requires the event and returned session IDs to match, exactly one
enrolled root match, empty or absent `subpath`, and fresh root identity
validation. Reads and writes reject reparse/non-directory ancestors below the
bound data root and use bounded canonical registry data. Path checks remain
non-transactional; adversarial concurrent filesystem swaps are not qualified.

The focused synthetic suite passed **20/20** using CPython 3.11.16:
`-B -m unittest discover -s tests -p test_opencode_project_registry.py -v`.
Independent static review by `e0_goal_evidence` returned PASS against module
SHA-256 `A5ABAF11DFAA6549CD0F8BDB5A64DBBB3E024CA53EF9F65F4E86A53C44562D6A`
and test SHA-256
`D1267DAD4E5D419EDD6A9949DB3E424BFC2C2ED25CF5DD43A95EE6FCADB84272`.
The review confirmed the reparse-ancestor and root-alias regressions and the
redacted `EnrolledProject` representation. Windows symlink creation was
unavailable, so reparse behavior was simulated through `lstat` metadata.
Storage remained within the 50 GB limit and the 10% RAM/VRAM reserves held;
the [registry report](../../reports/wrench-e0-opencode-context-adapter/project-registry.md)
records exact resource readings and the test command.

This registry is a root/scope prerequisite, not a connected runtime. No client
or plugin was installed, launched, loaded or invoked by this job; the
previously installed isolated OpenCode v2.0.15 CLI remains installed. The job
made no request to localhost:4000 or a provider and read no real project
source. Persistent store ownership, hook integration, request-lifetime pinning,
dispatch denial, exact request/tokenizer parity and full E0 acceptance remain
open. The exact-token gate remains unavailable for the mutable configured
route.

## Follow-up: enrolled-project snapshot input seam

The Wrench-owned registry now feeds the existing snapshot primitive through
`prepare_opencode_project_snapshot`. The operation resolves the event and
record session through the enrolled registry, then requires a finite explicit
selection of enrolled relative paths. It rejects malformed containers,
overlong iterables, duplicate or unenrolled paths, exclusions, and invalid
path forms before calling snapshot creation. The snapshot remains in memory
and binds to the enrolled `SourceRootBinding`; no artifact store or persistence
is involved. Registry file and aggregate byte caps are passed into the secure
source readers. The exact-token gate is explicitly unavailable.

The focused synthetic suite passed **9 tests in 1.229 seconds** using CPython
3.11.16; the exact interpreter invocation and temporary-root settings are
recorded in the [enrolled-project snapshot report](../../reports/wrench-e0-opencode-context-adapter/enrolled-project-snapshot.md).
During the run, RAM free was 54.5–54.6% and VRAM free was at least
15,588/16,311 MiB. Storage remained `WITHIN_LIMIT` at 1,714,866,044 bytes
actual with 20,103,000 bytes reserved. `git diff --check` passed with the
existing LF-to-CRLF advisory for `snapshot.py`.

The broader existing `tests/test_snapshot.py` compatibility check was
attempted by the orchestrator but did not start: the interpreter does not have
`pytest` installed (`ModuleNotFoundError`). No tests from that suite ran, and
no dependencies were installed.

Independent static review by `e0_goal_evidence` returned PASS on the frozen
source and test hashes. The changed-source and reparse-point fixtures inject
the underlying read errors with mocks and verify fail-closed propagation;
they do not exercise those failures through native reads. Existing snapshot
tests provide separate POSIX symlink and changed-data retrieval coverage.
This is synthetic input-seam evidence only. It does not establish actual
project-source use, plugin registration, runtime hook invocation, dispatch
denial, provider behavior, request-lifetime handling, or tokenizer parity.
The broader E0/E4 goals remain incomplete and the exact-token gate remains
closed.

## Follow-up: snapshot-to-hook boundary review

The OpenCode context event supplies a session ID but no authoritative source
root. A future adapter must fetch the session record for that exact event ID
and use its data record with the enrolled snapshot API. It must not take root
authority from the plugin directory, process working directory, model text,
repo configuration, or hook-provided paths. The Python API binds the event to
the enrolled root and validates a finite selected-path subset before source
reads.

The review found no IPC entry point yet. A snapshot-only plugin would discard
the result rather than produce E0 context. An insertion-capable integration
still needs a Wrench-owned store/context-preparation contract and pinned
serializer and tokenizer identities; until those exist, the exact-token gate
remains unavailable. The review recommends delaying an insertion-capable
plugin and treating any earlier bridge as synthetic input characterization.
See the [snapshot-to-hook boundary report](../../reports/wrench-e0-opencode-context-adapter/snapshot-to-hook-boundary.md).
No client, plugin, endpoint, provider, or real source was touched.

## Follow-up: synthetic offline E0 composition

The new `e0_offline_request_composition` seam carries an enrolled-project
snapshot through deterministic structural candidate selection, exact retrieval
and ArtifactStore roundtrip, existing E0 preparation, prepared-context
materialization, final string-content message lowering, and the fixture request
lease. The lowered body contains the prepared context message exactly once.
The content-free receipt joins source/candidate, preparation, insertion, and
request-body digests. Synthetic serializer and tokenizer IDs are explicit; the
exact-token gate remains unavailable.

The focused synthetic module passed seven directly invoked test functions on
the existing CPython 3.11 environment. It covers deterministic composition,
non-ready and pre-lease failures, request rejection, exact-once release at EOF,
timer-start rollback, and active timeout retaining pins until writer cleanup.
Independent read-only review passed the composition, timer rollback, and final
EOF callback-count assertion. The concise
[offline composition report](../../reports/wrench-e0-opencode-context-adapter/offline-e0-composition.md)
records exact commands, hashes, and resource accounting.

This establishes only synthetic offline fixture composition. It does not
connect OpenCode or a plugin, forward a request, prove runtime route or
tokenizer parity, provide complete lifecycle accounting, or close E0/E4.
Exact-token acceptance remains closed.
