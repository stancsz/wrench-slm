# Phase 29: unseen packed-tier evaluation

This phase evaluates the two calibrated text-only NVFP4 FTW packs on a new
28-case synthetic evaluation set generated independently from the calibration
fixture. The set contains accepted bounded reads, line reads, literal searches,
read-only Git and health actions, review-only patch drafts, and boundary
abstentions. Its external fixture hash is
`d84b9a4c4345d52c4518e7ec85b10ef47baf4cffe98c71983ec9a907f8d5e67f`.

Results are development-only. `exact_matches` means the independent verifier
returned the expected accepted or abstained status and fallback reason.
`proposal_exact_matches` is stricter and requires the model JSON object to
match the expected proposal exactly.

- 8E FTW: 8/28 verifier outcomes, 5/28 exact proposal objects.
- 16E FTW: 9/28 verifier outcomes, 6/28 exact proposal objects.

The 16E tier has a small observed edge on this fixture, but both scores are
well below a release gate. No human portfolio approval, real workflow value,
production enablement, or quality claim follows from this synthetic result.
