# Phase 197: v79 package retrieval-quality probe at 2M and 4M

Date: 2026-09-20

## Scope

This diagnostic exercised the bundled package worker directly with one
raw user message per case. Each payload contained a unique reference-only
needle, an old `path=src/wrench_harness/worker.py` anchor, and a newest
`CURRENT INTENT` suffix asking for that needle with a 65,536-byte read bound.
The anchor was placed at 1%, 50%, or 99% of the 2M or 4M payload.

No model weights were loaded and no model call was made. This isolates the
embedded deterministic MapReduce/retrieval path.

## Receipt

`PASS_PACKAGE_RETRIEVAL_2M_4M`, 6/6 cases:

- 2M payloads: all 3 placements recovered the exact path and byte limit;
- 4M payloads: all 3 placements recovered the exact path and byte limit;
- raw payload sizes: 16,749,966 and 33,499,966 characters;
- model calls: `0`;
- backend: `embedded-mechanical` for every case;
- elapsed range: `12.507 ms` to `473.255 ms`.

The complete hash-bound receipt is `package-retrieval-quality.json`.

## Interpretation

This proves useful retrieval from a monster raw payload at the package-local
worker boundary. It does not prove dense-native attention, learned MiniMax
parity, or final production quality. The 4M tail case is slower because the
current exact lookup scans linearly to the needle. The next performance step
is a reusable offset/index strategy that preserves the same hash-bound
correctness while avoiding repeated full-prefix scans.
