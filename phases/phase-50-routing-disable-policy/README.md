# Phase 50: explicit learned-routing hold

The learned route is now represented by a versioned repository policy with a
machine-checked `DISABLE` state and an explicit stronger-model fallback. The
policy lists the evidence and human approval required before enablement. A
regression test prevents accidental activation while the release gates remain
open.
