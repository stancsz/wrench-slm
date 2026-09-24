# E0 caller-owned context preparation

## Objective

Compose the existing bounded snapshot, structural index, artifact store,
context ledger, namespace registry, prompt gate, and reference-only outcome
receipt into one deterministic caller-scoped preparation operation.

## Boundary

The facade accepts finite explicit paths and an already-created snapshot. It
re-reads each path exactly, stores only verified bytes in the caller's store,
and holds request pins through assembly, deferred schema insertion, prompt
serialization, and receipt construction. Registry discovery and schemas are
inert descriptive data. `route` is always `none`; no model, provider, router,
executor, subprocess, or tool callback is accepted.

The prompt serializer and counter are caller injected. Their IDs are recorded,
but this contract does not establish that they match a target runtime. A
snapshot digest binds bytes and paths; it is not authorization. Artifacts may
remain stored if later context or prompt admission fails. Pins are
process-local to the supplied store instance.

## Limits and evidence

The facade accepts at most 16 paths, four deferred schema lookups, 256 prompt
and receipt references, a 256-character query, 8,192 context tokens, 8,192
prompt tokens, 64 KiB per source, 512 KiB aggregate source bytes, and an
aggregate reference receipt of 64 KiB. Exact reads are
revalidated before storage; structural candidates must match the source
snapshot, normalized path, and exact source digest. Retrieval misses and
non-text sources are represented as omissions. Failed prompt gates return no
prompt.

Callers can select `preserve_source_paths` to mark exact source evidence hot
for the current assembly, and `required_source_paths` to make those exact
source identities mandatory at the prompt gate. The returned source rows
expose deterministic evidence IDs for later caller-owned selection.

The outcome receipt reports no model calls, no verifier/tool work, route
`none`, unknown downstream task outcome, and incomplete coverage. It makes no
claim that a later task succeeded. Fixture tests use a local JSON serializer
and character counter only.

Each result also carries an in-memory-only metrics record for that facade
call. It records monotonic elapsed wall time and counters at the facade's
retrieval, artifact, structural index, schema, ledger, serializer/tokenizer,
and receipt call sites. Admission reads and structural-index reads are
reported separately, with an aggregate exact-read total. The structural
index result carries bounded counts and finite retrieval-status counts on
success and failure, including later parse/output failures. Put input bytes
count bytes offered to `store.put`; put success bytes count only bytes
accepted by a successful return. Process CPU, RSS, energy, OS cache, and
request-local page faults remain null, not estimated as zero. Metrics contain
no paths, IDs, hashes, or content and are
not persisted or exported. The zero model/provider/verifier/tool fields count
only call sites owned by this facade, not total request activity. Caller
serializer and tokenizer callbacks are arbitrary code; any external effects
they cause are not observed, so `callback_external_activity` is null. This is
preparation-scope measurement, not complete E0 accounting or acceptance.

Metrics also copy bounded content-free facts from a successful ledger assembly:
logical and selected token counts, lexical retrieval candidate count and
truncation flag, search limit, and token-count mode/counter label. The default
`word_estimate_v1` counts are not final prompt tokens or target-runtime tokens.
A successful structural index contributes file count, symbol count, and
canonical in-memory serialized payload bytes. These index facts remain null if
index construction fails or is not reached. Candidate count is not a count of
symbols scanned; serialized bytes are not disk I/O. No candidate IDs, query,
paths, hashes, or content are copied into metrics, which remain outside the
aggregate receipt hash.

## Follow-up: versioned accounting companion

Status: accepted as a component slice after independent review (2026-09-24).

The facade result optionally carries a versioned canonical companion for its
call-site counters. It joins those counters to `aggregate_sha256`, excludes
facade elapsed wall time, preserves unavailable values as null, and verifies
payload integrity and preparation-hash matching. Schema v2 includes the
measured, run-specific `ArtifactRequest` pin-scope duration when the facade's
own scope closes; an open caller-owned or unentered scope remains null. This
is preparation pin time, not request or client latency. The companion remains
in memory and separate from the outcome receipt. It does not authenticate
measurements, observe arbitrary callback effects, or satisfy complete E0
lifecycle accounting. See the [pin-scope join report](../../reports/wrench-e0-context-pipeline/pin-scope-accounting-join.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/pin-scope-accounting-join.md).

