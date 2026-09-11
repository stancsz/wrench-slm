> SUPERSEDED historical goal. Not an active instruction. The root goal.md controls current work.

# Wrench-SLM: establish practical usefulness beyond V21

Updated: 2026-09-10
Status: DECISIONS RESOLVED. Execute bounded NO-GO closure; no further training this cycle.
Weight status: Historical V21 package only: WEIGHTS READY FOR RELEASE. V22 is not release-approved.
Router status: Controlled comparison blocked by two consecutive fresh local quality gates; production integration and deployment deferred.

## Independent completion review, 2026-09-10

Verdict: the worker completed a bounded local NO-GO investigation, but did not
meet every requirement in this document. The model reliability objective has
not passed. Stopping at the failed quality gate was correct; completing an
experiment is distinct from qualifying a candidate or proving workflow value.

This review checked the actual completed run and summary receipts for all three
V2 evaluators and all three V22 development checkpoints. V21 scored 453/600;
V22 scored 105/110, 107/110, and 107/110. All six quality summaries report
`model_quality_passed: false`. V22 training reports `completed`, and all three
checkpoint adapter hashes match the selection receipt. V2 and V22 split hashes
match their manifests. No new model inference or sealed scoring was performed
for this review.

Fresh verification: 169 scoped tests passed in 14.03 seconds with one PEFT
warning; `verify_assets.py` verified 49 release files; Ruff passed on the
maintained changed Python files reviewed. Passing tests do not close the following
specification gaps found by source inspection.

| Requirement | Review disposition |
| --- | --- |
| V21/base/rules local comparison and V22 development decision | Complete as a failed quality experiment; no candidate GO |
| Frozen data and executable fixture labels | Counts, hashes, and preflight receipts present; full independence requirement remains partial |
| Independent author and full ancestor template/similarity audit | Partial retained-source audit now exists: zero observed overlap, but 22 declared ancestor sources are missing and authorship is unverified |
| Separate out-of-contract stress evaluation | 12-case V21 receipt passes all declared boundary observations; it is not a quality or production result |
| Runtime benchmarking | Corrected bounded receipt complete: 5 cold starts, 66 warm predictions, RSS, CUDA memory, serial throughput, and queue measurements; true parallel throughput remains unclaimed |
| Controlled cloud comparison | Correctly blocked by local quality; no workflow benefit established |
| Statistical design and analysis readiness | Power assessment and decision-rule corrections are now documented; paid workflow analysis remains blocked |

Required corrections before claiming the harness is ready for another pilot:

1. In `scripts/audit_usefulness_v2_data.py`, include the public/private-field
   audit in the overall pass condition. This is now fail-closed and has a
   negative test with a private key embedded in public context. This corrects a
   validation defect; it does not claim that the checked data leaked labels.
2. In `scripts/pilot_analyze_v2.py`, bind local quality receipts to the exact
   candidate, dataset, protocol, and completed run. The analyzer now rejects
   missing or mismatched receipts as INCONCLUSIVE, maps an identity-matched
   failed quality gate to NO-GO, and qualifies a latency regression above 10%.
   Focused decision tests cover these cases.
3. The prespecified power assessment is now recorded in
   `docs/reference/USEFULNESS_V2_POWER_ASSESSMENT.md`. With 120 families, the
   implemented all-success fallback is `0.05 ** (1/120) - 1 = -0.0246554`,
   below the -0.02 margin even when every episode succeeds. A simultaneous
   Bonferroni design needs at least 183 families, or 198 balanced families and
   990 cases for 11 kinds and two languages. The current result remains
   exploratory INCONCLUSIVE. Do not change the frozen V2 rule after scoring.
4. The separate stress receipt is now present at
   `artifacts/model-release/v21-usefulness-v2-stress` and covers 12 out-of-
   contract cases with no tool execution. Independent authoring and ancestry
   coverage remain unmet. The retained-source and overlap audit is recorded at
   `artifacts/model-release/usefulness-v2-lineage-audit.json`; it found zero
   exact or heuristic normalized-prompt overlaps in readable files, but 22
   declared ancestor sources are missing. Preflight already reads sealed labels for gold
   checking: "sealed not opened" means no candidate inference or selection on
   that set, not that no process accessed its rows.
   A 2026-09-10 recovery search found no additional declared sources in Git
   history or matching data files under `C:\Users\stanc\github`; the missing
   sources are not merely misplaced in the current local workspace.
5. Remeasure retained weights before any new candidate. This is now recorded in
   `artifacts/model-release/storage-audit-20260910.json` and fails the budget:
   7,974,854,728 bytes retained against 5,000,000,000. No deletion was done.
   The exact dry-run projections are recorded in
   `docs/reference/MODEL_STORAGE_RETENTION_HOLD.md`: removing all V21 snapshots
   leaves 4,538,456,176 bytes, removing all V22 snapshots leaves 4,538,456,193
   bytes, and removing both sets leaves 1,102,057,641 bytes. The V22-only removal option is selected in the closure plan below;
   this historical projection is not a cleanup completion receipt.

Next work is the executable closure plan below. The retention decision is
resolved, and unavailable historical provenance remains a documented limitation.

