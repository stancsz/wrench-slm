# Phase 56: fail-closed experimental tier resolver

The harness now exposes `select_experimental_tier`, which resolves only the
verified compact 8E or larger 16E catalog entry. It refuses unknown
preferences, missing artifacts, invalid catalog status, quality claims, or any
routing policy other than `learned_routing: DISABLE`. The result is explicitly
`EXPERIMENTAL_ONLY` and carries the stronger-model fallback policy.
