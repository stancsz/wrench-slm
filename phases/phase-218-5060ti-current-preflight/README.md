# Phase 218: current-commit 5060Ti preflight job

The Drive queue contains an older pending preflight bound to source commit
`0d6546a`. This new manifest is bound to current source commit `31f85be` and
the pinned private BF16 artifact commit from `docs/MODEL_ARTIFACT_TRANSFER.md`.

It requests only read-only artifact hash verification and one bounded local
smoke on the RTX 5060 Ti. A successful job will prove cross-host artifact and
runtime integrity, not 220-case quality, MiniMax parity, or v88 NVFP4 serving.
Those claims require separate receipts.
