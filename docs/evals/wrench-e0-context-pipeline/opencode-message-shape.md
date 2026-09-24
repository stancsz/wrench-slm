# OpenCode v2.0.15 text-message shape evaluation

## Result

The offline adapter now creates the pinned OpenCode text-part shape for both
prepared context and deferred schema messages. The projection rejects scalar
system entries and scalar message content, and the transition validator
accepts only a single user text part as Wrench's inserted message.
OpenCode preparation rejects malformed base messages before retrieval and
without invoking serialization or token counting.

Focused verification passed **135 tests** across prompt compilation, E0
context preparation, OpenCode projection and session adaptation, lifecycle
accounting, and route preparation/composition. Python 3.11.16 and cached
pytest 8.4.2 were used. No client request, provider call, model download, or
model job occurred. A separate owner-authorized CLI install and localhost
configuration job is in progress. Scratch and pytest output were kept under
`C:\wrench-slm-data\tmp\opencode-message-shape-20260925`.

Independent review returned **PASS** on the bounded typed-message adapter.

## Limits

This checks only the pinned hook's basic typed text-message subset. It does
not implement the full content-part union or prove that the installed client
accepts the insertion. Serializer/tokenizer parity, dispatch behavior, final
wire request shape, and overall E0 acceptance remain open.
