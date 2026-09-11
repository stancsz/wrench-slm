# V2 fresh-quality result

Date: 2026-09-10

Decision: **NO-GO for the immutable V21 package on the V2 local-quality
gate.** The V21 adapter is materially better than the unchanged base and the
current deterministic helper, but it is not reliable enough on this fresh
population to justify a cloud workflow comparison or a usefulness claim.

This is a bounded authored Windows result. It is not a production accuracy
estimate, a general agent benchmark, or evidence about arbitrary shell safety.

## Frozen inputs and preflight

- Data: `data/pilots/usefulness-v2`.
- Evaluation: 600 cases, 120 wording families, five instances per family.
- Language: 300 English and 300 Chinese cases.
- Kinds: all 11 contract kinds.
- Evaluation SHA-256: `f7cd33a3f546964a6d6eb6b49d90a3133713e0bffb4499c8e593c5eb7cce3351`.
- Data preflight: `data/pilots/usefulness-v2/preflight.json`, status `passed`.
- Gold rows independently exercised in disposable fixtures: 710/710.
- Public private-field audit: passed.
- Cross-split family overlap: 0.
- Cross-split exact public-input overlap: 0.
- Exact overlap with the historical roots scanned: 0.
- Invalid-range categories: 20 zero or negative, 20 reversed, 10 beyond EOF.

The labels are generated executable fixture labels and were checked by a
separate audit pass. They are not recovered production outcomes, and the
exact-input overlap check does not prove semantic independence.

## Receipts

The exact package, base, and rules receipts are:

- V21 package: `artifacts/model-release/v21-usefulness-v2-quality`.
- Unchanged pinned base: `artifacts/model-release/base-usefulness-v2-quality`.
- Deterministic helper: `artifacts/model-release/rules-usefulness-v2-quality`.
- Protocol: `docs/reference/USEFULNESS_PILOT_PROTOCOL_V2.md`.

The V21 package identity in the run receipt is adapter SHA-256
`6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`, package
manifest SHA-256
`219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`, and
base revision `7ae557604adf67be50417f59c2c2f167def9a775`.

Reproduction commands, from the repository root, are:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/audit_usefulness_v2_data.py --data data/pilots/usefulness-v2 --historical-root artifacts/archive/data/pilots --historical-root data/releases
.venv/Scripts/python.exe -X utf8 scripts/release_eval.py --data data/pilots/usefulness-v2 --split evaluation --package artifacts/model-release/package-selected-v21 --base-path artifacts/model-release/base-dependency-v1 --output artifacts/model-release/v21-usefulness-v2-quality --execute
.venv/Scripts/python.exe -X utf8 scripts/release_eval.py --data data/pilots/usefulness-v2 --split evaluation --output artifacts/model-release/base-usefulness-v2-quality --execute
.venv/Scripts/python.exe -X utf8 scripts/rules_eval_v2.py --data data/pilots/usefulness-v2 --split evaluation --output artifacts/model-release/rules-usefulness-v2-quality
```

The package ran on an NVIDIA GeForce RTX 5070 Ti with PyTorch 2.9.1+cu128,
Transformers 4.57.1, and PEFT 0.20.0. No cloud calls or workspace writes were
part of these quality runs.

## Results

| Evaluator | Exact proposals | Raw valid | Routine exact | Routine checked outcome | Fallback exact | Fixture changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V21 package | 453/600 (75.5%) | 599/600 (99.83%) | 245/385 (63.64%) | 265/385 (68.83%) | 208/215 (96.74%) | 0 |
| Pinned base | 10/600 (1.67%) | 458/600 (76.33%) | 10/385 (2.60%) | 17/385 (4.42%) | 0/215 (0%) | 0 |
| Deterministic helper | 300/600 (50.0%) | 600/600 (100%) | 90/385 (23.38%) | 90/385 (23.38%) | 210/215 (97.67%) | 0 |

The V21 result is a real improvement over both baselines on routine outcomes,
but it misses the required 95% routine exact and outcome gates by a wide
margin. The helper is faster because it has no model load or generation cost;
that latency is not a like-for-like neural-runtime comparison.

V21 local prediction latency was 1.179 seconds p50, 2.669 seconds p95, and
3.033 seconds p99. Peak CUDA allocation was 1,099,017,216 bytes and peak
reserved memory was 1,195,376,640 bytes. These are serial observations on one
machine, not throughput or service guarantees.

## Failure breakdown

| Kind | Cases | Exact | Checked outcome | Accepted proposals | Observation |
| --- | ---: | ---: | ---: | ---: | --- |
| config | 55 | 45 | 45 | 55 | Ten wrong accepted calls |
| lines | 55 | 50 | 50 | 54 | One abstention and four wrong accepted calls |
| search | 55 | 0 | 20 | 55 | All exact calls failed; some quoted or contextual paths still executed correctly |
| git_status | 55 | 52 | 52 | 55 | Three wrong accepted calls |
| git_log | 55 | 55 | 55 | 55 | Strong slice |
| health | 55 | 43 | 43 | 55 | Twelve wrong accepted calls |
| draft | 55 | 0 | 0 | 27 | Twenty-eight abstentions; accepted drafts did not match the complete requested body |
| ambiguous | 55 | 55 | 55 | 0 | Correct abstention slice |
| unsupported | 55 | 55 | 55 | 0 | Correct abstention slice |
| missing_tool | 55 | 55 | 55 | 0 | Correct abstention slice |
| invalid_range | 50 | 43 | 43 | 7 | Seven invalid requests were accepted instead of abstaining |

The routine accepted-call error was 91/356 accepted routine proposals. The
negative-case false-acceptance problem was concentrated in invalid ranges:
7/50 invalid-range requests received an accepted action. The workspace and
all disposable fixtures remained unchanged, so the containment boundary held
for this run even though proposal correctness did not.

English and Chinese exact rates were similar overall, 225/300 and 228/300.
The failure is therefore not explained by a simple language-only collapse.

## Interpretation and stop condition

V21 is effective for a narrower, familiar subset of the contract, especially
Git subject lookup and the explicit abstention categories. It is not effective
enough right now for the broader fresh-request claim in `goal.md`. A 75.5%
exact rate and 68.8% routine checked outcome rate are incompatible with the
predeclared 95% progression gate. Historical V8 scores cannot override this
result because those suites informed ancestor corrections.

The V2 cloud workflow comparison is blocked. Do not run `scripts/pilot_run.py`
against a paid or production endpoint from this result, and do not relabel
the failed V2 set as development data. Do not fine-tune V21 on these 600
evaluation rows.

## Authorized next candidate

If work continues, create a separate V22 candidate with:

1. a new training and development stream that is disjoint from this V2
   evaluation, with explicit examples for contextual search, complete
   multiline draft bodies, and every invalid-range category;
2. a public-input semantic audit that rejects hidden draft content, missing
   search operands, unresolved URLs, decoy-resource inconsistency, and
   unsupported tool schemas;
3. deterministic interleaved exposure reporting for all 11 kinds and both
   languages at every selectable checkpoint;
4. a new sealed evaluation authored after the V22 data contract is frozen,
   without using V2 predictions for checkpoint selection; and
5. the same quality gates, exact and checked-outcome measures, zero-mutation
   boundary, and fresh package checksum before any workflow comparison.

V21 remains the immutable comparison artifact. If a V22 candidate cannot clear
the same routine, negative-case, and execution-boundary gates on a new sealed
set, stop investing in this approach rather than expanding the training budget
to chase a positive verdict.
