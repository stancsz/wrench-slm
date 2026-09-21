# Phase 317: current-head 2M and 4M retrieval probe

The current-head portable candidate at
`D:\models\_wrench-release-candidate-a8a75c3` passed all six deterministic
package-local retrieval cases. Needles were placed at 1%, 50%, and 99% of
both 2,000,000-token and 4,000,000-token reference-only payloads.

- Cases: `6/6` passed
- Model calls: `0`
- 2M raw payload: `16,749,966` characters per case
- 4M raw payload: `33,499,966` characters per case
- Effective working context: `19` tokens in every case
- 2M gate latency: `14.70~19.67 ms`
- 4M gate latency: `25.12~40.66 ms`
- All proposals accepted and raw payload hashes were bound

This is deterministic embedded MapReduce and retrieval evidence. It is not a
dense-native attention or learned MiniMax quality claim.
