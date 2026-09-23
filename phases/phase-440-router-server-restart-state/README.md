# Phase 440: ProposalRouter server-process restart state

Date: 2026-09-22

## Finding

Phase 438 validates schema- and configuration-hash-bound router-state helpers
across `ProposalRouter` object reconstruction. The active test-only serving
path in `WrenchHTTPServer` keeps its injected router in memory and has no
router-state path at startup or shutdown. Existing serving tests therefore do
not establish recovery across a real operating-system process restart.

The focused current test run passed 24 tests:

```text
py -3 -m pytest tests/test_router_state.py tests/test_gate_e_serving_path.py -q
24 passed in 13.90s
```

The tests use deterministic callbacks and no model calls. Preflight observed
54.1% free RAM and 14,637 MiB free of 16,303 MiB GPU memory. No long-running
test or soak was started.

## Advisor review

Sol recommended option A: bind persistence only to the explicit opt-in,
loopback-only `ProposalRouter` path; load the snapshot before serving; and
atomically save each state-changing transition before acknowledging it. Verify
recovery across an actual OS-process restart with deterministic callbacks and
no model calls. Stop if an invalid or failed load silently resets state, a
failed save still allows a success response, or the ordinary server path is
affected. This regression would not constitute production Gate E acceptance.

Consultation: `codex-sol-advisor`, request
`chatcmpl-codex-advisor-3887b57ddf7e`; 435 prompt tokens, 234 completion
tokens, 669 total; `decision_changed: true`. The advice changes the next action
from inspecting helper recovery to proposing a test-only server-state binding,
with explicit fail-closed save/load semantics.

## Q4 human decision required

This is a `CHALLENGE` architecture choice. No `WrenchHTTPServer` lifecycle
changes have been made in this phase.

Recommended option: authorize a local-only state path that is accepted only
with the existing test-only router and invoker, requires an IP loopback bind,
loads validated state before requests are accepted, and persists each router
state transition atomically before returning a successful acknowledgement.
Add a bounded real OS-process restart regression using only deterministic
callbacks. The normal server default, model worker, and production routing stay
unchanged.

Alternative: keep `state.py` isolated and defer serving-process persistence.
The existing 24-test evidence remains helper-level, and Gate E stays open for
process restart and serving-state recovery.

Cost and risks: option A adds opt-in file I/O and a new fail-closed startup and
response behavior to the test-only server path. It is limited to one bounded
local integration slice and does not start a soak. A malformed state file,
configuration mismatch, directory or disk error, failed atomic write, normal
server-path change, or surviving test child is a stop condition. If the
implementation fails, rollback removes only the test-only persistence wiring
and its tests; preserve Phase 438 state helper and all receipts.

Deadline and timeout: human direction is required before editing
`src/wrench_harness/server.py`. No response means defer this server-lifecycle
change and leave the current helper-only evidence in place. This decision does
not authorize a provider request, credentials, another soak, production
routing, release, or deployment.

## Current state

- No server code, test code, or runtime state was changed for this phase.
- The advisor packet is
  [advisor-packet-router-server-restart.txt](advisor-packet-router-server-restart.txt).
- Production remains not ready. Gates C and D remain open, and Gate E remains
  open for restart/recovery, complete accounting, no-mutation evidence, and
  sustained operational evidence.

## Source identities at handoff

- `GOAL.md`: SHA-256
  `AF17701FF9217742EC450FE95EEED778F0C15CF7E388DEEAC68669F7EB6A77A9`
- `COLLABORATION_CONTRACT.json`: SHA-256
  `CF255E5C73AE9DF58C5FD29D879BD7AAA9A2972245EFB61A3C4C597F65D9B4B5`
- `src/wrench_harness/server.py`: SHA-256
  `B10E4513DB5210528D147181CF2672A331A0BD4CEC3042EEB69E57A35F74D41B`
- `src/wrench_harness/state.py`: SHA-256
  `8BA4E879D77F1959286C8C6BFCFE8DC23E45BAC5484655DC86F2BCEE8271196A`
- `src/wrench_harness/router.py`: SHA-256
  `204E56268463CC9BEF3D44D58026FD0383A3F18D1FB4BC1D501B507C6C691D48`
- `tests/test_router_state.py`: SHA-256
  `7160277E3C9FEEC8CCE2D047EAC76CE4C7DD451CF407EF9841EB7C6503086CE5`
- `tests/test_gate_e_serving_path.py`: SHA-256
  `BBF6263AB92E53F0062F530D6383EEF07D5426C12D4F99F6F8FDEEDDB5FD9647`
- `advisor-packet-router-server-restart.txt`: SHA-256
  `7DB182F00C715CF446A9E7599A69BB25DF8B86E2DE38C983AE3A6B78FCCA33B5`
