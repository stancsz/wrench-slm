# Wrench 25k corpus validator runtime repair

Date: 2026-09-23  
Reviewer and repair author: `/root` (same agent; review is not independent)  
Goal: [Wrench 25k quality data](../../goal/wrench-25k-data/GOAL.md)

## Finding and repair

The current validator referenced undefined `group_splits` while assembling its
summary, causing a `NameError` after processing even an invalid manifest. The
summary now counts distinct nonempty `template_id` values from validated train
and development row summaries.

## Verification

Ran:

```powershell
py -3 phases/phase-447-wrench-training-data-corpus/validate_corpus.py --manifest dataset/manifest.json --structural-only
```

Observed exit code 1 and structured JSON `status: FAIL`, with
`unique_template_groups: 0` and explicit manifest/schema and missing-split
errors. It did not crash and reports `sealed_final_read: false`. This is the
expected outcome for this input: `dataset/manifest.json` is the exclusion
manifest for quarantined external sources, not a `wrench.corpus-manifest.v1`
corpus manifest. The command therefore does not establish that an actual
training/development corpus validates.

## Limits and next action

No corpus rows were loaded or created. There are still zero accepted rows, no
valid corpus manifest, and unresolved possible sealed-final exposure. The
validator source and its focused isolation suite need a fresh hash-bound
review before corpus admission. This evaluation was done by the repair author,
so independent verification remains open.
