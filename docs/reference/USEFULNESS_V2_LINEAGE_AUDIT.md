# Usefulness V2 lineage and overlap audit

Updated: 2026-09-10

Status: PARTIAL COVERAGE, NO INDEPENDENCE PROOF.

The reproducible receipt is
`artifacts/model-release/usefulness-v2-lineage-audit.json`.

## Scope and result

The audit compared the 600-row V2 evaluation split against every readable
JSONL file under `data` and `artifacts/model-release`, excluding the target
evaluation file. It also inspected every retained `pro-training-*/run.json`
receipt to resolve its declared training source.

- V2 evaluation: 600 rows and 120 families.
- Exact public-input overlap found: zero across all readable comparison files.
- Heuristic normalized-prompt overlap found: zero across all readable comparison files.
- Training receipts inspected: 25.
- Declared training sources resolved locally: V20, V21, and V22.
- Declared training sources missing locally: 22.
- Authorship separation verified: no.
- Complete ancestor coverage verified: no.

The exact zero-overlap result is useful evidence for the files that remain
available. It does not prove semantic independence, because normalization and
exact matching cannot detect paraphrases, shared generator templates, or
unrecorded author consultation. The missing historical source files prevent a
complete ancestry audit.

## Recovery check

On 2026-09-10, the missing declared source paths were also checked against all
file paths present in the repository's Git history and against matching
JSONL, manifest, and generator paths under `C:\Users\stanc\github`. No
additional declared ancestor source was found. This confirms that the missing
sources are not merely absent from the current checkout. It does not recover
their contents, establish independent authorship, or replace the requirement
to preserve complete source data for a future pilot.

## Reproduction

```powershell
.venv\Scripts\python.exe -X utf8 scripts\audit_usefulness_v2_lineage.py `
  --evaluation data\pilots\usefulness-v2\evaluation.jsonl `
  --data-root data `
  --training-root artifacts\model-release `
  --output artifacts\model-release\usefulness-v2-lineage-audit.json
```

This receipt should be carried forward as a limitation. It must not be
rewritten as proof of independent authoring. A future pilot needs author
separation records and complete ancestor source retention before its
independence claim can be upgraded.
