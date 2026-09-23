# Owner-authorized training use of the generated suite

On 2026-09-23 the owner identified the 5,000 abstain cases as the corpus
approved for further classifier training. The suite contains 5,000 authored
abstain prompts and 600 authored eligible controls. These are repository-
grounded synthetic cases, not captured real Wrench requests. Their labels
have a structural audit but still lack independent human review.

This approval retires `cases.jsonl` as an evaluation set for every head fit
on these cases. Earlier scores remain historical diagnostics of earlier
heads. Any score of a newly fitted head on this same file is a training-set
or regression score, never a fresh accuracy estimate. The separate sealed
`evals/wrench-expanded-v2/final.jsonl` remains untouched and excluded from
training and model selection.

Training must preserve the original case hash
`26fafa2e008ed3b6ee1fefd11293802f47dcdd35b44a295cece1c2a301433ec1`
and record the checkpoint, feature encoding, fitted head, and resource
receipts. A new test suite and real labeled workflow holdout are needed for
readiness. The owner's approval to use this synthetic corpus does not
establish production representativeness or release authorization.
