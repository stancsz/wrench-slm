# Phase 325: current-head real client integration

The latest portable candidate `D:\models\_wrench-release-candidate-9cc0c68`
was exercised through the downloaded package's embedded mechanical endpoint.
The tests used an isolated client workspace and a read-only prompt against
`README.md`.

## Result

Status: `PASS_REAL_CLIENT_INTEGRATION`

- OpenCode: exit `0`, structured read observed.
- DeepSeek Harness: exit `0`, structured read observed.
- Claude Code: exit `0`, real `Read` tool result observed.
- Wrench traces used the embedded mechanical backend and settlement path.
- Total model calls: `0`.
- No mutation was claimed.
- Claude's first mechanical settlement completed in approximately `2.547 ms`.

This is real client integration evidence for the fast mechanical lane. It does
not claim learned MiniMax parity, native dense 4M decoder quality, or
independent RTX 5060 Ti verification.

Evidence: `receipt.json`, `wrench-client.trace.jsonl`, and
`claude.trace.jsonl` in this directory.
