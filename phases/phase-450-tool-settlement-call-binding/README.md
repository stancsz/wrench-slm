# Phase 450: bind tool settlement to Wrench read-only calls

Date: 2026-09-23

## Change

Embedded tool settlement now uses the existing verified-result boundary. It
settles only when a client tool result has a call ID matching a read-only call
in the submitted history. At this phase, the server did not keep issuance state,
so this established history correlation, not proof that Wrench issued the
call. Phase 454 adds that server-side check. OpenAI `tool_calls` and Anthropic
`tool_use` are normalized through the same boundary.

## Verification

- `python -m pytest tests/test_wrench_server.py -q`: 18 passed.
- Existing positive OpenAI and Anthropic settlement cases pass.
- New regressions reject a tool result with no preceding call, a mismatched
  call ID, and a matching ID for a non-read-only call.
- `git diff --check` passes.

## Limits

This phase closes one local correlation check only. The later Phase 454 adds
issuer provenance, but the client still supplies the reported result, so
neither phase independently attests to client execution. The focused server
suite does not close Gate B for all proposal types, nor establish Gate C or
Gate D production utility. No model inference, provider call, benchmark, or
real-workflow replay was run.
