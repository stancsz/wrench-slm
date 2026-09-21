# Phase 278: 5060TI direct 4M and retrieval partial evidence

Date: 2026-09-21

## Evidence obtained

The connected remote host `DESKTOP-KET1SKP` performed real read-only commands
on an NVIDIA GeForce RTX 5060 Ti. The resource snapshot reported 15,049 MiB
free of 16,311 MiB VRAM and 16,587,184 KiB free of 33,486,624 KiB system RAM,
which preserved the required host reserve.

The remote package-local direct 4M probe completed successfully:

- package path: `C:\Users\stanc\models\wrench-5060-preflight-20260921\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-Experimental-Preview`
- raw payload: 31,997,963 characters
- elapsed time: 570.417 ms
- status: `PASS_MODEL_LOCAL_SERVER_4M`

The same remote package passed the six-case 2M/4M retrieval probe with model
calls equal to zero and status `PASS_PACKAGE_RETRIEVAL_2M_4M`.

Remote receipts were written outside the checkout under
`C:\Users\stanc\wrench-independent-verify-20260921` as
`direct-4m-receipt.json` and `retrieval-2m-4m-receipt.json`.

## Limits

This is not a current-source 5060TI benchmark. The remote `origin/main` was
reported as `aaf0c79`, while the current source under test is newer. The remote
package is also the earlier Experimental Preview package, not the current v103
package used by phases 276 and 277. The follow-up 220-case diagnostic produced
no receipt, no final nonce echo, and no complete result. Therefore this phase
does not claim current 5060TI 220-case quality, teacher parity, or production
readiness.

The result does establish that the 5060TI machine and its package-local
model-local 4M intake and retrieval path are executable while maintaining the
10% memory and VRAM reserve. A fresh worker dispatch must sync the latest
commit and produce a nonce-bound 220-case receipt before those claims can be
promoted.
