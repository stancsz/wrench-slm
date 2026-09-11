# Wrench-SLM: evidence-backed, oracle-free selective offload

> Compatibility execution record. The canonical Goal-Driven Engineering
> contract is [`goals/active/selective-offload-real-runtime-v2/GOAL.md`](goals/active/selective-offload-real-runtime-v2/GOAL.md).

Updated: 2026-09-11
Status: active
Owner: agent executing this goal
Goal ID: selective-offload-real-runtime-v2
Target deliverable: one useful local completion path with a safe fallback, plus a measured enable or disable decision

## Steward contract

### Outcome and why

Make a small, genuinely useful fraction of routine developer work complete
locally when the result can be established from public request context and a
real tool observation. Send every other request to the stronger model with its
intent and context intact. The purpose is to reduce stronger-model work without
making the user absorb incorrect local results.

Small coverage is worthwhile if it is reliable and saves provider work after
all local execution, validation, fallback, retries, and latency are counted.
Rules may be the final product. The learned component earns inclusion only if
it improves on the same rules and fallback path.

The success decision also requires trusted scenario data. The evaluation must
include a provenance-labeled replay population derived from representative,
脱敏 production traces when available, plus clearly separated synthetic and
adversarial cases. It must model the actual cloud billing dimensions and
record enough per-episode usage to calculate token and cost impact. Authored
fixtures alone cannot establish production prevalence or savings.

### Source of truth

- `NORTHSTAR.md` owns durable product direction.
- This file is the only active execution contract.
- `docs/reference/SELECTIVE_OFFLOAD_V1_RESULT.md` and its receipts are
  historical diagnostic evidence, not proof of this goal's runtime gate.
- V21/V22 and V2 usefulness records remain historical evidence and must not be
  rewritten as product readiness.

### Critical runtime invariant

The local routing and completion decision must use only information that exists
in a real request: public prompt and context, declared tool schemas, policy
configuration, real tool observations, execution status, and a runtime-safe
filesystem or resource boundary.

It must not read `expected_answer`, fixture gold, task kind labels used only by
the evaluator, hidden fixture content, or an offline score while deciding
whether to return a local result. Offline gold may score a completed episode
after the route is fixed. It may never rescue, reject, or manufacture a
runtime result.

The historical selective route violated this invariant by using
`score_answer(env.task, ...)` before selecting `route: local`. The reported
305/600, 100% accepted-precision fixture result remains an offline diagnostic
only. The replacement runtime removes that dependency; its M1 and M2 evidence
is recorded below and must not be conflated with the historical result.

### Required behavior

1. Determine eligibility from public request/context and declared policy only.
   Prefer rules where they cover the request. A learned proposal is optional.
2. Allow only an explicit, narrow, read-only operation contract. Validate tool,
   complete arguments, visible resources, line bounds, command allowlist, and
   request-to-action alignment before execution.
3. Return a local result only when a runtime verifier proves that the observed
   tool output satisfies the declared shape of the request. The verifier must
   not be an expected-answer comparison in disguise.
4. If the action, observation, output format, boundary state, or verifier is
   uncertain, invalid, unavailable, timed out, or fails, fall back. Preserve
   the original request and relevant observation.
5. Keep writes as review-only drafts. Arbitrary shell, deployment, training,
   and broad tool autonomy are outside this goal.

### Ordered milestones

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| M1: Oracle-free local path | A callable or CLI route for one read-only task shape, returning a local result or explicit fallback | Runtime code and tests prove it works with no gold fields available, completes with zero cloud calls, and falls back on invalid, irrelevant, timeout, tool-error, and verifier-failure cases |
| M2: Fresh bounded evidence | One frozen selector and verifier evaluated on fresh disjoint families | Every row is routed without gold; offline scoring reports accepted coverage, correct local completions, errors, fallbacks, boundary results, and language slices |
| M2-data: Trusted scenario and cost evidence | A provenance-labeled replay set and a reproducible cost ledger without leaking private content | Production-derived, synthetic, and adversarial populations are separated; sampling, redaction, hashes, price assumptions, usage fields, and replay eligibility are recorded |
| M3: Practical value | Matched A/B/C complete workflow comparison on a fixed stronger model | Same tasks and executor across arms, complete token and latency accounting, final outcomes, and family-paired uncertainty |
| M4: Operator decision | Runnable documented default and bypass | Evidence mapping, supported-scope table, receipts, and an explicit learned-enabled, rules-only, or disable verdict |