## Follow-up: preserved hot evidence overflow

Status: accepted as a local preparation receipt slice after independent review.

When preserved evidence is also required and cannot fit the context budget,
the E0 facade now routes an explicit omission to the prompt gate. The gate
returns no prompt and the outcome receipt remains incomplete. The default
low-level ledger call still raises on preserved overflow. Required and
preserved evidence IDs are bounded together before assembly. This is local
fail-closed accounting; it does not establish runtime parity or dispatch
enforcement. See the [overflow report](../../reports/wrench-e0-context-pipeline/hot-region-overflow.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/hot-region-overflow.md).

## Follow-up: untrusted source formatting

Retrieved source is JSON-quoted and labeled as untrusted data before prompt
serialization and token counting. The authored regression covers instruction-
like and marker-like source bytes while confirming the route stays within the
explicit snapshot request. This is a prompt-format and offline route-scope
boundary only; it does not prove model resistance, dispatch enforcement, or
client runtime behavior. See the [source-injection report](../../reports/wrench-e0-context-pipeline/source-injection-boundary.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/source-injection-boundary.md).

## Follow-up: authored synthetic composition fixture

Status: accepted as a narrow composition-mechanics regression after independent
critic and verifier review (2026-09-24).

The new scenario snapshots one authored text file and one opaque binary file,
then calls the existing `prepare_e0_context` facade. It asserts selected text
evidence in a locally gate-ready prompt, explicit omission of non-text
evidence, `route == none`, an incomplete unknown-outcome receipt, a verifiable
preparation accounting join, and zero direct facade model/provider/verifier/
tool call-site counters. The preparation status is `SOURCE_MISSES` because the
binary input is intentionally omitted even though required text is available.

This is fixture mechanics only. It does not execute the task, compare against a
downstream baseline, verify artifact readback or pin lifetime, prove zero
external activity, establish runtime serializer/tokenizer parity, or close
E0/E4 acceptance. Details and independent findings are in the [composition
fixture evaluation](../../evals/wrench-e0-context-pipeline/composition-fixture.md)
and [pipeline report](../../reports/wrench-e0-context-pipeline/pipeline.md).

## Follow-up: snapshot-bound deterministic rule route

Status: bounded offline read-route component implemented; W4 integration and
E0 acceptance remain open.

`run_e0_rule_route` uses `mechanical_route` only to parse an allowlisted
proposal, then reads exact bytes through `retrieve_exact` with the carried
`SourceRootBinding` and supplied `SourceSnapshot`. It accepts only
`read_file`, `read_lines`, and literal search over snapshot members. It rejects
negated, contradictory, output-restricted, or consent/authorization-marked
read/search requests before retrieval. Snapshot manifests are validated
before route planning. Search is limited to 16 files and 512 KiB; reads are
limited to 256 KiB per file; line windows to 500; literals and returned lines
to 4,096 characters; and matches to the existing 200-match action cap.
Stale, missing, non-text, ambiguous, unsupported, or capped evidence is
represented as unknown or partial and never triggers a live-root executor.

This component returns a local `route=none` result with content-free source
hashes and exact-read counters. It does not consume `PreparationResult`, build
or finalize the E0 outcome receipt, prove user intent, authenticate the caller,
observe a client lifecycle, or veto OpenCode dispatch. A later E0 integration
must join the route to normalized context and reconciled outcome accounting.
Focused behavior and independent review are in the [rule-route report](../../reports/wrench-e0-context-pipeline/rule-route.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/rule-route.md).

## Follow-up: partial local lifecycle trace

Status: bounded structural join implemented; task-wide accounting remains open.

`build_partial_lifecycle_trace` joins a READY preparation record, its
accounting receipt, a self-consistent semantic hook projection, and a valid
finalized outcome receipt by session, snapshot, context, and accounting
digests. It emits only bounded references, hashes, projection-input byte
count, and an explicit unavailable-field inventory. The caller's run ID is
correlation metadata, not authenticated task identity. The two locally
measurable dimensions refer to preparation-facade counters and the projection
function's serialized input; they do not claim that OpenCode emitted or sent
those exact bytes.

