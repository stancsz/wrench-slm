# Session-scoped tool profiles for the SubRoute comparison

This is a source-only OpenCode V2 context-hook prototype. It is separate from
the synthetic request observer and is not registered in the current OpenCode
configuration. It makes no network or provider calls by itself.

The intended destination is the existing local SubRoute at
http://127.0.0.1:4000, through provider ID wrench-subroute and model alias
openrouter. Its current forced route is a remote OpenRouter deployment, so any
ordinary model request can incur provider charges. Use the caller-side durable
budget gate before any paid comparison request. A local GET health check does
not authorize or measure a generation.

## Behavior

- The local Wrench selector receives immutable JSON snapshots of the request
  context and the tool names. It may return only a profile ID from the fixed
  registry. With `sessionScoped: true`, it selects once per `sessionID` and
  reuses that choice while the complete schema hash stays the same. The
  integration must run that selector on a local Wrench LoRA; this prototype
  does not implement or call a model.
- Each profile is bound to a SHA-256 hash of the complete tool-name/schema map.
  The hook changes nothing when the inventory differs, a profile is unknown,
  a tool is unavailable, selection fails or times out, or the receipt sink
  cannot record the decision.
- A valid profile deletes only non-allowlisted entries from this model request.
  It never edits OpenCode configuration, tool implementations, permission
  rules, or the existing message-only Wrench transition. Retained schemas are
  passed through as the same objects.
- Receipts contain bounded decision metadata only. Supply a durable local
  receipt sink before enabling the hook. If a filtered receipt cannot be
  written, removed entries are restored and the hook rejects the request.

## Known deployment gaps

The legacy default mode still invokes the selector on every request. The new
`sessionScoped: true` mode requires an injected `sessionStateStore`; it freezes
one selection per session, restores it after a plugin restart, and caps durable
session claims at 256. The in-memory session/tool-name index is separately
capped at 1 MiB. It does not evict active sessions. Missing identity, schema
drift, corrupt stored state, and exhausted capacity pass the full map through.
Drift blocks filtering for the rest of that session.

The store interface requires `get(key)`, `set(key, value)`, and an atomic
`claim(key, maxKeys)` operation that returns `created`, `existing`, or
`capacity`. Claims cover the `session-profile/` prefix across all plugin
instances, persist even before the first profile write, and cannot exceed the
requested maximum. Keys contain only a SHA-256 digest of the OpenCode session
ID. Stored JSON is limited to 128 KiB and includes the inventory hash, profile
ID, bounded expansion counters, and tool names; it never stores prompts or
messages. If a process stops after claiming a session but before writing its
profile, later requests for that session pass through rather than reselect.
Claims are not evicted in this prototype.

A bounded SQLite adapter now exists in
[`wrench_root_session_store.mjs`](./wrench_root_session_store.mjs). Its fixed
default database path is
`C:\\wrench-slm-data\\opencode\\tool-profile-state\\session-state.sqlite`.
It validates the approved root and non-reparse ancestors, bounds each JSON
record to 128 KiB and the database to 48 MiB, enforces the 5 GB destination
free-space floor, and serializes process-wide claims with SQLite
`BEGIN IMMEDIATE`. Iteration 134 passes a four-process capacity race, restart
recovery, corruption/limit checks, and a source-hook restart integration test.
The operator must still reserve at least 125,000,000 bytes through the Wrench
storage checker before enabling persistent writes; SQLite rollback journals
can temporarily duplicate the bounded database, and this adapter does not
create or release that external reservation. Do not wire OpenCode's
`ctx.storage` directly because its documented API does not identify an
inventoryable Windows backing path.

Session-scoped mode registers `wrench_expand_tools`. Every profile must keep
this helper. Build the profile inventory with the exported
`createToolExpansionDefinition()` so its schema hash matches the registered
helper exactly. It can restore schemas only from the original hash-bound
inventory, with defaults of 8 requested schemas per call, 24 per session, 4
calls per session, and 32 KiB of added schemas per session. A single
`__list_available__` request can reveal omitted names before the model chooses
which schemas to expand, capped at 8 KiB of names by default. Successful
expansions and known-session rejections are recorded through the receipt sink.
These are bounded prototype limits, not token-savings evidence. Restart
recovery is implemented against the injected store interface. The Wrench-root
adapter is not registered in the active OpenCode configuration. Local checks
used Node v24.19.0 and `opencode v2.0.12`, but did not load the adapter inside
the installed plugin host or test crash/power-loss durability. Node documents
`node:sqlite` as a release candidate in the v24 line, so pin and revalidate the
actual plugin runtime before deployment. The helper is registered through the global
tool transform, so its visibility and overhead for other providers also need
measurement. Do not enable this prototype for repository engineering until
the adapter, tests, and installed-runtime behavior pass.

