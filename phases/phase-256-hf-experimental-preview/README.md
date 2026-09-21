# Phase 256: Hugging Face Experimental Preview labeling

The authenticated Hugging Face account listing returned five model repositories
under `stancsz`. All five repository IDs already use the
`-Experimental-Preview` suffix. This phase refreshed each model card so that
the non-production status is explicit before the first visible model-card
content.

The warning says the model is for research and preview evaluation only, must not
be downloaded for production deployment or safety-critical workflows, and must
not be treated as production validation. Model weights and runtime files were
not changed.

The publication commits and verification receipt are recorded in
`publication-receipt.json`. This publication label does not authorize release
readiness, MiniMax parity, native dense decoder quality, or independent RTX
5060 Ti verification.
