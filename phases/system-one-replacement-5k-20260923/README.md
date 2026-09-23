# Replacement binary diagnostic, 5,600 authored requests

The original 5,000-abstain suite was owner-approved for training on
2026-09-23 and is retired as an evaluation set for any new head. This
replacement contains **5,000 abstain cases and 600 eligible Wrench controls**
across 160 authored pattern groups. The prompts refer to 50 tracked files
that are disjoint from the original suite's file inventory.

The frozen [case file](cases.jsonl) has SHA256
`831e445d5a5d78e1182fd1d76c3ccc546b9494c487b9bbbb44501540850723ff`.
The [structural audit](audit.json) found 5,600 unique prompts, checked 50
eligible tracked files, and found no exact prompt overlap with the original
suite or the two other unsealed training inputs. It did not read the sealed
final split or call a model or provider.

This is a **synthetic diagnostic**, not captured real Wrench traffic. Cases
share wording patterns, so the prompt count is not an independent workflow
count. The labels have not received independent human review. Keep this
file out of all fitting, threshold selection and calibration. Score a
frozen candidate once, report both abstain recall and eligible coverage,
and retain the broader production gates as separate requirements. A strong
score here alone cannot establish production readiness or Jev parity.
