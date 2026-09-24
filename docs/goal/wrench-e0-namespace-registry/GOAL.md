# E0 bounded namespace discovery registry

Status: bounded implementation slice accepted; E0 remains incomplete
Job: `W2-E0-NAMESPACE-REGISTRY-20260924`
Nonce: `NSR-0d772c`
Baseline: `3198c6a39dcfe438f306389c881be0bd804b9ed0`

## Outcome

Expose a caller-supplied finite set of namespace IDs and summaries, with
operation schemas fetched only on explicit lookup. Discovery visibility is
descriptive metadata; it grants no permission or execution capability.

## Acceptance

- Reject duplicate/invalid IDs and schemas, and enforce namespace, operation,
  summary, identifier, per-schema, aggregate-schema, depth, and node limits.
- Return deterministically sorted bounded IDs/summaries from discovery without
  schema bodies.
- Return one immutable schema plus canonical SHA-256 digest from lookup, or an
  explicit unknown-namespace/unknown-operation status.
- Expose no execute, permission, routing, shell, provider, or model API.
- Test stable discovery/search, deferred lookup, mutation isolation, limits,
  unknown IDs, and absent execution authority.

## Limits

Descriptors are supplied by the caller at construction; this registry does
not discover namespaces from the environment. Schemas are descriptive JSON
data and are never interpreted as instructions or executed.

## Review

Independent review accepted the bounded traversal and string checks after
requesting explicit depth/node and temporary-allocation bounds. Follow-up
tests passed. This component acceptance does not complete E0 or authorize E1.