Observed correction verification after this review: the updated V2 audit passed
on a temporary copy with 710/710 gold rows, zero public/private leaks, and a
passed overall status. The identity-bound analyzer and decision rules are
covered by focused tests. The power receipt classifies the 120-family design as
exploratory INCONCLUSIVE and defines a balanced 198-family design. The storage
receipt records the current 7,974,854,728-byte total and a 2,974,854,728-byte
budget overage. The separate stress receipt records 12/12 boundary passes,
zero runtime errors, and zero tool executions.
The lineage receipt records partial coverage only: 25 training receipts
inspected, 22 missing declared sources, and no authorship proof.
Do not treat this review request as authorization to train V23 or spend a cloud
budget. Further training is conditional on that decision and the existing
fresh-data and all-slice gates. The recommendation remains to pause model
investment until the evaluation design is complete and a bounded next
experiment has a clear reason to succeed.

## Active objective

Close the current usefulness investigation as a local quality NO-GO with
preserved evidence and compliant storage. V21 and V22 failed their declared
quality gates. Workflow value remains unmeasured. A completed closure does not
mean the original reliability or workflow-benefit requirements passed.

## Decisions and executable closure plan, 2026-09-10

The user delegated the remaining decisions. This section supersedes earlier
requests for an owner retention choice, indefinite lineage recovery, and a
product/research decision. The stages below remain the historical experiment
specification, not instructions to resume its blocked cloud comparison.

1. **Stop this training cycle.** Do not train V23, extend V22, open V22 sealed
   evaluation for model scoring, or run a cloud comparison. Two failed quality
   gates and unproven workflow benefit do not justify another automatic repair
   cycle. No new model, endpoint, or paid budget is needed for closure.
2. **Accept the provenance limitation for closure only.** Record 22 missing
   ancestor sources and unverified author separation as unresolved historical
   limitations. Stop repeating the completed local recovery search. Do not mark
   independence as passed or generalize these scores to production. This gap
   prevents a stronger claim, but does not invalidate the observed local errors
   or prevent a bounded NO-GO decision.
3. **Keep the 5,000,000,000-byte storage budget. Remove V22 trainer snapshots.**
   Retain the base dependency, V20 and V21 packages, all three V21 snapshots,
   all datasets, and all textual V22 training, selection, and evaluation
   receipts. V21 retains the released artifact and its training recovery path;
   failed V22 training resumption is deliberately retired. The recorded
   projection after removal is 4,538,456,193 bytes, not a verified final total.
4. **Execute the selected cleanup without another policy decision.** First
   inspect the V22 training directory and selection receipt to identify the
   exact three snapshot paths (`step-000100`, `step-000200`, and `checkpoint`
   under `artifacts/model-release/pro-training-v22`). Record their current
   absolute paths, sizes, and weight hashes in a new retirement receipt. Copy
   any unique non-weight metadata needed to explain or reproduce the training
   configuration into a receipt directory outside those snapshots. Preserve
   `run.json`, selection, prediction, summary, and data receipts. Verify no
   active process is using these snapshots. Resolve each target and check it
   remains within the named V22 training directory, including junction/reparse
   targets, before deleting only those three snapshot directories with native
   PowerShell literal-path operations. Do not delete the parent training
   directory or any V21 files. If identities or paths disagree, stop cleanup
   and report the concrete mismatch rather than selecting substitute targets.
5. **Verify and publish closure.** Run `scripts/measure_model_storage.py` with a
   new output path; require `within_budget: true`, confirm the three retired
   snapshots are absent, and verify the retained release assets. Update
   `docs/reference/MODEL_STORAGE_RETENTION_HOLD.md` to record the executed
   choice and the loss of V22 resumability. Write a compact final closure report
   under `docs/reference/`, linking the quality, stress, runtime, power,
   lineage, and new storage receipts. Update this goal with observed results.

The worker can execute this closure plan now. Only an actual path, process,
receipt-integrity, or budget failure should block these steps. Do not request
another general decision about training, lineage, or retention.

### Closure acceptance criteria

- [x] Product/research decision made: stop the current training cycle.
- [x] Historical provenance gap disposition made: preserve as a limitation.
- [x] Storage retention choice made: retire only the three V22 trainer snapshots.
- [ ] V22 metadata and hashes preserved; scoped snapshot retirement verified.
- [ ] Fresh storage receipt is within budget and retained release assets verify.
- [ ] Final closure report and retention document reflect actual operations.
- [ ] Final status is CLOSED: LOCAL QUALITY NO-GO; workflow benefit unmeasured.

These decisions authorize the remaining work; they do not claim cleanup or
closure has already happened. A future research cycle requires a new objective,
complete prospective data lineage and author separation, and its own budget.
The V23 outline later in this file is an inactive design reference.

## Review corrections and starting evidence

The September 10 review reran the exact V21 package on two historical V8 suites:

| Suite | Exact predictions | Routine correct | Fallback correct | Meaning |
| --- | --- | --- | --- | --- |
| independent-challenge-v8 | 66/66 | 42/42 | 24/24 | Historical regression check |
| release-authoring-v8 | 436/440 | 276/280 | 160/160 | Historical regression check |

Receipts are under `artifacts/model-release/v21-package-independent-challenge-v8`
and `artifacts/model-release/v21-package-release-authoring-v8`.

