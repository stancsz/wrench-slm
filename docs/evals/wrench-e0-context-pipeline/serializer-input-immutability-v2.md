# Prompt serializer input immutability evaluation

## Decision

Accept this as a bounded offline input-mutation guard. Do not promote it to
serializer-authenticity, runtime-parity, or E0 acceptance evidence.

## Evidence

- Implementation report: [serializer input immutability v2](../../reports/wrench-e0-context-pipeline/serializer-input-immutability-v2.md)
- Report SHA-256: `FEE54B8C550AE50EA40AE50C603ADA05BB70D1D0B22C706111B91110C6936366`
- Base commit: `cd70a88e399fb722c7918b5c1fe87141141cf381`
- Final source SHA-256: `3201A779F940FF8506A1396157CBFC36A7C2F97032CF93B2F54F1C38502B4B43`
- Focused verification: **102 passed in 11.18 seconds** across eight modules
- Independent read-only review: `E0SMH-FINAL-24C8`, **PASS** for the final source hash

The reviewer confirmed recursively detached `MappingProxyType` mappings and
tuple sequences, direct built-in mutator resistance, callback materialization
for JSON encoders, arbitrary string/byte serializer output, and the documented
same-process reflection limitation. The reviewer ran no tests.

The Qwen system contract module did not collect because `torch` is absent from
the available Python 3.11 runtime. No package was installed. The prompt
compiler suite separately verifies arbitrary string and byte suffix behavior.

## Scope limits

The callback input cannot be changed through the standard interfaces and
direct built-in dict/list mutators tested here. A serializer that catches a
blocked mutation error may proceed with the unchanged input. The gate still
trusts arbitrary callback output and caller-declared callback identities.
Same-process reflection can reach mapping-proxy referents; callback execution
is not sandboxed. OpenCode integration, exact downstream serialization and
tokenization, dispatch enforcement, complete request accounting, task truth,
customer utility, and overall E0 acceptance remain open.
