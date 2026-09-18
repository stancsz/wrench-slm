# Phase 4: task portfolio and evaluation boundary

This is the proposed frozen portfolio for Wrench calibration and held-out
evaluation. It is intentionally narrow and remains `pending_human_approval`.
No training or pruning result may change these task families after evaluation
results are known.

The split is family-disjoint: 60% calibration, 20% development, and 20% final
evaluation. The final slice must remain unseen during routing, pruning, and
calibration decisions. English and Chinese wording are both in scope, but the
verifier and resource constraints are language-independent.
