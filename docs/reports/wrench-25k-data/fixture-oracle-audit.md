# Wrench fixture and oracle design audit

Audit job: `W25K-FIXTURE-AUDIT-20260924-B`
Nonce: `W25K-FA-91D2`
Repository HEAD inspected: `87909b958ac252b0b3b2cc720a300babb26b733d`
Scope: read-only design audit for synthetic fixture and oracle implementation. No examples were admitted.

## Decision summary

The repository has a usable deterministic execution oracle for the six action
families in `src/wrench_harness/core.py`, an independent structural and
authority verifier in `src/wrench_harness/toolbelt.py`, proposal schema
evaluation, a train/development corpus validator, and non-sealed examples and
tests. These parts are a foundation, not a complete 25,000-row data factory.
The active validator deliberately does not read sealed-final rows. No reviewed
fixture generator, corpus-ready source/context/oracle/review registry set,
split constructor, or accepted corpus was found in this audit.

Use generated repositories and explicit task specifications as the synthetic
source. Derive each expected accepted proposal or refusal from a hashed fixture
and an executable oracle, then require human review before corpus admission.
These records would measure authored contract coverage. They must not be
described as representative of production frequency or as evidence of
productive value. That distinction follows the North Star and the active
25k-data goal.

## Source of truth and implementation entry points

- `src/wrench_harness/core.py::execute_model_output` parses one JSON object,
  applies task-intent guards, then delegates to `execute_proposal`.
- `src/wrench_harness/core.py::execute_proposal` checks schema
  `wrench.proposal.v1` and dispatches the six allowlisted actions. It returns
  `accepted` with an observation, or `abstain` with a stable
  `fallback_reason`.
- The same file defines the hard bounds and action handlers:
  `_read_file`, `_read_lines`, `_literal_search`, `_git_read_status`,
  `_health_read`, and `_patch_draft`.
- `src/wrench_harness/toolbelt.py::multi_pass_verify` checks action allowlist,
  required argument sets, review-only patch authority, execution evidence, and
  request/proposal consistency. Its action fields are at lines 261-268.
- `phases/phase-447-wrench-training-data-corpus/validate_corpus.py` checks
  source, context, oracle, review, row hashes, exact/near duplicates, and
  repository/task-family/template split isolation. It validates train and
  development only and refuses to read sealed-final input.
- `tools/evaluate_schema_adapter.py::score_case` is the available exact
  proposal/status/reason scoring path for evaluation cases. `tests/test_harness.py`,
  `tests/test_schema_evaluation.py`, and `tests/test_expanded_evaluation_generation.py`
  contain relevant examples of executable acceptance, boundary and OOD scoring.

The handlers accept these argument bounds and semantics (a proposal always
also has `schema: "wrench.proposal.v1"` and the matching `action`):

| Action | Proposal arguments and executable contract | Oracle outputs / stable boundary examples |
| --- | --- | --- |
| `read_file` | `path`; optional `max_bytes`, default 262,144, integer 1..262,144. Path resolves under the supplied allowed root; target must be a UTF-8 file no larger than the requested byte cap. | Accepted observation binds resolved path, UTF-8 byte count, and exact text. Refusals include `path_outside_allowed_root`, `invalid_byte_limit`, `missing_path`, `file_size_limit`, and `encoding_or_read_error`. |
| `read_lines` | `path`, integer `start`, integer `end`; one-indexed inclusive range, `start >= 1`, `end >= start`, at most 500 lines, and end no greater than fixture file line count. | Accepted observation binds resolved path, range, and exact line array. Refusals include `path_outside_allowed_root`, `invalid_line_bounds`, `missing_path`, `line_end_out_of_range`, and `encoding_or_read_error`. |
| `literal_search` | `root`, nonempty literal up to 4,096 characters, optional `max_matches` default 200 and integer 1..200. Mode defaults to and must be `literal`. Roots stay under allowed root. Files over 8 MiB and configured generated/model paths are skipped; accelerated search has a 0.75-second bound. | Accepted observation binds resolved root, literal, ordered match records and `truncated`. Reaching the match cap is an accepted truncated result, not an abstention. Refusals include `literal_mode_required`, `search_root_outside_allowed_root`, `invalid_literal`, `invalid_match_limit`, `missing_search_root`, and `search_timeout`. |
| `git_read_status` | `repo_root`, resolved under allowed root, must be a directory with `.git`. Runs bounded `git status --short --branch --untracked-files=no`, disables `core.fsmonitor`, timeout 5 seconds. | Accepted observation binds repo root, exact stdout, and `mutated: false`. Invalid root returns `repository_root_invalid`; command or timeout failure returns `git_read_error`. |
| `health_read` | `url`; optional `timeout_seconds` default 3, positive and <=5; `max_bytes` default 65,536, integer 1..65,536. Only `http` at `127.0.0.1`, `localhost`, or `::1`, path `/health` or `/v1/models`, with no query or fragment. | Accepted observation binds original URL, HTTP status, and exact UTF-8 body; non-2xx alone does not cause abstention. Refusals include `invalid_health_request`, `invalid_health_bounds`, `health_endpoint_not_allowlisted`, `health_response_size_limit`, and `health_read_error`. |
| `patch_draft` | `files`: nonempty list of at most 3 existing in-root non-hidden files; `review_only: true`; nonempty UTF-8 diff <=131,072 bytes, containing `---`, `+++`, `@@`, and at least one added or removed content line. | Accepted observation binds resolved files and exact diff, with `review_only: true` and `applied: false`. Refusals include `patch_draft_requires_review_only`, `invalid_patch_diff`, `patch_file_invalid`, and `patch_not_unified_diff`. No patch is applied. |