Every input remains caller-supplied and unauthenticated. The envelope does not
measure dispatch, provider traffic or cost, tool execution, retries, task truth,
or runtime resource use, and it does not make the outcome receipt a trusted
measurement. Focused behavior and independent review are in the [partial-trace
report](../../reports/wrench-e0-context-pipeline/lifecycle-trace.md) and
[evaluation](../../evals/wrench-e0-context-pipeline/lifecycle-trace.md).

## Follow-up: route result joined to the partial trace

Status: synthetic offline route-to-trace join implemented as trace schema v2;
full E0 integration remains open.

`run_e0_rule_route` now returns the caller-supplied snapshot digest alongside
its result. `build_partial_lifecycle_trace` can optionally join that result
when its snapshot digest matches the preparation/outcome join. The v2 summary
contains route status/action/reason, hashed path references, content hashes,
and caller-reported exact-read counters. It excludes raw paths and observation
text, allowlists summary strings, and labels the result as caller-supplied and
untrusted. Synthetic coverage runs
preparation, a real bounded route call over the same snapshot, outcome
finalization, and trace construction, including an abstention and mismatched
snapshot case.

This is a structural record join only. A caller can construct or alter the
route result; the snapshot digest is not an authenticated invocation record.
The join does not establish route intent, dispatch prevention, task truth,
runtime behavior, or customer utility. Focused evidence and independent review
are in the [route-to-trace evaluation](../../evals/wrench-e0-context-pipeline/route-trace-join.md)
and [report](../../reports/wrench-e0-context-pipeline/route-trace-join.md).

## Follow-up: open synthetic fixture admission metadata

The synthetic matched-task manifest is now v2 and carries explicit origin,
declared use, sealed/final flags, split, root lineage, and a hash-bound fixture
mechanics review pointer. A small fail-closed validator recognizes only this
Wrench-authored synthetic open development fixture. It rejects missing or
unknown provenance/use, sealed/final state, unsupported split/lineage, and
invalid review metadata. The result is a local fixture classification only; it
does not prove rights or consent, authenticate reviewers, authorize real data,
or enter the separate production corpus/training admission process. See the
[admission report](../../reports/wrench-e0-synthetic-matched-tasks/admission.md)
and [evaluation](../../evals/wrench-e0-synthetic-matched-tasks/admission.md).

## Follow-up: bounded retrieval pages

Status: standalone in-memory W1 decision mechanics implemented; default E0
selection is unchanged.

`ContextLedger.retrieve_page` accepts a typed `ENOUGH` or `RETRIEVE_MORE`
decision and returns at most 32 known candidate IDs per page, with a maximum
of two pages. Continuation cursors bind to the ledger session and query, and
the result reports stop, exhaustion, candidate/work clipping, or invalid
cursor states. The cursor is caller-visible and replayable within the bounded
ledger; this is not an authenticated controller decision or usefulness
evidence. See the [report](../../reports/wrench-e0-context-pipeline/w1-retrieval-pages.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/w1-retrieval-pages.md).

## Follow-up: selected snapshot and source lineage receipts

Status: bounded selected-subset accounting and preparation lineage implemented.

The coverage receipt binds exact reads and parser status to a validated
snapshot, and explicitly describes only the caller-selected path subset. E0
preparation now includes reference-only rows for selected source IDs and
matching parser-reported structural candidates, plus explicit unavailable
reasons. The receipt digest and reasons feed the preparation aggregate and
outcome context hash. It emits no unselected source, source text, or claim
that parser spans are ground truth. Artifact handle IDs do not prove a live
pin, and summary lineage remains unavailable. See the [coverage report](../../reports/wrench-e0-context-pipeline/selected-subset-coverage.md)
and [preparation integration evaluation](../../evals/wrench-e0-context-pipeline/preparation-source-lineage-integration.md).

Standalone source-reference rows and the selected-subset coverage receipt
remain component evidence; neither establishes whole-repository coverage.
All additions remain offline mechanics and do not close runtime parity,
dispatch enforcement, authenticated lifecycle accounting, independent task
truth, or E0 acceptance.

