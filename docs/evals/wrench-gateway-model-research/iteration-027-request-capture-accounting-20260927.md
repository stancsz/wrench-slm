# Iteration 027: bounded request-byte receipt prototype

Date: 2026-09-27 (America/Edmonton)  
Status: fixture-only accountant implemented; OpenCode transport integration not done  
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Change

Added `src/wrench_harness/opencode_request_capture.py`, a pure bounded parser
and paired byte accountant for a future observation callback at OpenCode
2.0.15's final HTTP transport to the local SubRoute endpoint
`http://127.0.0.1:4000/v1/chat/completions`. It performs no I/O and is not
wired to OpenCode, the SubRoute proxy, or a provider.

For supplied raw request bytes, it records the exact body SHA-256 and length,
top-level raw-value byte lengths and SHA-256 values, message/role/tool counts,
the local route identity, and the requested model alias. It does not retain
prompt values, tool contents, request bodies, or headers. Known JSON field
names are allowlisted; unknown names are hashed before entering a receipt.
Whole-body and component hashes remain stable and linkable, so these receipts
are content-free but not anonymous.

The paired accountant includes all supplied retries/requests and reports
ratio-of-sums body-byte reduction. It rejects incomplete caller-marked pairs,
mixed model aliases, route or receipt identity mismatches, and duplicate
request IDs. It caps each body at 1 MiB, top-level fields at 64, episodes at
10,000, requests per aggregation at 2,048, and serialized receipt metadata at
32 MiB. Input-token reduction, task success, frontier-success retention, and
all-in cost reduction are returned as unavailable.

## Verification and review

The focused synthetic test file passed: 7 tests using
`PYTHONPATH=src python -B -m unittest discover -s tests -p test_opencode_request_capture.py`.
The cases cover exact body hashes and raw field slices, content-free receipts,
tool schemas, unknown-key redaction, wrong route/version/shape, duplicate JSON
keys, body limits, paired retries, zero-request episodes, alias mixing,
tampering, and incomplete/missing pairs. `git diff --check` passed. RAM was
11.98% free before the final focused run; no GPU work ran.

Independent review `WRENCH-REQUEST-CAPTURE-REVIEW-20260927-01` found mixed
aliases and unbounded episode aggregation; those were fixed. Review
`WRENCH-REQUEST-CAPTURE-REVIEW2-20260927-01` confirmed those fixes and found
caller-asserted completeness and untrusted field-name retention. Unknown field
names are now hashed, and request/metadata aggregate limits were added. The
remaining transport-completeness limitation is intentional and blocks using
this prototype as a complete task measurement. Final narrow source review
`WRENCH-REQUEST-CAPTURE-REVIEW3-20260927-01` passed the field-name and
aggregation-bound fixes, while explicitly retaining the fixture-only and
caller-asserted completeness limitations. The reviewed source hashes are:

- `src/wrench_harness/opencode_request_capture.py`:
  `32F024D46BB2A5AAB4CEFE9DD83746D21567389DD1AF2EAB2A022E3CA34EFD5D`
- `tests/test_opencode_request_capture.py`:
  `32D432A3DB059DD839082CD2B280236013944185DD868DDBBB43ADDB5B7C7D2B`

The metadata cap measures canonical receipt JSON bytes, not Python heap use.
Digests can identify repeated content and can leak guessed low-entropy values;
do not treat these receipts as anonymous.

## Evidence boundary

Passing fixtures prove only the parser and accountant's behavior on synthetic
bytes. The `capture_complete` flag is supplied by the caller, not established
by a transport observer. This code cannot detect a request or retry omitted by
its caller. It therefore does not prove capture completeness, live OpenCode
serialization, bytes sent on the active SubRoute, provider selection, provider
input tokens, billed cost, local task completion, or coding quality.

The next evidence step is a separately reviewed, no-provider integration at
the actual OpenCode post-lowering transport seam. That seam must observe every
request and retry, establish episode closure, bind the body and configured
route/model identities, and write bounded receipts. Until then, do not report
this prototype's byte ratios as real traffic savings. Do not infer token or
dollar savings from serialized bytes.

## Gates and storage

No model was selected or loaded; no inference, training, benchmark, SubRoute
generation, or provider spend occurred. The approved SubRoute endpoint remains
`127.0.0.1:4000`; there is no numeric aggregate spend cap, and this iteration
does not need a generation call. The staged 0.8B fit remains blocked by its
25% free-RAM start condition. This iteration's host samples stayed above the
10% general RAM/VRAM floor; the latest captured sample was 11.67% free RAM and
15,232 MiB free VRAM out of 16,311 MiB. No unrelated application was stopped.

The storage checker reported `WITHIN_LIMIT` before final report accounting.
Implementation reservation: `WRENCH-REQUEST-CAPTURE-IMPLEMENT-20260927-01`,
5,000,000 bytes. Final review reservation:
`WRENCH-REQUEST-CAPTURE-REVIEW3-20260927-01`, 100,000 bytes. Both were
released after the code, tests, and report were accounted for. The final
checker status after release is `WITHIN_LIMIT`, with more than 39 GB of
headroom under the 50 GB ceiling. Wrench-owned aggregate storage remains
subject to the 50,000,000,000-byte limit.
