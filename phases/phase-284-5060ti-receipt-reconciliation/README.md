# Phase 284: RTX 5060 Ti receipt reconciliation

Date: 2026-09-21

Status: `PARTIAL_STALE_SOURCE_DIAGNOSTIC`

This phase reconciles the independent worker receipts already present outside
the repository. The worker was `DESKTOP-KET1SKP` with an NVIDIA GeForce RTX
5060 Ti. The receipts use the pinned Experimental Preview package at Hub
revision `966a1720d84b330d90b6ad38f22e883e749448f3` and the worker's isolated
`origin/main` export at source commit
`aaf0c79b5fcef5105531793eacfbece0dc0c338f`.

Evidence reconciled:

- `C:\Users\stanc\wrench-independent-verify-20260921\direct-4m-receipt.json`
  (`PASS_MODEL_LOCAL_SERVER_4M`, SHA-256
  `b7a2a451d1783c1843c3bc0a70b9dff58b0c35ca496ac6159bd1ce1592da8312`):
  nominal 4,000,000-token direct package intake, 3,999,995 estimated input
  tokens, HTTP 200, 570.417 ms, 9-token effective working context, one
  embedded mechanical proposal, and zero model calls.
- `C:\Users\stanc\wrench-independent-verify-20260921\retrieval-2m-4m-receipt.json`
  (`PASS_PACKAGE_RETRIEVAL_2M_4M`, SHA-256
  `e0f5026204021adaa9ba3eb43974423ad70c5e027388855a04ca0a523c45c79b`): six
  retrieval cases at 2M and 4M payload sizes with needles at 1%, 50%, and 99%;
  all passed with zero model calls.
- `C:\Users\stanc\wrench-independent-verify-20260921\v2\evaluation-rerun.json`
  (`DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`, SHA-256
  `dc8d27cbacc28108d2575c35d52a3e66b9660062c98a7e8035c0d856fbedb854`): 220
  requests, 200 outcome matches, 100 exact proposals, 100 exact eligible
  accepts out of 120 eligible rows, zero prohibited accepts, zero
  transport/runtime abstentions, zero model calls, 1.998 ms median latency,
  and 105.298 ms p95 latency.
- `C:\Users\stanc\wrench-origin-main-provenance-20260921-v2\audit-receipt.json`
  (`PASS_PROVENANCE_PACKAGE_ONLY_DIAGNOSTIC`, SHA-256
  `87f22e3e5e0c0e8c56391f6d12bc13e1b4aa27e27cdd1c2110a9e445caed044d`):
  confirms the RTX 5060 Ti identity, source export, canonical v2 case hash
  `da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`, and
  that the dirty worker checkout was not modified.

The host reserve requirement was met in the corresponding worker snapshots:
RAM stayed near 49% free and VRAM stayed above 91% free. No provider calls,
commits, pushes, resets, or mutations were reported.

This phase does not claim current-source verification, MiniMax parity,
production readiness, native dense-attention quality, or OpenCode execution.
The receipts do not carry a nonce field, and the worker source commit is older
than the current checkout at `52852a6817e445b43adb69253168948aa4c8b446`.
Therefore the strict acceptance criterion remains open until a fresh
authenticated 5060 Ti run evaluates the current commit and emits a
nonce-bound final receipt.