**Correction to the previous review:**
[TRAINING_CORRECTNESS_AUDIT.md](docs/reference/TRAINING_CORRECTNESS_AUDIT.md)
explicitly records that V14 results on V8 informed V15, whose results informed
V16. These suites were exposed during ancestor development. A new V21 inference
run does not make the data fresh or independent. The combined 502/506 score is
descriptive regression evidence, not a production accuracy estimate. The
combined routine denominator is 318/322; 276/280 refers only to the larger
suite. The two V8 datasets share their generator and wording families, so their
rows must not be pooled as independent observations for a confidence claim.
The draft wiki review's stronger independence claim is superseded here.

The four larger-suite misses were two line-read abstentions, one draft-write
abstention, and a Chinese config prediction with `exec_command` and a `path`
argument that validation rejected. All four fell back; there were zero fixture
changes. This establishes observed failure containment for these cases, not
general command safety. Some historical fallback prompts explicitly tell the
model to return fallback, which limits what perfect refusal scores demonstrate.

The larger run measured full prediction latency of 1.133 s p50, 3.441 s p95,
and 3.630 s p99, with 1,123,057,152 CUDA allocated bytes and 1,249,902,592 reserved
bytes. These are single-machine, serial observations, not service guarantees.
The earlier cloud comparison used a different, older candidate and stopped on
routing/accounting failure; it establishes no V21 workflow benefit.

## V2 fresh-quality result

The new V2 data and executable gold audit passed preflight: 600 evaluation
cases, 120 families, 300 English and 300 Chinese cases, all 11 contract kinds,
zero public/private-field leakage, zero cross-split overlap, zero exact overlap
with the historical roots scanned, and 710/710 gold rows checked in disposable
fixtures. The labels are generated executable fixture labels, not recovered
production outcomes; exact-input overlap does not prove semantic independence.

The exact evaluation SHA-256 is
`f7cd33a3f546964a6d6eb6b49d90a3133713e0bffb4499c8e593c5eb7cce3351`.
The durable failure report is
[USEFULNESS_V2_QUALITY_RESULT.md](docs/reference/USEFULNESS_V2_QUALITY_RESULT.md).

| Evaluator | Exact | Routine exact | Routine checked outcome | Fallback exact | Fixture changes |
| --- | ---: | ---: | ---: | ---: | ---: |
| V21 package | 453/600 (75.5%) | 245/385 (63.6%) | 265/385 (68.8%) | 208/215 (96.7%) | 0 |
| Pinned base | 10/600 (1.7%) | 10/385 (2.6%) | 17/385 (4.4%) | 0/215 (0%) | 0 |
| Deterministic helper | 300/600 (50.0%) | 90/385 (23.4%) | 90/385 (23.4%) | 210/215 (97.7%) | 0 |

V21 raw protocol validity was 599/600 (99.83%). The routine accepted-call
error was 91/356. The seven false accepted actions in the negative set were all
invalid-range cases. Search was 0/55 exact and 20/55 checked-outcome correct;
draft was 0/55 checked-outcome correct; invalid-range abstention was 43/50.
V21 latency was 1.179 seconds p50, 2.669 seconds p95, and 3.033 seconds p99,
with 1,099,017,216 peak allocated CUDA bytes and 1,195,376,640 reserved bytes.

This is a real improvement over the base and helper on routine outcomes, but
it fails the predeclared 95% routine exact and checked-outcome gates by a wide
margin. It is not effective enough right now for the broader fresh-request
claim. The V2 cloud workflow comparison is therefore blocked and no paid or
production endpoint should be run from this candidate.

## V22 repair-candidate result

V22 was a separate repair candidate. It used new train and development families
and a new 600-task sealed set, with no V2 evaluation rows, predictions, or
labels copied into training. Its preflight checked 3,526/3,526 executable gold
rows with zero failures, zero cross-split family or public-input overlap, zero
public/private leakage, all 11 kinds, both languages, and the declared token
limits. The data manifest is under `data/pilots/usefulness-v22`; the split
hashes and full decision are recorded in
[USEFULNESS_V22_REPAIR_RESULT.md](docs/reference/USEFULNESS_V22_REPAIR_RESULT.md).

The run initialized from the immutable V21 adapter, reset the optimizer, and
completed 300 steps. Every selectable checkpoint was scored on development
only. The frozen selection rule chose step 200 at 107/110 exact, or 97.27%.

| Checkpoint | Exact | Routine exact | Routine outcome | Health | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 100 | 105/110 | 65/70 | 65/70 | 7/10 | FAIL |
| 200 selected | 107/110 | 67/70 | 67/70 | 7/10 | FAIL |
| 300 | 107/110 | 67/70 | 67/70 | 7/10 | FAIL |

All three checkpoints had 100% raw protocol validity, zero fixture changes,
and passing fallback, language, ambiguity, unsupported, missing-tool, and
invalid-range checks. They failed the mandatory per-kind floor because health
was 7/10 against a 90% minimum. The three failures are English examples from
one development family where the model proposed `read_file` for a selected
loopback health request instead of the visible `curl` request. This is an
observed model error, not a missing receipt or a fixture mutation.

The V22 sealed set was intentionally not opened. V22 therefore has no sealed
generalization result and is not a releasable candidate. The detailed receipts
are under `artifacts/model-release/pro-training-v22`,
`artifacts/model-release/v22-development-step{100,200,300}`, and
`artifacts/model-release/selection-v22`.

## Execution plan: what to do, how, and how to measure

