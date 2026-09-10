# Historical Wrench-Pro V12 model-weight handoff

Updated: 2026-09-10

Status: **HISTORICAL DIAGNOSTIC. SUPERSEDED BY V21.**

The current weight-release decision is recorded in
[MODEL_RELEASE_HANDOFF.md](MODEL_RELEASE_HANDOFF.md) and
[MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md). V12 remains here for
lineage and failure analysis; its status must not be used for the V21 package.

This is the current operator handoff for the model-weight release work. V12
completed the bounded training phase. The remaining work is fresh independent
evaluation, release packaging evidence, and an explicit release decision.
Router tuning, cloud routing, gateway integration, and deployment are deferred.

## Decision at a glance

V12 started from the selected V11 adapter, added 2,048 training-only rows,
and completed 300 optimizer steps with 4,800 presentations. All three V12
checkpoints scored 176/176 on the fixed development set. Step 300 was selected
using development evidence only. The exact PEFT package loads in a clean CUDA
environment and passes the dedicated 37-case packaged context guard.

V12 is still a candidate because fresh challenge v5 and sealed
release-authoring-v5 evaluations do not exist yet. V4 is historical diagnostic
evidence after guiding V11 and V12. Do not publish the package or call it
production-ready until every fresh gate below passes.

Current package: artifacts/model-release/package-selected-v12
Selected adapter SHA-256: 0fe126ea59bd367075ab25b7cc9fbd20dfaf6371a6fad64801a4b279bbe66990
Package manifest SHA-256: 05776c6ba2b3718d760523942f5c59946486411d3093b91ac8b25d3391e11bc4

## Verified receipts

| Area | Receipt | Observed result | State |
| --- | --- | --- | --- |
| Data | data/pilots/release-generalization-v12/manifest.json | 37,194 train rows, 280 families, 2,048 new rows, zero duplicates, zero label conflicts, dev and eval unchanged | Pass |
| Preflight | artifacts/model-release/data-preflight-v12/preflight.json | Passed; train SHA-256 edef37d121fbf5280688d29093f7bc5bc416955f962ed4ff4cb5537ba799877e | Pass |
| Warm start | artifacts/model-release/warmstart-diagnostic-v12/run.json | Loaded V11 adapter d9c1624493632b14d14baa1aa0e568c82f017295974a1012dc59e6440ae0c011; optimizer reset; finite loss | Pass |
| Training | artifacts/model-release/pro-training-v12/run.json | 300 steps, 4,800 presentations, 494.961 seconds, validation loss 0.000095673264, peak allocated 6,506,869,248 bytes | Pass |
| Development | artifacts/model-release/v12-development-step100, step200, step300 | Each 176/176 exact, routine 112/112, fallback 64/64, fixed gates true | Pass |
| Selection | artifacts/model-release/selection-v12/selection.json | Step 300 selected by exact rate, validation loss, then earliest step | Pass |
| Package | artifacts/model-release/package-selected-v12/release_manifest.json | PEFT adapter with pinned base revision and base hash; status TRAINED CANDIDATE | Candidate |
| Clean CUDA | artifacts/model-release/v12-clean-cuda/receipt.json | Load 2.888 seconds, first call 2.064 seconds, warm call 1.614 seconds, peak CUDA 1,076,785,152 bytes, process RSS 1,854,783,488 bytes | Pass |
| Context guard | artifacts/model-release/v12-package-context-development/summary.json | Dedicated 37/37 exact, 37/37 actual outcomes, zero filesystem changes | Pass |
| Retired V4 diagnostic | artifacts/model-release/v12-package-release-authoring-v4-diagnostic/summary.json | 432/440 exact, routine 272/280, fallback 160/160, English 220/220, Chinese 212/220, zero filesystem changes; all 8 misses are Chinese Git-status rows that emit read_file | Historical diagnostic only |
| Fresh external gates | Not yet created | Challenge v5 and release-authoring-v5 remain open | Blocker |

The small context guard has no fallback, ambiguity, or unsupported rows, so its
generic category flags are not the decision. Use the dedicated 37/37 and
zero-change requirement recorded above.

