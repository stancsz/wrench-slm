# OpenCode context-hook projection

Date: 2026-09-24  
Scope: offline Wrench-side projection of the pinned OpenCode context-hook shape

## Result

`project_opencode_context_hook` accepts the seven semantic fields exposed by
OpenCode `v2.0.15` `SessionHooks.context`: `sessionID`, `system`, `messages`,
`agent`, `model`, `tools`, and `options`. The upstream tagged declaration is
[SessionHooks.context](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/session.ts).
The model identity shape is defined by the tagged
[Model.Ref declaration](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/schema/src/model.ts).

The helper makes a bounded JSON copy, requires the expected top-level and
model fields, and retains arrays, tool-map entries, nested schemas, and
provider-specific option keys. The `payload_json` representation preserves
insertion and array order. `projection_sha256` is SHA-256 over canonical JSON
containing the projection schema, pinned source version, and complete copied
payload, so object-key ordering does not change semantic identity. A string
length lower-bound check runs before UTF-8 encoding; the exact UTF-8 aggregate
and final JSON serialization are also bounded to 1 MiB. Node count, nesting,
integer size, message count, system-part count, and tool count have separate
limits. The final serialized payload is rejected above 1 MiB. JSON escaping
can temporarily expand an already bounded input while forming that candidate
string (up to six output characters per control byte, plus bounded JSON
structure); it cannot expand from an unbounded source string.

The model variant may be absent or a valid string. An explicit null is
rejected to match the optional-string source shape. Cycles, non-JSON values,
non-finite numbers, malformed fields, invalid Unicode, and inputs beyond the
limits fail without returning a projection.

## Verification

Commit `0e1f2ec55a74c5ff916a017d5083a9f55f43e5e1` tightens the byte bound and
adds independent digest recomputation, object-key reorder, and explicit-null
fixtures. The focused command covered the projection, OpenCode context seam,
E0 context pipeline, and E0 request record:

```text
python -m pytest tests/test_opencode_hook_projection.py tests/test_opencode_context.py tests/test_e0_context_pipeline.py tests/test_e0_request_record.py -q -p no:cacheprovider
56 passed in 2.88s
```

## Limits

The caller must keep the event object stable for the duration of the call.
The copier can notice some container length changes, but same-length or nested
concurrent mutations cannot be detected atomically. The projection is
ephemeral and provider-free. It is not a registered OpenCode hook and is not
connected to prompt admission, a serializer or tokenizer, tool authorization,
or the model request path. It does not establish final wire payload or token
parity, callback failure behavior, a dispatch veto, or runtime behavior.
