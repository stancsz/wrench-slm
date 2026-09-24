# Wrench 25k dataset state audit

Audit date: 2026-09-23 (America/Edmonton)
Repository: `C:\Users\stanc\github\wrench-slm`
Expected and observed HEAD: `87909b958ac252b0b3b2cc720a300babb26b733d`
Scope: read-only inspection of data state, corpus contract, validator, and historical receipts. This report is the only file created by this audit.

## Finding

The target is **not ready**. The active `dataset/` directory contains zero JSONL files, and the approved `C:\wrench-slm-data` tree contains zero files at this inspection. The repository's independent audit receipt records **0 accepted training rows, 0 development rows, and 0 active training JSONL files**. No split for the requested 25,000-example corpus is present. Historical draft and diagnostic row counts are not admissions.

The current corpus validator also has a reproducible runtime error: its structural-only invocation ends with `NameError: name 'group_splits' is not defined` at line 782. This differs from the earlier independent receipt, which records a successful focused test run against another validator hash. The current checked-in validator file is unmodified relative to the checkout, so the earlier receipt does not establish that the current validator executes successfully.

## On-disk state

- `dataset/` contains only `README.md` and `manifest.json`; listing `dataset/*.jsonl` returned **0** files.
- `C:\wrench-slm-data` exists with `datasets/` and `logs/` directories; a recursive file listing returned **0** files. This is the approved data root. The old D: path in `dataset/README.md` and Phase 447 receipts is not present on this host (`Test-Path D:\wrench-slm-data` returned false), so historical D: payloads could not be inspected or rehashed.
- `dataset/manifest.json` is an exclusion/disposition manifest for three generic tool-call sources, not a `wrench.corpus-manifest.v1` training manifest. The sources are explicitly excluded due to task-fit and pending rights review.
- Repository evaluation files and past experiment datasets exist outside `dataset/`; they are historical evaluation/training artifacts, not rows admitted to this corpus, and are not credited toward 25,000.

## Counts and dispositions

| Material | Reported/present count | Admission status |
| --- | ---: | --- |
| Current accepted train | 0 | None present |
| Current accepted development/calibration | 0 | None present |
| Current accepted sealed final | 0 | None present |
| First authored draft batch | 350 reported | Review-only; production schema incomplete; potential final exposure unresolved |
| Supplemental authored draft batch | 52 reported | Review-only; semantic issues; zero accepted |
| First and supplemental authored drafts combined | 402 reported | Not accepted; D: source files absent from this host for fresh local verification |
| Real-workflow capture candidate | 397 reported | Excluded; consent/rights, general PII review, labels, independent outcome evidence, and complete accounting are insufficient |
| Generic external tool-call bundle | 5,000 historical rows | Excluded; license review pending and task mix does not fit Wrench |
| Historical V9 calibration | 466 reported | Candidate calibration material, not the new corpus; highly imbalanced and missing required row-level provenance/targets |
| Historical original/replacement synthetic suite | 5,600 each reported | Diagnostic seed only; synthetic, template-correlated, unreviewed; not accepted |

The independent receipt reports that the sealed-final source exposure is **unresolved** because broad worker searches surfaced records marked `final` and their exact paths were not retained. Do not reuse the current final set as untouched evaluation data or promote rows from either draft batch until exposure is resolved.

## Contract and validator gates

The goal fixes exactly 20,000 training rows, 2,500 development/calibration rows, and 2,500 sealed-final rows. The intended records teach the binary `continue`/`abstain` readout; retain the typed six-action proposal or exact abstention reason as an audit stratum/oracle. Synthetic authored data must not be presented as observed workflow frequency.

The production validator is `phases/phase-447-wrench-training-data-corpus/validate_corpus.py`. The contract requires, per row, `wrench.training-example.v1`, split and allocation metadata, one of six action families or four named out-of-scope families, typed expected proposal or exact abstention with no proposal, context and independent-oracle references with matching hashes, approved source provenance and repository/task-family IDs, a verified human review receipt, and a normalized model-input fingerprint. It validates train and development only and intentionally does not open sealed-final data. It checks source/context/oracle/review registries, split isolation by repository/task family/template, exact and near-duplicate leakage, coverage for each family, split hashes, and target sizes. The optional provisional-allocation gate checks 7,200 balanced-core, 9,600 observed-workflow, and 3,200 out-of-scope training rows.