The verifier's required argument map does not itself state every numeric/path
bound, so the corpus oracle should invoke the concrete handler and retain its
version/hash. Avoid duplicating its logic in a second, drifting implementation.

## Fixture and task-group matrix

Each row proposal should be paired with a task prompt and a fixture snapshot
whose content hashes are in the context registry. Each boundary pair is one
`task_family_id` and one isolation unit; the two members differ in one
specified condition. Expected arguments and acceptance come from the typed
task spec, not from a language model. Pair groups must not be split across
train, development, or final.

| Family / task group | Positive fixture case | Matched boundary counterfactual | Expected action oracle |
| --- | --- | --- | --- |
| `read_file` / `file_read_cap` | Existing UTF-8 fixture file; requested cap is valid and file bytes fit. Vary file role and path depth in separately named task groups. | Same task with one-byte-lower cap than actual file size, expected `file_size_limit`. Separate pairs should exercise `../` escape (`path_outside_allowed_root`) and missing path (`missing_path`). | Exact `read_file` proposal; compare resolved path, bytes, and full text. |
| `read_lines` / `line_window` | Existing UTF-8 file; valid 1-based inclusive window, length 1..500 and end within exact line count. | Same file and intent with end one past EOF (`line_end_out_of_range`); separate pairs for >500 line span or start 0 (`invalid_line_bounds`). | Exact `read_lines` proposal and exact line slice. |
| `literal_search` / `fixed_string_lookup` | Fixture contains known zero, one, or several literal matches; bounded root and cap. Include metacharacters as literal characters. | Request regex explicitly (`literal_mode_required`), or change root to an outside path (`search_root_outside_allowed_root`). Invalid max_matches 0 or 201 gives `invalid_match_limit`. For result count above a legal cap, expected outcome remains accepted with exactly cap matches and `truncated: true`; this is an output-bound case, not a refusal. | Exact fixed-string proposal; independently enumerate expected ordered paths, line numbers, text, and truncation from snapshot. |
| `git_read_status` / `repository_snapshot` | Generated isolated repository with committed baseline and a named tracked edit; compare exact branch/status stdout from that snapshot. Include clean and changed states as distinct task groups. | Same directory without `.git` (`repository_root_invalid`); separate case for a path outside allowed root. Do not use uncontrolled host repository state. | Exact repo root; compare status output from exact Git fixture and assert no mutation. |
| `health_read` / `loopback_health` | In-process test HTTP fixture served only on loopback, with fixed path, status, body, and declared byte length. Prompt specifies the exact allowlisted endpoint, timeout, and response cap. | Change only scheme/host/path/query to a nonallowlisted URL (`health_endpoint_not_allowlisted`); oversized fixed body (`health_response_size_limit`); timeout can be a separately controlled short fixture but should not be used as a generic boundary oracle. | Exact URL/bounds; compare status and body; fixture telemetry confirms one local GET. |
| `patch_draft` / `review_only_unified_diff` | Existing fixture file(s), explicit intended replacement and exact unified diff visible in task prompt; one to three files; review only. | Flip `review_only` false or request apply (`patch_draft_requires_review_only`); invalid/nonexistent/hidden/outside file (`patch_file_invalid`); missing hunk/header (`patch_not_unified_diff`). | Exact files and diff, `review_only=true`; assert `applied=false` and fixture bytes unchanged before/after. Human inspect every candidate patch. |

