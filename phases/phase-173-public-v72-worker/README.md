# Phase 173: public v72 mechanical worker package

Date: 2026-09-20

## Release action

Materialized and uploaded the portable package containing the bounded repair
pass and bounded multi-file reference retrieval to
`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`.

- Hub revision: `4d7c12facdc59e1adf47b76b00fb767c08b97fbc`
- Structural validation: `PASS_STRUCTURAL_PACKAGE`
- Package-local two-file 2.9M-character route: accepted in 16.479 ms to
  18.795 ms, zero model calls, TTC passed, `applied: false`.
- Package-local prompt-complete 220-case replay: 220/220 outcome matches,
  120/120 exact eligible proposals, zero prohibited accepts, zero transport or
  runtime abstentions, 220 mechanical fast paths, zero model calls, 0.578 ms
  median, 28.323 ms p95.

## Fresh Hub verification

Runtime-only download from the exact Hub revision matched the local package:

```text
wrench_runtime/patching.py  5AFB996C03A0C0338F2B5CA465A4299E8080594AF214FA75B6FC57CED929845E
wrench_runtime/worker.py    3EA28C73CA79CA6DBC3B38BA25DA26E9DB661D86D58E419FC92E83C4E178CADF
wrench_runtime/ttc.py       6F721B46D821F4CE2564E445161FB3857B3AE7980E67350DEEA731E0CAAAE8EF
wrench_runtime/server.py    F624649B28777761DB9CDCC83CEE037F0EEC1B480AF8ED15550A3DAF1ED94A86
```

## Boundary

This public artifact is a fast mechanical worker package. It demonstrates
model-local 4M-style intake plus MapReduce and zero-model-call execution for
eligible contract cases. It does not claim dense native 4M attention, MiniMax
matched-workflow parity, or that the 90 percent coverage and 95 percent net
savings gates have passed.
