# Phase 356: 5060TI network and authentication boundary

Status: `UNVERIFIED_5060TI_AUTH_BOUNDARY`

This phase records a bounded read-only connectivity check after the Codex
remote-control project surface returned no usable current receipt. It does
not execute a benchmark and makes no independent 5060TI claim.

Observed on 2026-09-21 from the local Wrench workstation:

- `DESKTOP-KET1SKP.local` resolved to `10.0.0.4`.
- ICMP did not return a usable ping result.
- TCP port `22` was reachable.
- SSH with the default local identity was rejected with
  `Permission denied (publickey,password,keyboard-interactive)`.
- SSH with the repository's `wrench_worker_ed25519` identity was rejected
  with the same error.
- `Test-WSMan DESKTOP-KET1SKP` was unavailable.
- No remote command ran, so there is no host identity, GPU snapshot, RAM
  snapshot, source commit, artifact receipt, or benchmark output from this
  attempt.

The next authorized recovery path is to provision an explicit worker
authentication method or restore a saved Codex project/job-queue surface for
the 5060TI host. Until then, local 5070TI results and package-only receipts
remain separate from the required independent hardware evidence.
