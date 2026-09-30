# Iteration 049: SubRoute 4000 and tool-profile prototype (2026-09-27)

## Owner direction and route

The owner directed use of the existing SubRoute at
http://127.0.0.1:4000. Fresh read-only GETs to /health/liveliness,
/api/active-model, and /models returned HTTP 200. The active-model response
reported alias openrouter, mode force, and policy version 4; the model
inventory contained 19 aliases.

The configured OpenCode provider ID remains wrench-subroute, with base URL
http://127.0.0.1:4000/v1 and model alias openrouter. This route currently
selects a remote OpenRouter-backed model. The port-4000 setup is the chosen
comparison route, not a local model endpoint.

No completion POST, provider generation, credential read, or SubRoute
configuration change occurred. A numeric aggregate USD cap is still absent,
so paid calls remain closed. Read-only reachability does not prove generation
identity, request-control propagation, usage, or cost.

## Source change

Added a separate, disabled-by-default OpenCode context-hook prototype under
examples/opencode_v2_subroute_tool_profiles:

- tool_profiles.mjs binds each fixed allowlist to a canonical hash of the
  complete tool inventory; it filters only non-allowlisted tools for one
  request and scopes registration to provider ID wrench-subroute.
- Unavailable or stale profiles, invalid inputs, selector errors, unknown
  profile IDs, timeouts, and inventory drift keep the full tool map. A failed
  durable receipt after filtering restores removed entries and rejects the
  request.
- The local Wrench selector is an injected callback and can return only a
  registered profile ID. The prototype does not implement or invoke a model.
  Integration must use the locally trained Wrench LoRA and a durable local
  content-free receipt sink.
- tool_profiles.test.mjs contains synthetic unit tests. README.md records the
  integration boundary and does not enable the plugin or change OpenCode's
  current default model.

Source identities:

| File | SHA-256 |
| --- | --- |
| examples/opencode_v2_subroute_tool_profiles/tool_profiles.mjs | FC8F07A383711D4FEF57A09EE614E9ABAB1E6B774E5E4E4A19AA0171F9850782 |
| examples/opencode_v2_subroute_tool_profiles/tool_profiles.test.mjs | D7E71F3C3CA4EE137E97B765711EEB4A059327DCA767809F8916FDE61667E5A4 |
| examples/opencode_v2_subroute_tool_profiles/README.md | 123F6BB7C1D6D346EFDA805B94E1C03DE42FB597B9253FC95ACE4BABF0150CC2 |

Repository HEAD before and after this iteration was
af01304824f079a64b6c3902397a2034b843511a.

## Checks and limits

The two JavaScript files passed node --check. The focused synthetic Node test
suite passed 10/10 cases. git diff --check exited successfully; Git emitted
line-ending conversion warnings for existing modified tracked files.

The tests do not load OpenCode v2.0.12, confirm hook ordering or rejection
semantics, capture a lowered request body, or measure prompt-token savings.
The prototype has not been registered or activated. No result from this
iteration demonstrates task success, 95/5 routing, 95% frontier-token savings,
95% lower all-in cost, or sustained coding ability.

After the unit test, system RAM was 3,588.8 / 32,701.8 MiB free (10.97%).
Storage, including the external SubRoute checkout, was WITHIN_LIMIT at
10,992,728,920 actual bytes plus 8,223,000 bytes in active reservations. The
0.8B training/inference screen remains closed: its fit gate requires 25% free
RAM, and no fresh model workload admission was performed.

## Next gate

First verify the hook in an isolated no-provider OpenCode v2.0.12 process and
capture the exact lowered request after the context hook. Keep egress blocked
and confirm the request cannot reach provider transport. Then prepare paired
task and token accounting against the frozen workload. Any paid comparison
still requires a numeric aggregate cap, a matching hash-bound approval, and
validated provider, usage, and billing receipts.
