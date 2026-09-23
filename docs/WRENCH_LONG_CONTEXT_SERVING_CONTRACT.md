# Wrench hybrid long-context serving contract

Status: active hybrid serving boundary

This contract covers the active long-context capability only: model-local raw
payload intake, deterministic retrieval and compaction, bounded working
context, proposal verification, and stronger-model fallback.

## Product boundary

Wrench may accept a large raw request at its package-local endpoint. It must
hash-bind the raw payload, preserve current intent and relevant tool state, and
select a bounded evidence window for model work. The active product claim is
hybrid retrieval and compaction, not dense-native attention over every raw
token.

The serving receipt must expose raw input identity, selected and omitted
evidence, effective working context, retrieval source, staging latency, model
calls, fallback, and verifier results. Context-management overhead belongs in
the paired workflow accounting.

For model-local HTTP requests, the client hashes the exact serialized request
body and the server hashes the bytes it reads. Before consuming a proposal or
attributing cost, the client checks the echoed body hash, workflow ID, attempt,
model identity, and a unique request ID consistently present in the response
JSON, HTTP header, and nested cost receipt. This binds receipts to a request
within the configured endpoint trust boundary. It does not authenticate the
server or protect against a malicious endpoint that can fabricate receipts.

## Required serving shape

```text
raw request
    -> payload hash and context admission
    -> deterministic search, AST, dependency, and intent extraction
    -> hash-bound evidence cards and bounded working context
    -> typed proposal or abstention
    -> independent verifier
    -> bounded read-only or review-only action, or stronger fallback
    -> hash-bound final answer when a tool result is returned
```

The default active working context is bounded. Large raw input must not be
silently truncated, and omitted context must remain auditable and retrievable.
Unsupported opaque state, uncertain retrieval, malformed output, or a boundary
change must fail closed and preserve the original request.

## Active acceptance

- Raw payload identity and no-truncation intake are recorded.
- Retrieval preserves the newest intent and relevant tool state.
- Selected evidence is traceable to source identifiers and hashes.
- The proposal passes the independent verifier before any bounded action.
- The paired canary includes intake, retrieval, compaction, verifier, retry,
  fallback, and final-answer costs and latency.
- Sustained operational testing covers cancellation, timeout, recovery, and
  request isolation.

## Explicitly out of scope

Dense-native 2M or 4M attention, native decoder quality comparisons, stock
Ollama, vLLM, GGUF adapters, and hardware-portability work are skipped by the
active goal. Historical design and measurement notes are preserved under
[docs/archive/2026-09-22/](archive/2026-09-22/).