### Current deliverables

The following is the current delivery list. Checked items are available as
local, receipt-backed capability evidence. They do not establish production
value or a released autonomous tool path.

- [x] **Bounded local completion:** an oracle-free `read_file` path for one
  visible file or configuration-region request, with a runtime verifier and
  explicit fallback.
- [x] **Safety and local-evaluation receipts:** gold-free fallback tests,
  frozen identity/protocol receipts, and a held-out 600-request English and
  Chinese evaluation. The verified supported slice is configuration reads and
  bounded line reads only.
- [x] **M2 evidence report:** route, observation, verifier, boundary, and
  post-route offline-correctness records, including the family-bootstrap
  receipt and zero observed accepted errors in the 90 locally returned rows.
- [x] **Trusted-data intake tooling:** source discovery, deterministic
  authorized-export redaction, scenario audit, replay scheduling, usage
  profiling, and a readiness verifier. This tooling is ready to process an
  authorized export but is not itself trusted replay evidence.
- [ ] **M2-data input package:** an authorized, redacted export containing
  public prompt/context, stable gateway request IDs, matching usage records,
  a versioned cloud price ledger, and a defined clean duration unit. Freeze
  its provenance-separated replay manifest and pass
  `scripts/verify_trusted_readiness.py`.
- [ ] **Future M3 matched workflow receipt:** only after a candidate passes
  its frozen local-quality gate, M2-data passes, and an operator supplies
  explicit provider attempt and cloud-token ceilings, run the fixed
  `minimax/minimax-m3` A/B/C comparison and capture every call, token, cost,
  latency, fallback, correction, boundary, and final-outcome record. The
  current V21 broad candidate is not eligible for this paid comparison.
- [ ] **M4 operator package:** publish the reproducible commands, hashes,
  scope table, bypass procedure, denominators, and one evidence-bounded
  verdict: learned-enabled, rules-only, or disable.

### Remaining work from independent repository review

Complete these items in order without weakening the M2-data, M3, or M4 gates
above. Documentation, plans, local fixtures, and preflight receipts do not
count as completion unless the stated observable evidence exists.

- [ ] **Preserve the current repository state:** split the current modified and
  untracked product documents, runtime code, datasets, tests, and evidence into
  small reviewable commits. Record the resulting commit SHAs and confirm that
  `git status --short` contains only explicitly identified unrelated user work.
- [ ] **Choose and prove the distribution contract:** either make the exact V21
  adapter and complete checksummed runtime package retrievable by an
  unauthenticated third party, or consistently label it a private release
  candidate. Verify a fresh clone can run one documented command sequence that
  fetches, checksum-verifies, loads, and predicts with the pinned base. Do not
  describe the LoRA adapter as standalone weights.
- [ ] **Obtain evidence outside the authored benchmark loop:** supply the
  authorized, deterministically redacted natural request/context records
  required by M2-data, or an independently authored external evaluation. Keep
  authored fixture results labeled as regression and local-capability evidence,
  not independent generalization or production prevalence.
- [ ] **Complete the matched product-value decision:** for a candidate that
  first passes a separately frozen local-quality gate, complete M2-data and the
  frozen cloud-only, rules-plus-fallback, and learned-plus-fallback M3 run.
  Measure final outcomes, calls, tokens, cached tokens, retries, corrections,
  billed or ledger-derived cost, local overhead, and total latency. Apply the
  M4 stop rule even when the correct answer is rules-only or disable.
- [ ] **Make the release package operationally ordinary:** provide installable
  project metadata or an equivalently reproducible entry point, remove the
  checksum dependency on mutable `__pycache__` files, and prove the package
  works without requiring callers to know the historical `python -B`
  workaround or repository-relative internal paths.
- [ ] **Establish enforceable repository quality gates:** make the maintained
  source pass its declared Ruff configuration, keep the full `tests` suite
  green, and add CI gates for lint, package construction, clean-package load,
  checksum verification, and a bounded security smoke test. Record exact
  commands and observed outputs rather than copying stale test counts.
- [ ] **Harden or retire the legacy sidecar:** before any network exposure,
  default it to loopback or require authentication, cap request-body size,
  reject malformed lengths, and add negative tests for unauthenticated,
  oversized, and concurrent requests. If it remains historical only, move it
  behind an explicit legacy boundary and remove deployment-ready implications.
