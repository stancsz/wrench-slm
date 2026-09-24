# Offline OpenCode request boundary

Date: 2026-09-24
Job: `W2-NS-OFFLINE-REQUEST-BOUNDARY-20260924`
Correction jobs: `W2-NS-OFFLINE-REQUEST-BOUNDARY-FIX1-20260924` and
`W2-NS-OFFLINE-REQUEST-BOUNDARY-FIX2-20260924`
Evidence class: synthetic offline development only

## Implemented seam

`src/wrench_harness/opencode_request_boundary.py` provides a reusable
loopback-only boundary. `LoopbackFixtureServer` binds only `127.0.0.1` on an
OS-assigned ephemeral port and terminates each request at immutable fixture
bytes. It has no upstream address, forwarding implementation, or user-provided
response callback. A caller transfers a prepared lease's release callback to
`RequestLeaseBoundary.prepare`; the boundary issues a unique one-use nonce.
The lowered request must carry exactly one `x-wrench-request-nonce` header
matching that live ticket. A successful request consumes the ticket before
validation, so an invalid body or route cannot be retried with the same lease.
Duplicate correlation headers consume and release any pending leases they
name. Missing, unknown, and previously consumed nonces fail closed.

The accepted request is restricted to `POST` at the fixed
`/v1/chat/completions` path and a small Chat Completions
shape: fixture model name, at most 64 text-only messages, streaming enabled,
and optional bounded `max_tokens`. Request bytes are capped at 64 KiB. Before
constructing the parsed header collection, the HTTP reader caps request lines
and individual header lines at 4 KiB, the raw header block at 8 KiB, and header
count at 64. Each message is capped at 8 KiB, each response chunk at 16 KiB,
the fixture response at 1 MiB and 128 chunks. Duplicate JSON keys and unknown
content fields are rejected. Transfer-Encoding and duplicate Content-Length
are rejected. Exactly one Content-Type is required. It must be
case-insensitive `application/json`, optionally followed only by
`charset=utf-8`; missing, duplicate, text/plain, and other parameters fail
closed. Rejections carry reason codes only and never include the request body,
message text, headers, or nonce in their representation.

`FixtureResponse` accepts an immutable tuple and checks every chunk and the
total bounds before dispatch. The server returns these bytes as a chunked event
stream held by `FixtureResponseStream`. Direct stream EOF, writer
failure/disconnect, and explicit close release the lease once. The HTTP server
defers release until it finishes the final chunk or closes the writer. At most 128 leases may be pending or
active. A pending lease timeout can release immediately. For an active lease,
timeout only marks cancellation and keeps the lease counted as active. The
stream notices cancellation, or the socket's 5-second read/write timeout ends
the request writer; cleanup then closes the stream and releases the lease.
This is cooperative timeout handling. No arbitrary response iterator or
responder callback runs; the caller's lease release callback runs only after
stream/request cleanup. The timer never releases an active lease while its
request writer is still running. The server caps concurrent connection workers at 128 and
suppresses access logging. It opens no upstream or provider connection.

## Evidence and limits

The focused tests use an ephemeral loopback HTTP server, synthetic request
data, immutable fixture bytes, raw sockets, and a controllable clock. They
cover request and response streaming, real client disconnect, pre-construction
request-line/header/count caps, aggregate-header rejection with nonce cleanup,
correlation failures/replay, content rejection, byte bounds, pending and active
timeout cleanup, and exact-once release. Direct API and actual loopback tests
both accept the supported JSON Content-Type and reject missing, duplicate, and
unsupported media types. A loopback timeout test holds a large synthetic
response in flight with a small receive buffer, observes timeout marking while
the lease remains active, then disconnects the client and checks release after
writer cleanup. The tests do not exercise OpenCode, port 4000, a client hook,
an external request, or exact tokenizer agreement.
The tests bind an OS-assigned loopback port and never connect to port 4000.
This boundary does not itself produce a provider response or guarantee how
another process applies the response.

`E0RequestScope` and the existing preparation join remain caller-owned: this
module accepts a lease ID and release callback instead of constructing either.
The runtime adapter must hold the same request scope through `prepare` and
provide its close callback. This is an ownership seam, not production dispatch
authority. Exact-token acceptance remains closed pending an immutable runtime
route, serializer, and tokenizer profile.
