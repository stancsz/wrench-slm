# Phase 336: Exact current-head 2M/4M retrieval probe

Status: `PASS_PACKAGE_RETRIEVAL_2M_4M`.

The exact current release-line package
`D:\models\_wrench-release-candidate-bbc680f` passed a deterministic
reference lookup probe at both 2,000,000 and 4,000,000 raw input tokens.
Each size placed a unique lookup needle near the beginning, middle, and end
of the payload while keeping the newest intent in the suffix.

## Evidence

- Cases: `6/6` accepted with the exact expected `read_file` proposal.
- 2M cases: `3/3` passed, about `1,750,502` scanned tokens each.
- 4M cases: `3/3` passed, about `3,501,008` scanned tokens each.
- Raw payload sizes: `16,749,966` and `33,499,966` characters.
- Elapsed range: `14.853` to `42.766 ms`; median `22.401 ms`.
- Model calls: `0`.
- Effective working context: `19` tokens, under the `64,000` token budget.
- Payload hashes were bound by the first-layer context gate.
- All cases used the embedded mechanical fast path and reference lookup.

This is evidence for the fast model-local deterministic MapReduce/reference
path. It does not claim dense-native attention quality, learned MiniMax parity,
or production approval. The native-input claim remains false for this probe.

Evidence: `phase-336-current-head-retrieval-2m-4m.json`.
