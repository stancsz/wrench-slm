# Phase 150: native shared-tokenizer startup

Date: 2026-09-20

## Change

The portable FreeToken launcher now passes `--num-tokenizer 0`. FreeToken
shares tokenization with the detokenizer instead of starting an additional
Torch tokenizer worker. The launcher runtime profile records the choice so a
future package verifier can distinguish the low-memory startup profile.

The standalone native launcher uses the same option. The change is bounded to
startup process pressure and does not change the native attention or retrieval
claim.

## Verification

- `pytest -q tests/test_portable_package_materializer.py tests/test_package_manifest.py tests/test_wrench_server.py`
- Result: `12 passed`
- Generated-package check: one `--num-tokenizer` launcher switch, native
  argument array contains `"--num-tokenizer", 0`, and runtime metadata reports
  `tokenizer_processes: 0`.
- A fresh FreeToken probe on port `28203` parsed `num_tokenizer=0` and still
  failed before model generation in both remaining Torch workers with
  Windows `WinError 1455` while loading `cufft64_12.dll` and
  `nvperf_host.dll`.

## Boundary

This reduces one worker and is aligned with portable native startup, but the
current host still has insufficient commit/pagefile headroom for the two
remaining Torch workers. Native 2M/4M generation and retrieval quality remain
unverified. No unrelated process was terminated.
