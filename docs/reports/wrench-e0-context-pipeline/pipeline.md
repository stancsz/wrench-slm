# E0 context preparation slice

This slice adds a caller-owned facade over existing bounded primitives. Its
single request scope pins successfully admitted artifacts until context
assembly, structural candidate verification, deferred namespace schema
insertion, final serialization/token counting, and reference receipt creation
finish. Source bytes are used only for the verified local artifact and ledger
flow; the returned receipt contains references and hashes, not content.

The facade has no provider, model, routing, execution, shell, subprocess, or
tool capability. A returned prompt is inert output for a caller. The
serializer and token counter in tests are fixture-only and do not prove target
tokenization or provider wire compatibility. Namespace schemas are inserted
as data and convey no permission.

Source hashes establish exact byte identity, not caller authority. The
caller-owned store can retain verified bytes if context/prompt compilation
later fails. Request pins are process-local. `actual_route` is always `none`;
there are no model attempts or verifier/tool calls. The receipt records an
unknown downstream outcome and incomplete status because no task result was
observed. This slice does not claim production E0 completion.

The facade caps the source set at 16 files, 64 KiB per file, and 512 KiB
aggregate bytes; schema lookups cap at four. Caller selected source paths can
be marked hot or required without needing to precompute their deterministic
evidence IDs. The prompt serializer and token counter in the focused tests are
fixture-only.

The focused tripwire fixture patches the known worker/model, client/provider,
mechanical route, proposal router, executor, subprocess, and common socket/HTTP
entry points. It checks that this fixture run calls none of them while the
facade has no execution parameter. This is scoped evidence for these patched
ports and inert callbacks, not universal proof about arbitrary caller
callbacks, future integrations, or every possible process/network path.

The returned `PreparationMetrics` object is local to one facade result and
is neither persisted nor exported. It records monotonic wall duration and
facade call-site counters without paths, evidence/artifact IDs, hashes, or
content. Artifact put input bytes count bytes offered to a put call; put
success bytes increment only after a successful put return. The zero
model/provider/verifier/tool counters describe direct call sites owned by the
facade and are not totals for the whole request. Caller supplied
serializer/tokenizer callbacks may be arbitrary code, and their external
effects are unmeasured (`callback_external_activity` is null). Admission and
structural-index exact reads have separate bounded attempts, successes, byte
totals, and finite retrieval-status counts, with an aggregate source exact
read total in the preparation metrics. Index results retain counts on
retrieval, parse, and output failures. Process CPU, RSS, energy, OS cache, and
request-local page faults are likewise null/unmeasured. This is preparation
scope only, not complete E0 accounting or an E0 acceptance claim.

`PreparationMetrics` additionally copies scalar/enum ledger assembly facts:
logical and selected token counts, retrieval candidate count, whether
retrieval was truncated, the search limit, and token-count mode/counter label.
With the current facade ledger configuration, `word_estimate_v1` is a word
estimate; it is not the final prompt token count or a target-runtime tokenizer
result. A successful structural index contributes its file count, symbol
count, and canonical in-memory serialized payload size in bytes. These remain
null unless index construction succeeds. Retrieval candidate count does not
measure symbols scanned, and serialized payload bytes do not measure disk
I/O. The values carry no IDs, query, paths, hashes, or content and are not
included in the aggregate receipt digest.

The result now also carries an optional deterministic companion accounting
receipt. Its canonical JSON includes stable facade counters and explicit nulls
for unmeasured dimensions, joins them to the existing aggregate preparation
hash, and has its own SHA-256. The companion is omitted when no aggregate
preparation hash exists or its bounded payload cannot be formed. Monotonic
elapsed time is excluded from its identity. This keeps counter evidence
verifiable without changing the existing content receipt or claiming that
metrics are persisted, exported, callback-complete, or complete E0 lifecycle
accounting. Its v1 counter projection is explicit so unrelated future metrics
do not silently alter the schema. The public verifier checks canonical form,
the field set, payload hash, and join to the caller-supplied preparation hash;
that proves integrity, not measurement authenticity or callback completeness.

## Follow-up task: deterministic preparation accounting companion

