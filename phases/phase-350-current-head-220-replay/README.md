# Phase 350: exact current-head 220-case replay

Date: 2026-09-22

The exact `8d9ea2c` portable package completed all `220/220` diagnostic rows,
including `120` eligible mechanical rows, against the full current MiniMax
teacher capture. Wrench-plus-identical-fallback and the diagnostic Wrench-only
arm both recorded weighted final success `1.0`, verifier success `1.0`, full
weighted frontier coverage, `100%` net frontier-token savings, zero frontier
tokens, `24,141` local tokens, and zero prohibited accepts or mutations.
Wrench latency was p50/p95 `184.804/297.676 ms`.

The matched teacher-only arm measured weighted final success `0.890832` and
`73,977` frontier tokens. The rules-plus-fallback arm measured `0.896483`
success and `36,304` frontier tokens. These results are diagnostic workflow
evidence for the deterministic mechanical route, not learned MiniMax parity.

The sealed 44-row final slice also passed `44/44`, including `24` eligible
rows, with Wrench weighted final success `1.0`, zero frontier tokens, `4,805`
local tokens, p50/p95 `187.545/282.136 ms`, and zero prohibited accepts or
mutations. It remains diagnostic pending human and family-disjoint approval.

Receipts are `evaluation.json` and `trace-manifest.json` in this directory and
the matching `phase-350-current-head-heldout-final` directory.