Proposed four explicit out-of-scope groups, matching the validator's
`OUT_OF_SCOPE_FAMILIES`, are:

| OOD family | Authored task variants | Label rule and current runtime limitation |
| --- | --- | --- |
| `unsupported_mutation_or_command` | Arbitrary shell, delete/write/apply, commit, deploy, or push request. | Abstain. Core markers cover several such phrases; exact reason should be `task_family_not_allowlisted` for marker-backed examples, or `action_not_allowlisted` where an unknown action is the only executable signal. Specify one accepted exact reason per reviewed task spec. |
| `credential_or_external_access` | Ask to retrieve/use credentials, contact an external API, or access remote/private resources. | Abstain. `external api` markers exist, but credential intent is not comprehensively recognized by the runtime marker list. The broad family label is not itself an executable classifier; task-spec/oracle coverage or a reviewed request-intent rule is missing. |
| `ambiguous_or_multistep` | Missing target/snapshot, request to debug across multiple files, or autonomous multi-step work. | Abstain. Some phrases are explicit `OUT_OF_DOMAIN_MARKERS`; underspecified ambiguity has no general intent classifier. Do not claim broad coverage from marker examples alone. |
| `unrelated_or_non_developer` | Clearly unrelated request such as recipe, travel, or trivia; also unsupported general requests. | Abstain by task policy. Current core markers include `general code generation` but no general unrelated-topic gate. A proposal may otherwise execute if a safe-looking action is emitted. This family currently lacks a general executable oracle. |

The four OOD family names are validated row categories, not `fallback_reason`
values. Before counting OOD rows as exact-oracle coverage, each task family
needs an approved mapping to exact runtime refusal behavior. Where the runtime
does not establish that mapping, mark the case as unresolved/needs-review and
do not admit it as accepted training data until a separately reviewed rule or
boundary-spec change provides a deterministic outcome.

## Fixture topology and reproducibility

Use a fixture generator that emits small, deterministic, self-contained repo
trees from structured seeds. A suitable fixture unit should have:

1. `repository_id` for the generated repository shape, independent of any
   prompt paraphrase;
2. immutable snapshot ID and SHA-256 for every included text file and the
   normalized fixture manifest;
3. controlled path topology: root files, nested source/docs/tests, hidden
   paths, missing paths, and an explicitly outside sibling used only for
   containment tests;
4. parameterized contents designed for known byte sizes, exact line counts,
   literal match positions, UTF-8 and invalid UTF-8 cases, and patch context;
5. a generated Git repository state where needed, with initial commit and
   declared branch/index/worktree state, so `git_read_status` observations
   derive from a committed fixture snapshot;
6. a loopback HTTP fixture server with fixed route map and byte responses for
   health tests. Never route data-generation examples to public endpoints;
7. fixture lifecycle checks: hash before and after oracle execution, reject
   unexpected changes, and record any server request count.

Avoid host-specific absolute paths in prompts and targets. Bind relative paths
to the declared fixture root, then normalize resolved paths in the oracle
receipt. For tests expecting absolute paths in observations, derive the
expected path from that run's temporary fixture root, but keep the row's
portable fixture identity content-addressed. Fixed health ports are race-prone;
an explicitly configured loopback fixture base or injected transport is
needed. `core.py::_health_transport_url` already offers
`WRENCH_TEST_HEALTH_FIXTURE_BASE_URL`, restricted to plain HTTP loopback,
which can redirect the allowlisted request path to an ephemeral fixture
server. Record that this is test transport and preserve the original proposal
URL. No real network request belongs in oracle execution.

Git fixture creation requires Git in the test environment. The checked-in
handler explicitly disables fsmonitor hooks, but repository settings and
generated files should still be controlled. Do not run status against the
current Wrench checkout as a synthetic snapshot.

## Oracle and corpus row derivation

For an eligible task, the task specification should provide an exact intended
typed proposal. Validate its fields, then run `execute_proposal` against the
frozen fixture and pass the returned result through `multi_pass_verify`.
Expected status must be `accepted`; the observation must match the
spec-derived oracle; authority invariants must pass; and before/after hashes
must prove no mutations. Store the proposal as `expected_proposal`, never the
execution result as a model target.

For a matched boundary task, alter a single boundary fact while holding the
task family and remaining fixture constant. Execute the boundary-specific
proposal through the same path. Store `expected_status: "abstain"`, the exact
returned `fallback_reason`, and `expected_proposal: null` per validator schema.
The row's `family` identifies the related allowlisted action, and
`category: "matched_boundary"` identifies the refusal. For OOD, use `category:
"out_of_scope"`, one of the four named OOD families, null proposal and exact
reason from the approved rule.

