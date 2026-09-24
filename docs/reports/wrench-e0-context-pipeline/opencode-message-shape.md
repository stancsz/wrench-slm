# OpenCode v2.0.15 text-message shape

Goal: [E0 OpenCode context adapter](../../goal/wrench-e0-opencode-context-adapter/GOAL.md)
Task: emit and validate the pinned hook's typed text-message subset
Job: `W2-NS-OPENCODE-MESSAGE-SHAPE-20260925`

## Change

OpenCode's pinned `SessionContext` declares `system: SystemPart[]` and
`messages: Message[]`. Wrench's OpenCode preparation path now selects the
`opencode-2.0.15` message format. Prepared context and deferred schema text
are emitted as `{role: "user", content: [{type: "text", text: ...}]}` and
the prompt-gate insertion digest covers that exact shape. Generic preparation
keeps its existing scalar-content default.

OpenCode base-message inputs are checked in both E0 preparation and the prompt
gate. Invalid roles, scalar content, malformed text parts, and non-array
content fail before source retrieval or serializer/tokenizer callbacks.

The hook projection requires system text parts, message roles from the pinned
role set, and content-part arrays with string discriminators. Transition
validation further requires Wrench's inserted item to be exactly one user
text part. This is a bounded text-message subset check; it does not validate
every OpenCode media, tool, reasoning, or metadata variant.

## Source references

- [`SessionContext` in the pinned Promise plugin](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts#L20-L33)
- [`SystemPart` and `Message` schemas](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/ai/src/schema/messages.ts#L16-L34)
- [Content-part and message declarations](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/ai/src/schema/messages.ts#L209-L248)

## Limits

The serializer and tokenizer remain caller-supplied research callbacks. No
OpenCode request was run in this code/test job; a separate owner-authorized
install and localhost configuration job is in progress. This change is local
structural conformance evidence; it does not establish provider
serialization/tokenizer parity, a supported dispatch veto, task utility, or
overall E0 acceptance.
