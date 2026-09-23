# Phase 434: test-only ProposalRouter serving path

Date: 2026-09-22

## Decision and scope

The human approved the Phase 411 recommendation to exercise `ProposalRouter`
through the actual local Wrench HTTP handler using deterministic fake
callables. The code path is enabled only by explicit test-only constructor
injection, requires an IP loopback bind, rejects an upstream URL, and leaves
the ordinary server defaults unchanged. Fake callbacks run in killable child
processes with monotonic deadlines, cancellation polling, bounded terminate
and kill grace periods, and joins. Access to the shared router state is
serialized while HTTP handlers accept concurrent requests.

This does not make provider calls, access credentials, enable production
routing, or exercise the model worker. It is a bounded integration test, not a
production resilience claim. Gate E remains open for sustained operational
evidence and any required production-equivalent shadow.

## Advisor consultation

Sol recommended a loopback-only injected callback in a killable child process,
with router state retained and serialized in the server process. The bounded
tests cover concurrent successful and failing handler requests, exact circuit
threshold under contention, cancellation, timeout-to-circuit transition,
abrupt fake-child exit, router reset, and circuit-open rejection.
The consultation request is recorded
in [advisor-packet.txt](advisor-packet.txt); its recommendation is summarized
here. It used 433 prompt tokens and 553 completion tokens, 986 total, with
request ID `chatcmpl-codex-advisor-f26539ab83c6`.

## Verification

- `py -3 -m pytest -q tests/test_gate_e_serving_path.py`: 14 passed.
- `py -3 -m pytest -q tests/test_harness.py tests/test_wrench_server.py tests/test_gate_e_serving_path.py`: 50 passed.
- Resource preflight before the full suite observed 54.9% free system RAM and
  89.5% free GPU memory. No model inference was started.
- Test-only integration rejects non-loopback binds and any configured
  upstream. Requests use an ephemeral `127.0.0.1` port and deterministic local
  callbacks only.
- A held-router test confirms queue waiting is bounded by one invocation
  timeout, not multiplied by the router's lifetime `max_attempts` ceiling.
- Trace tests verify router status is recorded without raw prompt text, local
  accounting stays explicitly unpriced with zero model and frontier calls, and
  the default server route exposes no test-only router metadata.
- Every exercised callback child was joined. The tests assert no tracked child
  remains after success, cancellation, timeout, and circuit-open rejection.
- A shutdown regression exposed concurrent handler/server cleanup of the same
  process handle. Child start and registration, liveness checks, joins,
  termination, removal, and close now share one lock. The regression confirms
  server shutdown terminates the in-flight fake child and the HTTP handler
  returns without a double-join or double-close race.
- `py -3 -m pytest -q`: 307 passed, with 18 existing Windows asyncio
  deprecation warnings.
- The Q4 collaboration contract validator returned `VALID`. The parent
  `monetary_budget` remains zero.

## Provider identity correction

The human clarified that the current service on port 4000 is GPT-6, not
MiniMax. The read-only `/v1/models` response lists gateway aliases but does not
establish which model an alias dispatches to. Phase 403 remains a historical
MiniMax experiment and is not evidence about the current port-4000 mapping. No
provider request was made for this phase. A future canary must bind and verify
the exact model route before any separately authorized call.

## Stop and rollback

Stop if a fake worker survives bounded termination, a request leaves loopback,
router state races, the resource reserve is breached, or the handler bypasses
the test-only path. Keep the patch local and uncommitted. Roll back only this
test-only wiring if it fails. This work does not change the zero-spend Q4
parent budget or authorize a paid canary.