- [ ] **Reconcile public claims and status surfaces:** update README, release
  cards, GitHub Pages data, status pages, and goal evidence so they agree on
  current test counts, private versus public distribution, V21's LoRA status,
  the fresh V2 NO-GO, 15% authored selective coverage, and the live canary's
  zero token savings. A mechanical documentation check must fail on stale or
  contradictory release-state fields.

Start with the smallest observation-complete read-only shape that can be
honestly verified, for example returning the contents of one explicitly
selected visible file. Add another shape only after the first passes M2 and
shows incremental value. English and Chinese belong in the fresh evaluation;
unsupported wording may fall back.

### Measurement and decision rules

For N assigned requests, report local attempts L, locally accepted results A,
offline-correct accepted results K, and final successful hybrid outcomes H:
L/N, A/N, K/N, K/A, (A-K)/A, and H/N. An empty accepted set has zero useful
coverage and cannot pass.

Record each request's route reason, proposed action, policy result, tool
observation, runtime-verifier result, fallback state, and offline score. Gold
is marked as post-route evaluation only. Unnecessary fallback is an offline
metric, never an input to routing.

For the same assigned tasks, compare provider prompt plus completion tokens:
T_A for cloud-only, T_B for rules plus the identical completion/fallback path,
and T_C for rules plus the learned proposal and that same path. Report token
deltas, cached tokens, calls, billed cost when present, local load/inference/
validation time, total latency, corrections, and failures. B must not be made
weaker than C.

Enable the learned proposal only when C improves on B with complete accounting
and no observed local-caused wrong completion or boundary violation. If B saves
work and C does not add value, use rules plus fallback. If neither earns value,
disable local completion. Any positive saving is useful but must be labeled
exploratory when the uncertainty interval includes no saving or the sample is
authored.

### Acceptance criteria

- [x] M1 removes the runtime dependency on `score_answer`, `env.task`, and all
  private gold fields. A mechanical regression test fails if the local route
  imports or reads them.
- [x] M1 has a runtime-safe verifier for the selected task shape and a test
  that completes a local result using an environment that exposes no expected
  answer or fixture gold. The successful case makes zero provider calls.
- [x] M1 tests explicit fallback for operator bypass, invalid proposal,
  irrelevant but syntactically safe proposal, timeout, tool error, malformed or
  insufficient observation, and unexpected boundary mutation.
- [x] Freeze candidate identity, operation contract, selector, verifier,
  threshold, data hashes, scoring, token budget, and A/B/C analysis before M2
  final evaluation. The old V1 selection may guide development but cannot be
  final evidence for this changed runtime boundary.
- [x] M2 evaluates fresh disjoint families, includes all rejections and
  adversarial cases, and records offline correctness separately from runtime
  routing. It has nonempty correct local coverage, zero observed wrong accepted
  outcome, zero accepted prohibited action, and zero unexpected mutation.
- [ ] M2-data establishes trusted scenario data before any production-value
  claim: read-only ingestion of representative production traces where
  authorized, deterministic redaction and provenance, separate synthetic and
  adversarial strata, a frozen replay manifest, and a versioned cloud price
  ledger. No generated fixture or teacher-distilled row may be labeled as
  production traffic.
- [ ] M3 runs complete matched A/B/C episodes on the same endpoint, model,
  task list, executor, outcome checker, bounded turns, and accounting. It
  records every call including fallback and losing episodes.
- [ ] M3 shows final observed outcomes no worse than cloud-only with no
  observed local-caused error or boundary violation, and reports family-paired
  uncertainty for outcome and token deltas.
- [ ] M4 publishes reproducible commands, hashes, receipt paths, supported
  scope, bypass steps, actual denominators, and the honest operator decision.
  It distinguishes authored fixtures from real traffic and never calls this
  release-ready or production-proven without separate evidence.

### Constraints and escalation

Use the immutable V21 package and existing helper. Do not retrain or create a
new model tier for this goal. Limit development to the oracle-free verifier
change plus at most one selection adjustment based on development evidence.
Use a new held-out split after that adjustment. Do not prune failed final rows
or tune against the final split.

