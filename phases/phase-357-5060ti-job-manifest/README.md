# Phase 357: nonce-bound 5060TI verification job

Status: `PENDING_REMOTE_EXECUTION`

This phase creates, but does not upload or execute, a self-contained 5060TI
package-preflight job. It is the handoff artifact for the private worker queue
or a manually authenticated worker session. The manifest contains the full
source pin, Hub revision, case hash, nonce, exact command, 10 percent RAM and
VRAM reserves, no-mutation boundaries, and the required receipt fields.

Frozen pins:

- Job ID: `wrench-5060ti-current-package-preflight`
- Claim nonce: `f9d26378d81c43b7b010f1ffc799de70`
- Source commit: `a422353469869785ba5b0ab1f2366dd82706f8f6`
- Hub repo: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview`
- Hub revision: `9c6303c2c17a3798a134388c7e544728b22bd481`
- Canonical 220-case hash: `da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`
- Target: `DESKTOP-KET1SKP`, NVIDIA GeForce RTX 5060 Ti

The exact manifest is [job.json](job.json). It invokes the existing
`run_5060ti_hf_preflight.ps1` with `-JobId` and `-ClaimNonce`. The preflight
now binds those values and the actual Windows `COMPUTERNAME` into the receipt,
and the verifier fails closed on mismatch. Tests for the manifest and receipt
chain passed: `8 passed`.
The full repository regression then passed `202 passed, 0 failed, 18 warnings`.

This is not a 5060TI result. The remote execution surface still needs an
authenticated queue or worker session. No hardware, latency, memory, or
quality claim is made until the terminal receipt echoes the nonce and exact
pins.
