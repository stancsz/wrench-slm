# Usefulness V22 repair result

Updated: 2026-09-10

Status: NO-GO at the development gate. The sealed V22 evaluation was not run.
No cloud workflow or production endpoint was used.

## Purpose and boundary

V22 was a separate repair candidate for the V21 fresh-quality failure. It was
intended to improve contextual search, complete draft bodies, and invalid-range
refusal without changing the immutable V21 package or reusing the exposed V2
evaluation set. This is an authored developer-tool population, not production
traffic, and its executable labels are fixture outcomes rather than recovered
user outcomes.

## Frozen data and preflight

The V22 data is under `data/pilots/usefulness-v22` and declares version
`usefulness-pilot-v22-repair`.

| Split | Tasks | Families | SHA-256 |
| --- | ---: | ---: | --- |
| train | 2,816 | 176 | `d6fabd0b1335dca342fbb21328c947cb5938d0c5406749d331e9ef62b95b3df0` |
| development | 110 | 22 | `4f77b2fd8b208a2b2cd62e0b5b6c2ff2c712b80fe56e1523f0eddc1275a7a3d6` |
| evaluation | 600 | 120 | `54e8bbf9f2a1c22217ae4b1067af1c8f8e32b76354e274da8e916ff3082fd99c` |

The V22 evaluation set was not opened. The preflight and audit observed:

- 3,526/3,526 executable gold rows checked with zero failures.
- Zero family overlap and zero public-input overlap across splits.
- Zero public/private-field leakage.
- All 11 task kinds and both languages present.
- Maximum training prompt and completion lengths within the declared limits.

## Training and checkpoint selection

The candidate was trained with a V21 initializer but a reset optimizer. The V21
package remained unchanged.

```powershell
.venv\Scripts\python.exe -X utf8 scripts\pilot_train.py `
  --train data\pilots\usefulness-v22\train.jsonl `
  --val data\pilots\usefulness-v22\development.jsonl `
  --output artifacts\model-release\pro-training-v22 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 2e-6 --seed 42 --checkpoint-every 100 `
  --initialize-adapter artifacts\model-release\package-selected-v21\weights
```

The completed receipt records 300 steps, 4,800 examples seen, validation loss
`0.0021693105`, and the V21 initializer SHA-256
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.

All three predeclared checkpoints were evaluated on development only. The
selection rule was highest exact rate, then lowest validation loss, then
earliest step. It selected step 200, but selection did not approve release.

| Checkpoint | Exact | Routine exact | Routine outcome | Health | Quality gates |
| --- | ---: | ---: | ---: | ---: | --- |
| 100 | 105/110 | 65/70 | 65/70 | 7/10 | FAIL |
| 200 | 107/110 | 67/70 | 67/70 | 7/10 | FAIL |
| 300 | 107/110 | 67/70 | 67/70 | 7/10 | FAIL |

The selected step 200 passed raw protocol validity, routine exactness, routine
checked outcomes, language floors, abstention checks, and zero fixture
changes. It failed the required task-slice floor because health was 7/10,
below the 90% minimum. Therefore the candidate failed the quality gate even
though its aggregate development exact rate was 97.27%.

## Failure analysis

The three health misses are all English instances from one development family.
The public prompt says to use the selected loopback endpoint, and the URL is
visible in `prior_results`. The expected action is the allowlisted `curl`
health request. The model instead proposed `read_file` against the selected
configuration record. The five Chinese health cases and the other ten task
kinds passed on development.

This is a model behavior failure, not an incomplete-run or protocol failure:
the raw outputs were valid, the expected URL was public, and the fixture
executor recorded the wrong accepted action without changing files.

## Decision

V22 is a trained candidate, not a releasable candidate. Do not package it, open
the V22 sealed evaluation, run a cloud comparison, or deploy it. The exact
receipts are:

- `artifacts/model-release/pro-training-v22/run.json`
- `artifacts/model-release/v22-development-step100/summary.json`
- `artifacts/model-release/v22-development-step200/summary.json`
- `artifacts/model-release/v22-development-step300/summary.json`
- `artifacts/model-release/selection-v22/selection.json`
- `artifacts/model-release/selection-v22/REPORT.md`

The V21 fresh-quality NO-GO remains unchanged. V22 shows that the repair data
improved the previously observed search, draft, and invalid-range weaknesses on
development, but it did not meet the all-slice reliability contract. This is
not evidence of production effectiveness.

## If another candidate is explicitly authorized

Do not increase the V22 training budget or tune against these three rows. Create
a new V23 contract with new train, development, and sealed evaluation families.
Keep V2 and V22 evaluation rows out of V23 training and checkpoint selection.
Add balanced English health examples that vary the wording around a selected
loopback endpoint, while keeping configuration reads and decoy resources as
hard negatives. Ensure the URL remains derivable from public context and audit
the labels before training.

Use the same fixed recipe first: rank 16, alpha 32, dropout 0.05, seven
projection targets, BF16 CUDA, 1,536 maximum input tokens, seed 42, and a
declared step budget. Evaluate every checkpoint on V23 development, then stop
unless all of these pass:

- raw protocol validity at least 99.5%;
- routine exactness at least 95%;
- checked routine outcomes at least 95%;
- every routine kind at least 90%, including health;
- English and Chinese routine slices at least 90%;
- ambiguity abstention at least 95%;
- exact zero acceptance for unsupported, missing-tool, and invalid-range cases;
- zero unauthorized execution and zero fixture changes.

Only after a candidate passes development may a new sealed set be scored. Only
after the sealed set passes may packaging, runtime benchmarking, fixed-model
cloud preflight, or a three-arm workflow comparison resume.
