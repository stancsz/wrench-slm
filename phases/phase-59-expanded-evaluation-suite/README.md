# Phase 59: expanded evaluation suite

Status: `DRAFT_PENDING_HUMAN_APPROVAL`

This phase records the design and validation of 220 deterministic evaluation
cases for the Wrench proposal boundary. The canonical case files now live at
the repository root under `evals/wrench-expanded-v1/`. This phase directory is
the historical record, not a second copy of the suite.

## Composition

The suite contains 20 eligible cases and 10 boundary cases for each approved
task family, plus 40 explicit out-of-domain negatives:

- bounded file reads
- bounded line reads
- literal search
- read-only Git status
- allowlisted local health reads
- review-only patch drafts
- unrelated coding, deployment, shell, publication, authentication, and destructive tasks

That produces 120 eligible cases, 60 boundary cases, and 40 out-of-domain
cases. The family-balanced split is 132 calibration, 44 development, and 44
final cases. Template groups
are kept within one split so the final slice can remain unseen during routing,
pruning, and prompt decisions.

## Canonical files

- `evals/wrench-expanded-v1/cases.jsonl`: all 220 model-evaluation cases
- `evals/wrench-expanded-v1/eligible/<family>.jsonl`: eligible cases grouped by family
- `evals/wrench-expanded-v1/boundary/<family>.jsonl`: boundary cases grouped by family
- `evals/wrench-expanded-v1/out_of_domain/out_of_domain.jsonl`: unrelated-task abstention cases
- `evals/wrench-expanded-v1/{calibration,development,final}.jsonl`: split views
- `evals/wrench-expanded-v1/manifest.json`: counts, hashes, split rules, and limitations
- `evals/wrench-expanded-v1/validation.json`: offline validation receipt

Regenerate with:

```powershell
py -3 tools/generate_expanded_evaluation.py --output-dir evals/wrench-expanded-v1
py -3 tools/validate_expanded_evaluation.py evals/wrench-expanded-v1/cases.jsonl --root . --output evals/wrench-expanded-v1/validation.json
```

The health-read accepted cases are marked `proposal_only` during offline
validation because they require a live allowlisted service. The suite still
requires live execution receipts before any service-quality claim.

This suite does not establish statistical power for the 15-point improvement
gate by itself. Human review must approve the task labels, case independence,
volume weights, and final split before the final slice becomes authoritative.
No case may enter training, expert selection, or prompt tuning after approval.
