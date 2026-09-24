# Offline request boundary evaluation

**Reviewer:** Codex subagent `/root/northstar_next_gate_supervisor/offline_boundary_readonly_review` (independent, read-only review)

**Revision reviewed:** `development` at `3fe4f48fa2a5d0ad826fc4b0657f06839f95824f` (starting and reviewed revision)

**Reviewed artifact identities:**

- `src/wrench_harness/opencode_request_boundary.py` SHA256 `D96451C50086CD6159268BFE2A5F77A9235A2655469F7A4167112AAADD6940FB`
- `tests/test_opencode_request_boundary.py` SHA256 `A4DF001333282F43C69D6CE2D08FC63083E43B126A40507B3C0718C9437379A0`
- `docs/reports/wrench-e0-opencode-context-adapter/offline-request-boundary.md` final SHA256 `B8C1081A33090B8C14A4A81489043D07CE3A4E3E248272F41FC34F63633536E6`. The report's correction-job metadata was edited after the review; the supervisor identified this as wording-only. The reviewed report hash was `1E85C00F84816DAE9B04A60CB0850C190EBB143ED95421AA47A0BC3D4F6932BC`.

## Review result

**PASS.** The seam provides one-use nonce correlation, strict supported request parsing, bounded immutable fixture responses, loopback-only HTTP on an ephemeral port, and lease release after writer cleanup. The wire parser enforces request-line and header bounds before constructing `HTTPMessage`; it sets the socket timeout before parsing and checks aggregate headers before reading the body. Exactly one case-insensitive `application/json` Content-Type is accepted, optionally with `charset=utf-8`. Correlation failures and unsupported content fail closed. Active timeout marks cancellation but keeps the lease counted until stream/request cleanup.

The first review returned NEEDS_CHANGES for late header-byte enforcement and a socket timeout set after parsing. A subsequent review also identified missing Content-Type enforcement and no actual loopback timeout evidence. The final revision corrected these with bounded raw-line parsing and early socket timeout, pre-body aggregate header validation, direct and wire Content-Type cases, and a loopback active-timeout case that observes `timeout_requested` while the lease remains active and verifies release after client disconnect and writer cleanup.

## Verification evidence

Supervisor-reported focused verification on Python 3.11:

```text
.venv\Scripts\python.exe -m unittest tests.test_opencode_request_boundary -v
17/17 passed
git diff --check
passed
```

The reviewer did not run tests or `git diff --check`. This evaluation records the supervisor's reported result, not an independently executed test result.

The pre-write storage check reported `WITHIN_LIMIT`: 1,714,618,491 bytes actual, 1,151,576 bytes in active reservations, and 48,284,229,932 bytes headroom under the 50,000,000,000-byte ceiling. The active reservation list included `W2-NS-OFFLINE-REQUEST-BOUNDARY-20260924`; it was used without duplicating or releasing it. This evaluation adds only a small Markdown file. No model, dataset, checkpoint, or runtime artifact was created.

## Limits

Evidence covers synthetic local loopback protocol mechanics only. It does not cover OpenCode runtime behavior or integration, a client/provider request, port 4000, or exact tokenizer agreement. The seam does not itself produce a provider response or guarantee how another process applies the response. Exact-token acceptance and E0 acceptance remain closed.
