# Phase 154: native low-memory environment profile

Date: 2026-09-20

## Change

The native launcher now sets lazy CUDA module loading and limits OpenBLAS,
OMP, MKL, and NumExpr pools to one thread. This targets the host-memory spike
observed during Windows Torch worker startup. The existing serial expert-load
and shared-tokenizer settings remain enabled.

## Verification

- Full repository regression: `146 passed, 14 warnings`.
- A direct FreeToken-environment Torch import failed with the default process
  environment due to OpenBLAS allocation retries.
- The same import succeeded with the new low-memory variables and reported
  `torch 2.11.0+cu130`.
- v58 structural validation: `PASS_STRUCTURAL_PACKAGE`, zero errors.
- v58 4M package route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`,
  `14.945 ms`, zero model calls.
- A real 64K-KV native probe parsed `expert_load=serial` and
  `num_tokenizer=0`, but both remaining workers still failed before model
  generation with Windows `WinError 1455` while loading `nvperf_host.dll` and
  `shm.dll`.

## Publication

The low-memory profile was synchronized to the public Hub package at revision
`0e9b16a70cff945eb9976079f6315e3bcf35963a`. Fresh Hub downloads confirmed the
launcher flags and runtime metadata.

## Boundary

The environment profile fixes single-process OpenBLAS import pressure but does
not overcome the current host's remaining Windows commit/pagefile shortage.
Native 2M/4M generation and retrieval quality still require a clean host or
independent 5060Ti run.
