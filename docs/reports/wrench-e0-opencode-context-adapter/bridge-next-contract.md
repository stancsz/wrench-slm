# OpenCode bridge next-contract recommendation

Date: 2026-09-24 (America/Edmonton)  
Starting revision: `11dd98a527ce44b4e7c425ca87e03b99c2e39993`

## Recommendation

For a future E0 integration, keep OpenCode's current local endpoint as the
upstream and put a Wrench-owned loopback request boundary in front of it. Do
not change or run the configured client as part of this recommendation. First
implement and exercise the boundary against an offline fixture responder. It
must capture the final Chat Completions body, enforce fixed route and payload
bounds, and hold source leases through stream completion, cancellation,
timeout, or failure. Before forwarding, it must validate an exact,
request-specific correlation from preparation to the lowered HTTP request;
session ID alone is insufficient for concurrent or retried attempts. Missing,
duplicate, stale, or ambiguous correlation must fail closed. Use no arbitrary
forwarding, provider access, or prompt logging.

The pinned Promise API exposes a candidate path: each
`SessionModelRequest.prepare` runs the context hook before `session.model.request`,
whose event has mutable headers; the later `session.http.request` event sees
the concrete HTTP `Request`. A unique request ID could travel in a header from
that point to the boundary. However, the context event has no attempt ID or
`kind`, and no implementation has established one-to-one matching across
concurrent preparation, retry, or failures between hooks. A per-key serialized
handoff is only a design candidate until implemented and exercised. The offline
boundary must reject requests without validated correlation. See the pinned
[Promise session hook types](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts)
and [request preparation order](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts).

This is the only reviewed shape that can observe the body after OpenCode's
request lowering and provide a `try/finally` boundary around the actual stream.
OpenCode's context hook is earlier than tool reconciliation, media handling,
protocol lowering, and HTTP overlays, and does not expose a proven settlement
signal for the downstream attempt. Its source-level rejection behavior is
limited to a primary attempt and is not a global veto guarantee.

The E0 exact-token gate must remain **CLOSED** for the current
`http://127.0.0.1:4000/v1` route. The checked-in OpenCode profile identifies
the OpenAI-compatible Chat Completions protocol, while the mounted gateway
configuration previously inspected routes `current` to MiniMax M3 through
OpenRouter. That alias does not pin an immutable provider/model revision,
tokenizer bytes, or final server-side template; an environment override also
remains uninspected. The MiniMax upstream tokenizer repository does not bind
those files to the deployed route. An offline proxy can establish final-body
structure, byte caps, and lease mechanics only. It cannot establish downstream
tokenizer parity. Do not substitute `o200k_base` or call a byte limit an exact
token budget.

## Wrench-owned project and source policy

If project sources are later enrolled, keep enrollment in a strict,
versioned registry under `C:\\wrench-slm-data`, writable only by an explicit
Wrench enrollment action. Repository files and hook payloads must not expand
access. Bind an opaque project ID to one qualified local canonical root and
captured `SourceRootBinding`; derive the store path from the project ID.
Require exact session-ID equality, reject nonempty or ambiguous `subpath`,
and require exactly one enrolled root match before revalidating root identity
and reading.

The profile should allow only a Wrench-owned finite relative-path set, fixed
policy ID, exclusions, and hard caps. Existing E0 preparation caps are 16
paths, 64 KiB per file, and 512 KiB total. Do not scan `.` by default or claim
that `.gitignore` or filename patterns protect secrets; inventory exclusions
are path-prefix based. Keep real-project source access disabled until the
owner enrolls exact paths and approves access, retention, and deletion terms.
Synthetic fixtures remain the default.

## Store and data lifecycle

Use one long-lived Python owner for each enrolled store root, one
`ArtifactStore` instance per root, and bounded serialized requests. The store
uses process-local locking and pins; per-hook subprocesses or independent
instances sharing a root are unsupported. A local fixture stream should prove
that every request lease is released on normal completion and each failure
path.

