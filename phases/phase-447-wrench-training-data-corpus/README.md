# Wrench 20,000-row training corpus

Status: source audit and draft cross-validation in progress. On 2026-09-23,
402 agent-authored draft rows were reported across two D: batches and frozen
for audit; zero rows have passed the training quality gate and no training job
has started. The batches are distinct by path, but row-level overlap across
them has not been ruled out.
Two broad worker searches exposed evaluation material, including rows marked
`final`; exact source paths are unavailable, so sealed-final exposure is
unresolved and the current final set is not trusted as untouched evidence.

## Owner target

Prepare exactly 20,000 quality-screened training records for Wrench's six
allowlisted action families and their boundary cases. Keep evaluation records
outside this training count. For an 80/10/10 ratio, add 2,500
development/calibration rows and 2,500 sealed final evaluation rows. This is
25,000 total examples: 20,000 train, 2,500 development/calibration, and 2,500
sealed final. If only 4,000 evaluation rows are added, the 24,000-row total is
83.3% training and 16.7% evaluation, not 80/20.

The active training target is the binary System 1 readout on frozen Qwen
weights. Its supervised label is `continue` or `abstain`. The six action
families and expected typed proposals are retained as audit strata and
verifier oracles. This corpus does not fine-tune the full Qwen backbone or
grant execution authority.

The target is a corpus, not a promise that 20,000 arbitrary prompts will make
the model better. Each row must be useful, attributable, independently
reviewable, and grouped by underlying task family so repeated paraphrases do
not masquerade as independent coverage.

## Provisional allocation

The allocation below is an initial structure. The traffic-weighted portion
cannot be filled or divided honestly until approved real-workflow traces and
their task-frequency distribution are available.

| Portion | Rows | Allocation |
| --- | ---: | --- |
| Balanced action and matched-boundary training core | 7,200 | 600 eligible and 600 matched boundary cases for each of the six actions: `read_file`, `read_lines`, `literal_search`, `git_read_status`, `health_read`, and `patch_draft`. |
| Observed, high-value workflow training | 9,600 | Allocate by measured task frequency, useful frontier-token mass, verifier success, and final task outcomes. Preserve a minimum per-action floor. |
| Out-of-scope and escalation training | 3,200 | Allocate across unsupported mutation or command requests, credential or external-access requests, ambiguous or multi-step work, and unrelated or non-developer requests. |
| **Training split** | **20,000** | Evaluation data is additional. |
| Development/calibration | 2,500 | Tune thresholds and diagnose errors. Keep separate from training and sealed final data. |
| Sealed final evaluation | 2,500 | Untouched until the candidate and scoring protocol are frozen. |
| **Total examples** | **25,000** | 80% training, 10% development/calibration, and 10% sealed final evaluation. |

For the traffic-weighted portion, use an evidence-based priority score such as
`observed frequency × eligible completion rate × verifier success × frontier
token mass`. Report raw request frequency and token-weighted frequency
separately. A frequent task with negligible savings should not crowd out a
less frequent task that removes a large amount of repeated context.

## Current source audit

### Action families and expected value

These are value hypotheses from Wrench's bounded product contract, not
measured traffic rankings. The repository has no verified real-request
frequency distribution yet.

| Action family | Expected practical value | Current data gap |
| --- | --- | --- |
| `read_file` | High when it avoids sending large files to the frontier model; path and byte cap are checkable. | Only a small authored calibration slice; real task frequency and saved token mass are unknown. |
| `read_lines` | High for narrow evidence retrieval with explicit line limits. | Same gap; ensure examples include both valid ranges and boundary failures. |
| `literal_search` | High for repository discovery and context reduction. | Same gap; include no-hit, many-hit, root and match-limit boundaries. |
| `git_read_status` | Very verifiable for simple tracked-file state, but each request may save few tokens. | Overrepresented in V9 calibration and prior accuracy work; do not mistake that history for production demand. |
| `health_read` | Easy to verify when the endpoint is authorized and response is bounded. | Likely narrow; endpoint frequency and practical savings are unknown. |
| `patch_draft` | Potentially high value on routine review-only changes. | Higher consequence and semantic burden; keep it review-only and require strong independent label and verifier evidence. |

The first three are the strongest initial value hypotheses because they can
reduce repeated repository reading. The priority order must be replaced by
observed frequency and paired utility results once those exist.

