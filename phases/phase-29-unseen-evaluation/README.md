# Phase 29: unseen packed-tier evaluation

This phase evaluates the two calibrated text-only NVFP4 FTW packs on a new
28-case synthetic evaluation set generated independently from the calibration
fixture. The set contains accepted bounded reads, line reads, literal searches,
read-only Git and health actions, review-only patch drafts, and boundary
abstentions. The corrected fixture has unique case IDs and its external hash
is `fece7c33e933be21ac067aa0a21546654602b5cc6ef872920f1e5546647de87f`.

The first v1 receipt is retained for traceability but is invalid for comparison:
the generator assigned the same ID to two health cases, allowing an expected
row collision in the scorer. All results below use the corrected v2 fixture.

Results are development-only. `exact_matches` means the independent verifier
returned the expected accepted or abstained status and fallback reason.
`proposal_exact_matches` is stricter and requires the model JSON object to
match the expected proposal exactly.

- 8E FTW: 8/28 verifier outcomes, 7/28 exact proposal objects.
- 16E FTW: 9/28 verifier outcomes, 7/28 exact proposal objects.

The 16E tier has a small observed edge on this fixture, but both scores are
well below a release gate. No human portfolio approval, real workflow value,
production enablement, or quality claim follows from this synthetic result.
