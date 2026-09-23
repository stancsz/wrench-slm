# Phase 452: retain partial local usage across failures

Date: 2026-09-23

## Change

The worker now emits a bounded partial usage receipt when local generation
raises. The receipt records observed prompt tokens, completed earlier attempts,
and an explicit unknown completion count for the failed attempt. The client
and server validate and preserve that receipt while leaving local and total
workflow token totals unknown.

The server also retains a validated local partial receipt in its timeout and
server-error trace when later frontier fallback fails. The overall model-call
count and cost accounting remain unknown in those traces. The
`input_tokens_not_sent_to_model` diagnostic uses the first local attempt's
prompt count, so retries do not count repeated prompts as input that was never
sent.

## Verification

- `python -m pytest tests/test_embedded_worker.py tests/test_wrench_server.py -q`: 37 passed.
- Regression coverage includes generation failure on first and repair attempts,
  partial usage through client aggregation, successful frontier fallback, and
  failed frontier fallback with trace retention.
- `git diff --check` passed. Git reported only configured LF-to-CRLF working
  copy notices.

## Limits

The tests use local fakes and loopback HTTP, not a production model, paid
provider, real client trace, or matched workflow replay. A client disconnect
after the server writes a success trace can still make delivery status differ
from trace status. Exceptions after `generate()` returns but before the worker
builds its normal result are also outside this receipt path. Gate C parity,
Gate D net savings, and Gate E sustained serving resilience remain open.
