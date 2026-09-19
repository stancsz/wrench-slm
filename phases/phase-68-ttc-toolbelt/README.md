# Phase 68: bounded test-time-compute toolbelt

This phase adds the local support layer for Wrench's mechanical worker:

- latest-intent tracking;
- Python AST and cross-language lexical symbol extraction;
- import and call dependency evidence;
- repository map, symbol lookup, and changed-file test selection;
- failure fingerprinting;
- read-only syntax and placeholder checks;
- structural, authority, evidence, consistency, blind-critic, and final gates;
- fast, guarded, and deep profiles with hard pass budgets and clean-path early
  exit.

The toolbelt cannot execute shell commands, write files, apply patches, or
override the independent verifier. Its receipts are implementation evidence,
not model-quality or teacher-parity evidence.
