# E0 OpenCode V2 context adapter contract

Status: contract slice documented; integration remains uninstalled and unrun
Job: `W2-E0-OPENCODE-CONTRACT-DOCS-20260924`
Started: 2026-09-24 (America/Edmonton)

## Product outcome

Define a small, reviewable first-client boundary for Wrench's deterministic
Layer 1 context runtime. OpenCode V2 is the selected first integration target.
This slice records what a future adapter may observe and which assumptions must
remain blocked until OpenCode and provider identities are pinned. It adds no
plugin code, dependency, install, provider call, or production route.

## Contract

- OpenCode documents two distinct hook boundaries. The `prompt` hook runs at
  user-prompt admission, before attachments, skill resolution, and durable
  inbox admission. The guide says a failed or interrupted preparation does
  not admit that prompt, but the API still has no typed rejection result; a
  future release-pinned implementation must establish and test the supported
  failure signal. This hook runs once per admission, not before each model
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
- A future context hook obtains the active session using its event
  `sessionID`, then reads the session record using the documented session API.
- The adapter derives its candidate source root from the active session's
  returned `location.directory`, which must be present and valid. It must not
  substitute the plugin load location, current process directory, a remembered
  path, or a guessed worktree path.
- The session `subpath` semantics must be pinned and tested against the chosen
  OpenCode release. Until then, reject nonempty or otherwise ambiguous
  subpaths. Convert the accepted root once and bind snapshot v2 to that
  configured lexical absolute path.
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
- The contract names the remaining release, serializer, tokenizer, root
  semantics, and dispatch-authority prerequisites without inventing them.
- The parent E0 goal and goal index point to this slice and retain all broader
  E0/E4 gates as open.
- Independent read-only review and `git diff --check` complete; commit contains
  only this slice and owned index/goal updates.

## Limits and evidence

OpenCode documents a session context hook and a session query surface, but the
documentation is not version-pinned. The contract does not establish exact
provider payload reconstruction, model dispatch control, tokenizer parity,
tool authority, recovery qualification, complete lifecycle accounting, or
production fitness. The integration has not been installed or run.

References: official [OpenCode V2 plugin guide](https://opencode.ai/v2/docs/build/plugins),
[OpenCode V2 API](https://opencode.ai/v2/docs/api), and
[V1-to-V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1).
The [V2 compaction guide](https://opencode.ai/v2/docs/compaction) describes
its preflight size estimates and explicitly warns heuristic estimates cannot
prevent every provider-specific overflow.

## Next action

Revisit implementation only when the exact OpenCode release and provider
request/tokenization boundary can be pinned, and when the client supplies a
fail-closed dispatch contract or an explicitly approved integration design
that does not claim one. Select a consented matched-task corpus and outcome
oracle before measuring E4 utility.
