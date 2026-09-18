# Phase 42: router recovery and bounded control receipt

This phase exercises the existing routing controls across a persisted-state
boundary. A circuit opens after a bounded failure, the disabled state is
written and loaded by a fresh router instance, a configuration-hash mismatch
is rejected, the matching hash permits an operator reset, and cancellation is
observed after an in-flight attempt.

The receipt is `router-control-receipt.json`. It is local no-mutation control
evidence. It does not claim that an external alert transport, a blocking
kernel interrupt, or a production rollback store has been exercised.
