# Phase 453: bound read-lines resource use

Date: 2026-09-23

## Change

The `read_lines` verifier now streams only through the requested line range and
caps the cumulative file bytes it can read at `MAX_FILE_BYTES` (256 KiB). A
single requested line that exceeds the cap fails closed with
`file_size_limit`. Large files remain readable when the requested lines occur
near the beginning, without loading the rest of the file into memory. UTF-8
errors in the requested range retain the existing structured abstention.

## Verification

- `python -m pytest tests/test_harness.py -q`: 21 passed.
- Regression cases show a one-line request reads only that line from a file
  with more than 256 KiB of following content, oversized requested lines abstain, invalid
  UTF-8 abstains, and the existing path-containment and ordinary-range case
  still passes.

## Limits

This bounds the verifier's read and decoded working set for this action. It is
local fixture evidence, not a latency or production workload measurement. The
read-only client result still depends on the named client to execute and return
the proposed tool call; settlement provenance and delivery accounting remain
separate production gaps. Gates C, D, and E remain open.
