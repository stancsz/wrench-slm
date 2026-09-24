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

## Provider-free session-root resolver slice

The follow-on implementation adds a Wrench-side boundary that consumes the
event session ID and session record as data. It requires an exact record-ID
match, an absolute usable `location.directory`, and absent or empty `subpath`;
it rejects ambiguous subpaths and does not infer a root from process or plugin
state. It returns the configured lexical root for existing snapshot-v2
binding. It is not an installed OpenCode hook and has no dispatch authority.

Independent read-only code review found no material findings. The reviewer
confirmed the v2.0.15 tagged session fields, matching session ID, fail-closed
root validation, lexical-root preservation, and the documented limits. The
review ran `git diff --check`, which passed. Reviewed Python file hashes:

- `src/wrench_harness/opencode_session_root.py`:
  `D9DDE5B6511347C832DB3AE8A3E8BD366FB35647F9612B8133BEAF5B69E314C1`
- `src/wrench_harness/snapshot.py`:
  `89E5CAEDCA8E4B2566210A7E197D60FE46299926D9D2FACE509669D436866C82`

No tests were run. No OpenCode install, client/provider/model call, benchmark,
participant capture, or utility evaluation occurred. The runtime callback
failure path, exact serializer/tokenizer boundary, and complete E0 lifecycle
remain open.

## Follow-on root-to-preparation review

Review job `W2-NS-OC-BIND-SUP-20260924` (nonce `OCB-SUP-E812`) accepted the
provider-free `prepare_opencode_e0_context` seam. Its fixtures include mocked
root-forwarding and invalid-session cases plus a call through the real E0
preparation path against a snapshot made from the resolved root. No tests were
run. Session lookup, provider dispatch, callback/tokenizer identity, Windows
ancestor reparse policy, and full E0 acceptance remain unresolved.

## Root/snapshot mismatch review

Read-only review job `W2-NS-OC-MISMATCH-REVIEW-20260924` (nonce `OMR-6F10`)
confirmed that a byte-identical second directory has a different lexical-root
hash, so the preparation path returns `SOURCE_MISSES` / `unknown_snapshot`
before source bytes are accepted. The fixture expects no prompt and no selected
evidence. It now also asserts that serializer and tokenizer callbacks are not
invoked. This is source and fixture evidence only; tests remain unrun.

## Windows root-chain audit

Read-only audit job `W2-NS-WIN-ROOT-AUDIT-20260924` (nonce `WRA-9C20`)
identified a time-of-check gap between resolving the Windows source root and
opening the root handle. The existing parent-relative child walk is bounded
once that handle is open, but the full root path is first opened by name.
Hardening and Windows race/junction tests remain open; no code or runtime
behavior was changed by this audit.

### Handle-walk follow-up

Commit `6118a12` implements the bounded component-relative root walk and adds
Windows fixtures for normal roots, static ancestor symlinks, and a reparse
ancestor swap before handle acquisition. Independent read-only review
`W2-NS-WIN-ROOT-REVIEW-20260924` (nonce `WRR-6C72`) found the specific reparse
TOCTOU gap closed. It left ordinary-directory replacement identity binding
and UNC root behavior open. Focused tests could not run because pytest is
unavailable in the launchable Python 3.13 runtime; the listed 3.11 runtime is
not launchable. `git diff --check` passed. This evidence does not qualify
Windows runtime behavior or change E0 acceptance.

### Snapshot root identity design review

Read-only job `W2-NS-WIN-IDENTITY-DESIGN-20260924` (nonce `WID-1A8C`)
identified a same-path ordinary-directory replacement case that the
component-relative handle walk does not distinguish when source bytes match.
The recommendation is a separate v3 snapshot schema with required root object
identity committed into `snapshot_sha256`, consistent across source reads and
checked during retrieval. It affects public snapshot compatibility and
hash-derived IDs, so it remains a scoped follow-up rather than a silent v2
canonicalization change. No code or tests changed from this design-only review.

## Sources

- [OpenCode V2 plugin guide](https://opencode.ai/v2/docs/build/plugins)
- [OpenCode V2 API](https://opencode.ai/v2/docs/api)
- [V1-to-V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1)
- [OpenCode V2 compaction guide](https://opencode.ai/v2/docs/compaction)
