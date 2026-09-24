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
