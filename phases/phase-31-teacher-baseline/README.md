# Phase 31: original-teacher baseline

The original `Qwen3.6-35B-A3B-NVFP4` teacher was served through the same
FreeToken path and evaluated on the corrected 28-case fixture from Phase 30.
The raw teacher output uses a generic tool-call dialect (`action` plus
`params`) rather than Wrench's strict top-level `wrench.proposal.v1` object.
Therefore the raw strict score is 0/28 and is a serialization mismatch, not a
capability conclusion.

For a semantic baseline only, `score-teacher-v4-adapted.json` applies the
explicit deterministic adapter in `tools/score_tier_receipt.py`. It maps the
known generic fields into the Wrench proposal schema and then runs the normal
independent verifier:

- adapted verifier outcomes: 12/28
- adapted exact proposal objects: 7/28
- teacher FTW directory: 21,809,952,707 bytes, approximately 20.31 GiB

The adapter is not enabled in Wrench runtime. This baseline demonstrates that
the pruned 3--4 GiB packs are being compared against a stronger source path,
while keeping serialization and model capability separate.
