# Iteration 033: campaign-wide SubRoute caller budget (2026-09-27)

## Question

Can the Wrench research caller reserve spend before a request and keep one
aggregate ceiling across separately approved jobs on the existing SubRoute
`127.0.0.1:4000`?

## Implementation

Added a host-side caller in `tools/capture_subroute_teacher_traces.py` and a
durable SQLite ledger in `tools/subroute_budget_guard.py`. It requires an
explicit human approval file bound to the current Wrench commit, a hash of the
caller and its imported policy code, and an exact hash of a Wrench-authored
synthetic case file. Approval fixes the local SubRoute endpoint, `openrouter`
alias, expected OpenRouter/MiniMax M3 identity, provider allowlist, rate
ceilings, request and token ceilings, expiry, and one fixed research campaign
ID. The tool does not create approval files. Only this host-side caller reads
`WRENCH_SUBROUTE_API_KEY` or `GATEWAY_MASTER_KEY` from the environment when a
real request is attempted; it never logs or stores the secret, and the learned
controller cannot access it.

The ledger is shared by all jobs in that campaign. SQLite `BEGIN IMMEDIATE`
serializes reservations across processes. The first admitted approval pins the
campaign-wide cap and route identity; later approvals must use the same cap.
Creating another job cannot reset the total or increase the cap. One unresolved
call blocks every job. Each request reserves its worst-case amount before
dispatch; a missing or inconsistent provider/model/generation/usage/cost
receipt leaves the full reservation outstanding and blocks further calls.
Requests are non-streaming, single-attempt, bounded in bytes and output tokens,
and explicitly request one provider with fallbacks disabled. Receipts retain
normalized proposals and usage fields, not prompts or raw model output.

OpenRouter documents `provider.max_price` as a per-million-token price ceiling
that fails when no provider satisfies it. That is a necessary request-level
control, not a wallet-wide dollar limit. The local ledger is still only a
caller-side control. It assumes the gateway forwards the limits, the pinned
provider honors the selected rate ceiling, the bounded request maps to no more
than the approved input-token ceiling, and the configured SubRoute runtime has
retries and fallbacks disabled. If a provider bills beyond the reservation,
the caller can detect and halt later calls, but cannot undo that first charge.
OpenRouter's live selected endpoint and billing response have not been
observed. See [OpenRouter cost controls](https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/) and the
[Chat Completions usage fields](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request).

The SubRoute checkout's current config source sets `router_settings.num_retries`
to `0` and `fallbacks` to an empty list. This source setting was read without
restarting the service. The running process's loaded configuration and the
metadata-header patch from iteration 032 are not verified. No route setting was
changed.

## Verification

- Python AST parsing passed for the caller, budget guard, and focused test file.
- An earlier draft with a per-job-only ledger passed its six isolated mock
  tests. Review found that a new approval could reset that draft's allowance.
  The final implementation changed the schema to a campaign-wide ledger and
  added a cross-job cap and cap-increase regression test.
- The final campaign-wide implementation's unit tests were not run. The latest
  host sample had 3,198.1/32,701.8 MiB free RAM (9.78%), below the required
  10% reserve, so the test job was stopped before execution. The prior 6/6
  result does not verify this final schema.
- No POST was sent to port 4000, no upstream generation ran, and no provider
  spend occurred. The mock transport test from the prior draft did not send
  network traffic.
- No numeric owner spend cap or approval file exists. The user specified the
  route but did not supply the requested dollar amount. Paid calls remain
  disabled.

The storage checker reported `WITHIN_LIMIT`: 10,989,899,564 actual bytes and
8,103,000 bytes in active reservations. The completed OpenCode capture-test
reservation was released; the caller reservation remains active for its
pending isolated test. The 50 GB aggregate limit was not
approached. The latest GPU sample was 15,127/16,311 MiB free; no model
inference or training was run.

| File | SHA-256 |
| --- | --- |
| `tools/subroute_budget_guard.py` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` |
| `tools/capture_subroute_teacher_traces.py` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` |
| `tools/capture_minimax_teacher_traces.py` | `CA696597753995024650DEC7470379AAF91E2CF5F4EFAB26F19AEF07E361BA47` |
| `tools/provider_budget_guard.py` | `5D48687A5CF0CCB58C8B5D686256AD9FC2ECA713F9F36DA51D445E9BBAE21114` |
| `tests/test_subroute_budget_guard.py` | `62B8C3BFE58A0D46BE2189C766DF1FB348540A9A5B1A6363E64DF5076A8801B9` |

## What this establishes

It establishes that the final source parses and that the earlier prototype's
local reservation and mock receipt path passed six tests. It does not establish
the campaign-wide code's runtime correctness, loaded SubRoute behavior, a
provider charge bound, model quality, Wrench LoRA effectiveness, 95/5 task
completion, 95% frontier-token reduction, 95% all-in savings, or all-day
engineering. The existing 0.8B general-controller screen remains 0/10; the
separate synthetic tokenizer diagnostic remains 12.11% over its eligible
pairs. Neither changes here.

## Next gate

After at least 10% free RAM is observed, run the isolated campaign-wide unit
suite under the existing storage reservation. Review the exact hash and
exercise the 4000 request-control path without a provider transport. Do not
make a generation request until a numeric aggregate cap is supplied and the
approval binds that exact cap, code, and synthetic cases. Then verify a single
capped request's returned endpoint, usage, and bill before interpreting any
effectiveness result.