### Candidate seeds, not high-confidence production data

- The original Wrench-or-abstain suite has 5,600 authored prompts: 600
  eligible controls and 5,000 abstentions, across 160 pattern groups. It has
  useful schema, path, bounds, and boundary structure, but the 89:11 class
  ratio is heavily abstention-skewed. The prompts are synthetic and correlated
  within pattern groups. Human label review is absent. Treat it as a candidate
  seed for review, not 5,600 independent workflow examples.
- The V9 calibration set has 466 records. Of these, 320 are `git_read_status`,
  18 belong to each of the other five actions, and 56 are out of domain. This
  is strongly imbalanced across action families. Its 224-row development set
  is separate and must stay out of fitting for that candidate.
- The replacement 5,600-case diagnostic is explicitly not a training split.
  It is synthetic, has 160 pattern groups, and still awaits human label review.
  Keep it out of training unless its owner and role are explicitly changed and
  the labels are reviewed.
- A metadata-only audit of V9 calibration found 466 rows in 124 template
  groups: 320 `git_read_status`, 56 out-of-domain, and 18 for each other
  action family. The expected labels are 220 accepted and 246 abstain. Of
  these rows, 352 inherited records have no explicit category or typed target;
  the other 114 have category/target fields but no row-level `data_origin`.
  These are historical candidate-calibration data, not reviewed rows for the
  new training corpus.

### Cleanup completed on 2026-09-23

- Removed 5,000 low-fit external tool-call rows from the active `dataset/`
  directory: 2,000 short pyromind rows, 1,000 long pyromind rows, and 2,000
  Glaive rows. The source mix does not match Wrench's six-action proposal
  protocol, and license review is pending. All three files were copied to
  `D:\wrench-slm-data\quarantine\dataset-general-tool-call-2026-09-23`,
  verified byte-for-byte with SHA-256, then removed from the active directory.
  See [`quarantine-manifest.json`](quarantine-manifest.json) for the receipt.
- The original and replacement synthetic diagnostic suites remain audit
  material only. They are not accepted training rows because labels have not
  been reviewed and examples share a small number of templates.
- V9 calibration and development records remain tied to their historical
  candidate evaluation. They are not included in the new training corpus and
  do not establish real usage frequency.
- The new 20,000-row corpus currently has no accepted rows. Historical data
  counts are not credited toward the target unless each row passes the stated
  provenance, label, task-fit, and duplicate checks.

### Authored draft batch and cross-audit on 2026-09-23

- Nine JSONL draft shards totaling 350 reported rows were written under
  `D:\wrench-slm-data\scratch\phase-447-authored-drafts-2026-09-23`. All nine
  files have the Windows read-only attribute and SHA-256/byte-count records in
  [`draft-batch-cross-audit.json`](draft-batch-cross-audit.json). These files
  remain on the D: scratch path as review-only artifacts; none are accepted
  training, development, or sealed-final rows.
- Independent checks parsed 250 rows across seven shards and found zero
  normalized prompt duplicates in that group. Four OOD shards (100 rows) also
  passed their candidate-schema and abstention checks. The three action shards
  do not satisfy the production corpus contract: they omit required fields,
  and the `git_read_status`/`health_read` abstention rows retain proposals.
  The production validator was not passed by this batch.
- `literal_search` is excluded until its author's source-access scope is
  established. `read_lines` is excluded because broad search output included
  historical calibration rows. `patch_draft` is excluded because broad search
  output included evaluation rows marked `final`. The workers did not retain
  exact matched paths; whether sealed-final content appeared is unresolved.
- A previous 397-row capture file is not eligible: metadata review found
  content-bearing prompt/context fields. Its 397 records self-report
  `capture_redaction.status=complete` with method `deterministic-pattern-v1`,
  but that pass covers selected credential patterns and does not establish
  general PII redaction. A metadata-only audit found email-shaped strings in
  199 records as a review flag; this does not establish that every match is
  personal data or that the redactor failed. There is no hash-bound full-file
  redaction review or row-bound training authorization receipt. The owner
  authorized inspection in the current conversation, which does not establish
  third-party rights or complete training-use consent.
