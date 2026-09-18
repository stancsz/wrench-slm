# Phase 16: bounded routing guard

This phase adds a small routing-control layer around the verifier. It enforces
an attempt ceiling, opens a circuit after repeated abstentions or invocation
errors, supports an explicit operator bypass, and only permits reset with the
current configuration hash.

The guard is control-plane evidence, not a quality or production-readiness
claim. It does not grant the model tool authority and it does not replace the
independent verifier.
