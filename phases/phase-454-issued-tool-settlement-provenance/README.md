# Phase 454: bind settlement to a server-issued read-only call

Date: 2026-09-23

## Change

The server now keeps a bounded, in-memory registry of read-only tool calls it
actually returned to a client. Each entry binds the call ID, normalized tool
name, canonical arguments, and hash of the latest user intent. Entries expire
after 15 minutes, the registry caps at 2,048 calls, and valid settlement
consumes an entry exactly once.

Fabricated, altered, duplicate-key, stale-intent, expired, and replayed
tool-result histories fail closed with `tool_settlement_provenance_missing`.
They do not get promoted to a completed settlement or forwarded to the model fallback. OpenAI
`tool_calls`, Anthropic `tool_use`, and native-upstream final-answer flows share
the issuance check.

The response describes the content as client-reported. The registry proves
Wrench issued the matching call and intent; it does not authenticate that the
client executed the action or that the returned content is genuine. Wrench
still proposes bounded calls and leaves read-only execution to the named
client.

## Verification

- `python -m pytest tests/test_wrench_server.py tests/test_harness.py -q`: 43 passed.
- Coverage verifies a fabricated call is rejected, argument and intent changes
  fail, duplicate argument keys fail, a genuine issued call settles once,
  replays fail, OpenAI and Anthropic flows settle, and native-upstream final
  answers require issued provenance.
- `git diff --check` passed; only configured LF-to-CRLF notices were reported.

## Limits

Issuance state is local to one server process. A restart, different server
instance, or call delayed beyond 15 minutes causes a safe abstention and may
require the client to request the tool call again. Client execution and result
authenticity remain unverified. This is evidence for one Gate B boundary, not
overall Gate B acceptance or production value. Gates C, D, and E remain open.