Local coding, fixtures, tests, and non-provider receipts are authorized. A
complete A/B/C provider run requires a concrete explicit spending ceiling and
fixed endpoint/model identity. If none is already available after M2, record
the precise run plan and mark only M3 blocked. Do not treat it as zero cost or
an unlimited budget.

No production deployment, arbitrary shell, broad model mastery, or storage
cleanup is required. Low coverage is not a blocker. A missing provider ceiling,
evidence-integrity failure, or a product decision outside this contract is an
escalation condition.

### Evidence and completion

Write the frozen contract to
`docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md`, immutable
receipts to `artifacts/selective-offload-real-runtime-v2/<run-id>/`, and the
durable result to
`docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_RESULT.md`. Include exact
commands, source/config/data hashes, assigned IDs, route and verifier receipts,
tool observations, endpoint identity, usage, outcomes, and environment facts.
Do not include secrets.

The goal is done only when M1 through M4 have evidence and the operator verdict
is recorded. `MEASURED SELECTIVE BENEFIT`, `RULES-ONLY VALUE`, and `NO MEASURED
BENEFIT` are valid final verdicts. A local implementation without the A/B/C
comparison is not done and cannot claim measured savings.

## Builder execution record

### Current approach

Replace oracle-dependent local success with a runtime-safe observation verifier
for one read-only shape. Keep gold scoring in the offline evaluator only. Then
freeze a new protocol and fresh fixtures, evaluate the narrow path, and only
then seek the bounded provider comparison.

### Immediate next action

First establish the trusted scenario-data gate. Use the existing read-only log
ingestion path, but stop and report missing or unauthorized production traces
instead of fabricating them. For each candidate row, retain a stable source
identifier, timestamp bucket, platform, request/tool shape, redaction status,
and provenance class such as `observed_production_replay`, `synthetic`, or
`adversarial`. Exclude secrets, credentials, raw user content, and unresolved
rows from evaluation. Freeze the resulting replay manifest and hashes.

Then create a versioned cloud cost ledger containing provider, model, input
price, output price, cached-input price if applicable, currency, effective
date, and source. Replay the same assigned IDs through A/B/C and capture
prompt tokens, completion tokens, cached tokens, request count, retries,
latency, fallback, final outcome, and calculated cost. Report production-
derived, synthetic, and adversarial strata separately, with weighted and
unweighted results. Never mix cost estimates with provider-reported cost
without labeling the difference.

Run M3 only after the trusted-data gate passes and the user supplies an explicit
provider token ceiling and attempt ceiling for the fixed endpoint
`http://127.0.0.1:4000/v1/chat/completions` and model
`minimax/minimax-m3`. Do not guess either ceiling. Then:

1. Run the prepared `scripts/selective_pilot_run.py` command in the protocol
   with `--max-attempts <approved-attempt-ceiling>`,
   `--max-cloud-tokens <approved-token-ceiling>`, and
   `--authorize-paid-run`. Use the frozen package, split, selector, and
   receipt. Stop on any accounting, budget, or boundary failure.
2. Run `scripts/analyze_selective_workflow.py` on the completed receipt and
   record all A/B/C rows, provider prompt/completion/cached/billed tokens,
   calls, retries, fallbacks, corrections, failures, local load/inference/
   policy/execution/formatting time, total latency, final outcomes, and
   family-paired uncertainty.
3. Calculate B versus A and C versus B for token use, latency, cost, and final
   success. Enable learned C only if C improves on B with complete accounting,
   no local-caused wrong result or boundary violation, and no worse final
   outcomes than A. Otherwise retain rules-only B or disable local completion.
4. Update the result and this record with the measured verdict. If no ceiling
   is authorized, leave M3 open as the only gap and use the verified read-only
   shape with a bypass for everything else.

### Progress

- [x] Removed the runtime route's dependency on `score_answer`, `env.task`,
  and private gold fields.
- [x] Added a pre-execution `read_file` operation boundary and a public-input
  observation verifier.
- [x] Added gold-free, zero-cloud, operator-bypass, invalid, irrelevant,
  timeout, tool-error, malformed-observation, verifier-failure, and mutation
  tests.
- [x] Created and froze the new protocol, runtime hash, package identity, and
  fresh data campaign before held-out evaluation.
- [x] Completed the frozen v2 600-task held-out local evaluation and family
  bootstrap receipt.