Every row needs the Phase 447 production row contract, including
`wrench.training-example.v1`, split/stratum/category/family/template IDs,
system and prompt, fixture `context_ref` and hash, exact status/proposal/reason,
oracle reference and hash, provenance, review metadata, and
`fingerprint_sha256`. The manifest binds approved `sources`, `contexts`,
`oracles`, and `reviews` registries. For authored synthetic data, provenance
should be `verified_authored` with `project_authored`; do not mislabel generated
fixtures as observed or verified-real. The current validator requires a
hash-bound review receipt with reviewer, verified status, and `label`,
`task_fit`, and `privacy` scopes. A batch receipt may attest to a reviewed
generator/spec/template family, but each row must reference that receipt and
still pass its own deterministic execution and data-integrity checks. Human
review is especially mandatory per row for all `patch_draft` proposals, per
the active goal.

The `score_case` evaluation format and the corpus row format are distinct.
The former uses a stringified proposal `target`; the latter requires an
`expected_proposal` object and separate exact abstention reason. A builder must
not assume existing evaluation JSONL can be copied into the corpus. In
particular, sampled existing examples include shared `template_id`s and use
calibration metadata, not the required registries and hash-bound row review
receipts.

## Unique-task and template strategy

Vary task substance, not just wording. A task family should encode the actual
question answered, fixture facts, target location, required evidence, or
operation boundary. Candidate independent dimensions include different
repository layouts and file roles; distinct expected facts in those files;
valid line-window locations; literal strings with varied character classes,
hit counts and order; clean, staged/tracked and modified Git state; different
fixed health payloads; and independently authored patch intents with
different source contexts. Parameter variation is useful only when it changes
the task evidence and expected proposal in a meaningful, reviewable way.

Assign one stable `task_family_id` to the underlying intent and its
counterfactuals, one `template_id` to a prompt-generation/template family, and
an additional group ID to each paired boundary cluster. Treat paraphrases,
numeric substitutions, renamed copies of the same fixture, and repeated
boundary flips from one specification as correlated. They may be retained as
controlled variants if useful, but they do not count as new independent tasks
for coverage claims. Track at least three counts separately: raw rows,
unique task/specification groups, and unique repository × task-family ×
template combinations. Report category/action/task coverage and review
coverage alongside all row counts.

There is no defensible way to promise that the existing provisional 7,200
balanced-core rows or a fixed number of prompt paraphrases will produce 25,000
quality examples. The active goal requires 20,000 train, 2,500 development,
and 2,500 sealed-final examples, but acceptance depends on distinct reviewed
task groups and hard isolation. If the generator cannot provide enough
independent task groups, record the shortfall rather than inflate the count
with paraphrases. The goal's 9,600 `observed_workflow` rows specifically
require `verified_real` rows. Current synthetic fixtures cannot fill that
stratum and must not be relabeled to do so. Historical real captures remain
ineligible under the active provenance/consent/outcome audit.

## Split boundary and sealed-final handling

The validator's `isolation_errors` checks repository, task-family, and
template-group dimensions, plus cross-split duplicate/near-duplicate checks.
Split at the connected-component level: if any row shares a repository,
underlying task family, template group, or paired-counterfactual cluster with
another row, place the entire connected group in one split. Make repository,
task family and template groups disjoint between train and development, and
between either open split and final. Do not rely on hashing individual rows
into splits.

Train and development construction must not read the sealed-final file.
Construct final only after generator/spec family, oracle, prompts, candidate,
and scoring freeze. Use held-out fixture repository families, task families,
and templates. Keep final inputs and keys in a separate access boundary; the
current train/development validator's `sealed_final_read: false` is a guard,
not proof of complete final isolation. The Phase 447 README records prior
evaluation-material exposure with unknown exact source paths, so the currently
existing final set is not acceptable as untouched evidence without source
resolution.

## Gaps and proposed sequence with acceptance criteria

1. **Freeze action/oracle contract.** Add a versioned task-spec schema that
   binds prompt intent, exact target arguments, fixture ID, action bounds,
   expected status, and exact refusal reason. Resolve OOD exact-reason rules
   and lack of broad credential/unrelated intent detection before claiming
   runtime coverage. Acceptance: every family/edge has an executable spec;
   no expected status/reason is supplied by a teacher.
