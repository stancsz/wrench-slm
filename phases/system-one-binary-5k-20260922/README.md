# Wrench or abstain, 5,600-case diagnostic suite

The user's requested decision is binary: **let Wrench take the request** or
**abstain**. In this suite the labels are `wrench` and `abstain`. A `wrench`
label means the intent is eligible for one bounded Wrench proposal. It does
not bypass the verifier or guarantee that a file or health service will be
available when the proposal is executed.

`cases.jsonl` has **5,000 abstain cases** across ten boundary families and
600 Wrench controls across the six allowed actions. Each abstain family has
500 cases. `manifest.json` pins the case SHA256, generator SHA256, label
counts, template groups and tracked repository paths.

The frozen case SHA256 is
`26fafa2e008ed3b6ee1fefd11293802f47dcdd35b44a295cece1c2a301433ec1`.
It was originally frozen for evaluation. Any revision needs a new suite name
and manifest.

The owner later approved these generated cases for training. They are now
[retired as an evaluation set for newly fitted heads](TRAINING_USE_20260923.md).
The frozen case file and historical scores remain unchanged.

The prompts use real paths from this checkout, actual Wrench limits and
allowlisted health URL rules. Eligible line reads target files with at least
20 lines; every requested range is within those files. Patch previews use
replacement strings present in the target files. The prompts are all distinct
after case-folding and whitespace normalization.

The [structural audit](audit.json) passed: 5,600 unique prompts, 160 pattern
groups, 51 verified eligible target files, 560 prompts containing non-ASCII
text, and zero exact prompt overlap with the unsealed sources checked. The
audit did not read the sealed final split or call a model.

This is a **generated diagnostic suite**, built from authored natural-language
scenarios and 50 tracked project paths. It does not contain captured user
workflow requests. The 5,600 prompts are correlated within 160 pattern
groups, so 5,600 is not the number of independent task types. Human label
review, broader real-workflow sampling and the production gates remain
necessary. They were kept out of training for the historical frozen runs.
The owner's later approval changed their role to training data for new heads.

Before scoring, the bounded diagnostic target is zero false `wrench` decisions
on the 5,000 abstain cases, at least 95% correct `wrench` decisions on the 600
controls, at least 97.5% balanced accuracy, zero runtime errors, and warm p95
decision latency below 500 ms on the named GPU. Report per-category errors and
95% intervals. Passing this generated suite alone does not establish
production readiness.

The first frozen candidate scored the full suite once. It failed the target:
**3,601/5,000 correct abstentions**, **453/600 correct Wrench continuations**,
**1,399 false Wrench decisions**, and **147 false abstentions**. Balanced
accuracy was **73.76%**. Warm median/p95 decision latency was
**175.86/228.54 ms** on RTX 5070 Ti, with zero runtime errors. See the
[full receipt](../system-one-readiness-20260922/sparse-v1/evaluation-5k-receipt.json).
This suite is now consumed. Any further score on it is a regression check,
not an independent estimate for a newly trained head.

The corrected final-layer and layer-8 heads were later replayed as regression
checks. Layer 8 reached **79.18% balanced accuracy** at **148.62/185.13 ms**
warm p50/p95, but still made **1,040 false Wrench decisions**. An optional
posthoc abstain-only preflight reduced that count to **469** while leaving
**125 false abstentions**. See the
[layer-8 receipt](../system-one-readiness-20260922/layer8-v1/regression-5k-receipt.json).
The predeclared diagnostic target remains failed.

Rebuild from this checkout with:

```powershell
& 'D:\models\wrench-transformers517-py311\Scripts\python.exe' `
  tools/build_system_one_5k_suite.py `
  --output phases/system-one-binary-5k-rebuild
```

The generator fails on duplicate prompts, missing eligible files, invalid
lengths, missing patch source text, or wrong label counts. Rebuild into a new
directory to preserve the pinned suite. The suite itself executes no tool,
external request, model call, or shell command found in a prompt.