- [x] Built and tested the trusted-data intake and independent readiness gate.
- [ ] Obtain and validate the authorized M2-data input package.
- [ ] Record the current V21 no-paid-M3 decision and define any future
  candidate's separate quality gate before seeking an A/B/C comparison.

### Verified evidence and remaining gap

- A fresh V2 usefulness receipt now provides a direct quality stop signal for
  the immutable V21 package: on 600 authored, independently exercised Windows
  cases, V21 achieved 245/385 routine exact outcomes (63.64%) and 265/385
  routine checked outcomes (68.83%). There were 91 wrong accepted routine
  proposals and 7/50 invalid-range requests were incorrectly accepted. The
  package caused zero fixture mutations, but its local prediction latency was
  1.179 seconds p50, 2.669 seconds p95, and 3.033 seconds p99. This is a
  bounded authored result, not production evidence. It establishes that V21
  is useful only for narrower slices and is NO-GO for the broader workflow
  comparison; do not spend provider budget on A/B/C for this candidate.
- The available V22 development candidate is not a passed replacement: its
  selected step-200 checkpoint scored 107/110 overall and 67/70 routine
  outcomes, but `task_slice_floor` failed because the frozen per-kind floor is
  90% and the health slice was only 7/10. The selection receipt therefore
  records `TRAINED CANDIDATE, QUALITY GATES FAILED` and
  `release_approved: false`. This confirms that overall accuracy alone is not
  sufficient evidence of practical usefulness for an automatic tool path.

- The prior 305/600 result used the oracle-dependent route and is retained only
  as historical diagnostic evidence.
- The new targeted oracle-free suite passes 10 tests. The scoped repository
  suite passes 179 tests with the archived duplicate test tree excluded. The
  default repository-wide pytest command still has duplicate module names in
  `artifacts/repository-cleanup/clean-export/tests`.
- The frozen development receipt is
  `artifacts/selective-offload-real-runtime-v2/development-eligible-v2`:
  20/120 local results, all offline-correct, with zero accepted errors and
  zero mutations.
- The authoritative held-out receipt is
  `artifacts/selective-offload-real-runtime-v2/evaluation-eligible-v2`:
  90/600 local results (15.00%), all 90 offline-correct, with zero accepted
  errors, zero prohibited local actions, and zero mutations. English and
  Chinese each returned 45/300 local results with 100% observed precision.
- The 20,000-resample family-bootstrap receipt reports exploratory useful
  coverage of 9.17% to 21.67% and accepted precision of 100% to 100%:
  `artifacts/selective-offload-real-runtime-v2/evaluation-eligible-v2/family-bootstrap.json`.
- The current frozen identity is recorded in
  `artifacts/selective-offload-real-runtime-v2/selection-eligible-v2.json`.
  The policy, runtime, protocol, package, and split hashes in that receipt
  are the authoritative M2 identity.
- The M3 runner preflight completed without loading the local model or making
  provider calls. It verified the frozen receipt for all 600 assigned
  evaluation tasks at the fixed endpoint/model:
  `artifacts/selective-offload-real-runtime-v2/preflight-3/run.json`.
- Trusted production-derived scenario data has not yet been supplied to this
  workspace. The existing authored 600-task campaign is valid for the local
  safety gate but cannot support a real-traffic prevalence or cost claim.
- The next data deliverable is a frozen, redacted replay manifest plus a
  versioned cloud price ledger and a no-provider replay report. Its required
  measures are stratum counts, source coverage, redaction failures, route
  coverage, local and cloud token totals, cached tokens, request/retry counts,
  latency, fallback rate, final outcomes, and cost sensitivity to the stated
  price assumptions.
- The trusted scenario audit entry point is
  `scripts/trusted_scenario_audit.py`, with four passing tests in
  `tests/test_trusted_scenario_audit.py`. It rejects private evaluator fields,
  likely secrets, incomplete redaction, duplicate IDs, invalid provenance,
  invalid price ledgers, and production claims with no observed production
  replay. Its procedure is documented in
  `docs/reference/TRUSTED_SCENARIO_DATA_V1.md`.
- The read-only source discovery tool is
  `scripts/discover_production_sources.py`. It records only file metadata,
  hashes, event counts, and tool distributions, never raw log content. Its
  receipt must remain a source inventory, not a replay dataset or production
  claim.