2. **Build deterministic fixture generator.** Implement content-addressed
   repo trees, Git snapshots, exact boundary file/search states, and the
   loopback health fixture. Acceptance: repeat generation from the same seed
   and generator hash yields byte-identical manifest and file hashes; fixtures
   are unchanged after oracle execution; no external network is used.
3. **Build proposal/oracle runner.** Call existing `execute_proposal` and
   `multi_pass_verify`, compare typed outputs, collect mutation hashes and
   exact fallback reasons. Add action-specific matrix coverage including all
   bounds and OOD families. Acceptance: zero schema errors, exact eligible
   target matches, exact refusal reasons, zero prohibited accepts, and
   deterministic replay from fixture/oracle hashes.
4. **Add task and near-duplicate audit.** Generate variants from structured
   task specifications, normalize prompts, calculate row and group
   fingerprints, and inspect repeated task/template clusters. Acceptance:
   documented counts of unique task groups/templates/repositories; no
   paraphrase-only count inflation; unresolved candidates remain in quarantine.
5. **Create review receipts and manifest registries.** Bind reviewer decision
   to generator/task-spec hash, fixture/context hash, oracle hash, row IDs or
   batch membership, checked scopes, and reviewer identity. Acceptance:
   validator's source/context/oracle/review references and hashes all resolve;
   every admitted row is individually linked to a verified review; each
   higher-risk patch row receives direct human inspection.
6. **Split only after group audit.** Freeze group assignments; reserve final
   task/repository/template components before prompt development and prevent
   final prompts entering teacher calls or development. Acceptance: 20,000
   accepted train, 2,500 development, 2,500 independently held-out final;
   all isolation and duplicate checks pass; final access and exposure receipt
   is independent. Do not fill the verified-real allocation using fixtures.
7. **Run independent corpus validation.** Validate manifest and open splits;
   independently rerun fixture/oracle checks and compare aggregate and
   row-level hashes. Acceptance: production-ready validator result,
   zero validation errors, exact split totals, review and source hashes, and
   no leakage. This synthetic-data completion still does not establish Gates
   C/D real-workflow value, production frequency, publication rights, or
   release approval.

## Repository pieces absent at audit time

- General-purpose generated repository/task-spec fixture factory covering all
  six actions and the required four OOD categories.
- A one-command deterministic dataset builder that emits production
  `wrench.training-example.v1` rows and manifest registries.
- A unified oracle/replay path that invokes the runtime and independent
  verifier for every candidate row while enforcing no-mutation hashes and
  offline health transport.
- A reviewed broad intent oracle for credentials, generic unrelated
  requests, and underspecified tasks; current `OUT_OF_DOMAIN_MARKERS` are
  finite string markers rather than a general classifier.
- A complete action-specific cross-product of valid, edge, and exact-refusal
  fixtures, particularly health body-size/timeout cases, search timeouts and
  invalid caps, filesystem symlink/path edge cases, and patch file-count/diff
  boundaries.
- A human review tooling/receipt workflow connecting per-row prompt, task
  spec, fixture, oracle, and provenance hashes. The validator checks registry
  consistency, but it cannot establish that review was thoughtful or the
  reviewer was independent.
- A group-aware split assignment constructor and an independent final-set
  build/access process. Validation exists for train/development isolation;
  no current corpus manifest or trusted sealed-final set was identified.
- A real-workflow distribution for the provisional `observed_workflow`
  allocation and a valid training source for it. Synthetic task mix cannot
  supply that evidence.

## Checks and limits

Inspected root `AGENTS.md`, `docs/northstar/README.md`,
`docs/goal/wrench-25k-data/GOAL.md`, `docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md`,
`phases/phase-447-wrench-training-data-corpus/README.md`, its
`validate_corpus.py` and `test_validate_corpus_isolation.py`, the runtime
`core.py` and `toolbelt.py`, tests `test_harness.py`,
`test_schema_evaluation.py`, `test_expanded_evaluation_generation.py`, and
non-sealed `evals/wrench-expanded-v2` action examples. Did not inspect raw
production traces or sealed-final data. No tests, provider calls, downloads,
generation, training, or artifact-producing jobs were run. This audit does not
validate the production row count or accept any records.

Assumption for the proposed implementation: project-authored synthetic
fixtures may use `project_authored` provenance after the corpus owner approves
the source/task specifications. No external dataset or model output is needed
to derive fixture ground truth. The previously unknown MiniMax billing and
route-rights matters remain separate blockers to teacher-generated records,
but do not prevent implementing a provider-free fixture/oracle path.
