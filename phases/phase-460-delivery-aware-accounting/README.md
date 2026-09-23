# Phase 460: preserve accounting across response delivery failures

Date: 2026-09-23

## Change

The model server now writes one trace row after each response-write attempt.
The existing proposal status and usage/cost receipt are preserved, with a
separate `response_write_status` of `server_write_completed`,
`server_write_interrupted`, or `server_write_error`. A completed server-side
write is not evidence that a client received or used the response.

The paired-canary accounting proxy now records one event per upstream request.
It keeps provider status, usage, and cost when the downstream write fails,
and records that write outcome separately. `snapshot()` waits up to two
seconds for in-flight handlers to finalize and marks the snapshot incomplete
if any remain. Incomplete snapshots cannot report complete accounting.

## Verification

- `python -m pytest tests/test_wrench_server.py -q`: 28 passed.
- `python -m pytest tests/test_paired_client_canary.py -q`: 58 passed.
- `python -m ruff check src/wrench_harness/server.py tools/probe_paired_real_client_canary.py tests/test_wrench_server.py tests/test_paired_client_canary.py`: passed.
- Regressions verify a completed server write, a deterministic server write
  failure with one preserved compute row, a completed error response, and a
  failed canary-proxy write with one upstream event and once-counted tokens
  and cost.

## Limits

These are focused local and loopback mechanics checks. They do not prove
client-application receipt, production server delivery, provider-export
authenticity, complete task outcomes, or matched real-workflow utility. The
proxy accounting completeness field remains fail-closed when any usage, cost,
identity, attribution, purpose, delivery, or snapshot evidence is missing.
Gates C, D, and E remain open.
