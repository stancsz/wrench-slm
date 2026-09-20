# Phase 176: public v73 cost-accounting package

Date: 2026-09-20

## Publication

The portable package containing model-local cost accounting was uploaded to
`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`.

- Hub revision: `db49ccc21b372ff91ace35bcbb69ccc1d5ee52d9`
- Structural package validation: `PASS_STRUCTURAL_PACKAGE`
- The package-local server returned a `wrench.cost-accounting-receipt.v1`
  with zero model prompt tokens and positive input tokens not sent to a model
  for a mechanical read.
- Fresh runtime-only download matched local hashes:

```text
wrench_runtime/server.py   36B1731C938DFC6822C97525B3DCB93D9A549FF2704C0DF5214C7EC8B48253DD
wrench_runtime/worker.py   3EA28C73CA79CA6DBC3B38BA25DA26E9DB661D86D58E419FC92E83C4E178CADF
wrench_runtime/patching.py 5AFB996C03A0C0338F2B5CA465A4299E8080594AF214FA75B6FC57CED929845E
wrench_runtime/ttc.py      6F721B46D821F4CE2564E445161FB3857B3AE7980E67350DEEA731E0CAAAE8EF
```

## Boundary

This makes token-flow measurement portable with the model directory. It does
not assign USD prices and does not close the matched MiniMax utility gates.
