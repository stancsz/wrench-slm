# OpenCode prepared-context materialization evaluation

Job: `W2-NS-E0-OPENCODE-PREPARED-ADAPTER-20260925`  
Nonce: `PREP-7A62`  
Base commit: `d705e11e336f8909ee626976fe9e406377996443`

## Result

The independent read-only review passed with no materialization correctness
findings. It verified the frozen implementation hashes recorded in the
[worker report](../../reports/wrench-e0-opencode-context-adapter/prepared-context-adapter.md).
The four focused modules passed **112 tests in 4.64 seconds** using the
existing cached Python 3.11.16 and pytest 8.3.5 runtime. `git diff --check`
passed. The reviewer ran no tests and made no edits.

The seam checks the pinned event projection and joins `event.sessionID` to the
READY local admission result. It uses only the ephemeral compiler-produced
message, validates that message against the prompt-gate digest, rejects
duplicates and bounds failures, inserts at the recorded position, and
requires a verified prepared-transition receipt before returning READY. The
input event is copied, and the protected fields and original message sequence
are checked by the existing transition validator. Synthetic tests cover
session/admission failure, message/hash/gate errors, event immutability,
ordering, bounds, and content-free evidence.

## Limits and next step

The returned transition receipt is not consumed directly by the existing
partial lifecycle-trace builder. A caller must separately project the
materialized event and provide it to trace construction; a test should join
the adapter result into that envelope in a follow-up increment. The bridge is
available to the caller in memory, so callers must not serialize the full
preparation result with generic dataclass conversion. No source path currently
does so. The adapter remains a provider-free Python seam: no plugin was
registered or run, and it does not authenticate hook execution, veto
dispatch, establish final provider/tokenizer parity, or accept E0.

The reviewed diff and test evidence use authored synthetic fixtures only. No
OpenCode client, gateway/provider request, prompt, inference, network access,
or real capture occurred. Storage was `WITHIN_LIMIT` at 1,710,630,437 actual
bytes with 103,000 bytes in other active reservations; both task reservations
were released after accounting. The unrelated untracked `uv.lock` was
preserved.
