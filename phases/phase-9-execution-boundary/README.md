# Phase 9: independent execution boundary

This phase adds the first executable Wrench component. A proposal must use the
versioned schema and one of the approved portfolio actions. The verifier owns
path resolution, byte and line limits, literal-search semantics, fixed Git
read-only invocation, local health allowlisting, and review-only patch checks.

Unsupported actions, path escapes, invalid bounds, non-local endpoints, and
automatic patch application abstain with a stable fallback reason. The module
contains no generic shell runner and never applies a patch.

The tests exercise accepted reads and Git observation plus rejected traversal,
external health, and automatic-write proposals. They are safety-contract tests,
not evidence that a model can generate correct proposals.
