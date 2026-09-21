# Phase 242: direct Hugging Face 5060 Ti preflight

This queue item makes the worker download the compact current v97 NVFP4 Wrench
package directly from Hugging Face at a pinned revision. It validates the
package with the current source tools, runs the bounded mechanical smoke, and
records host RAM and VRAM reserve checks before and after download.

This is an independent package and runtime preflight. It does not claim
MiniMax parity, dense-native 4M attention quality, retrieval quality, or
production readiness. The Hugging Face revision is an experimental compact
v97 dense-native-gate package, not a completed quality or parity release.

The local package receipts `local-v97-validation.json` and
`local-v97-smoke.json` are development-host evidence only. The independent
RTX 5060 Ti result remains the verified receipt produced by the queued job.
