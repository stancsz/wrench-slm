# Phase 198: v80 bounded lookup evidence window

Date: 2026-09-20

## Change

The v79 retrieval route recovered a correct needle but still extracted and
regex-scanned an entire logical line. A 4M transcript serialized as one line
therefore paid a second full-payload pass. v80 keeps the raw payload intact,
uses bounded `find` ranges for the old/reference boundary, and parses only a
small window around the exact lookup needle.

The change is inside the bundled runtime's mechanical route. It does not add
model calls, mutation authority, or a gateway dependency.

## Receipt

The v80 package passed structural validation and `PASS_PACKAGE_RETRIEVAL_2M_4M`
on all six placements. The unique old-reference needle was placed at 1%, 50%,
and 99% of both 2M and 4M payloads. Every case recovered the exact path and
65,536-byte bound with zero model calls.

Across three repetitions, 18/18 retrieval cases passed:

- all-case median: `6.895 ms`;
- all-case p95: `16.063 ms`;
- worst observed case: `17.688 ms`;
- 4M 99% needle: `16.06 ms`, `15.28 ms`, `17.69 ms`.

The raw receipts are `package-validation.json`,
`package-retrieval-quality.json`, and `repetition-1.json` through
`repetition-3.json`.

## Boundary

This is strong deterministic package-local retrieval and latency evidence for
the hybrid raw-intake path. It is not dense-native attention quality, learned
MiniMax parity, or final production authorization.