The current V2 API docs define the context event as a `SessionRequestHook`
with a read-only `sessionID`; it adds the agent and mutable tools map. The
`context` hook runs for agent-loop calls, including tool-driven continuations.
This identifies the right key for session state, but the installed v2.0.12
event payload and ordering still need a local no-provider check.

The `sessionScoped` implementation selects once per `sessionID` and reuses that
reviewed profile while the complete tool-inventory hash remains unchanged.
Missing identity and inventory drift pass the full tool map through. Keep the
reviewed execution and verification set in every profile. The expansion tool
restores only schemas from the original hash-bound inventory under explicit
per-call, per-session, and byte limits, and records each expansion. The helper
does not change native execution permissions or tool implementations. Verify
behavior and hook ordering on installed v2.0.12 before enabling the hook.

## Integration boundary

OpenCode's V2 context hook runs immediately before a model request, includes a
mutable tools map, and can be scoped to a provider. The documented API shows
deleting one tool entry from the map. Register the factory only after the
local selector, fixed inventory profiles, and durable receipt sink have been
implemented and reviewed:

    import { Plugin } from "@opencode/plugin";
    import { createToolProfilePlugin } from "./tool_profiles.mjs";
    import { WrenchRootSessionStateStore } from "./wrench_root_session_store.mjs";

    const delegate = createToolProfilePlugin({
      enabled: true,
      sessionScoped: true,
      profiles: reviewedProfilesIncludingExpansionTool,
      selectProfile: localWrenchSelector,
      emitReceipt: durableLocalReceiptSink,
      sessionStateStore: new WrenchRootSessionStateStore(),
    });
    export default Plugin.define({ id: delegate.id, setup: delegate.setup });

Do not add this registration to the active OpenCode configuration yet. The
installed v2.0.12 hook and filtered request shape have now been exercised with
a loopback mock, including one scripted `read` round trip. This does not verify
the active OpenCode configuration, SubRoute integration, ordering with other
plugins, permission behavior in production, or a real provider request.

The source suite in `tool_profiles.test.mjs` contains 24 cases for
deterministic hash binding, fail-through behavior, session freezing and
restart restoration, bounded schema discovery and expansion, storage failure,
count and byte cache capacity, provider scoping, and disposal. The restart
cases there use a test-only in-memory store. The additional Wrench-root store
tests use SQLite under the approved data root and verify state across a normal
process restart. Earlier
10/10, 13-case, and 20-case receipts apply to older source hashes. The 24-case
suite passed on 2026-09-28 with `node --test` after the selector snapshot was
adapted for enumerable data fields on OpenCode message instances. The installed
v2.0.12 no-provider hook and actual lowered request were also exercised; see
[Iteration 099](../../docs/evals/wrench-gateway-model-research/iteration-099-opencode-lowered-request-profile-20260928.md)
and [Iteration 100](../../docs/evals/wrench-gateway-model-research/iteration-100-opencode-single-tool-upper-bound-20260928.md).
The three-tool profile measured 35.8539%; a one-tool `read` profile measured
42.5735% on one synthetic request. Iteration 101 then ran a paired scripted
read-tool cycle and measured 42.2967% fewer MiniMax M3 target-token input
tokens across both requests (13,306 to 7,678). The mock, not a language model,
issued the tool call and final answer. This is request-shaping evidence only;
it does not establish frontier savings, task utility, 95/5 routing, or all-day
engineering. See [Iteration 101](../../docs/evals/wrench-gateway-model-research/iteration-101-opencode-read-tool-cycle-20260928.md).
Rerun the source suite from the repository when RAM is safely above the
reserve with:

    node --test examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs

Passing these source tests would not establish provider token savings, task
quality, 95/5 routing, 95% cost reduction, or all-day coding ability. Measure
the exact final request and response usage on the same frozen task set to
establish those outcomes.

Reference: [OpenCode V2 plugin hooks](https://opencode.ai/v2/docs/build/plugins#hooks).
