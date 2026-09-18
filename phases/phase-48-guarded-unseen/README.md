# Phase 48: guarded broad unseen comparison

Both quantized tiers were evaluated with the adaptive prompt policy on the
same 28-case explicit-schema fixture after the request-intent guards.

The larger 16E tier accepted 14/28 cases, matched 22/28 expected outcomes,
and produced zero prohibited accepts in 71.416 seconds. The compact 8E tier
initially accepted 12/28 and matched 18/28, but had one prohibited traversal
rewrite. After the traversal guard it accepted 11/28, matched 19/28, and
produced zero prohibited accepts in 54.202 seconds.

The compact tier is faster and smaller, while the larger tier is more useful
on this fixture. Both results are synthetic local diagnostics, not production
or real-workflow evidence. The receipts and before/after comparison are in
`comparison.json`.
