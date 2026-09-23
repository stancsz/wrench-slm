# Phase 427: subprocess-tree timeout cleanup

> Follow-up testing found that the initial Windows `taskkill /T` implementation
> covered a live root but not a root that exited before a descendant closed its
> inherited output pipe. Phase 428 supersedes the Windows strategy with an
> owned Job Object and covers both cases.

## Finding

The paired real-client canary runner used a bounded subprocess timeout, but
terminating the direct client process did not guarantee cleanup of processes it
spawned. A regression test launched a Python parent that started a detached
60-second child, then blocked. The helper timed out after one second and
returned while the exact child PID was still alive. Test teardown inspected
and terminated only that child PID.

## Change

`tools/probe_paired_real_client_canary.py` now launches each bounded command
with an owned process group. On timeout it attempts Windows process-tree
termination with `taskkill /T /F`, or signals the POSIX process group with
SIGTERM followed by SIGKILL if needed. Cleanup is bounded, and the result
records `tree_cleanup_complete` so a failed cleanup is visible instead of
silently treated as successful. Normal completions report cleanup complete.
The Windows path is not Job Object containment and should not be treated as a
guarantee for descendants that outlive the root process before cleanup starts.

Windows tree termination follows the documented [`taskkill /T` behavior](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/taskkill).
Python's timeout behavior and process management are documented in the
[subprocess reference](https://docs.python.org/3/library/subprocess.html).

## Verification and limits

- The spawned-child timeout regression confirms the child is no longer alive
  after timeout.
- Focused `tests/test_paired_client_canary.py`: 31 passed.
- Full test suite: 279 passed, with 18 existing warnings.
- A consultation was attempted through the user-requested local API at
  `http://localhost:4000`; it returned HTTP 502 (`litellm.BadGatewayError`).
  No advisor response, request ID, token usage, or advice was received. The
  submitted question and evidence are preserved in `advisor-packet.txt`.
- No provider call or spend occurred.

This is local canary-runner timeout hygiene only. It does not verify
`ProposalRouter` serving-path cancellation, establish Gate E, close a release
gate, or authorize provider activity. If tree cleanup reports false, treat the
run as failed and investigate the exact owned process before any promotion.
The live-root Windows case remains a regression in Phase 428. The root-exits-
first gap and resulting cleanup stall were reproduced in the follow-up probe
and are addressed by Phase 428's suspended-create, assigned-job launcher.
