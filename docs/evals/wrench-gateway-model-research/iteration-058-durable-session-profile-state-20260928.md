# Iteration 058: add restart-safe session profile state behind a bounded store

## Source change

Extended `examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs` with
durable session-state restoration through an injected storage adapter. A saved
state binds one profile to the complete inventory SHA-256 and carries bounded
schema-expansion and name-discovery state. Session IDs are SHA-256 hashed in
storage keys; request messages and prompts are not persisted.

The adapter must provide `get`, `set`, and a process-wide atomic `claim` for
the `session-profile/` key prefix. Claims are limited to 256; records are
limited to 128 KiB. A profile is persisted before the hook filters a request,
and expansion/discovery state is persisted before the helper returns it. Missing
or corrupt state, inventory drift, failed selection, and capacity exhaustion
fail through with the complete tool map. A storage write failure rejects the
hook before it filters tools. A claim left without a saved profile by a process
failure fails through on later requests rather than selecting again.

Added three source cases for new-hook restoration after a simulated restart,
inventory drift after restart, and write failure before filtering. The suite now
contains 23 cases, confirmed by static source count only. They use an in-memory
fake store and do not establish disk durability or process-wide atomicity.

## Storage boundary and OpenCode API

The official [OpenCode V2 plugin reference](https://opencode.ai/v2/docs/build/plugins#storage)
documents durable JSON storage scoped to a plugin, with `get`, `set`, `remove`,
and prefix `scan`. It does not identify the Windows backing path. Wrench's
50 GB policy requires all Wrench-owned state to live under
`C:\\wrench-slm-data`, so the prototype does not write directly to
`ctx.storage`. No approved Wrench-root adapter exists yet. Implement and
inventory that adapter, its atomic claim operation, its bounded writes, and its
storage reservations before enabling session mode.

The README now specifies this boundary and updates the example to require an
injected Wrench-root adapter. The prototype remains unregistered in the active
OpenCode config. The test-only fake does not prove OpenCode runtime ordering,
SubRoute request contents, or restart behavior on the installed v2.0.12 build.

## Current gates

At the latest sample, free RAM was 3,185.4 / 32,701.8 MiB (9.74%), below the
10% job floor. No tests, OpenCode runtime, inference, training, benchmark,
packaging, or delegated job ran. Storage status was `WITHIN_LIMIT`: actual
10,993,147,543 bytes, active reservations 8,353,000 bytes, projected
11,001,500,543 bytes. The durable-state source-edit reservation remains active
until its files are accounted for and the reservation is released.

The SubRoute at `http://127.0.0.1:4000` remains the selected comparison path.
It is forced to the remote `openrouter` alias, so this iteration used no
provider POST and incurred no spend. The numeric campaign USD cap remains
unspecified; do not send generation traffic without it and the caller's
pre-dispatch ledger.

Correction for the historical record: Iteration 057's source suite had 20
cases; its final next-step sentence mistakenly called it a 19-case suite. The
historical report is left intact.

The LoRA's effectiveness, 95/5 task mix, 95% frontier-token reduction, 95%
all-in cost reduction, and all-day engineering ability remain unproven. Keep
the goal active. Next implement and inventory the Wrench-root atomic store
adapter, then run the 23-case suite and a no-provider v2.0.12 path check only
after RAM and VRAM remain safely above their reserves.
