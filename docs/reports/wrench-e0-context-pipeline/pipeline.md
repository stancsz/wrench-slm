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
