# Phase 34: matched workflow-arm protocol

Phase 34 adds a receipt-only evaluator for three matched arms:

1. cloud-only teacher execution,
2. rules plus identical teacher fallback,
3. learned Wrench plus identical teacher fallback.

The evaluator requires one trace manifest with the same trace IDs and task
families for all three arms. It computes final success, prohibited accepts,
unexpected mutations, stronger-model token use, nearest-rank p95 latency, and
paired bootstrap intervals for learned token savings against both comparators.

It refuses to score a release conclusion unless the manifest explicitly carries
`authorization: approved_real_workflow`. No real traces were added in this
phase, and no production or token-savings claim follows from the protocol tests.