Important gaps recorded in the validator receipt remain: review receipts are not cryptographically bound to the precise row/model input; declared consent/license/redaction is not independently verified by the validator; the near-duplicate threshold has not been calibrated on an approved corpus; and the validator cannot establish that ordinary-named train/dev files do not contain copied final examples. The final-access history must be resolved separately.

## Checks run

- Read `AGENTS.md`, `docs/northstar/README.md`, `docs/goal/wrench-25k-data/GOAL.md`, `dataset/README.md`, `dataset/manifest.json`, the Phase 447 README, validator, validator tests, and Phase 447 audit/approval/pilot/quarantine receipts.
- Confirmed HEAD equals the requested commit and recorded that the working tree has pre-existing edits. No pre-existing file was changed by this audit.
- Inspected `dataset/` and recursively listed files under `C:\wrench-slm-data`: 0 active JSONL files and 0 data-root files, respectively.
- Ran `py -3 phases/phase-447-wrench-training-data-corpus/validate_corpus.py --manifest dataset/manifest.json --structural-only`. It failed at the end with `NameError: name 'group_splits' is not defined` (`validate_corpus.py:782`). No report or dataset files were written by this command. The manifest is an excluded-source manifest, not the expected corpus manifest.
- Did not run tests, generate or process data, access credentials, make external calls, or train a model.

## Hashes

SHA-256 values observed during this audit:

- `docs/northstar/README.md`: `188AF12656DD95A675F488E8A4D50474192D2858B7B3A6C4BF7AB10B99366523`
- `docs/goal/wrench-25k-data/GOAL.md`: `69326EA9AAD972BEC602A5EE241F901BCC54D7B531324ACB2582615655944F2D`
- `dataset/manifest.json`: `8D37E0F1337B9293A8487200D7815BEFF56E7C1DEAB05AEA876AD1446C62BC7B`
- Current `phases/phase-447-wrench-training-data-corpus/validate_corpus.py`: `BB1B2743AB81F05568FEFA4FAB7957169E5626936422304D4A0A49B0BC9B421F`
- `phases/phase-447-wrench-training-data-corpus/independent-audit-receipt.json`: `620C54AFE83157032C434A1037A81C1268EE69ABFDFEDAB17BFDB4A2E8563877`

The independent receipt records validator hash `8B37B8A68E942A3F2FEA3D0996CEB6647C66302048FB760E3C2B80A173CAB21E` and isolation-test hash `63DBFF4264B29D8AA0580833258123F12190504436ABEE3DA3D5BE4230096998`. The receipt's 18-test pass is historical evidence for those recorded files, not verification of the current validator hash.

## Recommended bounded path to admission

1. Repair and independently review the current validator runtime failure, then rerun its focused isolation suite. Confirm the validator hash and receipt match the exact files being used.
2. Resolve possible sealed-final exposure and identify the actual historical draft payloads. Keep all affected rows quarantined unless source identity and separation can be proved.
3. Restore a bounded MiniMax route and bind a corpus-specific cost receipt before any paid request. The recorded one-request pilot returned HTTP 401, no model/usage receipt, and unknown charge status. Reconcile the possible charge before requesting more. The approval caps all corpus calls at USD 100; the recorded pilot has one request, 128 output tokens, and zero automatic retries.
4. Establish a controlled generator and executable fixtures/oracles for all six actions and boundary flips. Secure one human review protocol whose receipt identifies reviewed row/input hashes, task-fit, label, privacy, and reviewer. Keep authored data explicitly separate from verified-real usage data.
5. Create source/context/oracle/review registries and hash-bound train/dev manifests in the approved C: data root. Build group-aware splits so repository, task family, and template groups do not cross. Use only reviewed train and development rows during iteration.
6. Construct sealed final separately after generators, families, scoring, prompt, and candidate are frozen. Audit prompt/hash exposure and access history before any final evaluation claim.
7. Run production corpus validation, independently review rights/privacy and validator limitations, and stop for concrete publication rights/artifact review before external release. Dataset preparation is authorized; model training and production routing are not reactivated by this data goal.

Do not start a download, generation, inference, packaging, training, or other artifact-producing job until `python tools/check_wrench_storage_budget.py status` and a peak-byte reservation pass under the current strict 50 GB aggregate ceiling. Before paid generation, resolve the unknown charge and enforce the USD 100 corpus ceiling. No current data set is ready for training or publication.