Complete the following stages in order. Keep V21, its tokenizer, formatter,
validation runtime, and base hashes fixed throughout the primary evaluation.
Store new receipts in a new directory for each run; never overwrite old runs.
Keep sibling gateway configuration and production services outside this work.

### 1. Make the experiment reproducible and freeze its protocol

1. Read the release handoff, training correctness audit, and usefulness protocol
   V1. Preserve V1 and its aborted comparison as history. Write a separate
   `docs/reference/USEFULNESS_PILOT_PROTOCOL_V2.md` for this V21 experiment.
2. Verify the adapter and base hashes listed below. Record checkout commit,
   dirty diff, package manifest, source hashes, Python/dependency versions,
   hardware, and token limits in each run's metadata.
3. Use the scoped test command below. Plain root `pytest -q` previously collected
   duplicate tests from the ignored clean-export directory. Configure collection
   to target `tests/` if repairing the default command. Do not delete archives
   to make collection pass. Ruff was missing in the local environment; install
   the declared development dependencies before claiming lint passed.
4. Audit the experiment runner before use: `scripts/pilot_run.py` currently
   hardcodes the older candidate and dataset. Add explicit package, base path,
   data, endpoint, protocol, seed, and budget inputs, loading V21 through its
   checksummed runtime. Implement ledger and analysis changes under V2; old
   commands must not silently run the old candidate and be labeled V21.
5. Add meaningful tests for wrong-package rejection, hidden-label exclusion,
   incomplete-run rejection, model mismatch, missing usage, and budget stops.

Existing verification commands, run from the repository root:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_assets.py
.venv/Scripts/python.exe -X utf8 -m pytest --import-mode=importlib tests -q
```

Completion: passing relevant tests, verified asset hashes, a frozen V2 protocol,
and documented working CLI examples for the revised runner. Record missing
dependencies as missing, not passed. The previous scoped run passed 158 tests;
that is historical evidence, not a substitute for checking changes.

Observed stage-1 completion: the V2 protocol, explicit V21-only runner,
analysis ledger, and boundary tests are present. `verify_assets.py` verified 49
release files. Scoped collection passed 163 tests with one existing PEFT warning.
After installing `requirements/dev.txt`, Ruff 0.16.7 passed on all changed
Python files. The revised runner records package, base, data, endpoint,
protocol, seed, budget, source, Git, hardware, and dependency identities.

The prepared workflow smoke command is below. It requires a fixed endpoint and
must not be run until the local quality gates pass for a future candidate:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/pilot_run.py --phase smoke --data data/pilots/usefulness-v2 --package artifacts/model-release/package-selected-v21 --base-path artifacts/model-release/base-dependency-v1 --output artifacts/usefulness-pilot/v21-v2/smoke-v1 --max-attempts 12
```

### 2. Build a genuinely new evaluation and independent labels

Create `data/pilots/usefulness-v2` with separate development and sealed evaluation
splits. Start with 120 evaluation families and five instances per family (600
cases), balanced across English and Chinese. This is an initial evaluation
budget, not a claim that 600 cases can certify production reliability.

Have a separate author construct new wording families without copying V8 or
V21 templates or consulting their predictions. Audit the candidate's entire
adapter ancestry, not only V21's final train file, for exact-input and template
overlap. Shared supported tool schemas are intentional. Record authoring method,
family definitions, similarity checks, and any uncertain lineage coverage.
Split families before generating instances; changing IDs and paths does not
create an independent family. Keep final examples out of tuning and checkpoint
selection. Freeze their hashes and scoring code before inference.

Cover all 11 contract kinds. Include ordinary concise requests, paraphrases,
quoted/Unicode paths, literal search strings, inclusive and invalid line bounds,
conflicting prior selections, decoy resources, reordered tools, missing tools,
ambiguous service selection, and unsupported requests. Require public context
to contain enough information to derive each label. Include negative cases
that require recognizing the problem without saying "return ROUTER_FALLBACK"
or announcing "this range is invalid" in the request.

Independently review labels and execute gold calls in disposable fixtures before
model scoring. Keep fixture contents and expected answers out of model inputs.
Add a separately reported stress set for over-budget input, unfamiliar schemas,
instruction-like text in resources, and tool failures. Mark out-of-contract
cases explicitly rather than folding them into supported-task accuracy.

Completion: manifest with counts, hashes, family/language/kind allocations,
lineage audit, public-input semantic audit, token preflight, and gold outcomes.
Any ambiguous label must be fixed before freezing, not after seeing a model miss.

Observed partial stage-2 completion: the manifest and preflight receipts pass
the implemented structural and gold checks for the V2 data. Independent
authoring and complete ancestor template coverage remain unestablished as
detailed in the review above. The retained-source lineage audit is recorded as
partial coverage only. The separate stress receipt is not part of the V2
quality score. The data is frozen and must not be moved into training
after seeing V21 failures. A new repair candidate requires a new evaluation set;
V2 is now exposed and cannot be reused as an independent V22 gate.

### 3. Evaluate frozen V21 quality against useful baselines

Run the new supported evaluation with V21, the unchanged pinned Qwen base, and
the deterministic helper. Give each the same public context and schemas. Freeze
baseline configuration on development data. Do not make baseline rules mimic
sealed labels. Score full arguments and checked fixture outcomes; report exact
call accuracy separately from semantically equivalent successful calls.