## Follow-up: rule-route to preparation composition

Status: authored synthetic composition fixture accepted after independent
review.

The fixture runs bounded literal search over one source, one log, and one test
file in the same validated snapshot. It carries the caller-owned route result
and matched paths into E0 preparation, then checks that exact-read source
hashes join to the route evidence and all required/preserved IDs are selected
when budget permits. With a one-token budget, it verifies no prompt, explicit
omission reasons for all required evidence, and an incomplete outcome receipt.
The route result and path selection remain caller-supplied and unauthenticated;
the fixture does not establish task truth, utility, runtime parity, or dispatch
enforcement. See the [composition report](../../reports/wrench-e0-context-pipeline/route-preparation-composition.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/route-preparation-composition.md).

## Follow-up: route-owned preparation orchestration

Status: accepted as a bounded local composition slice after independent source
review (2026-09-25).

`route_and_prepare_e0_context` invokes the snapshot-bound rule route itself,
derives required and preserved preparation paths only from successful exact-
read evidence, and emits a bounded receipt joining route counters and content
hashes to preparation and accounting digests. Five focused pytest cases passed;
independent source review returned PASS. The reviewer did not run tests, and
the inter-step filesystem race is not dynamically exercised. This does not
prove authenticated route provenance, dispatch enforcement, final request or
tokenizer parity, complete lifecycle accounting, task truth, or customer
utility. Overall E0 acceptance remains open. See the [report](../../reports/wrench-e0-context-pipeline/route-preparation-orchestrator.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/route-preparation-orchestrator.md).

## Follow-up: bind route evidence into the partial trace

Status: bounded trace-binding implementation and focused verification complete;
independent review passed. Overall E0 acceptance remains open.

Completed route evidence is now admitted to the partial lifecycle trace only
through a successful route-to-preparation receipt, whose exact preparation
object must also be carried by the session join. The v3 trace records the
receipt digest; standalone
completed route results are rejected. This validates cross-record structure
and content hashes only. Caller provenance, dispatch enforcement, final
request/tokenizer parity, complete lifecycle accounting, task truth, and E0
acceptance remain open. See the [report](../../reports/wrench-e0-context-pipeline/route-trace-join.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/route-trace-join.md).

## Follow-up: exercise the route/preparation source-change boundary

Status: one authored inter-step source-change regression passed; independent
read-only review passed. `route_and_prepare_e0_context` now has a fixture that
mutates a routed source immediately before preparation reads the snapshot and
verifies `EVIDENCE_JOIN_MISMATCH` with no accounting receipt. This covers the
specific change case only. It does not prove general race freedom, atomic
multi-file snapshots, client dispatch, or full E0 acceptance. See the
[orchestrator report](../../reports/wrench-e0-context-pipeline/route-preparation-orchestrator.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/route-preparation-orchestrator.md).

## Follow-up: bind the OpenCode transition to prepared context

Status: offline structural binding implemented, independently reviewed, and
committed as `ac0e775`; overall E0 acceptance remains open.

The prompt-gate receipt now carries a digest and insertion position for the
exact Wrench context message produced by a READY preparation. These values are
included in preparation aggregate schema v2. When a partial trace includes
route-preparation evidence, it must also include a hook transition that
matches that preparation, exact message, insertion position, session, and
after-projection digest. The trace envelope is schema v4 and stores only
bounded hashes, references, and position.

Focused tests passed 97 cases across prompt compilation, E0 preparation,
OpenCode projection, and lifecycle accounting. The transition compares
caller-supplied projections and is not authenticated client evidence. Nested
message schema validation, dispatch enforcement, final request/tokenizer
parity, complete lifecycle accounting, task truth, utility, and overall E0
acceptance remain open. See the [prepared
transition report](../../reports/wrench-e0-context-pipeline/prepared-context-transition.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/prepared-context-transition.md).

## Follow-up: serializer mutation and context identity

Status: initial mutation boundary implemented and focused verification passed;
later serializer-input hardening is recorded in the v2 follow-up below.

