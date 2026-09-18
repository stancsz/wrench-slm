# Phase 2: dataset audit

This phase audits the locally staged JSONL inputs before any training decision.
The raw files are deliberately ignored by Git. The audit records file identity,
JSON validity, structure, and coarse content indicators without copying samples
into a release artifact.

Run:

```powershell
py -3 tools/audit_dataset.py dataset `
  --output phases/phase-2-dataset-audit/dataset-audit.json
```

The audit is not a quality or licensing approval. A human still needs to review
source terms, rights, task-family fit, contamination risk, and redaction before
the files can become calibration or training data.
