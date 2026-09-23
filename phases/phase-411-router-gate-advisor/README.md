# Phase 411: Gate E routing design review

Date: 2026-09-22

## Evidence reviewed

- Gate E requires concurrency, cancellation, timeout, and circuit-breaking
  evidence through `ProposalRouter`.
- `ProposalRouter` currently runs a synchronous zero-argument callable and
  checks cancellation only before and after that call. It does not set a
  deadline.
- The serving server does not reference `ProposalRouter`. Phase 392 exercised
  the portable server in mechanical-only mode, so its `200/200` result does not
  establish ProposalRouter behavior through the serving request lifecycle.
- Existing focused router tests passed `4/4`, covering sequential controls,
  not concurrency or invocation timeouts.
- Resource preflight observed 50.04% available system RAM and no CUDA device
  available. No workload was started.

## Advisor consultation

Sol recommended a test-only local serving path with deterministic fake
callables. The advisor judged a standalone router stress harness insufficient
for Gate E because it would bypass request lifecycle behavior. For deadline
handling, it recommended isolated subprocesses with monotonic deadlines,
termination, grace-period kill, and join. Stop if a worker survives, circuit
transitions race, or the test bypasses the serving path.

Receipt: [advisor-receipt.json](advisor-receipt.json). Usage was 409 prompt,
532 completion, 941 total tokens. `decision_changed` is true because this
review changed the proposed next experiment from a standalone shadow to a
test-only server-path integration.

## Decision and boundary

No serving code or provider request was changed or run. Q4 classifies this as a
human architecture decision. Gate E remains open. Before integration, the
human must approve the test-only serving architecture and its local bounds.
This is separate from the paid-baseline child contract and provider cost
receipt, which remain outstanding for the productive-value gates.

## Human decision requested

Typed handoff: `human.choose_option`.

Decision: authorize a test-only integration of `ProposalRouter` through the
actual local request handler so Gate E can be tested, without changing the
production default route or making any provider request.

Recommended option: authorize a bounded, repository-local implementation
using deterministic fake proposal callables and loopback-only requests. Run
deadline and cancellation cases in isolated subprocesses with monotonic
deadlines, terminate/grace-period-kill/join behavior, and a check for surviving
workers. Exercise success, invocation failure, cancellation, timeout, and
circuit transitions through the same handler lifecycle. Keep the patch
uncommitted and the serving mode test-only.

Alternative: defer the Gate E integration. Gate E remains open, and no
standalone router stress result will be presented as a substitute.

Evidence and impact: the current router has only cooperative before/after
cancellation checks and no deadline; `server.py` does not reference it. The
test-only route would exercise more concurrency and lifecycle code but would
not establish production resilience, hardware behavior, provider quality, or
any other release gate. It should use local CPU/memory only, preserve the
10-percent RAM/VRAM reserves, and make no network call beyond loopback.

Stop conditions: a worker survives its bound, circuit state races, a request
escapes loopback, an unexpected mutation occurs, a reserve is breached, or the
test bypasses the serving path. On any stop, preserve logs and mark Gate E
inconclusive.

Rollback and timeout: changes remain local and uncommitted; remove only the
test-only wiring if it fails, leaving prior router and server behavior intact.
No response or approval timeout means defer and leave Gate E open. Approval
must precede implementation. This request does not authorize provider spend,
deployment, publication, or production enablement.
