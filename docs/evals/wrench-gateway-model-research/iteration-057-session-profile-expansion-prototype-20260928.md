# Iteration 057: implement session-frozen profiles and bounded schema recovery

## Source change

Added opt-in `sessionScoped` behavior to
`examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs`:

- Select once for a session ID and reuse the profile only while the complete
  tool-name/schema hash remains unchanged.
- Pass through the full tool map for missing identity, inventory drift, or a
  reached cache capacity. Do not evict cached sessions. Cap state at 256
  sessions and 1 MiB of aggregate session/tool-name indexing.
- Require every session profile to retain the `wrench_expand_tools` helper.
  The new `createToolExpansionDefinition()` export supplies the exact schema
  used both for inventory hashing and OpenCode registration.
  It can list omitted names once per session and expose named schemas only
  from the hash-bound inventory. Name discovery is capped at one call and 8
  KiB. Defaults cap expansion at 8 tool names per call, 24 per session, 4
  expansion calls, and 32 KiB of schema bytes.
- Emit receipts for selection, expansion, discovery, and known-session
  rejection. A receipt failure leaves the request unfiltered or rejects the
  hook; it does not authorize a tool or change its implementation or native
  permissions.

The plugin helper registers the expansion tool and a SubRoute-scoped context
hook only when explicitly enabled with `sessionScoped: true`. It remains
unregistered in the active OpenCode configuration. The helper uses a global
tool transform, so its visibility and prompt overhead for other providers
must be measured.

Added seven focused cases, bringing the source suite to 20 cases. They cover
profile freezing, name discovery limits, inventory drift, expansion bounds,
cache count/byte capacity, and helper registration. The suite was not run:
current free RAM is 3,141.6 / 32,701.8 MiB (9.61%), below the 10% job floor. The RTX
5060 Ti has 15,227 / 16,311 MiB free, but that does not waive the RAM gate.

## Remaining gaps

Session state is in-memory only. A plugin restart can select a different
profile for a resumed session; durable state or a restart fail-through marker
is needed before enabling the integration. The exact installed OpenCode
v2.0.12 hook payload, hook order, expansion-tool result, and final lowered
request remain unverified. The local selector is still an injected callback,
not a trained Wrench LoRA. No exact request token counts, cache-tier prices,
task success, or local/remote comparison was measured.

Read-only GETs still show the existing SubRoute at
`http://127.0.0.1:4000` with `active_model=openrouter`, `mode=force`, and 19
models. No provider POST, credential read, or spend occurred. The numeric
campaign USD cap remains absent.

The LoRA, 95/5 task mix, 95% frontier-token reduction, 95% all-in cost
reduction, and all-day engineering targets remain unproven. Keep the goal
active. Next, resolve restart handling and run the 19-case suite only after
RAM and VRAM are comfortably above their floors; then verify the exact
v2.0.12 request path without upstream transport.
