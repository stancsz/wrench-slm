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
