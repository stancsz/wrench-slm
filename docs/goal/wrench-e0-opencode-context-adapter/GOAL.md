# E0 OpenCode V2 context adapter contract

Status: provider-free session-to-preparation seam implemented; client integration remains uninstalled and unrun
Job: `W2-E0-OPENCODE-SESSION-ROOT-20260924`
Started: 2026-09-24 (America/Edmonton)

## Product outcome

Define a small, reviewable first-client boundary for Wrench's deterministic
Layer 1 context runtime. OpenCode V2 is the selected first integration target.
This increment pins a candidate OpenCode release and implements provider-free
validation from a hook session ID and returned session record to an existing
source root. It adds no OpenCode plugin, dependency, install, provider call,
dispatch gate, or production route.

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
- The context hook receives the semantic request before provider protocol
  lowering. OpenCode's later `http.request` hook can observe native HTTP
  requests; WebSocket traffic follows separate experimental hooks. Neither
  boundary supplies a provider-agnostic tokenizer or documented dispatch
  veto. Automatic compaction starts from the latest response's provider input
  usage when available, then adds output and newer content; without provider
  usage, OpenCode estimates text, media, instructions, and tools locally. It
  can retry a recognized overflow once when automatic compaction is enabled,
  but its heuristic estimate cannot prevent every provider-specific overflow.
  This is not an exact E0 prompt gate.
- The release candidate is OpenCode `v2.0.15`, tag commit `6f3639d`, with the
  matching `@opencode/plugin` package at `2.0.15`. This is a source/API pin for
  review, not evidence that the client or hook was installed or run.
- `resolve_opencode_session_root` accepts the event `sessionID` and returned
  session record as data, requires both IDs to satisfy the pinned `ses`
  prefix and the record `id` to match, accepts only an absolute usable
  `location.directory`, rejects parent path components, and rejects nonempty
  or null `subpath` values. It never falls back to a cached path, plugin
  location, process directory, or guessed worktree.
- The validated root remains a configured lexical path and can be passed to
  the existing snapshot API, which binds snapshot v2 to that configured root.
  Source selection remains an explicit finite path list.
- Source selection stays an explicit finite path list. Exact snapshot
  retrieval and existing deterministic preparation limits remain in force;
  no adapter-driven recursive discovery is introduced.
- At the context hook boundary, account for the complete semantic projection
  visible to that hook: session ID, system instructions, messages, agent,
  model identity, the full supplied tools map, and options. Preserve the tools
  map unchanged. Do not treat tool descriptions or schemas as authorization.
- Context-hook edits affect the outgoing model call. They do not rewrite
  persisted conversation history or establish an alternate no-model dispatch
  path. The documentation provides no typed veto result and does not specify
  callback failure behavior, so the adapter cannot claim to prevent dispatch
  when preparation fails. The context hook type has no `kind` field for
  distinguishing primary and auxiliary requests.
- No exact final provider token budget or wire-equivalence claim is allowed
  until an OpenCode release, final request serializer, provider/model identity,
  and tokenizer are pinned and measured at the corresponding boundary. Any
  hosted token-count endpoint is a provider-specific external call and does
  not itself block a later model dispatch.
- Authored fixtures may verify mechanics only. No consented matched-task
  corpus or outcome oracle is designated; E4 utility remains unevaluated.

## Acceptance

- Official OpenCode V2 plugin and API references are recorded and checked on
  2026-09-24; their mutable documentation is not a release pin.
- Session lookup, location/subpath handling, visible hook fields, supplied tool
  preservation, hook effect, and unavailable dispatch-veto behavior are
  explicitly bounded above.
- Prompt-admission and model-context hooks are distinguished; the documented
  prompt failure behavior is not claimed as a final-request veto.
- The release and matching plugin package are pinned to `v2.0.15`; runtime
  hook behavior, callback failure semantics, provider serializer, tokenizer,
  and dispatch authority remain unresolved.
- Offline validation rejects mismatched IDs, missing/invalid roots, ambiguous
  subpaths, and unusable directories before snapshot creation; isolated resolver
  fixtures cover these cases and the pinned session-ID prefix.
- `prepare_opencode_e0_context` injects the resolved root into the existing
  preparation facade and carries session/root/snapshot identity with its result;
  fixture coverage includes invalid-session short-circuiting and the real
  preparation path. The new fixtures have not been executed in this slice.
- The parent E0 goal and goal index point to this slice and retain all broader
  E0/E4 gates as open.
- Independent read-only review and `git diff --check` complete; commit contains
  only this slice and owned index/goal updates.

## Limits and evidence

The resolver is a Wrench-side data boundary, not a registered OpenCode hook.
It does not establish exact provider payload reconstruction, model dispatch
control, tokenizer parity, tool authority, recovery qualification, complete
lifecycle accounting, or production fitness. The integration has not been
installed or run.

Implementation details and review evidence are in the
[session-root resolution report](../../reports/wrench-e0-opencode-context-adapter/session-root-resolution.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/review.md).

References: official [OpenCode v2.0.15 release](https://github.com/anomalyco/opencode/releases/tag/v2.0.15),
[tagged plugin package manifest](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/package.json),
[tagged context hook type](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/session.ts),
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
gated on the provider/model serializer and tokenizer plus a documented or
verified fail-closed dispatch contract. Select a consented matched-task corpus
and outcome oracle before measuring E4 utility; the current pilot proposal is
not capture authorization.

For bounded offline characterization, the proposed provider target is
OpenCode's OpenAI Responses route with the fixed `gpt-4.1-2025-04-14` model
snapshot and OpenAI's Responses input-token count endpoint. This is a candidate,
not a production gate: it sends the prompt to OpenAI and requires separate
provider-data and spending approval before any call. It does not establish that
OpenCode's final request matches the count request or that a failure blocks
dispatch.

For corpus mechanics, use only a small Wrench-authored synthetic matched-task
fixture set with a deterministic task-specific test oracle and independent
blinded verification. This can check harness behavior but cannot establish E4
customer utility. Real utility work still needs an approved, consented source
and a reviewable retention/deletion process; none is designated here.

The follow-on `prepare_opencode_e0_context` seam resolves the supplied session
record and passes only its configured root to `prepare_e0_context`. It returns
a join object containing the session ID, root, snapshot hashes, and preparation
result. Exact retrieval still checks the snapshot's root identity. This helper
performs no session lookup, provider request, or dispatch. A future OpenCode
adapter must explicitly pass the `session.get` response's `data` record; the
resolver does not accept the outer response wrapper. Optional `workspaceID`
is not part of the current join. Windows ancestor reparse-point handling is
not qualified as a complete root-chain policy and must be reviewed before
relying on this boundary for hostile paths.
