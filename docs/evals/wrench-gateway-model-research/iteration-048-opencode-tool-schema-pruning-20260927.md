# Iteration 048: OpenCode tool-schema pruning boundary (2026-09-27)

## Question

Can the current Wrench/OpenCode hook path remove irrelevant tool schemas from a
single model request, a potentially large repeated input cost?

## Source findings

The current Wrench projection accepts the `tools` field, but its context
transition explicitly requires that field to remain unchanged. That specific
message-insertion transition cannot perform tool-schema pruning. Current
source SHA-256:

`src/wrench_harness/opencode_hook_projection.py`:
`914462BD8EDCCE4805DCA6C6A96CC651C1155536D50F4BE77AB99DDC4F890D06`

The official OpenCode V2 plugin documentation exposes a separate supported
path: its `context` hook runs immediately before the agent model request, and
the mutable context includes the `tools` map. The documentation demonstrates
deleting one entry from `event.tools`. This means per-request pruning is
possible without changing the existing message-only Wrench transition. Exact
compatibility with the installed v2.0.12 package and actual lowered request
serialization still need runtime verification.

The local OpenCode v2.0.12 example registers an `http.request` hook, but the
current sample is a no-provider observer for one pinned synthetic body. It
records the number of tool schemas and then throws
`provider_transport_disabled`; it neither filters a request nor proves, in an
installed OpenCode process, that transport was not invoked. Sources and
identities:

| File | SHA-256 |
| --- | --- |
| `examples/opencode_v2_subroute_capture/plugin_setup.mjs` | `D520D28F563118FA8DDE1BE049CB16BD3BE5D3F6D3936F6027A33502135C61B6` |
| `examples/opencode_v2_subroute_capture/observer.mjs` | `89382B6183DE4C4F11FEFFFC31B6823ED650823D11593E3540F9BE1B4C11FC6C` |

The separate V1 `tool.definition` API exposes description/parameter rewriting
but no per-call omit field. Open issue #42869 requests omission for that older
surface. Its author reports that a manually configured per-agent deny list
removed 178 of 214 tools and reduced input-token usage by 37.6% across their
own 404-session sample. This is one user's self-reported setup, not an
independently reviewed benchmark or a Wrench result; it does not negate the V2
`context` hook path.

Sources: [OpenCode V2 plugin docs](https://opencode.ai/v2/docs/build/plugins),
[OpenCode V1 plugin API source](https://github.com/anomalyco/opencode/blob/dev/packages/plugin/src/index.ts),
[tool omission issue #42869](https://github.com/anomalyco/opencode/issues/42869).

## Implication for the experiment

The next engineering step is a separate, fail-closed V2 context-hook tool
profile. It should only remove entries from the tool map, leave retained
schemas and execution permissions unchanged, and pass through the full tool
set or abstain when its bounded profile cannot be validated. Keep the existing
message-only transition unchanged. Pair the hook with request-body observation
to verify which filtered schemas reach SubRoute, then measure task success,
tool recovery, and token usage on the same frozen tasks. The 37.6% report does
not support the 95% target. A low frontier-call percentage alone is not
token-savings proof: the remote token denominator must include difficult-task
escalation, retries, verification, compaction, fallback, and recovery fetches.

## Resource and evidence status

Current system RAM was 2,897.1 MiB of 32,701.8 MiB free (8.86%), below the 10%
runtime floor. The RTX 5060 Ti reported 15,229 MiB of 16,311 MiB free and 0%
utilization. Storage including the SubRoute checkout was `WITHIN_LIMIT` at
10,992,668,918 actual bytes plus 8,103,000 bytes in active reservations. No
tests, OpenCode runtime, inference, training, benchmark, or provider request was
run. The next live integration check remains gated on the RAM floor; any paid
request remains gated on the separately authorized aggregate USD cap.

**Disposition:** OpenCode V2 documents a direct per-request tool-pruning hook;
the Wrench implementation has not used it yet. The 95% frontier-token saving,
95/5 routing, trained Wrench LoRA, and all-day engineering goals remain
unproven.