- A separate Phase 448 metadata audit reports joins from the 397 capture IDs to
  September 11 and 12 event logs, with incomplete event coverage. It records
  routing/provider token counts and request-handling outcomes, but no joined
  independent verifier results, final coding-task correctness, provider cost,
  or full retry/correction accounting. Event dates refer to those log joins;
  capture-row timestamps were not established here. These metadata do not make
  the capture training-ready or prove Wrench task-family frequency.
- Phase 303/238 inventories still do not provide training-eligible row-level
  evidence. The previous five-row snapshot does not cover the current 397-row
  source.

### Supplemental authored draft batch on 2026-09-23

- A distinct six-shard batch reports 52 synthetic review candidates under
  `D:\wrench-slm-data\scratch\phase-447-authored-drafts-next-2026-09-23`.
  The D: receipt reports 29 accepted-proposal drafts and 23 abstain drafts.
  Its `PASS` means static shard checks only. It does not mean 29 accepted
  training examples. The root independently confirmed all six shard hashes,
  sizes, read-only attributes, row counts, and cross-shard unique IDs, prompts,
  and template IDs. The independent receipt is
  `D:\wrench-slm-data\scratch\phase-447-authored-drafts-next-2026-09-23\independent-cross-validation-W447-ROOT-XV-20260923.json`
  (SHA-256 `687C1F1EA9922CAE73D7434C7AA18870EBEA0FBF2D0BBF3B1511EE1D36A7D716`).
- A second semantic review found the batch non-promotable. Some `read_file`
  rows have null oracle/context hashes; `read_lines` references an older
  `core.py` hash; `literal_search` lacks required label/oracle/review fields;
  `patch_draft` uses two abstention reasons outside the current runtime
  taxonomy, and its accepted examples refer to fictional files. No runtime or
  oracle was executed. All 52 remain review-only, and training acceptance is 0.
- The 350-row first batch and 52-row supplemental batch have separate scopes.
  The first batch's `read_file_worker_wrote_shard: false` and its
  `read_lines`/`patch_draft` exposure findings apply only to that batch. The
  supplemental batch does not resolve the first batch's unresolved possible
  sealed-final exposure.
- The corpus validator was hardened against sealed/final path components and
  path aliases before reading the manifest or split inputs. It also rejects
  report paths that alias inputs and bounds both near-duplicate work and error
  diagnostics. The root independently reran all 18 focused isolation tests
  and Python compilation successfully; the final validator and test hashes
  are recorded in `independent-audit-receipt.json`. This does not establish
  consent, license, review-receipt integrity, or a training-ready corpus.

### Exclude from current Wrench training

- The 5,000-row general tool-call bundle was excluded and moved out of
  `dataset/` after the task-fit audit. Its long-context portion is broad web
  research and finance/crypto heavy. A sampled short record teaches market-data
  tool calls, while sampled long records use general web research and tools
  outside Wrench's allowlist. The Glaive subset is generic function calling,
  not Wrench's typed proposal protocol. Its files are retained in D: quarantine
  with a SHA-256 receipt, and license review remains pending.
- Exact-deduplicated but template-correlated rows are not automatically
  garbage. Keep a small number as controlled variations, group them together,
  and do not count each paraphrase as an independent task.
- Any row with an unverified expected action, invalid bounds, missing target,
  mismatched tool authority, stale repository context, private information,
  or unclear consent is quarantined until fixed or discarded.

### Disposition of currently inspected material

- **Useful structure, not yet training-grade:** the original six-action
  controls and authority-boundary families. The schemas and target checks are
  aligned to Wrench, but the generated patterns need human label review and
  group-aware deduplication.
- **Low coverage for real task learning:** V9's five non-Git actions have 18
  calibration examples each. Do not infer adequate coverage from its 466-row
  total.
- **Excluded from this Wrench corpus:** the external general tool-call bundle.
  Its records are parseable, but the audited topic mix and sampled tool
  schemas are mostly outside the current six-action contract. The files were
  removed from the active `dataset/` directory, preserved on D: quarantine,
  and have a hash-bound disposition receipt. License review remains pending.
- **Not automatically junk:** boundary examples for mutation, shell,
  credentials, outside-root access, ambiguity, and multi-step requests. They
  are useful safety data when labels are precise and examples are diverse.
  Their current large synthetic volumes and repeated templates should be
  reduced to reviewed, representative cases.

