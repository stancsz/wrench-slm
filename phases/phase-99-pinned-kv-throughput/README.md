# Phase 99: pinned 4M KV geometry

This phase fixes the native serving geometry that was wasting VRAM in the
zero-full-layer long-context profile. Without an explicit capacity pin,
FreeToken's cache budget planner selected about `885,354,496` address pages for
the full-to-SWA mapping. The resulting setup allocated `8.69 GiB` for KV and
left effectively no free GPU memory for the NVFP4 expert path.

The launcher now passes `--num-tokens 4000000`, which preserves the 4M address
space while bounding the actual mapping to the declared capacity. With
`--moe-cache-auto`, the v25 experiment allocated `1.59 GiB` for the 4M KV
capacity and left `8.29 GiB` free after initialization.

## Matched native probes

- Unpinned 4M-capacity profile, direct 64K input: `65,470` actual prompt
  tokens, no truncation, HTTP 200, `77,205.615 ms`.
- Pinned 4M-capacity profile, direct 64K input: `65,471` actual prompt tokens,
  no truncation, HTTP 200, `23,449.596 ms`.
- Pinned profile, roughly 1K input: `972` actual prompt tokens, HTTP 200,
  `706.233 ms`.

The 64K native probe is about 3.3x faster after the geometry fix, but
`23.450 s` is still not a throughput pass. The fast 4M mechanical route remains
the practical path for eligible work while native generation is optimized.

The launcher fix is now in the public v27 package at Hub revision
`9dd2d4f4039ce0e0affa8d3f6fb1d153ac626f9f` (v28, with the same v27 launcher).
Remote hashes for `serve_freetoken.ps1`, `wrench-package.json`, and `README.md`
match the local v28 package.
