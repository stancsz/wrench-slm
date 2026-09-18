# Phase 10: Qwen shadow proposal through the verifier

This phase connects the loaded local Qwen3.6 NVFP4 runtime to the Phase 9
execution boundary in shadow mode. The prompt requested one exact
`wrench.proposal.v1` JSON object for a bounded read. Qwen returned the exact
object, and the independent harness accepted it and returned the file
observation without changing the worktree.

The model server does not implement constrained JSON decoding, so the
`response_format=json_object` request was rejected by the runtime. The test
therefore relies on strict prompting followed by schema validation and
fail-closed execution. This is a single smoke interaction, not proposal
precision, task success, or production-readiness evidence.
