# Local work envelope diagnostic 01

Date: 2026-09-24 (America/Edmonton)

## Result

The current deterministic router passed its exact proposal screen on all six
bounded action families in the calibration/development split. It matched all
96 eligible proposal objects exactly, handled all 48 boundary cases without
an unsafe proposal, and abstained correctly on all 32 out-of-domain cases.
There were zero case failures and zero unsafe proposals across 176 scored
cases.

| Local action family | Eligible proposals | Exact | Boundary abstentions | Unsafe proposals | Screen |
| --- | ---: | ---: | ---: | ---: | --- |
| `read_file` | 16 | 16 | 8/8 | 0 | Pass |
| `read_lines` | 16 | 16 | 8/8 | 0 | Pass |
| `literal_search` | 16 | 16 | 8/8 | 0 | Pass |
| `git_read_status` | 16 | 16 | 8/8 | 0 | Pass |
| `health_read` | 16 | 16 | 8/8 | 0 | Pass |
| `patch_draft` | 16 | 16 | 8/8 | 0 | Pass, review-only draft |
| Out of domain | 0 | N/A | 32/32 abstained | 0 | Escalate/abstain |
| **Total** | **96** | **96** | **80/80** | **0** | **176/176 cases passed** |

## Interpretation

This supports a narrow local envelope for generating exact, bounded proposals
in the six listed families. The route recognizes request shape and target
parameters. It did not execute file, line, search, Git, or health operations;
it did not invoke the independent verifier; and it did not apply any patch.
The `patch_draft` result only covers review-only proposals. Thus this is a
proposal-screen pass, not evidence that a complete local coding task finished
correctly.

The 176 cases are Wrench-authored synthetic prompts drawn from exposed
calibration and development splits. They measure route mechanics and do not
estimate real-work quality or generalization. All rows marked `final` were
excluded from scoring. Keep this result out of utility, customer, training,
and production aggregates.

This route-only result does not change the local SLM decision. The pinned
Qwen3.5-0.8B diagnostic scored 0/10 and made no required evidence-tool calls;
no generative SLM task class is acceptable on current evidence. Frontier-token
savings remain N/A, with zero valid matched frontier usage pairs.

## Identity and accounting

- Protocol: [local work envelope diagnostic protocol](../../evals/wrench-local-acceptability/local-work-envelope-protocol.md), committed before execution.
- Input: `evals/wrench-expanded-v2/cases.jsonl`; selected calibration/development subset: 176 rows.
- Candidate revision: `5e9ce91`; router source SHA-256: recorded in the receipt.
- Selected case subset SHA-256: recorded in the receipt; final rows were not scored or included in that digest.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-work-envelope-20260924-01.json`.
- Receipt SHA-256: `138fee0c901bc09ab815aabb0c304b73bf59d9218ca28102660fac526d8547fe`.
- Actions executed: 0. Verifier runs: 0. Model calls: 0. Provider calls: 0.
- Route elapsed time: recorded in the receipt; this measures only local parsing and proposal construction.
- Frontier-token savings: N/A.

## Decision

For local deterministic routing, the measured proposal envelope currently
includes bounded exact file reads, line reads, literal searches, read-only Git
status proposals, allowlisted health-read proposals, and review-only patch
draft proposals. Requests in the measured out-of-domain set were rejected.
Every proposal still requires bounded execution and the independent verifier
before it can count as a completed task.

Do not start training from this result. The useful next local step is a separate
offline evaluation that runs proposals through the verifier and safe fixture
executor, with frozen task outcomes. Do not claim downstream token savings
until matched frontier receipts exist.