- **Worker:** root agent as E0 pipeline supervisor and implementer
- **Status/date:** accepted as a bounded component slice after independent repair review, 2026-09-24
- **Artifact:** `src/wrench_harness/e0_context_pipeline.py`
- **Revision:** implementation based on `52438e2`; code and evaluation committed together
- **Verification:** focused `tests/test_e0_context_pipeline.py` on Windows
  Python 3.11.16 with the existing cached pytest 8.4.2 dependency path: **8
  passed**. `git diff --check` passed. Coverage includes stable hashes,
  elapsed-time exclusion, null-versus-zero, stale and prompt-rejected results,
  missing receipts, oversized/deep payloads, and strict schema validation.
- **Review repair:** independent review found that verifier parsing occurred
  before its size check and an unreached structural query looked like zero
  candidates. The verifier now checks input size first, catches recursion,
  validates exact v1 keys/value types, and candidate count remains null until a
  query returns. Final read-only re-review accepted the repairs. An intermediate test run caught
  a misplaced test block; it was corrected before the passing run.
- **Storage:** the 50,000,000-byte reservation was released after the test
  stopped and its 8,916-byte temporary tree was accounted; final checker status
  was within limit with no active reservations.
- **Limitations:** no POSIX pytest, OpenCode plugin, runtime-matched tokenizer,
  provider call, or downstream task was exercised. This does not close E0's
  complete lifecycle accounting, authority, or client integration gates.
- **Review record:** [accounting companion evaluation](../../evals/wrench-e0-context-pipeline/accounting-companion.md)

## Follow-up: authored synthetic composition fixture

- **Worker:** `e0_composition_supervisor`; integrated by the orchestrator
- **Status/date:** accepted as a bounded mechanics fixture after separate
  critic and verifier review, 2026-09-24
- **Artifact:** `tests/test_e0_context_pipeline.py`,
  `test_authored_synthetic_composition_keeps_valid_prompt_and_records_non_text_omission`
- **Verification:** Windows Python 3.11.16 with cached pytest 8.3.5, focused
  test: **1 passed in 0.84s**. `git diff --check` passed.
- **Storage:** job `W2-NS-E0-COMPOSE-20260924` reserved 10,000,000 bytes and
  released that reservation after the test. The final checker reported
  654,114,954 actual bytes and 103,000 bytes in other active reservations.
- **Review:** independent critic and verifier read the actual test and
  concluded the `SOURCE_MISSES` plus locally READY prompt and incomplete
  unknown-outcome receipt are coherent. They found no blocking issue and
  emphasized the narrow synthetic scope.
- **Limits:** no task execution, baseline comparison, artifact readback/pin
  lifetime assertion, runtime token parity, client hook, dispatch veto, or
  complete lifecycle accounting. The zero counters cover only direct facade
  call sites. This does not establish E0 or E4 acceptance. See the
  [composition fixture evaluation](../../evals/wrench-e0-context-pipeline/composition-fixture.md).
- **Next:** connect the selected OpenCode preparation seam to an approved,
  pinned client lifecycle only after request-boundary, serializer/tokenizer,
  and dispatch contracts are established. The current helper does not install
  or run a plugin, establish dispatch veto, or prove runtime parity.

## Follow-up task: caller-owned request-lifetime pins

- **Status/date:** implemented as a provider-free lifecycle seam, 2026-09-24
- **Evidence:** `ArtifactRequest` is one-shot, checks active state under the
  store lock, releases its pin set idempotently, and exposes a store-identity
  check. `prepare_e0_context` and `prepare_opencode_e0_context` accept an
  already active request scope. The default remains preparation-only; callers
  that need request-lifetime protection must keep `with store.request()` open
  across preparation, downstream completion, failure, timeout, or cancellation
  cleanup. Focused fixtures check retention after return, eviction after
  close, cleanup on an exception, overlap/refcount behavior, and rejection of
  inactive or foreign scopes.
- **Limits:** This provides only same-process caller-owned pin lifetime. It
  does not observe completion, enforce dispatch, record complete lifecycle
  activity, coordinate other processes, or qualify crash recovery. The
  OpenCode plugin remains uninstalled and unrun; no provider, client, or
  participant data was used.
- **Verification:** Three independent read-only reviews passed, and bounded
  Python 3.11 generic and OpenCode-wrapper smoke runs passed. `pytest` is not
  installed in the available Python environments, so the new pytest fixtures
  could not be executed; no dependency was installed. `git diff --check` passed.
