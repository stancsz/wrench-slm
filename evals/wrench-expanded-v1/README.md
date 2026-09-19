# Wrench expanded evaluation suite v1

Status: `DRAFT_PENDING_HUMAN_APPROVAL`

This is the canonical root-level evaluation suite for Wrench. It contains 220
deterministic proposal cases across the six approved task families plus an
explicit out-of-domain negative set.

## Layout

```text
evals/wrench-expanded-v1/
  eligible/<family>.jsonl   # 20 accepted workflow cases per family
  boundary/<family>.jsonl   # 10 boundary or failure cases per family
  out_of_domain/out_of_domain.jsonl # 40 unrelated-task abstention cases
  calibration.jsonl         # 132 cases
  development.jsonl         # 44 cases
  final.jsonl               # 44 draft held-out cases
  cases.jsonl               # canonical all-case view
  verifier-cases.json       # proposal objects and expected verifier outcomes
  manifest.json             # counts, hashes, and limitations
  validation.json           # offline validation receipt
```

The category files are the preferred way to inspect or run one task family.
The split files are the preferred way to build calibration, development, and
held-out evaluation jobs.

Regenerate and validate:

```powershell
py -3 tools/generate_expanded_evaluation.py --output-dir evals/wrench-expanded-v1
py -3 tools/validate_expanded_evaluation.py evals/wrench-expanded-v1/cases.jsonl --root . --output evals/wrench-expanded-v1/validation.json
```

This suite expands coverage but does not itself establish model quality or
statistical power. The final slice remains subject to human review and must
not be used for training, routing selection, or prompt tuning after approval.
