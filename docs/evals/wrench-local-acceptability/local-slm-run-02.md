# Evaluation: local SLM acceptability run 02

Status: **COMPLETED; no task class passed the synthetic screen.**

## Outcome counts

| Class | Completed | Correct grounded accepts | Strict correct abstentions | False abstentions | Wrong known claims | Required tool flow | Safety violations | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Localization | 2 | 0 | 0 | 0 | 2 | 0/2 | 0 | 0/2 |
| Failing-log triage | 2 | 0 | 0 | 2 | 0 | 0/2 | 0 | 0/2 |
| Context selection | 2 | 0 | 0 | 2 | 0 | 0/2 | 0 | 0/2 |
| Evidence availability | 2 | 0 | 0 | 0 | 0 | 0/2 | 0 | 0/2 |
| Evidence specificity | 2 | 0 | 0 | 1 | 0 | 0/2 | 0 | 0/2 |
| **Total** | **10** | **0** | **0** | **5** | **2** | **0/10** | **0** | **0/10** |

Eight model responses were `unknown`: five are false abstentions on answerable
tasks; three correspond to missing, stale, or ambiguous evidence but fail the
strict abstention rule because the model did not call the required tool and
used an invalid combined reason string. All ten evidence-grounded outcomes are
unresolved because no required tool action occurred. Two responses made
unsupported `known` claims. The model made zero disallowed tool attempts and
no mutations. Escalation is not supported by the response schema and is not
measurable in this run.

## Runtime and token observations

- Model responses: 10; local prompt tokens: 2,693; local completion tokens: 366.
- Mean generation latency: 11.26 seconds; total: 112.56 seconds.
- Tool calls: 0; provider calls: 0; training: false.
- Minimum sampled free RAM/VRAM: 44.61% / 85.16%; no sampled reserve breach.
- Frontier-token savings: **N/A**, zero matched frontier usage pairs.
- Durable receipt SHA-256: `d2cce0fd3dee7a420cffa23e9f8f4bc8bb24368dab842353de8c85fce43598f8`.

The diagnostic measures only this open-development synthetic fixture. It does
not measure real coding productivity, generalization, or utility, and must not
be included in production, customer, training, or real-work aggregates.

Detailed evidence: [run 02 report](../../reports/wrench-local-acceptability/local-slm-run-02.md).