- A read-only inventory of the available LeanRouter log source found 11
  candidate files, 12,226 completed tool records, and 92,002 event records
  with no read errors. The receipt is
  `artifacts/trusted-scenarios/source-discovery-20260910/source-discovery.json`.
  The source still requires operator authorization and deterministic redaction
  before any row can enter replay.
- The refreshed inventory receipt is
  `artifacts/trusted-scenarios/source-discovery-20260910-v2/source-discovery.json`.
  It found 11 files, 12,226 completed tool records, and 92,024 valid event
  records with no read errors. Field coverage includes prompt and completion
  token fields on 30,730 events, cached-token fields on 883 events, duration
  fields on 30,730 events, and served-model fields on 16,608 events. These are
  metadata-coverage observations only; they do not prove authorization,
  redaction, provider billing accuracy, or production representativeness.
- A replay-readiness inventory is recorded in
  `artifacts/trusted-scenarios/source-discovery-20260910-v3/source-discovery.json`.
  It confirms that the source has tool, request ID, prompt-token,
  completion-token, cached-token, served-model, and duration fields, but no
  real prompt or context field. Therefore the source supports cost and route
  distribution analysis, but cannot by itself support a trusted Wrench
  semantic replay. A separately authorized prompt/context export is required.
- A fresh read-only inventory was run after the usage profile and is recorded
  in `artifacts/trusted-scenarios/source-discovery-20260910-v4/source-discovery.json`.
  It scanned 11 files, 12,226 completed tool records, and 92,028 valid event
  records with zero read errors. This confirms the profile's event denominator
  for that run, but does not change replay readiness: prompt and context fields
  remain absent.
- Because the source logs continued changing, a newer paired snapshot is now
  recorded in `artifacts/trusted-scenarios/source-discovery-20260910-v5/` and
  `artifacts/trusted-scenarios/usage-profile-20260910-v3.json`. The paired
  snapshot contains 92,045 events, 30,910 complete usage events (33.5814%
  coverage), 6,540,151,762 prompt tokens, 1,266,112,420 completion tokens,
  and 30,566,337 cached tokens. Cost remains uncalculated without a price
  ledger, and duration remains `MIXED_OR_OUTLIER` with 168 values over one
  hour, so this newer snapshot still cannot support latency or savings claims.
- A metadata-only usage profile is recorded in
  `artifacts/trusted-scenarios/usage-profile-20260910-v2.json`. Across 92,028
  events, 30,908 have both prompt and completion token fields, for 33.59%
  usage-field coverage. The observed totals are 6,540,151,521 prompt tokens,
  1,266,108,564 completion tokens, and 30,566,337 cached tokens. No cost is
  estimated because an approved versioned price ledger is not present. Raw
  duration values are not production-latency evidence: 168 values exceed one
  hour, the maximum is 1,788,985,792.96, and the profiler therefore reports
  `MIXED_OR_OUTLIER` with no mean. A duration-unit definition and clean
  latency export are required before latency claims.
- An existing 27-sample local Codex-session corpus was inspected as a possible
  source. Its receipt explicitly says it is real user-message policy replay,
  not exact gateway replay, and that gateway joining is unverified:
  `C:\Users\stanc\github\lean-router\analysis\backtest\out\policy-on-real-corpus.json`.
  It remains ineligible for M2-data production replay or cloud-cost savings
  claims. The concrete missing join is an authorized export carrying the
  request/context body, stable gateway request ID, and matching usage record
  for the same episode.
- The audit entry point now also emits a deterministic, source-stratified
  `replay-schedule.json` and records its hash in the manifest. Six focused
  audit tests pass, and the scoped repository suite passes 192 tests with the
  archived duplicate test tree excluded.
- The authorized-export intake path is now implemented in
  `scripts/redact_production_scenarios.py`. It hashes the source export,
  deterministically replaces recognized credential patterns, rejects
  evaluator-only fields, and writes only the trusted-scenario fields consumed
  by the audit. Its three focused tests pass. This is ready for an authorized
  prompt/context export, but has not been run on production content because no
  such export is present or authorized in the workspace.
- The intake redaction review now replaces complete private-key blocks,
  including their body, rather than only replacing a key header. The focused
  intake, profiler, discovery, and audit tests pass 13/13, and the scoped
  repository suite remains green at 192 passed with one existing warning.
