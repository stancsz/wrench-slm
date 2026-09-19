# Phase 62: full 220-case Wrench evaluation

Status: `COMPLETED_DIAGNOSTIC_EVALUATION`

This phase ran the canonical `evals/wrench-expanded-v1/cases.jsonl` suite
through the current 8E experimental artifact. It is the first full-suite run;
the earlier 28-case receipts are not the full evaluation.

## Run identity

- Model: `Wrench-Code-4B-Qwen3.6-8E-Safety-Experimental`
- Endpoint: `http://127.0.0.1:28208/v1/chat/completions`
- Input: `evals/wrench-expanded-v1/cases.jsonl`
- Input SHA-256: `54d06dff69c2a330fbba5ed13ba22817c287cb7ec384a59458eb4f5e291bb45a`
- Prompt policy: adaptive safety few-shot
- Receipt: `receipt-8e.json`

## Full-suite result

| Metric | Result |
| --- | ---: |
| Requests completed | 220 / 220 |
| Unique case IDs | 220 / 220 |
| Transport failures | 0 |
| Overall correct outcomes | 90 / 220 |
| Eligible exact proposal matches | 30 / 120 |
| Boundary correct outcomes | 20 / 60 |
| Out-of-domain correct abstentions | 40 / 40 |
| Prohibited accepts | 15 |
| Model accepted outputs | 84 / 220 |
| Wall time | 539.780 seconds |

## Eligible-family results

| Family | Exact matches |
| --- | ---: |
| `git_read_status` | 10 / 20 |
| `health_read` | 0 / 20 |
| `literal_search` | 6 / 20 |
| `patch_draft` | 0 / 20 |
| `read_file` | 6 / 20 |
| `read_lines` | 8 / 20 |

Health-read eligible cases could not be treated as live-service evidence in
this run because the allowlisted health service was not part of the evaluation
setup. The raw model output is retained, but live health execution must be
rerun separately before using those cases as workflow evidence.

This is diagnostic evidence only. The suite is still marked
`DRAFT_PENDING_HUMAN_APPROVAL`, and the 15 prohibited accepts mean this run is
not a release pass.