The current repository does not contain a verified real-traffic frequency
distribution for these six action families. Existing synthetic category
counts cannot substitute for production frequency. This is the input needed
before allocating the 9,600 traffic-weighted training records.

## Training workflow experience and tooling

The requested developer-experience improvement is a smoother data-to-training
workflow, not a seventh developer-experience task family. Current tools are
fragmented: `tools/audit_dataset.py` checks JSONL parsing and broad keywords,
while `tools/train_qwen_abstain.py` consumes fixed calibration/development
files. There is no single path that explains which records were admitted,
which were rejected, whether each label is independently checked, and whether
the exact training split is ready.

The workflow should answer those questions in one guided pass:

1. **Intake** records source, license or consent, redaction status, hashes,
   task family, and storage location. Large source files stay on D:.
2. **Review** presents small batches with the request, proposed label, typed
   oracle, boundary rationale, provenance, and duplicate family. A reviewer
   can accept, correct, or reject each row and see a concise reason.
3. **Build** deterministically separates training, development/calibration,
   and sealed final data by repository, task family, and template group.
4. **Validate** gives one readable pass/fail report with split sizes, action
   balance, boundary coverage, duplicate/leakage counts, quality dispositions,
   source hashes, and frequency/utility coverage.
5. **Train and evaluate** remain separate commands. The training command must
   refuse unreviewed data and sealed-final inputs, then save a hash-bound
   receipt and per-family results.

The first tooling slice is
[`validate_corpus.py`](validate_corpus.py). It validates only training and
development inputs, never accepts a sealed-final file argument, and keeps raw
request text out of error reports. A review queue and deterministic builder
remain follow-up work after an approved real-trace source is located.

## Row-level quality requirements

Each accepted row must include:

- stable case ID, source class, provenance, and license or consent status;
- one of the six action families or a named abstention/fallback family;
- the request and the minimum context needed to decide correctly;
- the expected typed proposal, or an exact abstention reason;
- an executable verifier oracle where applicable, with no autonomous tool
  execution during labeling;
- repository and snapshot identity for path- or state-dependent requests;
- a task-family and template-group ID used for split isolation and duplicate
  analysis;
- reviewer identity or review receipt, review status, and correction history;
- exact and near-duplicate fingerprints, label-confidence notes, and an
  explicit quality disposition.

The first validator expects `schema`, `split`, `allocation_stratum`,
`category`, `family`, `template_id`, `system`, `prompt`, `context_ref`,
`expected_status`, `expected_proposal`, `abstention_reason`, `oracle_ref`,
`provenance`, `review`, and `fingerprint_sha256`. Real rows also require
observed request counts, frontier input tokens, verifier outcomes, final task
outcomes, and an observation window. Authored rows cannot claim production
frequency. The exact row and split rules are enforced by `validate_corpus.py`.

Use four dispositions: `verified_real`, `verified_authored`,
`needs_review`, and `reject`. Only reviewed `verified_real` and
`verified_authored` rows can enter training. `needs_review` and `reject` rows
must not be mixed into a training file.

## Split and release discipline

- Split by repository, underlying task family, and template group. Related
  paraphrases must remain in one split.
- Keep training, calibration, unsealed development, and sealed final data
  distinct. Never train or tune on `final.jsonl`.
- The 20,000-row target is training data only. Keep the 5,000 evaluation
  records additional, with 2,500 development/calibration rows and 2,500
  sealed final rows. Keep the sealed final set untouched until the candidate
  and scoring protocol are frozen.
- Validate class and action counts, exact duplicates, near-duplicates,
  schema/oracle validity, path/bounds validity, provenance, and leakage before
  fitting.
- Train only after the corpus and label audit pass. Training still needs the
  host's 10 percent RAM and VRAM reserves.
- Store large JSONL corpora and derived artifacts under
  `D:\wrench-slm-data`; keep small manifests, validators, and receipts in
  the repository.

## Required next input

Provide the approved, redacted real-workflow request traces or their exact
local location, including enough metadata to estimate per-action frequency,
frontier-token use, verifier outcome, fallback, and final task success. Do
not include credentials or unredacted private content. Without these traces,
the balanced training core can be prepared, but the usage-frequency claim and
the 9,600-row traffic allocation cannot be made honestly.
