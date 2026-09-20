# Phase 153: native serial expert-load profile

Date: 2026-09-20

## Change

The native launch profile now uses both FreeToken `--expert-load serial` and
`--num-tokenizer 0`. Serial loading avoids the parallel whole-shard host-memory
buffer; shared tokenization avoids an extra Torch worker.

## Verification

- Full repository regression: `146 passed, 14 warnings`.
- v57 structural package validation: `PASS_STRUCTURAL_PACKAGE`, zero errors.
- v57 4M mechanical route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`,
  `15.403 ms`, zero model calls.
- Real FreeToken probe on port `28204` parsed
  `expert_load=serial`, `num_tokenizer=0`, `num_token_override=65536`, and
  `max_seq_len_override=4000000`.
- The remaining scheduler and detokenizer workers both failed before model
  generation while loading `nvperf_host.dll` with Windows `WinError 1455`.

## Publication

The profile was synchronized to the public Hub package at revision
`b47ced8c6ccec42d24104418a29c6401f848a369`. Fresh Hub downloads confirmed the
launcher flag, README documentation, and runtime metadata.

## Boundary

Serial expert loading did not clear the current host's Windows commit/pagefile
failure, so native 2M/4M generation and retrieval quality remain unverified.
The package remains an experimental public artifact, not a production pass.
