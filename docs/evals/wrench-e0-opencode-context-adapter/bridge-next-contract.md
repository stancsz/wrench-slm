# Independent review: OpenCode bridge next-contract recommendation

Reviewer: `opencode_debug_config_safety` (independent read-only review)  
Starting revision: `11dd98a527ce44b4e7c425ca87e03b99c2e39993`  
Reviewed HEAD: `11dd98a527ce44b4e7c425ca87e03b99c2e39993`  
Result: **PASS**

## Findings resolved

- The contract requires an exact, request-specific, one-to-one correlation
  between preparation lease and lowered HTTP request. Session ID alone is
  explicitly insufficient; missing, duplicate, stale, or ambiguous
  correlation fails closed. It also states that no supported correlation
  mechanism is established yet and the proxy is only a candidate architecture.
- Storage admission now specifies peak-byte reservation, accounting for
  retained and temporary copies, status rechecks during long work and before
  checkpoints, release after final accounting, the strict 50 GB aggregate
  ceiling, and at least 5 GB of C: physical free space after projected writes.
  The goal carries the aggregate limit, 5 GB volume headroom, and 10% RAM/VRAM
  reserve for client/runtime jobs.

The route and tokenizer boundary remains honest: the installed route is an
OpenAI-compatible Chat Completions alias, while the inspected gateway mapping
does not pin an immutable serving revision, matching tokenizer, or final
server-side template. The report keeps exact-token E0 closed and limits offline
fixture evidence to structure, byte caps, correlation, and lease mechanics.
It preserves opt-in and repository authorization for future data and explicitly
grants no collection, retention, provider transfer, or training authority.

The goal-to-report link and the report's local evidence links resolve. `git
status` showed only the intended goal update and bridge report, plus the
pre-existing untracked `uv.lock`, which was left untouched.

## Scope and limitations

Reviewed the report and goal diffs and the cited local bridge-feasibility,
request-lowering, session-root, and storage/recovery reports. No tests or
scripts were run; no OpenCode client, provider, model, or localhost endpoint
was used. This review evaluates the written source claims and design contract;
it does not independently re-run the tagged-source audit or establish runtime
correlation, stream settlement, dispatch denial, provider route identity,
tokenizer parity, or E0/E4 utility.

## Addendum: candidate request-correlation path

Reviewed the added v2.0.15 source-order statement against the cited hook and
request-preparation references and the existing local request-lowering and
failure-path audits. The stated sequence is appropriately framed as a
candidate: preparation invokes the context hook before the model-request hook
where headers can be changed, and the later HTTP-request hook receives the
concrete `Request`. A header marker could therefore be carried to a boundary,
but this source order alone does not establish that a marker binds a specific
preparation lease to exactly one request.

The report and goal keep that gap explicit: there is no established attempt
ID on the context event, and correlation across concurrency, retries, and
failures between hooks remains unproven. They require validated one-to-one
matching and fail closed otherwise. The candidate-path addition does not
change the earlier **PASS**. The existing storage admission, 5 GB physical
headroom, closed exact-token gate, and no-runtime/no-forwarding boundaries are
unchanged and remain appropriately scoped.

This addendum is source-document review only. No tagged-source fetch, test,
script, OpenCode client, endpoint, or network call was used; it does not verify
marker propagation or runtime behavior.

## Addendum: ticket algorithm and response-hook ordering

Result for this addendum: **REQUEST CHANGES**. The prior PASS remains valid for
the earlier contract and storage/correlation safeguards; the new lifecycle
paragraph contains the response-hook ordering error below.

The added candidate correlation path is supported at source-order level by the
pinned `v2.0.15` sources. `SessionModelRequest.prepare` awaits the context hook
before calling `session.model.request`; the latter carries `kind` and mutable
headers. The later `session.http.request` hook receives a concrete `Request`
with the same session/agent/model/kind scope. The runner's outer `Retry`
outcome loops back through primary preparation. This supports the described
candidate ticket algorithm, but not its one-to-one guarantee: serialization,
timeout poisoning, nonce uniqueness, and hook-order control remain design
requirements that need offline adversarial verification. Scope “fresh nonce
per retry” to retries that re-enter primary preparation; transport/internal
retries may reuse a prepared request and are not established by this source
trace.

One claim needs correction before relying on the lifecycle rationale. In
`SessionModelRequest.prepare`, OpenCode awaits the HTTP handler, then creates a
`Response` wrapping `res.stream` and triggers `session.http.response`, and only
then converts the returned response with `HttpClientResponse.fromWeb`. Thus
the response hook runs before downstream protocol parsing and before body EOF;
the claim that EOF precedes parsing is reversed. A plugin response hook could
wrap the body stream to observe later EOF/cancel, but it is skipped if the HTTP
handler fails or hangs before returning a response and does not establish full
runner settlement. The recommendation for a boundary that owns both send and
response-stream cleanup remains reasonable, but its advantage should be based
on coverage of pre-response failures and explicit stream ownership rather
than the current EOF-order claim.

Sources reviewed via read-only browsing: [pinned request preparation](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts),
[Promise hook types](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts),
and [runner retry loop](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts). This is source review only; no
runtime or failure injection was performed; no localhost or provider endpoint
was contacted.

## Final re-review: response-hook lifecycle and retry scope

Result: **PASS** for the requested corrections. In the current report and goal
diff, the `session.http.response` hook is correctly described as running after
the HTTP handler returns and before OpenCode's downstream response conversion
and protocol framing. The text no longer claims that body EOF precedes the
hook or protocol parsing. It limits the hook's cleanup coverage to a returned
response and states that pre-response handler failures or hangs are outside
that hook's boundary; the fixed-upstream proxy recommendation is grounded in
owning send and response-stream cleanup.

Retry wording is also appropriately scoped: a fresh nonce is required for
outer retries that re-enter primary preparation, while transport retries may
reuse the prepared request and are not claimed to mint a new nonce. The ticket
algorithm remains explicitly a candidate, not implemented or verified, and
requires offline concurrency/retry/timeout-poisoning/nonce-reuse checks before
acceptance. No remaining actionable issue found in the requested corrections.

Scope: re-reviewed only the current report and goal diffs against the pinned
source-order audit already cited above. No runtime, client, tests, scripts,
localhost:4000, provider, or endpoint was accessed. This confirms wording and
source-order consistency only; it does not verify the candidate algorithm or
runtime stream settlement.