The current storage policy requires live-context handles to remain pinned
through request completion. Keep that requirement. A context-hook-only bridge
cannot satisfy it because no proven callback joins that hook to completion of
the specific model attempt. The request boundary is therefore required for
lease lifetime, not an optional optimization.

Every fixture, store, log, cache, or other Wrench artifact created for the
offline increment must follow the repository's storage admission rules:
reserve peak additional bytes before each artifact-producing job, account for
all retained and temporary copies, recheck status during long work and before
checkpoints, and release only after final files are accounted for. Keep total
Wrench-owned data below 50,000,000,000 bytes and verify C: free space
separately, with at least 5 GB physically free after projected writes. Any
client/runtime or benchmark job must preserve the 10% free RAM and VRAM
reserves. Prefer ephemeral bounded fixtures; do not persist prompts or request
bodies.

## Task and outcome oracle

Use the already-selected future corpus direction: prospective,
per-task-opt-in OpenCode tasks on participant- and repository-authorized
snapshots, initially repository localization and failing-test/log triage.
Keep the existing 10-case synthetic seed as development regression only; no
real tasks are currently admitted.

For E0, freeze the expected relevant evidence and permitted abstention before
replay, then score selection against independent adjudication. For E4, freeze
task-specific acceptance checks on a clean snapshot; code changes need passing
checks plus an arm-blinded reviewer for task fit and scope, with participant
completion recorded separately. Flaky, irrelevant, ambiguous, or conflicting
oracle evidence remains inconclusive. `you decide` delegated this source and
oracle recommendation only; it did not authorize collection, retention,
provider transfer, or training.

## Setup and evidence boundary

The isolated OpenCode v2.0.15 install is configured at
`C:\\wrench-slm-data\\opencode\\W2-NS-OPENCODE-LOCALHOST-INSTALL-20260925\\workspace\\opencode.json`.
It points `wrench-local/current` to `http://127.0.0.1:4000/v1`; SHA-256:
`BF30BF301159C947D3632640962C32ED943356D792E1CE89E5C79F715E121F4D`.
The JSON and fields were checked offline. Actual config loading and active
route resolution remain unverified. Prior setup evidence records one
`GET /v1/models`; no generation request was made during this work. No
OpenCode runtime, plugin, localhost endpoint, provider, or model was used in
this next-contract review.

## Next step and approval boundary

Proceed with an offline-only Wrench loopback request-boundary increment using
a fixture responder and synthetic data, leaving the static OpenCode
configuration untouched. Review protocol, request correlation, payload
bounds, stream outcomes, storage admission, and lease cleanup before any
client/config change. Any later config change or live forwarding to port 4000
is a separate explicit step. Keep exact-token E0 acceptance closed until an
immutable route and matching tokenizer profile are available.

The alternative is to keep OpenCode directly pointed at port 4000 and defer
the integration until OpenCode or its configured route exposes a verified
request-completion and exact-token boundary. That preserves the simpler client
path but leaves request pinning and E0 parity unproven.

## Evidence reviewed

- [`bridge-implementation-preflight.md`](bridge-implementation-preflight.md):
  bridge feasibility and source-level hook limits.
- [`config-load-preflight.md`](config-load-preflight.md): static client setup
  and unverified config loading.
- [`request-lowering-source-audit.md`](request-lowering-source-audit.md):
  OpenCode request construction and protocol lowering.
- [`session-root-resolution.md`](session-root-resolution.md): root/session
  binding limits.
- [`STORAGE_AND_RECOVERY.md`](../../northstar/STORAGE_AND_RECOVERY.md):
  storage ownership and live context pin invariant.

Official route sources: [OpenCode v2.0.15 OpenAI-compatible provider](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/ai/src/providers/openai-compatible.ts), [Chat Completions route](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/ai/src/protocols/openai-compatible-chat.ts), [request preparation](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts), [HTTP body overlays](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/ai/src/route/transport/http.ts), [OpenRouter routing](https://openrouter.ai/docs/guides/routing/provider-selection), and the [pinned MiniMax-M3 repository tree](https://huggingface.co/MiniMaxAI/MiniMax-M3/tree/f0e1c1e04d40177e4673a22097036854f536e9c0).