## Frozen contract

- Base: Qwen/Qwen2.5-0.5B-Instruct.
- Revision: 7ae557604adf67be50417f59c2c2f167def9a775.
- Base SHA-256: fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe.
- LoRA rank 16, alpha 32, dropout 0.05.
- Targets: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj.
- Trainable parameters: 8,798,208.
- Input limit 1,536 tokens; output limit 192 tokens.
- Formatter SHA-256: 3c3d37ec3481da3bedc4f4148c20699c55b3358566e2f253a4caac7b2c4e3ade.
- Greedy structured protocol. Invalid output is a failure.

Release format is a PEFT adapter plus the exact base dependency. Do not merge,
quantize, or convert without evaluating the converted artifact separately.
Trainer checkpoints containing optimizer state are not release packages.

## V12 data and storage record

V12 targets the V11 failure boundary: natural Chinese Git-status paraphrases
with selected-file distractors, reordered resources and prior results, and path
variation. It also adds English Git-status and bilingual config contrasts.
The generator is scripts/release_generalization_v12_data.py, SHA-256
eca3bcee26ed6a1f365c3b448b007e056ee56e9ec159dc1bab7807c90acb7c6d.
The V11 parent train SHA-256 is
3f851130e14f44f946a4cc7bff449b12993aec58dbf3996b0b16f369cde3a5ca.
The V12 train SHA-256 is
edef37d121fbf5280688d29093f7bc5bc416955f962ed4ff4cb5537ba799877e.

The first V12 main attempt failed at checkpoint write because C: was nearly
full, after finite training state. Its receipt is preserved at
artifacts/model-release/pro-training-v12-failed-disk-v1/run.json. Before the
successful retry, 45 immutable historical optimizer states totaling
49,245,277,635 bytes moved to D:/wrench-slm-artifacts-archive/2026-09-10/
trainer-states. The index at D:/wrench-slm-artifacts-archive/2026-09-10/
trainer-states/index.json records source paths, sizes, and SHA-256 values.
Keep current candidate artifacts on C:. Archive only immutable historical states
after checking space and writing an indexed hash record.

## Exact commands

Run from C:/Users/stanc/github/portfolio/wrench-slm. Confirm dirty work before
starting and preserve unrelated files:

    Get-Content artifacts/model-release/selection-v12/selection.json -Raw
    Get-Content artifacts/model-release/package-selected-v12/release_manifest.json -Raw
    Get-PSDrive -Name C | Select-Object Used,Free
    git status --short

V12 training command, recorded for provenance. Do not rerun into the same output:

    .venv/Scripts/python.exe -X utf8 scripts/pilot_train.py --train data/pilots/release-generalization-v12/train.jsonl --val data/pilots/release-generalization-v12/development.jsonl --output artifacts/model-release/pro-training-v12 --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 --learning-rate 0.000005 --seed 42 --checkpoint-every 100 --gpu-memory-fraction 0.55 --initialize-adapter artifacts/model-release/package-selected-v11/weights

Selection is development-only: highest exact rate, then lowest validation loss,
then earliest step. Never select after inspecting external predictions.

## Next step: create fresh v5 sets

Create data/pilots/independent-challenge-v5 and
data/pilots/release-authoring-v5 with new generators, values, paths, wording,
and family IDs. Never copy scored V4 rows. Every non-fallback target must be
derivable from public context. If required selection is absent, use
ROUTER_FALLBACK or expose the target path before freezing labels. Do not retain
the V4 contradiction where two public contexts required hidden file paths.

Include English and Chinese config, literal search, Git status versus file read,
tool and context order changes, quoted and Unicode paths, selected and missing
selections, ambiguity, unsupported, missing-tool, and invalid-range cases.
Retain the sealed denominator of 280 routine plus 160 fallback cases unless a
protocol change is frozen before scoring. Preserve per-kind and per-language
denominators.

Authoring order:

