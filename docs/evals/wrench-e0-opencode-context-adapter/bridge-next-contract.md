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
scripts were run; no OpenCode client, provider, model, localhost endpoint, or
network call was used. This review evaluates the written source claims and
design contract; it does not independently re-run the tagged-source audit or
establish runtime correlation, stream settlement, dispatch denial, provider
route identity, tokenizer parity, or E0/E4 utility.

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
