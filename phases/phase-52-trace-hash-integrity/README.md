# Phase 52: trace-set hash integrity

The approved real-workflow evaluator now recomputes the canonical SHA-256 of
the trace list and compares it with `trace_set_sha256`. A valid-looking but
mismatched hash is blocked before any paired savings calculation. The
provenance fields from Phase 51 remain required.

This strengthens the evidence boundary without adding real workflow data.