1. Generate only into the new versioned directories.
2. Check family and exact-input isolation, language and kind counts, and context completeness.
3. Run release_preflight for each set.
4. Run release_gold_check without loading the model.
5. Review every fallback and context-dependent target.
6. Freeze generator, manifest, split, and gold hashes.
7. Only then score the package.

Example sealed checks:

    .venv/Scripts/python.exe -X utf8 scripts/release_preflight.py --data data/pilots/release-authoring-v5 --output artifacts/model-release/data-preflight-release-authoring-v5
    .venv/Scripts/python.exe -X utf8 scripts/release_gold_check.py --data data/pilots/release-authoring-v5 --split evaluation --output artifacts/model-release/gold-release-authoring-v5

Run equivalent checks for independent-challenge-v5. Stop when preflight or gold
checks fail. A generator or plan is not label evidence.

## Package, verify, and score

If V12 remains selected, package and clean-verify the exact checkpoint:

    .venv/Scripts/python.exe -X utf8 scripts/package_weights.py --checkpoint artifacts/model-release/pro-training-v12/checkpoint --output artifacts/model-release/package-selected-v12 --license artifacts/model-release/licensing-v1/LICENSE-QWEN
    .venv/Scripts/python.exe -X utf8 scripts/verify_weight_package.py --package artifacts/model-release/package-selected-v12 --python artifacts/model-release/clean-env-v1/Scripts/python.exe --base-path artifacts/model-release/base-dependency-v1 --output artifacts/model-release/v12-clean-cuda --device cuda

Run challenge and sealed evaluations sequentially:

    .venv/Scripts/python.exe -X utf8 scripts/release_eval.py --data data/pilots/independent-challenge-v5 --split evaluation --package artifacts/model-release/package-selected-v12 --base-path artifacts/model-release/base-dependency-v1 --output artifacts/model-release/v12-package-independent-challenge-v5 --execute
    .venv/Scripts/python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-authoring-v5 --split evaluation --package artifacts/model-release/package-selected-v12 --base-path artifacts/model-release/base-dependency-v1 --output artifacts/model-release/v12-package-sealed-release-v5 --execute

Preserve predictions, summaries, run receipts, protocol snapshots, source
snapshots, and fixture outcome receipts. Never overwrite a prior output.

## Release gates

- Raw protocol: at least 99.5 percent valid calls or explicit abstentions.
- Routine exact calls: at least 95 percent over all 280 routine sealed cases.
- Routine outcomes: at least 95 percent over those same 280 cases.
- Useful coverage: at least 70 percent correct usable supported predictions.
- Every supported kind: at least 90 percent exact for config, lines, search,
  Git status, Git log, health, and draft.
- Both English and Chinese routine slices: at least 90 percent exact.
- Ambiguous cases: at least 95 percent explicit fallback.
- Unsupported, missing-tool, and invalid-range cases: zero non-fallback outputs.
- Execution boundary: zero unexpected filesystem changes; draft writes unexecuted.

Use point estimates. Confidence intervals are descriptive only. Never remove a
case, change a denominator, or lower a threshold after seeing predictions.

## Final package and stop rules

After every fresh gate passes, include adapter and tokenizer files, chat
template, frozen training contract, metrics, exact base revision and hash,
minimal runtime, pinned requirements, model card, data card, evaluation report,
lineage record, measured resources, LICENSE, LICENSE-QWEN, NOTICE, and a
checksum manifest covering every distributed file except the manifest.

If any runtime, README, model card, or license file changes, rebuild the
manifest and repeat clean verification. Do not include optimizer states, local
caches, hidden absolute paths, private fixtures, or router and hosted-service
claims. Keep status TRAINED CANDIDATE when any gate, license, or artifact check
is unresolved.

Stop and preserve receipts on preflight, gold, warm-start, loss, checkpoint,
clean-load, licensing, or external-gate failure. Write failures by kind,
language, context, and actual outcome before another bounded correction. Never
train on scored evaluation rows.

At the current state it is accurate to say that V12 training completed, the
adapter is identifiable and loadable, fixed development passed, and the
packaged context guard passed. It is not accurate to say that weights are
release-ready, production-ready, router-ready, or representative of production
traffic.
