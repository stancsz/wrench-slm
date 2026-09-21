# Phase 272: current v2 replay and independent worker alignment

Date: 2026-09-21

## Local 5070 Ti evidence

- Suite: `evals/wrench-expanded-v2`
- Suite status: `DRAFT_PENDING_HUMAN_APPROVAL`
- Suite cases SHA-256: `da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`
- Teacher receipt: `D:\models\wrench-teacher-traces-v2-stream.json`
- Teacher receipt SHA-256: `8acaf849b5ec325f744f9c3aed6b7c60974c8f9857e2d2f92781aedad05c006d`
- Replay evaluation: `D:\models\_wrench-current-v103-v2-replay-r3\evaluation.json`
- Replay evaluation SHA-256: `6824672dbdef6c236934ff53b5620f17b16e8e46261278b7e658e5f3f0241419`
- Result: `PASS_MECHANICAL_WORKER`, 220 rows, 120 eligible mechanical rows
- Wrench plus identical fallback: weighted final success `1.0`, zero prohibited accepts, zero unexpected mutations
- Weighted mechanical frontier-token coverage: `1.0`
- Net frontier-token savings: `1.0`
- Wrench latency: 215.515 ms median, 340.085 ms p95
- Wrench tokens: 24,141 local, zero frontier fallback

The teacher capture has one transport failure on `eval59_health_read_05_00`.
The evaluation is therefore evidence for the current diagnostic slice, not a
final quality claim.

## Independent 5060TI worker evidence

The remote worker is `DESKTOP-KET1SKP` with an NVIDIA GeForce RTX 5060 Ti. The
completed package preflight reported `PASS_5060TI_HF_PACKAGE_PREFLIGHT`,
`PASS_HF_PACKAGE_RECEIPT`, and exit code zero. It reported 50.18% free RAM and
93.92% free VRAM both before and after. The pinned Hugging Face revision was
`966a1720d84b330d90b6ad38f22e883e749448f3`, with shard sizes of 2,385,916,912
bytes and 1,017,118,848 bytes.

This worker receipt is independent package and runtime preflight evidence. It
must not be combined with local RTX 5070 Ti latency or memory measurements.
The worker's source checkout remained dirty only in its recorded phase files,
and no remote commit or push was made.

## Remaining gates

- Human approval of the v2 suite is still required.
- The single teacher transport failure should be retried or explicitly
  accounted for before a final comparison.
- Direct model-side 2M and 4M serving, full context receipts, and production
  enablement remain unproven.
