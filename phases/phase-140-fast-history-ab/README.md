# Phase 140: native readiness and fast-history diagnosis

The v49 launcher treated FreeToken's `/v1/models` response as readiness. In a
real `FastHistoryKeepTokens=8192` attempt, the frontend answered but the
native backend worker exited during CUDA/runtime initialization. The public
package server then exposed a false healthy port and returned HTTP 500 on the
first native request.

The v50 launcher now sends a real non-mechanical completion smoke request
before exposing the public API. It captures native startup logs and exits when
the backend cannot complete the smoke request.

Observed v50 result under the current competing GPU/resource state:

- launcher status: fail closed before public API startup
- native port: 28993
- profile: `FastHistoryKeepTokens=8192`, `MoeCacheSize=16`, `KvReserveTokens=1024`
- failure evidence: FreeToken backend worker import/CUDA resource failure
- public API false-ready behavior: removed

The existing 64K direct-native receipt remains a timeout at 120.079 seconds.
This phase therefore improves runtime truthfulness and diagnostics, but does
not claim native 2M/4M speed or retrieval quality.