The existing model evaluator supports packaged inference. Once stage 2 has
created a compatible manifest and evaluation split, use:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/release_eval.py --data data/pilots/usefulness-v2 --split evaluation --package artifacts/model-release/package-selected-v21 --base-path artifacts/model-release/base-dependency-v1 --protocol docs/reference/USEFULNESS_PILOT_PROTOCOL_V2.md --output artifacts/model-release/v21-usefulness-v2-quality --execute
```

This command requires the new dataset; it does not create it. The separate
stress command is `scripts/stress_eval_v2.py`; it records boundary behavior
without executing actions and is not pooled into the V2 quality score.

Report counts and denominators for:

- Raw valid output, invalid output, explicit abstention, and input-budget rejection.
- Routine exact accuracy and routine outcome success, each over all routine cases.
- Useful coverage: correct accepted routine proposals / all supported routine cases.
- Accepted-call error: incorrect accepted calls / all accepted calls, with numerator
  also shown against all requests. Validation success alone is not correctness.
- Negative-case false acceptance, by ambiguity, unsupported, missing-tool, and
  invalid-range category. Inspect raw generation and the final accepted action.
- Kind, language, and perturbation slices; preserve every failure's input and output.

Carry forward release point gates: raw validity >=99.5%, routine exact and outcome
success >=95%, routine kind and language floors >=90%, ambiguity abstention >=95%,
and zero accepted actions on unsupported, missing-tool, or invalid-range cases.
Require zero unauthorized execution and zero unexpected fixture changes.
These are progression gates for this authored population, not production SLAs.
Report uncertainty clustered by wording family. An all-success bootstrap interval
of [1,1] is not proof of zero failure risk; include a conservative bound or explicitly
state that the sample cannot support the intended reliability claim.

If a gate fails, publish the failure and stop progression to executing model
proposals in a workflow. Any repair becomes a separate candidate with separate
development data and a new sealed evaluation. Do not fine-tune V21 on these tests.

Observed stage-3 result: the V21 package failed routine exactness, checked
outcomes, routine kind floors, language floors, and the invalid-range negative
gate. It passed raw validity, ambiguity, unsupported, missing-tool, and
zero-mutation checks. The base and rules receipts are complete for comparison.
The failure is published in
[USEFULNESS_V2_QUALITY_RESULT.md](docs/reference/USEFULNESS_V2_QUALITY_RESULT.md).

### 4. Measure local runtime cost

Benchmark the unchanged packaged runtime on the intended machine with the same
frozen workload and explicit 1,536-input / 192-output token limits. Time tokenization,
generation, validation, and any queue wait. Record output lengths, warm-up policy,
and concurrent host activity. Report model loading separately from warm inference.

Measure five cold process starts and three warm passes at concurrency 1. Before
testing concurrency 2 and 4, implement or verify a bounded request queue and safe
model access; include queue time and rejected requests. Use fixed scheduled loads
and report actual completions/second rather than inferring throughput from p50.

Report p50/p95/p99, all-request mean, failures/timeouts, process RSS, CUDA allocated
and reserved memory, and device memory observations with their distinct scopes.
Do not extrapolate these GPU results to CPU or Pi. No millisecond target is assumed.
Completion requires reproducible timings and resource receipts; the workflow
comparison in stage 5 determines whether this overhead buys any net benefit.

Observed stage-4 result: the corrected receipt at
`artifacts/model-release/v21-usefulness-v2-runtime-rerun1` recorded five cold
starts, a 2.517-second model load, 66 warm predictions over three passes, serial
throughput of 1.010 completions per second, p50/p95/p99 prediction latency of
0.986/2.400/2.490 seconds, RSS from 639,012,864 to 1,874,182,144 bytes, CUDA
peak allocation of 1,093,508,096 bytes, and zero inference errors. The bounded
queue admitted 2 or 4 requests and rejected the next 2 or 4 requests while
serializing the shared model handle. This is not parallel GPU throughput or a
service guarantee. The first benchmark directory is retained as a corrected
harness-failure receipt.

### 5. Run a controlled end-to-end usefulness comparison

Proceed only after quality gates pass and cloud preflight establishes a usable
control. Use a fixed-model endpoint whose actual model identity and provider usage
are recorded on every turn, including turns after tool observations. The previous
gateway ignored model-pinning intent; repeating its requested model name does not
resolve that problem. Do not change the production slider to force a result.
If no suitable endpoint exists, finish local work and record the endpoint blocker.
A dynamic gateway experiment requires a separate protocol and answers a different,
policy-dependent question; do not silently relax model identity checks.

Current blocker: V21 local quality failed before endpoint work. Do not execute
the V2 workflow against a cloud or production endpoint. The revised runner is
configuration-complete but intentionally has no completed V2 workflow receipt.

Compare three arms on every assigned case:

| Arm | Workflow |
| --- | --- |
| A | Cloud chooses tools, receives observations, and returns the final answer |
| B | Deterministic helper proposes a bounded read or draft before the same cloud workflow |
| C | Immutable V21 proposes a bounded read or draft before the same cloud workflow |

Use matched fixtures and public inputs, the same cloud instructions and schemas,
randomized case and arm order with a recorded seed, and identical turn limits.
Run the primary comparison serially; report concurrent operation separately.
Include local prediction and validation inside C's episode clock, and helper work
inside B's. Include cloud verification, corrections, failed attempts, and tool
execution in every arm. Writes stay review-only drafts. Correct final answers must
have supporting real observations; matching answer strings alone is insufficient.

Freeze a maximum of three cloud turns per episode, two tools per turn, 45 seconds
per HTTP attempt, and zero automatic retries. For 600 cases across three arms,
reserve at most 5,400 scored attempts plus 12 development smoke attempts. Before
any paid run, record the endpoint price, an explicit dollar ceiling, and a token
admission budget covering maximum input plus output on outstanding requests.
An unavailable spending allowance is a blocker for paid execution, not for local
preparation. This plan itself does not authorize an unspecified cloud bill.
Record all prior pilot consumption separately; do not erase it on restart.

Stop on missing usage, unexpected model identity, unaccounted compound calls,
budget exhaustion, or a boundary violation. Retain the terminal receipt and all
assigned failures. Do not publish a completed comparison from a partial run.

Measure final task success, all-episode latency, prompt/completion/cached tokens,
actual monetary cost where available, tool calls, correction turns, failed or
unused proposals, and fallback overhead. Report routine and negative cases
separately. Authored task balance cannot estimate production offload prevalence.

### 6. Analyze and decide

Freeze the sample size and statistical method in V2 before scored runs. Use paired
case differences and family-level uncertainty with 10,000 seeded resamples, plus
a prespecified conservative treatment for zero observed failures. Account for
both comparisons and preselect latency or tokens as the primary benefit metric.
Do not choose whichever metric looks best after the run.

Before spending the cloud budget, simulate the planned analysis on development
assumptions to assess whether the design can resolve a two-percentage-point quality
margin. V1's Hoeffding bound is too wide for that margin in a small family sample;
do not reuse it and expect a likely GO. Document a defensible V2 method and power
assessment. If the feasible budget is too small, label the experiment exploratory
and accept INCONCLUSIVE rather than weakening the margin after seeing results.

GO for a limited supervised pilot requires all of:

- Stage 3 quality and execution-boundary gates pass.
- C's observed final success is no worse than A or B, and the prespecified one-sided
  95% lower bounds on C-minus-comparator success are at least -0.02 for both.
- C improves the preselected primary metric by at least 10% versus both A and B,
  with uncertainty excluding no improvement. Define savings as
  `1 - mean(C) / mean(comparator)` using all assigned episodes.
- Report the other resource metric and tail latency. An observed deterioration
  above 10% in either is a material tradeoff and requires a qualified decision,
  not an unqualified GO.
- Complete accounting, reproducible receipts, and no unauthorized execution.

NO-GO applies when a quality/boundary gate fails or evidence demonstrates a
material regression. INCONCLUSIVE applies when uncertainty, incomplete accounting,
or an unavailable control prevents a decision. A GO authorizes a recommendation
for a limited pilot, not production deployment. Any observed advantage applies
only to the stated task distribution, hardware, and cloud control.

Write `artifacts/usefulness-pilot/v21-v2/<run-id>/REPORT.md` and `summary.json`,
with a compact durable report under `docs/reference/`. Preserve raw predictions,
attempt/episode receipts, protocol/data hashes, source snapshots, resource samples,
failure analysis, uncertainty, and exact reproduction commands. Recommend one
evidence-driven follow-up: broader real-intent evaluation, runtime optimization,
a new candidate, or stopping investment in this approach. Quantization or grammar
changes come after the baseline and require their own paired reevaluation.

## Next-phase definition of done

- [x] Audit fail-closed behavior, identity-bound local quality decisions, and focused regression tests are complete. Full provenance remains partial.
- [x] Dataset hashes, declared family splits, and executable gold-label receipts are present.
- [ ] Independent authoring and full ancestor template audit are established.
- [x] V21, unchanged base, and rules have comparable local quality receipts.
- [x] V22 repair data has a separate manifest, preflight, semantic audit, training receipt, and development-only checkpoint selection.
- [x] V22 development failure is reproduced at all selectable checkpoints and has a bounded failure analysis.
- [x] Family-level power assessment and simultaneous-comparison coverage are documented prospectively.
- [x] Local latency, serial throughput, memory, cold starts, and bounded queue behavior are measured under declared conditions.
- [ ] V22 sealed evaluation is intentionally not run because development quality failed.
- [ ] Independent authoring and complete ancestor-lineage coverage are established.
- [x] Retained-source lineage and overlap audit is recorded with explicit limitations.
- [x] Separate out-of-contract stress receipt is complete and kept outside quality scoring.
- [ ] Retained model/checkpoint files are within the 5,000,000,000-byte budget.
- [x] The exact local quality blocker is documented.
- [ ] A complete matched workflow comparison and prospectively justified statistical analysis establish workflow value.
- [x] Final bounded local NO-GO report states what the evidence supports for V21 and V22. No workflow verdict is claimed.

## Current stop and next action

V21 and V22 are stopped at local quality gates. Do not run a cloud workflow,
do not change the V21 package, do not package V22, and do not rerun V8 as an
independent gate. Preserve the following evidence:

- `artifacts/model-release/v21-usefulness-v2-quality`
- `artifacts/model-release/base-usefulness-v2-quality`
- `artifacts/model-release/rules-usefulness-v2-quality`
- `data/pilots/usefulness-v2`
- `artifacts/model-release/pro-training-v22`
- `artifacts/model-release/v22-development-step100`
- `artifacts/model-release/v22-development-step200`
- `artifacts/model-release/v22-development-step300`
- `artifacts/model-release/selection-v22`
- `data/pilots/usefulness-v22`
- `docs/reference/USEFULNESS_V22_REPAIR_RESULT.md`
- `data/pilots/usefulness-stress-v2`
- `artifacts/model-release/v21-usefulness-v2-stress`
- `artifacts/model-release/v21-usefulness-v2-runtime-rerun1`
- `artifacts/model-release/v21-usefulness-v2-runtime`
- `docs/reference/USEFULNESS_V2_STRESS_PROTOCOL.md`
- `artifacts/model-release/usefulness-v2-lineage-audit.json`
- `docs/reference/USEFULNESS_V2_LINEAGE_AUDIT.md`
- `docs/reference/MODEL_STORAGE_RETENTION_HOLD.md`

The product and research decision is resolved above: execute bounded NO-GO
closure, including the selected V22 snapshot retirement. Treat the current model as a research candidate that shows a
large improvement over the unchanged base on authored local tasks, but does
not meet its reliability contract. Do not advertise it as production-ready,
workflow-proven, or generally effective. The cloud comparison remains
unanswered, not positive.

Inactive future design reference: if a new research cycle is separately
opened, V23 would require the following. These steps are outside this closure:

1. Author `data/pilots/usefulness-v23` and a matching protocol before training.
   Use new train, development, and sealed evaluation families. Do not copy V2
   or V22 evaluation rows, predictions, or labels into training or checkpoint
   selection. Add balanced English health prompts that vary the wording around
   a selected loopback endpoint, while retaining configuration reads and decoy
   resources as hard negatives. Keep the URL derivable from public context.
2. Run semantic preflight before CUDA. Verify public/private separation,
   concrete health URLs, selected-resource consistency, all 11 kinds, both
   languages, token limits, family-disjoint splits, and executable gold
   outcomes. Record exact hashes, family counts, language counts, kind counts,
   and label exposure. Fix any ambiguous label before training.
3. Start a fresh V23 adapter run only after preflight. A V21 initializer is
   allowed as a separate candidate, but V21 and V22 remain immutable. Keep the
   current recipe unless a new choice is documented before training:
   rank 16, alpha 32, dropout 0.05, seven projection targets, BF16 CUDA,
   maximum 1,536 tokens, seed 42, and a declared step budget. Report rows
   presented by kind and language at every checkpoint.
4. Evaluate every selectable V23 checkpoint on V23 development only. Select by
   the predeclared exactness, validation-loss, and earliest-step rule. Never
   select on a sealed set.
5. Require all development gates before opening the sealed set: raw validity
   at least 99.5%, routine exactness and checked outcomes at least 95%, every
   routine kind at least 90% including health, English and Chinese routine
   slices at least 90%, ambiguity abstention at least 95%, exact zero
   acceptance for unsupported, missing-tool, and invalid-range cases, zero
   unauthorized execution, and zero fixture changes.
6. Only after development passes, freeze and score at least 120 new sealed
   wording families with five instances each. Report search, draft, invalid-
   range, health, language, and family-clustered uncertainty separately.
7. Only after the sealed set passes may the selected adapter be packaged and
   its manifest, base hash, cold and warm latency, throughput, memory, fixed-
   model cloud preflight, and three-arm workflow comparison be measured. If
   V23 fails the same gates, stop investment rather than expanding the training
   budget toward a predetermined positive result.

## Completed weight-release record

## Outcome

The V21 Wrench-Pro adapter trained successfully, passed the frozen quality
gates on an unused holdout, passed a fresh context perturbation suite, and
loaded from the final package in a newly provisioned environment. The package
is usable by another operator when paired with the pinned Qwen base and the
documented dependencies.

This is a release decision for an adapter and its local inference runtime. It
does not certify a hosted service, a router policy, cloud failover, arbitrary
shell execution, or production traffic reliability. Those remain separate
workstreams.

## Final artifact

- Package: `artifacts/model-release/package-selected-v21`
- Package manifest status: `WEIGHTS READY FOR RELEASE`
- Package manifest SHA-256:
  `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`
- Adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Base: `Qwen/Qwen2.5-0.5B-Instruct`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Base weight SHA-256:
  `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`

The package contains the adapter, exact tokenizer files, inference runtime,
training contract and metrics, pinned requirements, runnable example, model
card, data card, evaluation report, lineage, resource report, evaluation
receipts, checksums, and upstream plus Wrench license notices.

## Evidence

| Gate | Observed result | Receipt |
| --- | --- | --- |
| Training | 300 steps, 4,800 presentations, finite loss, optimizer reset from V20 | `artifacts/model-release/pro-training-v21/run.json` |
| Data semantics | Zero errors and zero warnings for train, development, and evaluation | `artifacts/model-release/audit-v21-semantic-{train,development,evaluation}.json` |
| Data preflight | All splits valid within the 1,536 input and 192 output token budgets | `artifacts/model-release/data-preflight-v21-clean/preflight.json` |
| Exposure | Every task kind and language present at steps 100, 200, and 300, with no repeated rows | `artifacts/model-release/audit-v21-exposure.json` |
| Checkpoint selection | Steps 100, 200, and 300 each scored 176/176; step 200 selected by the frozen rule | `artifacts/model-release/selection-v21/selection.json` |
| Frozen holdout | 440/440 exact, 280/280 routine, 160/160 fallback, 11 kinds, both languages, zero filesystem changes | `artifacts/model-release/v21-package-independent-evaluation/summary.json` |
| Fresh context suite | 220/220 exact, 140/140 routine, 80/80 fallback, reordered context and unseen invalid-range wording | `artifacts/model-release/v21-package-context-release-v2b/summary.json` |
| Fresh package load | Passed in new Python 3.14 environment with pinned CUDA dependencies and empty model cache | `artifacts/model-release/v21-release-verifier-final3/receipt.json` |

The final holdout and context suite were scored after the adapter was frozen.
Neither set was imported into training. The earlier V16 and V20 failures are
preserved as diagnostic history and are not reused as release evidence.

## Training record

V21 used `data/pilots/release-generalization-v21` with 6,144 authored rows in
192 training families, 176 development rows, and 440 frozen evaluation rows.
The train split has SHA-256
`7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`.
English and Chinese are balanced. The 11 task kinds are balanced except for a
deliberate double-sized `lines` slice. Invalid ranges cover zero or negative,
reversed, and beyond-EOF cases with the file length visible in public context.

The run used microbatch 2, accumulation 8, learning rate 2e-6, seed 42, and
the pinned Qwen base. It initialized a fresh optimizer from the V20 adapter
SHA-256 `a15d22b2f30287a1ccc26100c4e0e552f0516c8d05a8639bbbf07ee3be2e0fda`.
The selected step-200 validation loss was `0.000010001144472248717`.

The run's sequential loader exposed all kinds and languages at every declared
checkpoint. At step 300 it had presented 4,800 unique rows, 2,400 in each
language, with no repeated presentations. This corrects the V16 exposure
failure documented in [the correctness audit](docs/reference/TRAINING_CORRECTNESS_AUDIT.md).

## Quality interpretation

Within the authored task contract, the measured model behavior is usable:

- It returns valid tool calls for supported operations with complete arguments.
- It explicitly abstains for ambiguous, unsupported, unavailable-tool, and
  invalid-range cases.
- It preserves the execution boundary. The packaged runtime proposes an action
  and executes no generated tool. Disposable evaluator fixtures recorded zero
  unexpected filesystem changes.
- On the final Windows and CUDA measurements, prediction latency was 1.175
  seconds at p50 and 2.466 seconds at p95. These are one-machine observations,
  not service targets.

The evidence does not support claims about arbitrary repositories, arbitrary
PowerShell, POSIX environments, CPU throughput, high-concurrency serving,
router savings, cloud routing, or production traffic. A merged, quantized, or
converted artifact needs a new evaluation before release.

## Completed weight-release definition of done

- [x] Corrected training data passes semantic and structural audits.
- [x] Training exposure is deterministic, mixed, and recorded at each
  checkpoint.
- [x] A bounded V21 run completed with finite losses and recoverable retained
  checkpoints.
- [x] Every selectable checkpoint was evaluated on development data and the
  selected adapter was frozen before final scoring.
- [x] The exact package passes the frozen holdout and the fresh context suite.
- [x] The exact package loads and predicts in a newly provisioned environment.
- [x] Package documentation, provenance, evidence, resource measurements, and
  licensing notices are present and checksummed.
- [x] Historical V21 model and checkpoint files were outside Git and within the storage budget at release time.
- [x] Router tuning, gateway integration, and deployment remain explicitly
  deferred.

## Storage policy and retained files

The model and checkpoint budget is 5,000,000,000 bytes. The measured retained
weight and checkpoint total is 4,447,301,853 bytes. It includes the pinned base,
the V20 initializer package, the final V21 package, and exactly three V21
trainer snapshots: `step-000100`, `step-000200`, and final `checkpoint`.

That figure is historical. The current explicit audit, which also preserves the
three V22 development snapshots, totals 7,974,854,728 bytes and exceeds the
budget by 2,974,854,728 bytes. The receipt is
`artifacts/model-release/storage-audit-20260910.json`. No V23 weights may be
created until retention is explicitly resolved and a new audit is within the
budget.

Superseded selected packages V16 through V19 were pruned after their receipts
were preserved. The continuous sidecar trainer is stopped. No model weight or
checkpoint is tracked by Git; the current index contains zero files with model
weight suffixes. The separate `clean-env-v21` virtual environment is retained
for reproducibility and is dependency storage, not part of the model/checkpoint
budget. The older duplicate `clean-env-v1` environment was removed.

The detailed operator instructions and recovery notes are in
[MODEL_RELEASE_HANDOFF.md](docs/reference/MODEL_RELEASE_HANDOFF.md). The historical data
repair rationale remains in [TRAINING_REPAIR_HANDOFF.md](docs/reference/TRAINING_REPAIR_HANDOFF.md)
and [TRAINING_CORRECTNESS_AUDIT.md](docs/reference/TRAINING_CORRECTNESS_AUDIT.md).

## Weight preservation during the next phase

Keep the final V21 package immutable. The plan above establishes whether further
training or optimization is worth doing. If new failures justify a candidate,
create a versioned training and evaluation contract first. Preserve the original
release evidence and the historical storage record; remeasure storage before
adding weights. Production deployment remains a separate decision.
