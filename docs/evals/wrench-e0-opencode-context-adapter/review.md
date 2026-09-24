# E0 OpenCode V2 context adapter contract review

## Decision

Accept the bounded documentation contract. OpenCode V2 is selected as the
first client target, while the adapter remains uninstalled and unrun. The
contract uses only documented semantic hook/session surfaces and explicitly
blocks claims the available API does not support.

## Review boundary

The official V2 plugin guide and API were checked on 2026-09-24. They describe
a context hook with session ID, agent, model identity, mutable system
instructions, messages, the supplied tools map, and options, plus session
lookup and session location metadata. The hook surface does not document a
typed context-hook rejection or dispatch-veto result, nor does the guide
specify callback failure behavior. The plugin load location is not treated as
the active session source root.

The guide also describes a separate prompt-admission hook. It runs once before
attachment and skill resolution and durable inbox admission, and the guide
states failed or interrupted preparation does not admit the prompt. It does
not run before each model request and does not provide the fully assembled
model context. The documented admission behavior therefore does not establish
a final-request veto.

The contract requires a present valid session location directory and
nonempty or ambiguous session subpaths to fail closed until their meaning is
pinned for a release. The supplied tools map must be preserved unchanged.
Exact provider request serialization and tokenizer identity are not
documented by this hook, so exact final token accounting and runtime
equivalence remain open.

The context hook precedes provider protocol lowering. A later native HTTP hook
is the closest documented observation point for a lowered request, while
WebSocket hooks are separate and experimental. Automatic compaction starts
from the latest response's provider input usage when available, then adds
output and newer content; without provider usage, OpenCode estimates text,
media, instructions, and tools locally. It can retry a recognized overflow
once when automatic compaction is enabled, but its estimate cannot prevent
every provider overflow. Neither that estimate nor a provider-specific
token-count API establishes a provider-agnostic exact gate or blocks a later
model dispatch.

## Scope limits

No plugin, dependency, client installation, provider call, benchmark, corpus,
or production route was added or run. Authored fixtures can test mechanics
only. No consented matched-task corpus or outcome oracle was identified, so
this review supplies no E4 utility evidence. Full E0 acceptance remains open.

## Sources

- [OpenCode V2 plugin guide](https://opencode.ai/v2/docs/build/plugins)
- [OpenCode V2 API](https://opencode.ai/v2/docs/api)
- [V1-to-V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1)
- [OpenCode V2 compaction guide](https://opencode.ai/v2/docs/compaction)
