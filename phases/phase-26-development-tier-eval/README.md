# Phase 26: provisional development evaluation

This phase exercises fresh prompt templates against the final text-only 8- and
16-expert packs and scores the returned text through the independent Wrench
verifier. It is deliberately not the final evaluation: the portfolio remains
`pending_human_approval`, and these synthetic development cases must not be
used to tune the final split or make a quality claim.

`cases.jsonl` contains accepted and boundary-abstention cases from the same
narrow task families, with different wording from the earlier boundary
receipts. `score_tier_receipt.py` checks both the expected status and any named
fallback reason after strict JSON parsing and verifier execution.

The authoritative final gate remains a human-approved, family-and-template-
disjoint split with teacher comparison, retries, latency, memory, and workflow
success. A passing receipt here only proves that the evaluation plumbing ran.

The first comparison is recorded in `comparison.json`. Both final text-only
packs served all ten prompts, but both scored `0/10` exact matches. The outputs
often repeated an incomplete JSON fence, so these artifacts are loadable and
quantized but not behaviorally calibrated. This result keeps the quality gate
open and does not justify increasing expert count as a substitute for
calibration.
