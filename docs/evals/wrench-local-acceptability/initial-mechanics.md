# Evaluation: initial local acceptability mechanics

Status: **PASS for synthetic mechanics only; SLM and utility gates not run.**

## Frozen scope

- Fixture: `tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json`
- Fixture SHA-256: `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`
- System: `run_e0_rule_route`, provider-free rule route at current repository
  HEAD `5267dadecf3e9d2d8c38160a633e071448c7b263`
- Oracle: independent source-derived rules plus frozen expected answers in the
  manifest and its reviewed receipt
- Split/use: open development, authored synthetic mechanics only

## Results

| Outcome | Count |
| --- | ---: |
| Correct completed answer | 7 |
| Correct abstention | 3 |
| Wrong/prohibited accept | 0 |
| Incorrect abstention | 0 |
| Unresolved | 0 |
| Total | 10 |

Class breakdown and exact scope are in the [measurement report](../../reports/wrench-local-acceptability/initial-mechanics.md).
The denominator is ten synthetic cases, not ten real coding tasks. Do not
compute a production acceptance rate from it.

## Verification

- Eight focused test functions invoked directly: passed.
- Ten actual rule-route case outputs matched frozen mechanics/task oracles.
- Three required unknown cases (`evidence-missing`, `evidence-stale`,
  `evidence-ambiguous`) abstained; the specific-source case completed.
- Pytest was unavailable in both checked Python environments, so no pytest
  run is claimed. Direct invocation is recorded in the report.
- No inference, client prompt, provider call, training, or network request.

## Gates still open

- Local SLM acceptability: no local weights, pinned inference runtime, or
  runtime-matched tokenizer was identified.
- Real-task quality: no consented matched-task utility corpus or independent
  real-outcome oracle is admitted.
- Token savings: no paired downstream requests or complete frontier usage
  accounting; measured savings are **not established**, not zero.
- Latency/throughput: not measured.

This evaluation is not E0 or E4 acceptance and does not authorize model
download, training, provider use, or production routing.
