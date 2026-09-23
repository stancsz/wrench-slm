# Phase 461: hash exact native-upstream request bodies

Date: 2026-09-23

## Change

Each native-upstream attempt receipt now includes the SHA-256 of the exact
serialized request body passed to the transport. This includes failed
transport attempts, where the body is known even though provider processing
and usage are unknown. Retries retain separate attempt rows and hashes, so a
repair request can be distinguished from the initial request. Error traces
preserve these attempt receipts.

## Verification

- `python -m pytest tests/test_wrench_server.py -q`: 29 passed.
- `python -m pytest tests/test_paired_client_canary.py -q`: 58 passed.
- `ruff check src/wrench_harness/server.py tools/probe_paired_real_client_canary.py tests/test_wrench_server.py tests/test_paired_client_canary.py`: passed.
- `git diff --check`: passed; Git printed only existing LF-to-CRLF notices.
- A deterministic transport stub confirmed the recorded digest equals the
  bytes passed to transport. A loopback retry fixture confirmed each attempt
  digest matches its serialized body and that the repair body has a distinct
  digest.

## Limits

A locally computed request-body hash proves only which bytes the harness
prepared for a transport call. It does not prove that a provider received,
processed, or billed for those bytes. A hash does not establish response
authenticity, provider usage completeness, or final task correctness. No live
provider call or workflow replay was performed. Gates C, D, and E remain open.
