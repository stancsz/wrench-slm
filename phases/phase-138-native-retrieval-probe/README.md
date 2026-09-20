# Phase 138: reducer-bypassed native long-context probe

This phase sends raw payloads through the public package endpoint with a
generic inert prompt that does not match the embedded mechanical route. The
package therefore forwards the request to the internal native backend.

## Current evidence

- v48 64K direct-native request: `status=599`, 120.079 seconds, no provider
  usage returned, `native_context_pass=false`
- v48 2M direct-native request: client-side 600-second timeout before the probe
  tool was fixed to persist timeout receipts; no success or truncation claim
- package and native processes were owned by this run and stopped afterward
- the 64K receipt is `native-64k-v48.json`

This is a real native-path performance failure, not a gateway compaction
failure. It confirms that the current 4M-configured NVFP4 backend can expose
the direct-input surface but cannot yet meet the fast native prefill target at
64K, much less 2M or 4M. The package mechanical route remains separate and is
covered by Phase 137.
