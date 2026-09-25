# Local work envelope diagnostic protocol

Status: preregistered for one offline deterministic-route replay. No model,
provider, client, training, or real-task capture is in scope.

## Question

Which bounded action families can the current local deterministic proposal
router recognize exactly, and does it safely miss or abstain on boundary and
out-of-domain cases?

## Frozen input and exclusions

- Input: `evals/wrench-expanded-v2/cases.jsonl` at the committed measurement
  revision, using only rows labelled `calibration` or `development`.
- Exclusion: every row labelled `final` is excluded before scoring. The final
  split remains quarantined and contributes no prompt, target, count, or score
  to the selected task set.
- Classes: `read_file`, `read_lines`, `literal_search`, `git_read_status`,
  `health_read`, `patch_draft`, and `out_of_domain`; eligible, boundary, and
  out-of-domain rows remain reported separately.
- The task fixture is Wrench-authored and synthetic. Its exposed calibration
  and development prompts do not estimate real-work quality or generalization.

## Measurement

Run `tools/measure_local_work_envelope.py` against the current repository root.
For an expected accepted row, pass only when the deterministic router's full
proposal object exactly equals the frozen target. For an expected abstention,
pass when the router explicitly abstains with the expected reason or returns
no proposal, which hands work to a fallback. Any proposal on an abstain row is
an unsafe proposal. A family screen passes only when all of its eligible rows
match exactly and it makes no proposal for an abstain row.

The run does not execute actions, call the independent verifier, or assess
whether a fallback succeeds. `patch_draft` means a review-only patch proposal;
it never applies a source edit. Record case counts, exact proposal matches,
false abstentions, safe fallback handoffs, unsafe proposals, reason mismatches,
and route latency by family and case category. Keep frontier-token savings N/A.

## Admission and stop rules

This is one bounded, local, deterministic route-only diagnostic with a small
JSON receipt under `C:\wrench-slm-data\artifacts\wrench-local-acceptability`.
Before writing it, run the storage status and reserve commands in `AGENTS.md`,
verify the destination volume has room, and preserve at least 10% RAM/VRAM.
Stop on any unexpected split, invalid case schema, route exception, or storage
reserve failure. Do not train, tune, or alter the route against these exposed
cases. Keep this result out of utility, customer, training, and production
aggregates.
