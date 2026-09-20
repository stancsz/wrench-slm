# Phase 79: safety checkpoint portable-package audit

Status: `REJECTED_LONG_CONTEXT_CONFIG`

The BF16 safety-calibrated 8E checkpoint was materialized as a candidate
portable package and passed weight copying, but structural validation rejected
it because its checkpoint configuration declares `max_position_embeddings` of
262,144. The Wrench native package contract requires at least 2,000,000 native
positions before a 4M runtime overlay can be considered a release candidate.

This checkpoint remains useful as a worker-quality diagnostic. Its 220-case
replay is recorded in Phase 78, but it cannot replace the public native
long-context artifact without a long-context-compatible training or weight
conversion step. No package from this failed materialization was published.

Receipt: `portable-package-validation.json`
