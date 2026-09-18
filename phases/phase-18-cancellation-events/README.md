# Phase 18: cancellation and control events

This phase adds cooperative cancellation checks before and after a bounded
router attempt, plus an optional event sink for cancellation, circuit-open,
reset, and bypass events. Event-sink failures are swallowed so observability
cannot change the fail-closed execution decision.

The tests cover pre-attempt cancellation and event delivery alongside circuit,
reset, and bypass transitions. This does not claim interruption of a blocking
kernel or durable external alert delivery.
