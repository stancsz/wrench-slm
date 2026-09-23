# Phase 419: Direct-call attribution instrumentation

Date: 2026-09-22

## Result

Updated the paired-canary loopback accounting proxy to retain content-free
request shape, per-request timing, purpose classification, and client
attribution. Direct-client start and finish timestamps define the attribution
windows. A request receives a client only when exactly one window contains its
timestamp; overlapping, absent, or invalid windows produce `null` with an
explicit reason. Purpose receipts carry a versioned reason code. Unknown
purpose, incomplete client attribution, missing route/model identity, missing
request IDs or usage, or missing cost keeps `accounting_complete=false`.

Purpose classification is deliberately narrow. It labels only the two exact
source-confirmed OpenCode and DeepSeek Harness title markers as
`session_title_auxiliary`, records a versioned marker identifier, and leaves
all other purposes `unknown`. Request text is inspected in memory and is not
written into the capture. The persisted shape includes message count and
roles, tool-definition count, and tool-result presence. Phase 403 remains
unchanged and cannot be retroactively attributed.

## Advisor review

Sol was consulted through the requested local API at
`http://localhost:4000/v1`, model `codex-sol-advisor`. The recommendation was
to capture source-marker purpose and unique subprocess-window client identity,
leave other cases unknown, add local reordered-request and privacy tests, and
preserve historical receipts. Usage was 330 prompt tokens and 468 completion
tokens, 798 total. This changed the next implementation and test selection
(`decision_changed: true`). See [`advisor-receipt.json`](advisor-receipt.json).

## Verification and limits

- Focused paired-canary tests: `15/15` passed.
- Full repository regression: `261/261` passed with 18 existing deprecation
  warnings.
- Q4 contract validation: `VALID`.
- Python compilation and `git diff --check` passed. Git emitted only existing
  LF-to-CRLF working-copy notices.
- Probe SHA-256:
  `8843420476299fc4f4e62ec451496cf19f060c00c0392933d312200463fd7c9f`.
- Focused test file SHA-256:
  `74fbe02cfb8ca21e8aba941dc55cca7df3576830994673565571b7eda75c778f`.
- These identify the initial Phase 419 implementation snapshot. Phase 420
  extended the proxy for local-stub end-to-end capture; see its README for
  current source hashes.
- Local synthetic upstream only. No worker/provider request, spend, or package
  promotion occurred.
- The test verifies both title markers in reversed client order, near-match
  abstention, unique/overlapping/missing client windows, and absence of raw
  prompt or marker text in persisted capture data.
- This is instrumentation evidence, not a new paired workflow result. It does
  not complete provider-cost accounting, Gates C or D, or production readiness.

## Next decision

Phase 420 verified the source fingerprints and exercised the updated proxy
through the pinned clients against a deterministic local stub. Keep the
historical Phase 403 accounting incomplete and preserve `unknown` for
tool-bearing calls without task-purpose proof. Do not use the updated proxy
against a paid route while `monetary_budget` is zero. Any canary-based purpose
check must be separately bounded to ensure its marker does not appear in title
or follow-up calls.