- The intake now also requires an explicit provenance class and has no default
  to `observed_production_replay`, preventing unclassified or generated rows
  from being mislabeled as production. The focused intake/audit/profile/
  discovery tests pass 14/14, and the scoped suite passes 193 tests with one
  existing warning.
- The intake writer now uses a same-directory temporary file and atomic
  replacement. If any input row is rejected, no partial scenario export is
  left behind and an existing output is not overwritten. The focused intake
  tests pass 16/16 and the scoped suite passes 195 tests with one warning.
- The CLI intake now requires an authorization receipt declaring
  `authorized: true` and the exact SHA-256 of the input export. A mismatched
  or non-authorized receipt is rejected before any output is written. This
  turns the operator-approval requirement into a machine-checked gate.
  The focused intake/audit/profile/discovery tests now pass 18/18 and the
  scoped suite passes 197 tests with one warning. A CLI integration test covers
  both successful authorized conversion and rejection without output on a
  mismatched source hash.
- Source discovery now reports both provider-reported token fields and the
  `input_tokens_estimate` / `output_tokens_estimate` fallback fields consumed
  by the profiler, so usage coverage is not understated by naming differences.
  The focused suite passes 18 tests and the scoped suite passes 197 tests with
  one warning.
- A paired metadata-only receipt command is now available at
  `scripts/build_production_readiness_receipt.py`. Its live receipt is
  `artifacts/trusted-scenarios/production-readiness-20260910-v1/receipt.json`:
  discovery and profile both observed 92,071 event records in the same run,
  with `event_count_match: true`. Replay remains false because prompt/context
  fields are absent, cost remains `PRICE_LEDGER_REQUIRED`, and duration remains
  `MIXED_OR_OUTLIER`. The paired command has 19 focused passing tests.
  The scoped repository regression suite passes 198 tests with one existing
  warning.
- Read-only schema and aggregate checks were also performed on the three
  adjacent SQLite stores. `conversation_lanes.sqlite3` contains lane/config
  metadata only, `expert_attempts.sqlite3` contains model/conversation/time
  rows only, and `consultations.sqlite3` contains 21 valid JSON message rows
  but zero top-level prompt, context, request-id, or gateway-join fields. No
  message bodies were read. These stores cannot currently supply the required
  trusted Wrench replay association and remain outside the production gate.
- SQLite metadata inspection is now part of
  `scripts/discover_production_sources.py`. It records database file hashes,
  table names, column names, and row counts in the receipt while excluding all
  cell values. The paired v2 receipt was regenerated successfully, and the
  scoped suite passes 199 tests with one existing warning.
- The intake now also requires `replay_eligible` to be explicitly set to a
  boolean. Missing approval no longer defaults to replay eligibility. The
  focused intake/audit/profile/discovery suite passes 20 tests and the scoped
  repository suite passes 200 tests with one warning.
- The redactor now hashes and parses one in-memory input snapshot, so the
  authorization hash and emitted rows cannot silently refer to different file
  contents due to a concurrent rewrite. The focused suite remains 20 passed
  and the scoped suite remains 200 passed with one warning.
- The downstream trusted audit now independently requires
  `replay_eligible` to be an explicit boolean, so callers cannot bypass the
  intake approval gate by submitting a hand-authored redacted JSONL directly.
  The focused suite passes 21 tests and the scoped repository suite passes 201
  tests with one warning.
- A later paired v3 snapshot was run against the changing logs and is recorded
  at `artifacts/trusted-scenarios/production-readiness-20260910-v3/receipt.json`.
  Both readers observed 92,114 events and matched exactly. Replay is still
  false because prompt/context fields remain absent; cost is still
  `PRICE_LEDGER_REQUIRED`, and duration is still `MIXED_OR_OUTLIER`.
- Paired receipts now include machine-readable `readiness_reasons`. The v4
  receipt records `MISSING_PROMPT_OR_CONTEXT`, `PRICE_LEDGER_REQUIRED`, and
  `DURATION_UNIT_UNVERIFIED_OR_OUTLIER`, making the exact remaining data gates
  explicit instead of leaving only `replay_ready: false`.
- The new protocol is
  `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md`; the durable
  result is `docs/reference/SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_RESULT.md`.
- No completed provider A/B/C receipt exists. Provider-token saving, billed
  cost, complete-workflow latency, paired outcome uncertainty, and real-traffic
  value remain unmeasured. M3 is the remaining execution gap and M4 depends on
  its result. Both await an explicit provider ceiling.
