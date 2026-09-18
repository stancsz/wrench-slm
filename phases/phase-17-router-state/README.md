# Phase 17: durable router state

This phase adds schema- and configuration-hash-bound persistence for the
routing guard. State is written with a same-directory atomic replace and is
restored only when counters, flags, schema, and the exact configuration hash
validate. A different router configuration cannot silently reuse old state.

The tests cover save, restore, counter recovery, and hash-mismatch rejection.
This is local control-plane evidence. It does not yet prove process crash
recovery, cancellation, alert delivery, or rollback of model artifacts.