The prompt gate gives the serializer a recursive copy and rejects ordinary
mutation attempts, including attempts caught by the callback. This protects
the compiler-owned message digest from callback writes. Python base-class
mutators can change the serializer copy, and arbitrary callback output is not
verified against its input. Four focused suites passed 98 tests; the initial
run's 43 setup errors came from a missing reserved scratch parent, which was
created before the successful rerun. See the [task report](../../reports/wrench-e0-context-pipeline/serializer-input-mutation.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/serializer-input-mutation.md).
Runtime parity and callback serialization correctness remain open.

## Follow-up: OpenCode v2 typed text messages

Status: implemented; focused offline verification passed.

The OpenCode adapter now emits prepared context and deferred schema text as
typed text-part messages, and the projection checks the pinned role, system
text-part, and message content-array shape. The transition validator binds a
single inserted user text part. The focused set passed 132 tests. Full
OpenCode content-part union validation, client execution, serializer and
tokenizer parity, dispatch behavior, and E0 acceptance remain open. See the
[report](../../reports/wrench-e0-context-pipeline/opencode-message-shape.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/opencode-message-shape.md).

## Follow-up: serializer input immutability v2

Status: implemented in `adc4cbc`; 102 focused tests passed and independent
source review passed. The serializer now receives detached read-only mappings
and tuple sequences, with a bounded materializer for callbacks that require
ordinary JSON containers. This blocks supported interface mutation and common
built-in mutators; same-process reflection and arbitrary serializer output
remain outside the guarantee. Qwen contract tests could not collect because
`torch` is unavailable. See the [v2 report](../../reports/wrench-e0-context-pipeline/serializer-input-immutability-v2.md)
and [evaluation](../../evals/wrench-e0-context-pipeline/serializer-input-immutability-v2.md).

## Follow-up: bounded request and version scope

Status: implemented and committed as `277d3de`; eight focused synthetic tests
passed and independent review closed the request/run identity gap. The scope
joins one artifact request, a lifecycle version pin, READY context preparation,
its accounting and incomplete preparation receipt, and a separate terminal
outcome receipt. It emits a bounded reference envelope only when the joins
validate. Early artifact-pin closure fails closed, and the terminal run ID must
match the caller-supplied request ID. This equality is correlation only, not
authentication. The model pin does not retain version files, and the
coordinator is not an atomic transaction across stores. See the [request-scope
report](../../reports/wrench-e0-context-pipeline/request-version-scope.md) and
[evaluation](../../evals/wrench-e0-context-pipeline/request-version-scope.md).

## Follow-up: OpenCode-compatible SSE fixture

Status: socket-free encoder fixture and evidence committed as `d8dcad1`;
documentation whitespace cleanup followed in `1684bc6`. The focused server
suite passed 18 tests. A synthetic non-tool completion checks role, content,
stop, SSE framing, and `[DONE]`; production code did not change. This checks
one local success shape only. It does not establish OpenCode runtime parsing,
port routing, hook behavior, provider or tokenizer parity, dispatch enforcement,
or full E0 acceptance. See the [report](../../reports/wrench-e0-opencode-context-adapter/sse-contract.md)
and [evaluation](../../evals/wrench-e0-opencode-context-adapter/sse-contract.md).

## Current client setup status (2026-09-24)

OpenCode `v2.0.15` is installed in an isolated directory under
`C:\wrench-slm-data\opencode` and configured for `wrench-local/current` at
`http://127.0.0.1:4000/v1`. A subagent revalidated the CLI, wrapper, config,
and executable identities; `--version` matched, and a GET to `/v1/models`
returned HTTP 200 with `current`. This is configuration and model-list
connectivity evidence only. No prompt, task, chat, provider POST, inference,
Wrench hook, or plugin ran. The install's current measured size is 1,042,047,920
bytes across 609 files, about 5.6 MB above its initial report measurement,
with new growth in local log/database state; no cleanup was attempted. The
[install report](../../reports/wrench-e0-opencode-context-adapter/local-client-install.md)
and [mock preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
retain the identities and exact runtime boundary. A future mock prompt remains
gated on validated process-level egress confinement and a separately approved
single synthetic request. Overall E0 acceptance remains open.
