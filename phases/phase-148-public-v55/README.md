# Phase 148: public v55 native usage receipt

The public package server now preserves native backend `usage.prompt_tokens`
when the backend supplies it, alongside the direct or staged prefill receipt.

## Evidence

- structural package validation: `PASS_STRUCTURAL_PACKAGE`
- public Hub revision: `e0016ac291bb81401818ad2c8c68b099da39b5c9`
- updated file: `wrench_runtime/server.py`
- weights changed: no
- fresh Hub download SHA-256:
  `30EB00093018B32F498D08D07A772E3060A443A0CD29005EDD23C41C5AA3B9BE`

This improves native-context evidence quality. Clean-GPU native 2M/4M
generation and retrieval quality remain open.
