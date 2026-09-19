# Phase 64: logical context at the local model boundary

`execute_local_qwen` now supports an optional `ContextLedger`. In that mode it
assembles a bounded request from system/developer instructions, retrieved
context, and the latest user request. Older raw message history is excluded
from the outbound model payload. The response includes the context assembly
receipt for independent accounting.

The focused client integration test verifies that a 2M-capable logical ledger
forwards only the bounded working set and preserves an atomic tool-call/result
unit. The full repository suite remains the authoritative regression check.

This phase does not establish long-context answer quality, native 2M attention,
provider performance, cost savings, or production readiness.