- A review of `scripts/selective_pilot_run.py` found that its preflight enforces
  the frozen selector identity and explicit attempt/token ceilings, but does
  not yet consume the trusted-data readiness receipt. Therefore the M2-data
  prerequisite is currently documented process control rather than a runner
  hard gate. Adding that gate requires a new protocol/frozen-identity revision;
  it must happen before any paid M3 invocation, not as an unrecorded runner
  edit.
- Added `scripts/verify_trusted_readiness.py` as an independent M3 prerequisite
  gate without changing the frozen runner. Running it against the current v4
  receipt correctly returns `REJECTED` with four explicit reasons:
  missing prompt/context, missing price ledger, unverified/outlier duration,
  and replay not ready. Its focused tests pass 24/24. This gate does not
  authorize spending; it only prevents proceeding when M2-data is incomplete.
- The readiness gate now also rejects invalid receipt schema, non-read-only
  receipts, and any receipt flagged as writing raw content. Its focused suite
  passes 25 tests, including the new integrity checks.
- The readiness gate now requires the paired receipt's full observation shape,
  including source identity, both event counts, capabilities, usage coverage,
  cost status, and duration status. This prevents a minimal hand-authored
  boolean receipt from passing. The focused suite passes 26 tests and the
  scoped repository suite passes 205 tests with one warning.
- The readiness gate now recomputes equality of `source_event_records` and
  `profile_events` instead of trusting the declared `event_count_match` flag,
  and rejects malformed `readiness_reasons` plus negative or mismatched counts.
  The focused readiness/data suite passes 27 tests. The latest scoped full
  regression passes 206 tests with one existing warning.
- The gate now also validates that `usage_coverage` is a real numeric value in
  the inclusive range 0 to 1, rejecting booleans, strings, and impossible
  percentages. The focused readiness/data suite passes 28 tests and the
  scoped repository suite passes 207 tests with one warning.
- The gate now restricts `cost_status` and `duration_unit_status` to the
  statuses emitted by the profiler, rejecting unknown strings rather than
  treating them as evidence. The focused readiness/data suite passes 29 tests
  and the scoped repository suite passes 208 tests with one warning.
- A fresh paired v5 receipt is recorded at
  `artifacts/trusted-scenarios/production-readiness-20260910-v5/receipt.json`.
  Both readers matched at 92,135 events. The same three readiness reasons
  remain: missing prompt/context, missing price ledger, and unverified/outlier
  duration. Replay therefore remains hard-stopped.
- The readiness gate now handles malformed non-string `readiness_reasons`
  without crashing or allowing a pass. The focused readiness/data suite passes
  30 tests and the scoped repository suite passes 209 tests with one warning.
- The gate now also rejects a false `event_count_match` declaration even when
  the two numeric counts happen to match. It requires both recomputed equality
  and the receipt's explicit success flag. The focused readiness/data suite
  passes 31 tests.
- The current v5 readiness receipt was rechecked by
  `scripts/verify_trusted_readiness.py` and returned exit code 1 with the same
  four explicit hard-stop reasons. This confirms the gate is actively blocking
  M3 rather than merely documenting the missing evidence.

### Blocked condition

The current V21 broad candidate is ineligible for M3 because it failed its
frozen local-quality gate. Do not spend provider budget on its A/B/C run.
Any future candidate must satisfy a separately frozen local-quality gate before
it can reach the M2-data and M3 sequence.

For an eligible future candidate, M3 is blocked first by M2-data: this workspace has no authorized export that
joins public prompt/context, stable gateway request ID, and matching usage for
the same episode. The current readiness receipt also lacks a versioned price
ledger and a verified clean duration unit. Passing
`scripts/verify_trusted_readiness.py` is required before a paid run.

After M2-data passes, M3 additionally requires an explicit provider attempt
ceiling and cloud-token ceiling from the operator. The prepared runner rejects
provider execution without those values and `--authorize-paid-run`. The fixed
endpoint is `http://127.0.0.1:4000/v1/chat/completions` and the requested
model is `minimax/minimax-m3`. No provider call has been made for this goal,
so no spending or token-saving claim may be inferred. Resume from the verified
`preflight-3` receipt only after all three conditions are satisfied.
